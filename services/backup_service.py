import os
import json
import base64
import time
import threading
import requests
from datetime import datetime
from config import Config
from models import RFQQuotation, RFQItem, AdminNote, SystemSetting

def serialize_database_snapshot() -> dict:
    """Serializes all RFQ orders, items, notes, and settings into portable JSON"""
    rfqs = RFQQuotation.query.all()
    rfq_list = []
    for r in rfqs:
        d = r.to_dict()
        d['items'] = [{'code': i.service_code, 'title': i.service_title, 'specs': i.get_specs_dict(), 'price': i.estimated_price} for i in r.items]
        d['notes'] = [{'author': n.author, 'content': n.content, 'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S')} for n in r.notes]
        rfq_list.append(d)

    settings = {s.key: s.value for s in SystemSetting.query.all()}

    return {
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'total_rfqs': len(rfq_list),
        'rfqs': rfq_list,
        'settings': settings
    }

def backup_to_github() -> dict:
    """
    Exports data snapshot to GitHub cloud-backup branch via GitHub REST API.
    Uses commit message with [skip ci] to prevent infinite build loops.
    """
    token = SystemSetting.get_val('github_token', Config.GITHUB_TOKEN)
    repo = SystemSetting.get_val('github_repo', Config.GITHUB_REPO)
    branch = SystemSetting.get_val('github_branch', Config.GITHUB_BACKUP_BRANCH)

    if not token or not repo:
        return {'status': 'skipped', 'message': 'GitHub Token 或 Repository 未設定，略過自動備份'}

    try:
        snapshot = serialize_database_snapshot()
        content_json = json.dumps(snapshot, ensure_ascii=False, indent=2)
        encoded_content = base64.b64encode(content_json.encode('utf-8')).decode('utf-8')

        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Wooinhome-Backup-Service'
        }

        # 1. Check if file already exists in cloud-backup branch to get its SHA
        file_path = "backups/rfq_backup_latest.json"
        api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
        
        get_res = requests.get(api_url, headers=headers, timeout=10)
        sha = None
        if get_res.status_code == 200:
            sha = get_res.json().get('sha')

        # 2. Put file to branch
        put_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        commit_msg = f"Automated cloud data backup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [skip ci]"
        payload = {
            'message': commit_msg,
            'content': encoded_content,
            'branch': branch
        }
        if sha:
            payload['sha'] = sha

        put_res = requests.put(put_url, headers=headers, json=payload, timeout=15)
        if put_res.status_code in [200, 201]:
            print(f"[Backup Success] Pushed backup to GitHub {repo}@{branch} [skip ci]")
            SystemSetting.set_val('last_cloud_backup_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            return {'status': 'success', 'commit': put_res.json().get('commit', {}).get('sha', '')}
        else:
            print(f"[Backup Failed] HTTP {put_res.status_code}: {put_res.text}")
            return {'status': 'error', 'message': f"GitHub API 回應 {put_res.status_code}: {put_res.text[:100]}"}
    except Exception as e:
        print(f"[Backup Exception] {e}")
        return {'status': 'error', 'message': str(e)}

def restore_from_github(db) -> dict:
    """Restores database from GitHub cloud-backup branch if local DB is newly created or empty"""
    token = SystemSetting.get_val('github_token', Config.GITHUB_TOKEN)
    repo = SystemSetting.get_val('github_repo', Config.GITHUB_REPO)
    branch = SystemSetting.get_val('github_branch', Config.GITHUB_BACKUP_BRANCH)

    if not token or not repo:
        return {'status': 'skipped', 'message': '未配置 GitHub 備份參數'}

    try:
        file_path = "backups/rfq_backup_latest.json"
        api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Wooinhome-Restore-Service'
        }
        res = requests.get(api_url, headers=headers, timeout=10)
        if res.status_code != 200:
            return {'status': 'not_found', 'message': '雲端尚未有備份檔案'}

        content_b64 = res.json().get('content', '')
        decoded_json = base64.b64decode(content_b64).decode('utf-8')
        snapshot = json.loads(decoded_json)

        # Restore records if DB has no RFQ items
        if RFQQuotation.query.count() == 0:
            for item in snapshot.get('rfqs', []):
                new_rfq = RFQQuotation(
                    rfq_number=item['rfq_number'],
                    customer_name=item['customer_name'],
                    gender=item.get('gender', '先生'),
                    phone=item['phone'],
                    email=item.get('email'),
                    line_id=item.get('line_id'),
                    preferred_contact_time=item.get('preferred_contact_time', '全天皆可'),
                    city=item.get('city', '台南市'),
                    district=item.get('district'),
                    address=item.get('address'),
                    property_type=item.get('property_type', '整棟透天'),
                    size_ping=item.get('size_ping', 30.0),
                    room_count=item.get('room_count', 3),
                    current_status=item.get('current_status', '空屋閒置中'),
                    requirements=item.get('requirements'),
                    estimated_monthly_rent=item.get('estimated_monthly_rent', 0),
                    renovation_budget=item.get('renovation_budget', 0),
                    expected_roi=item.get('expected_roi', 0.0),
                    attachment_filename=item.get('attachment_filename'),
                    attachment_orig_name=item.get('attachment_orig_name'),
                    status=item.get('status', 'pending')
                )
                db.session.add(new_rfq)
                db.session.flush()

                for sub in item.get('items', []):
                    db.session.add(RFQItem(
                        rfq_id=new_rfq.id,
                        service_code=sub.get('code', 'custom'),
                        service_title=sub.get('title', '客製服務'),
                        specs=json.dumps(sub.get('specs', {})),
                        estimated_price=sub.get('price', '專人估價')
                    ))
            db.session.commit()
            print(f"[Restore Success] Restored {len(snapshot.get('rfqs', []))} RFQ records from GitHub cloud backup!")
            return {'status': 'success', 'restored_count': len(snapshot.get('rfqs', []))}
        return {'status': 'skipped', 'message': '本地資料庫已有資料，未執行覆蓋'}
    except Exception as e:
        print(f"[Restore Error] {e}")
        return {'status': 'error', 'message': str(e)}

def start_keep_alive_worker():
    """Starts background thread to ping /api/health periodically, preventing cloud platform spin-down"""
    def worker():
        while True:
            time.sleep(Config.KEEP_ALIVE_INTERVAL)
            url = Config.KEEP_ALIVE_URL or "http://127.0.0.1:5000/api/health"
            try:
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    pass # Keep-Alive successful
            except Exception:
                pass

    t = threading.Thread(target=worker, daemon=True)
    t.start()

