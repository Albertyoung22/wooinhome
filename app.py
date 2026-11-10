import os
import io
import csv
import json
import time
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file, Response

from config import Config
from models import db, RFQQuotation, RFQItem, AdminNote, SystemSetting, CaseStudy, Article
from services.tts_service import generate_speech
from services.email_service import send_rfq_notifications_async, test_smtp_connection
from services.backup_service import backup_to_github, restore_from_github, start_keep_alive_worker
from services.ai_agent_service import get_ai_response

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload and audio cache directories exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.AUDIO_CACHE_FOLDER, exist_ok=True)
os.makedirs(Config.DATA_FOLDER, exist_ok=True)

db.init_app(app)

APP_START_TIME = time.time()

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def is_spa_request() -> bool:
    return request.headers.get('X-Requested-With') == 'SPA'

def render_hybrid(template_name: str, context: dict, title: str):
    """Renders full HTML for SSR or JSON {html, title} for SPA requests"""
    context['page_title'] = title
    if is_spa_request():
        # Render the template, then return JSON
        full_html = render_template(template_name, **context)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(full_html, 'html.parser')
        main_content = soup.find('main', id='spa-main-content')
        html_payload = str(main_content) if main_content else full_html
        return jsonify({
            'html': html_payload,
            'title': title
        })
    return render_template(template_name, **context)

def seed_initial_data():
    """Initializes rich authentic seed data from wooinhome_crawled_data.json or defaults"""
    crawled_file = os.path.join(app.root_path, 'data', 'wooinhome_crawled_data.json')
    if os.path.exists(crawled_file):
        try:
            with open(crawled_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # If no cases or placeholder cases, populate authentic cases
            if CaseStudy.query.count() == 0 or CaseStudy.query.filter_by(slug='park-rd-townhouse').first() is not None:
                CaseStudy.query.delete()
                
                # Case 1: 永康機能升級宅
                c1_imgs = data['cases'][0]['images'] if len(data.get('cases', [])) > 0 else []
                c1 = CaseStudy(
                    slug='yongkang-upgrade',
                    title='永康機能升級宅 ｜ 空間重構與高質感美學租賃',
                    category='suite',
                    location='台南市永康區 (近科技園區)',
                    area_ping=48.0,
                    before_rent=16000,
                    after_rent=39000,
                    roi_boost='+143%',
                    vacancy_rate='0% (完工即滿租)',
                    tags='永康區,機能升級,獨立套房,科技菁英',
                    image_before=c1_imgs[0] if len(c1_imgs) > 0 else '/static/images/case_townhouse.jpg',
                    image_after=c1_imgs[1] if len(c1_imgs) > 1 else '/static/images/hero_living_cozy.jpg',
                    gallery=json.dumps(c1_imgs, ensure_ascii=False),
                    summary='針對南科與科技菁英租客需求，將原本格局破碎的老舊空間重新調整動線，導入模組化收納系統與日式乾濕分離衛浴，提升出租坪效。',
                    highlights='全室配置一級節能變頻冷暖空調、獨立洗脫烘滾筒洗衣機與智慧門禁密碼鎖，完工一週內即全數滿租。'
                )

                # Case 2: 東區老屋新生宅
                c2_imgs = data['cases'][1]['images'] if len(data.get('cases', [])) > 1 else []
                c2 = CaseStudy(
                    slug='east-rebirth',
                    title='東區老屋新生宅 ｜ 40年透天老宅 侘寂風格改造',
                    category='townhouse',
                    location='台南市東區 (近文化中心)',
                    area_ping=56.0,
                    before_rent=18000,
                    after_rent=52000,
                    roi_boost='+188%',
                    vacancy_rate='100% 穩定託管中',
                    tags='東區,老屋新生,整棟透天,日式侘寂',
                    image_before=c2_imgs[0] if len(c2_imgs) > 0 else '/static/images/case_townhouse.jpg',
                    image_after=c2_imgs[1] if len(c2_imgs) > 1 else '/static/images/hero_living_cozy.jpg',
                    gallery=json.dumps(c2_imgs, ensure_ascii=False),
                    summary='40年台南傳統磨石子老透天，經窩在家工程團隊水電全室換新、加強結構防水試水48小時，保留老宅採光天井並注入現代極簡軟裝。',
                    highlights='分層獨立規劃，每層均具備開闊陽台與優雅茶席空間，兼具住宅質感與極高租金抗跌性。'
                )

                # Case 3: 東區租屋優化宅
                c3_imgs = data['cases'][2]['images'] if len(data.get('cases', [])) > 2 else []
                c3 = CaseStudy(
                    slug='east-rental-optimized',
                    title='東區租屋優化宅 ｜ 大樓家庭宅 精準代租代管',
                    category='apartment',
                    location='台南市東區 (林森路商圈)',
                    area_ping=38.0,
                    before_rent=24000,
                    after_rent=36000,
                    roi_boost='+50%',
                    vacancy_rate='外商主管長期簽約',
                    tags='東區大樓,代租代管,家庭住宅,外商主管',
                    image_before=c3_imgs[0] if len(c3_imgs) > 0 else '/static/images/case_apartment.jpg',
                    image_after=c3_imgs[1] if len(c3_imgs) > 1 else '/static/images/case_commercial.jpg',
                    gallery=json.dumps(c3_imgs, ensure_ascii=False),
                    summary='屋主長住台北無暇往返帶看，委託窩在家代租代管。運用 4 道嚴格徵信程序，迅速媒合南科外商高階主管簽訂 3 年長期租約。',
                    highlights='每月提供數位化對帳單，日常水電修繕由專屬管家即時抵達排除，屋主真正實現零負擔收租。'
                )

                db.session.add_all([c1, c2, c3])

            # If no articles or placeholder articles, populate all 8 authentic articles
            if Article.query.count() < len(data.get('articles', [])):
                Article.query.delete()
                for art_data in data.get('articles', []):
                    cover_img = art_data['images'][0] if art_data.get('images') else '/static/images/hero_living_cozy.jpg'
                    new_art = Article(
                        slug=art_data['slug'],
                        title=art_data['title'],
                        cover_image=cover_img,
                        category='法規與稅務' if '稅' in art_data['title'] or '法規' in art_data['title'] else '包租代管實務',
                        author='窩在家資產管理團隊',
                        date_published=art_data.get('date') or '2026-03-01',
                        read_time='5 分鐘閱讀',
                        summary=art_data.get('summary', ''),
                        content=art_data.get('content', ''),
                        tags='台南包租代管,房東稅務,合法收租,老屋翻新'
                    )
                    db.session.add(new_art)

            db.session.commit()
            return
        except Exception as e:
            print(f"[Seed Authentic Data Warning] {e}")

    # Fallback default seed if json not present
    if CaseStudy.query.count() == 0:
        c1 = CaseStudy(
            slug='yongkang-upgrade',
            title='永康機能升級宅 ｜ 空間重構與高質感美學租賃',
            category='suite',
            location='台南市永康區 (近科技園區)',
            area_ping=48.0,
            before_rent=16000,
            after_rent=39000,
            roi_boost='+143%',
            vacancy_rate='0% (完工即滿租)',
            tags='永康區,機能升級,獨立套房,科技菁英',
            image_before='/static/images/case_townhouse.jpg',
            image_after='/static/images/hero_living_cozy.jpg',
            summary='針對南科與科技菁英租客需求，將原本格局破碎的老舊空間重新調整動線，導入模組化收納系統與日式乾濕分離衛浴，提升出租坪效。',
            highlights='全室配置一級節能變頻冷暖空調、獨立洗脫烘滾筒洗衣機與智慧門禁密碼鎖，完工一週內即全數滿租。'
        )
        db.session.add(c1)
        db.session.commit()

# Application startup initialization
with app.app_context():
    try:
        db.create_all()
        # Ensure migration columns exist
        import sqlite3
        conn = db.engine.raw_connection()
        cur = conn.cursor()
        try:
            cur.execute("ALTER TABLE case_studies ADD COLUMN gallery TEXT")
        except Exception:
            pass
        try:
            cur.execute("ALTER TABLE articles ADD COLUMN cover_image VARCHAR(255)")
        except Exception:
            pass
        conn.commit()
    except Exception as e:
        if "already exists" in str(e).lower():
            pass
        else:
            print(f"[DB Init Notice] {e}")

    try:
        seed_initial_data()
    except Exception as e:
        db.session.rollback()
        print(f"[Seed Notice] {e}")

    # Attempt to restore from cloud backup if available
    try:
        restore_from_github(db)
    except Exception as e:
        print(f"[Startup Restore Notice] {e}")

# Start Keep-Alive Background Worker
try:
    start_keep_alive_worker()
except Exception as e:
    print(f"[KeepAlive Notice] {e}")


# ==============================================================================
# Public Website Routes (SSR + SPA Hybrid)
# ==============================================================================

@app.route('/')
def index():
    cases = CaseStudy.query.limit(3).all()
    return render_hybrid(
        'index.html',
        {'cases': cases},
        '台南包租代管公司【窩在家包租代管】專業包租代管與空間活化一站式服務'
    )

@app.route('/manage-host')
def manage_host():
    return render_hybrid(
        'manage_host.html',
        {},
        '台南包租代管 ｜ 窩在家 3~5 年保證固定租金 ｜ 零空置風險'
    )

@app.route('/manage-agent')
def manage_agent():
    return render_hybrid(
        'manage_agent.html',
        {},
        '台南代租代管 ｜ 窩在家 4 重嚴格房客徵信 ｜ 掌握市場最高租金'
    )

@app.route('/spatial-renovation')
def spatial_renovation():
    return render_hybrid(
        'spatial_renovation.html',
        {},
        '老屋空間活化 ｜ 日式侘寂美學與老宅翻新改造 ｜ 租金翻倍躍升'
    )

@app.route('/works')
def works():
    cases = CaseStudy.query.all()
    return render_hybrid(
        'works.html',
        {'cases': cases},
        '實績案例展示庫 ｜ 台南透天、公寓、套房空間活化精選 ｜ 窩在家'
    )

@app.route('/calculator')
def calculator():
    return render_hybrid(
        'calculator.html',
        {},
        '空間活化與租金收益增值試算機 ｜ 投報率與租稅優惠模擬'
    )

@app.route('/blog')
def blog():
    articles = Article.query.order_by(Article.id.desc()).all()
    return render_hybrid(
        'blog.html',
        {'articles': articles},
        '物業管理與法規專欄 ｜ 房東三大法定租稅優惠解析 ｜ 窩在家'
    )

@app.route('/faq')
def faq():
    return render_hybrid(
        'faq.html',
        {},
        '常見問題 Q&A 知識庫 ｜ 包租代管、契約公證與修繕責任說明'
    )

@app.route('/contact')
def contact():
    return render_hybrid(
        'contact.html',
        {},
        '線上智慧詢價單 (RFQ) ｜ 預約專人到府勘查屋況 ｜ 窩在家'
    )

@app.route('/privacy')
def privacy():
    return render_hybrid('faq.html', {}, '隱私權保護政策 ｜ 窩在家包租代管')

@app.route('/terms')
def terms():
    return render_hybrid('faq.html', {}, '服務條款與公證細則 ｜ 窩在家包租代管')


# ==============================================================================
# Dynamic Core API Endpoints
# ==============================================================================

@app.route('/api/tts/generate', methods=['POST'])
def api_tts_generate():
    """Generates speech using edge-tts with local disk caching"""
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    lang = data.get('lang', 'zh-TW')

    if not text:
        return jsonify({'error': '文字內容不可為空'}), 400

    try:
        result = generate_speech(text, lang=lang)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/chat', methods=['POST'])
def api_ai_chat():
    """AI Customer Service Assistant with comprehensive knowledge base"""
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    lang = data.get('lang', 'zh-TW')

    reply = get_ai_response(query, lang=lang)
    return jsonify({
        'reply': reply,
        'timestamp': datetime.now().strftime('%H:%M')
    })

@app.route('/api/rfq/submit', methods=['POST'])
def api_rfq_submit():
    """Handles online RFQ submission with cart items and optional file upload"""
    try:
        customer_name = request.form.get('customer_name', '').strip()
        phone = request.form.get('phone', '').strip()

        if not customer_name or not phone:
            return jsonify({'status': 'error', 'message': '請填寫必填欄位：姓名與聯絡電話'}), 400

        # Generate unique RFQ number: RFQ-YYYYMMDD-XXXX
        today_str = datetime.now().strftime('%Y%m%d')
        random_suffix = uuid.uuid4().hex[:4].upper()
        rfq_number = f"RFQ-{today_str}-{random_suffix}"

        # Handle attachment upload safely
        attachment_filename = None
        attachment_orig_name = None
        attachment_full_path = None

        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename and allowed_file(file.filename):
                orig_name = secure_filename(file.filename)
                ext = orig_name.rsplit('.', 1)[1].lower() if '.' in orig_name else 'jpg'
                saved_name = f"{rfq_number}_{uuid.uuid4().hex[:6]}.{ext}"
                save_path = os.path.join(Config.UPLOAD_FOLDER, saved_name)
                file.save(save_path)
                attachment_filename = saved_name
                attachment_orig_name = orig_name
                attachment_full_path = save_path

        # Create RFQ Database Record
        new_rfq = RFQQuotation(
            rfq_number=rfq_number,
            customer_name=customer_name,
            gender=request.form.get('gender', '先生'),
            phone=phone,
            email=request.form.get('email', '').strip(),
            line_id=request.form.get('line_id', '').strip(),
            preferred_contact_time=request.form.get('preferred_contact_time', '全天時段皆可'),
            city=request.form.get('city', '台南市'),
            district=request.form.get('district', '').strip(),
            address=request.form.get('address', '').strip(),
            property_type=request.form.get('property_type', '整棟透天厝'),
            size_ping=float(request.form.get('size_ping', 30.0) or 30.0),
            current_status=request.form.get('current_status', '空屋閒置中'),
            requirements=request.form.get('requirements', '').strip(),
            attachment_filename=attachment_filename,
            attachment_orig_name=attachment_orig_name,
            status='pending'
        )

        db.session.add(new_rfq)
        db.session.flush()

        # Parse RFQ Cart Items JSON
        cart_items_json = request.form.get('cart_items', '[]')
        try:
            cart_items = json.loads(cart_items_json)
        except Exception:
            cart_items = []

        item_objects = []
        for item in cart_items:
            rfq_item = RFQItem(
                rfq_id=new_rfq.id,
                service_code=item.get('code', 'custom'),
                service_title=item.get('title', '客製諮詢項目'),
                specs=json.dumps(item.get('specs', {}), ensure_ascii=False),
                estimated_price=item.get('price', '專人估價')
            )
            db.session.add(rfq_item)
            item_objects.append({
                'title': rfq_item.service_title,
                'specs_summary': ", ".join([f"{k}: {v}" for k, v in item.get('specs', {}).items()]),
                'price': rfq_item.estimated_price
            })

        db.session.commit()

        # Trigger Async Email Notification to Admin & Confirmation to Customer
        rfq_dict = new_rfq.to_dict()
        send_rfq_notifications_async(
            rfq_dict=rfq_dict,
            items=item_objects,
            attachment_path=attachment_full_path,
            orig_filename=attachment_orig_name,
            app=app
        )

        # Trigger background cloud backup sync to GitHub (if configured)
        def trigger_auto_backup():
            with app.app_context():
                try:
                    backup_to_github()
                except Exception as e:
                    print(f"[Auto Backup Notice] {e}")

        import threading
        threading.Thread(target=trigger_auto_backup, daemon=True).start()

        return jsonify({
            'status': 'success',
            'rfq_number': rfq_number,
            'message': '詢價單已成功提交，專人將儘速與您聯繫！'
        })

    except Exception as e:
        db.session.rollback()
        print(f"[RFQ Submit Error] {e}")
        return jsonify({'status': 'error', 'message': f'提交失敗: {str(e)}'}), 500

@app.route('/api/health')
def api_health():
    """Health check & Keep-Alive endpoint for Render/uptime monitoring"""
    db_status = 'ok'
    rfq_count = 0
    try:
        rfq_count = RFQQuotation.query.count()
    except Exception as e:
        db_status = f'error: {str(e)}'

    uptime_seconds = int(time.time() - APP_START_TIME)

    return jsonify({
        'status': 'healthy' if db_status == 'ok' else 'degraded',
        'db': db_status,
        'uptime_seconds': uptime_seconds,
        'total_rfqs': rfq_count,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'version': '2.0.0-enterprise'
    })


# ==============================================================================
# Admin CRM Routes (Protected by HMAC / Session)
# ==============================================================================

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Check against Config credentials
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            error = '帳號或密碼錯誤，請重新輸入'

    return render_template('admin/login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    search_q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = RFQQuotation.query

    if search_q:
        like_pattern = f"%{search_q}%"
        query = query.filter(
            (RFQQuotation.customer_name.ilike(like_pattern)) |
            (RFQQuotation.phone.ilike(like_pattern)) |
            (RFQQuotation.rfq_number.ilike(like_pattern)) |
            (RFQQuotation.line_id.ilike(like_pattern))
        )

    if status_filter:
        query = query.filter(RFQQuotation.status == status_filter)

    rfqs = query.order_by(RFQQuotation.created_at.desc()).all()

    # Calculate statistics
    stats = {
        'total': RFQQuotation.query.count(),
        'pending': RFQQuotation.query.filter_by(status='pending').count(),
        'contacting': RFQQuotation.query.filter_by(status='contacting').count(),
        'signed': RFQQuotation.query.filter_by(status='signed').count()
    }

    return render_template(
        'admin/dashboard.html',
        rfqs=rfqs,
        stats=stats,
        search_query=search_q,
        status_filter=status_filter
    )

@app.route('/admin/rfq/<int:rfq_id>')
@login_required
def admin_rfq_detail(rfq_id):
    rfq = RFQQuotation.query.get_or_404(rfq_id)
    return render_template('admin/rfq_detail.html', rfq=rfq)

@app.route('/admin/rfq/<int:rfq_id>/status', methods=['POST'])
@login_required
def admin_update_rfq_status(rfq_id):
    rfq = RFQQuotation.query.get_or_404(rfq_id)
    new_status = request.form.get('status', 'pending')
    rfq.status = new_status
    db.session.commit()
    return redirect(url_for('admin_rfq_detail', rfq_id=rfq.id))

@app.route('/admin/rfq/<int:rfq_id>/add-note', methods=['POST'])
@login_required
def admin_add_rfq_note(rfq_id):
    rfq = RFQQuotation.query.get_or_404(rfq_id)
    note_content = request.form.get('note', '').strip()
    if note_content:
        new_note = AdminNote(
            rfq_id=rfq.id,
            author=session.get('admin_username', '管理員'),
            content=note_content
        )
        db.session.add(new_note)
        db.session.commit()
    return redirect(url_for('admin_rfq_detail', rfq_id=rfq.id))

@app.route('/admin/export-csv')
@login_required
def admin_export_csv():
    """Exports all RFQs to UTF-8 BOM CSV compatible with Microsoft Excel"""
    rfqs = RFQQuotation.query.order_by(RFQQuotation.created_at.desc()).all()

    output = io.StringIO()
    # Write UTF-8 BOM for Excel Chinese support
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow([
        '詢價單號', '客戶姓名', '稱謂', '聯絡電話', 'Email', 'LINE ID',
        '便利聯絡時段', '縣市', '行政區', '概略地址', '物業型態', '坪數',
        '現況', '狀態', '附言需求', '隨附檔案名稱', '項目數量', '建立時間'
    ])

    for r in rfqs:
        writer.writerow([
            r.rfq_number,
            r.customer_name,
            r.gender,
            r.phone,
            r.email or '',
            r.line_id or '',
            r.preferred_contact_time,
            r.city,
            r.district or '',
            r.address or '',
            r.property_type,
            r.size_ping,
            r.current_status,
            r.status,
            r.requirements or '',
            r.attachment_orig_name or '',
            len(r.items),
            r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
        ])

    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)

    filename = f"wooinhome_rfq_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/admin/settings', methods=['GET'])
@login_required
def admin_settings():
    msg = request.args.get('msg')
    return render_template(
        'admin/settings.html',
        msg=msg,
        github_token=SystemSetting.get_val('github_token', Config.GITHUB_TOKEN),
        github_repo=SystemSetting.get_val('github_repo', Config.GITHUB_REPO),
        github_branch=SystemSetting.get_val('github_branch', Config.GITHUB_BACKUP_BRANCH),
        last_backup_time=SystemSetting.get_val('last_cloud_backup_time', ''),
        smtp_server=SystemSetting.get_val('smtp_server', Config.SMTP_SERVER),
        smtp_port=SystemSetting.get_val('smtp_port', str(Config.SMTP_PORT)),
        smtp_user=SystemSetting.get_val('smtp_user', Config.SMTP_USER),
        smtp_pass=SystemSetting.get_val('smtp_pass', Config.SMTP_PASS),
        admin_email=SystemSetting.get_val('admin_email', Config.ADMIN_EMAIL),
        keep_alive_url=SystemSetting.get_val('keep_alive_url', Config.KEEP_ALIVE_URL)
    )

@app.route('/admin/settings/github', methods=['POST'])
@login_required
def admin_save_github_settings():
    SystemSetting.set_val('github_token', request.form.get('github_token', '').strip())
    SystemSetting.set_val('github_repo', request.form.get('github_repo', '').strip())
    SystemSetting.set_val('github_branch', request.form.get('github_branch', 'cloud-backup').strip())
    return redirect(url_for('admin_settings', msg='GitHub 雲端備份參數已更新儲存！'))

@app.route('/admin/settings/smtp', methods=['POST'])
@login_required
def admin_save_smtp_settings():
    SystemSetting.set_val('smtp_server', request.form.get('smtp_server', 'smtp.gmail.com').strip())
    SystemSetting.set_val('smtp_port', request.form.get('smtp_port', '587').strip())
    SystemSetting.set_val('smtp_user', request.form.get('smtp_user', '').strip())
    SystemSetting.set_val('smtp_pass', request.form.get('smtp_pass', '').strip())
    SystemSetting.set_val('admin_email', request.form.get('admin_email', '').strip())
    return redirect(url_for('admin_settings', msg='SMTP 郵件通知設定已更新儲存！'))

@app.route('/admin/settings/keepalive', methods=['POST'])
@login_required
def admin_save_keepalive_settings():
    SystemSetting.set_val('keep_alive_url', request.form.get('keep_alive_url', '').strip())
    return redirect(url_for('admin_settings', msg='防休眠網址已更新儲存！'))

@app.route('/api/admin/trigger-backup', methods=['POST'])
@login_required
def api_admin_trigger_backup():
    result = backup_to_github()
    return jsonify(result)

@app.route('/api/admin/test-smtp', methods=['POST'])
@login_required
def api_admin_test_smtp():
    server = SystemSetting.get_val('smtp_server', Config.SMTP_SERVER)
    port = int(SystemSetting.get_val('smtp_port', str(Config.SMTP_PORT)))
    user = SystemSetting.get_val('smtp_user', Config.SMTP_USER)
    password = SystemSetting.get_val('smtp_pass', Config.SMTP_PASS)

    success, msg = test_smtp_connection(server, port, user, password)
    return jsonify({'success': success, 'message': msg})


# ==============================================================================
# SEO: Robots.txt & Dynamic Sitemap.xml
# ==============================================================================

@app.route('/favicon.ico')
def favicon():
    return send_file(os.path.join(app.root_path, 'static', 'favicon.ico'), mimetype='image/vnd.microsoft.icon')

@app.route('/robots.txt')
def robots_txt():
    content = "User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: " + request.url_root.rstrip('/') + "/sitemap.xml\n"
    return Response(content, mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap_xml():
    base = request.url_root.rstrip('/')
    pages = [
        ('/', '1.0', 'daily'),
        ('/manage-host', '0.9', 'weekly'),
        ('/manage-agent', '0.9', 'weekly'),
        ('/spatial-renovation', '0.9', 'weekly'),
        ('/works', '0.8', 'weekly'),
        ('/calculator', '0.8', 'monthly'),
        ('/blog', '0.8', 'weekly'),
        ('/faq', '0.7', 'monthly'),
        ('/contact', '0.9', 'daily')
    ]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p, pri, freq in pages:
        xml.append(f'  <url><loc>{base}{p}</loc><changefreq>{freq}</changefreq><priority>{pri}</priority></url>')
    xml.append('</urlset>')
    return Response("\n".join(xml), mimetype='application/xml')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
