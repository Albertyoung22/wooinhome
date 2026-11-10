import smtplib
import threading
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import Config
from models import SystemSetting

def get_smtp_config():
    """Retrieve SMTP settings from Database or fallback to Config"""
    try:
        server = SystemSetting.get_val('smtp_server', Config.SMTP_SERVER)
        port = int(SystemSetting.get_val('smtp_port', str(Config.SMTP_PORT)))
        user = SystemSetting.get_val('smtp_user', Config.SMTP_USER)
        password = SystemSetting.get_val('smtp_pass', Config.SMTP_PASS)
        admin_email = SystemSetting.get_val('admin_email', Config.ADMIN_EMAIL)
        enabled = SystemSetting.get_val('email_notifications_enabled', 'true').lower() == 'true'
        return {
            'server': server,
            'port': port,
            'user': user,
            'password': password,
            'admin_email': admin_email,
            'enabled': enabled
        }
    except Exception as e:
        print(f"[SMTP Config Error] {e}")
        return {
            'server': Config.SMTP_SERVER,
            'port': Config.SMTP_PORT,
            'user': Config.SMTP_USER,
            'password': Config.SMTP_PASS,
            'admin_email': Config.ADMIN_EMAIL,
            'enabled': False
        }

def _send_email_sync(to_email: str, subject: str, html_body: str, attachment_path: str = None, orig_filename: str = None):
    cfg = get_smtp_config()
    if not cfg['enabled'] or not cfg['user'] or not cfg['password']:
        print(f"[Email Skipped] SMTP not fully configured or notifications disabled. Recipient: {to_email}")
        return False

    msg = MIMEMultipart('alternative')
    msg['From'] = f"窩在家包租代管 <{cfg['user']}>"
    msg['To'] = to_email
    msg['Subject'] = subject

    part = MIMEText(html_body, 'html', 'utf-8')
    msg.attach(part)

    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, 'rb') as f:
                mime_part = MIMEBase('application', 'octet-stream')
                mime_part.set_payload(f.read())
            encoders.encode_base64(mime_part)
            fname = orig_filename or os.path.basename(attachment_path)
            mime_part.add_header('Content-Disposition', f'attachment; filename="{fname}"')
            msg.attach(mime_part)
        except Exception as e:
            print(f"[Email Attachment Error] {e}")

    try:
        with smtplib.SMTP(cfg['server'], cfg['port'], timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(cfg['user'], cfg['password'])
            server.sendmail(cfg['user'], [to_email], msg.as_string())
        print(f"[Email Success] Sent email to {to_email} ({subject})")
        return True
    except Exception as e:
        print(f"[Email Failed] Error sending to {to_email}: {e}")
        return False

def send_rfq_notifications_async(rfq_dict: dict, items: list, attachment_path: str = None, orig_filename: str = None, app = None):
    """Triggers background thread to deliver admin alert and customer confirmation"""
    def worker():
        if app:
            ctx = app.app_context()
            ctx.push()
        try:
            cfg = get_smtp_config()
            # 1. Admin Email
            admin_subject = f"【新詢價單通知】單號 #{rfq_dict.get('rfq_number')} - {rfq_dict.get('customer_name')} 貴賓"
            items_html = "".join([f"<li><strong>{item.get('title')}</strong> - {item.get('specs_summary')}</li>" for item in items])
            
            admin_html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e0dbd3; border-radius: 12px; background-color: #faf9f6;">
                <div style="background-color: #2b2823; padding: 18px 24px; border-radius: 8px; text-align: center;">
                    <h2 style="color: #d6b27e; margin: 0; font-size: 20px; letter-spacing: 2px;">窩在家物業資產管理 ｜ 新進詢價委託通知</h2>
                </div>
                <div style="padding: 20px 0; color: #333333; line-height: 1.6;">
                    <p style="font-size: 15px;">親愛的業務團隊主管，您好：</p>
                    <p>官網甫收到一筆全新客戶詢價與託管評估需求，詳細資訊如下：</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 14px;">
                        <tr style="background: #edeae4;"><th style="padding: 10px; border: 1px solid #ddd; text-align: left; width: 35%;">詢價單號</th><td style="padding: 10px; border: 1px solid #ddd;"><strong>{rfq_dict.get('rfq_number')}</strong></td></tr>
                        <tr><th style="padding: 10px; border: 1px solid #ddd; text-align: left;">客戶姓名</th><td style="padding: 10px; border: 1px solid #ddd;">{rfq_dict.get('customer_name')} {rfq_dict.get('gender')}</td></tr>
                        <tr style="background: #edeae4;"><th style="padding: 10px; border: 1px solid #ddd; text-align: left;">聯絡電話</th><td style="padding: 10px; border: 1px solid #ddd;"><a href="tel:{rfq_dict.get('phone')}" style="color: #9f7944; font-weight: bold;">{rfq_dict.get('phone')}</a></td></tr>
                        <tr><th style="padding: 10px; border: 1px solid #ddd; text-align: left;">LINE ID</th><td style="padding: 10px; border: 1px solid #ddd;">{rfq_dict.get('line_id') or '無提供'}</td></tr>
                        <tr style="background: #edeae4;"><th style="padding: 10px; border: 1px solid #ddd; text-align: left;">便利通話時段</th><td style="padding: 10px; border: 1px solid #ddd;">{rfq_dict.get('preferred_contact_time')}</td></tr>
                        <tr><th style="padding: 10px; border: 1px solid #ddd; text-align: left;">物業位置</th><td style="padding: 10px; border: 1px solid #ddd;">{rfq_dict.get('city')} {rfq_dict.get('district')} {rfq_dict.get('address')}</td></tr>
                        <tr style="background: #edeae4;"><th style="padding: 10px; border: 1px solid #ddd; text-align: left;">物業格局/坪數</th><td style="padding: 10px; border: 1px solid #ddd;">{rfq_dict.get('property_type')} ｜ {rfq_dict.get('size_ping')} 坪 ｜ {rfq_dict.get('room_count')} 房</td></tr>
                        <tr><th style="padding: 10px; border: 1px solid #ddd; text-align: left;">預估試算效益</th><td style="padding: 10px; border: 1px solid #ddd; color: #9f7944; font-weight: bold;">預估月租 NT${rfq_dict.get('estimated_monthly_rent', 0):,} ｜ 預估年化 ROI {rfq_dict.get('expected_roi', 0)}%</td></tr>
                    </table>

                    <h4 style="color: #2b2823; margin-top: 20px;">委託與詢價項目：</h4>
                    <ul>{items_html if items_html else '<li>一般資產委託諮詢</li>'}</ul>

                    <h4 style="color: #2b2823; margin-top: 15px;">客戶備註需求：</h4>
                    <div style="background: #f1eee9; padding: 12px; border-radius: 6px; font-style: italic;">{rfq_dict.get('requirements') or '無特別附言'}</div>
                </div>
                <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #888;">
                    窩在家包租代管 CRM 系統自動發送 ｜ 台南市中西區公園路56號1樓 ｜ (06) 289-4168
                </div>
            </div>
            """
            _send_email_sync(cfg['admin_email'], admin_subject, admin_html, attachment_path, orig_filename)

            # 2. Customer Confirmation Email
            cust_email = rfq_dict.get('email')
            if cust_email and '@' in cust_email:
                cust_subject = f"【窩在家包租代管】已收到您的物業託管詢價需求 (單號: #{rfq_dict.get('rfq_number')})"
                cust_html = f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e0dbd3; border-radius: 12px; background-color: #faf9f6;">
                    <div style="background-color: #2b2823; padding: 18px 24px; border-radius: 8px; text-align: center;">
                        <h2 style="color: #d6b27e; margin: 0; font-size: 20px; letter-spacing: 2px;">WOO IN HOME 窩在家包租代管</h2>
                    </div>
                    <div style="padding: 20px 0; color: #333333; line-height: 1.6;">
                        <p style="font-size: 15px;">親愛的 <strong>{rfq_dict.get('customer_name')} {rfq_dict.get('gender')}</strong>，您好：</p>
                        <p>感謝您對「窩在家包租代管」的信任與支持！我們已成功接收您的物業諮詢與估價委託需求，專屬服務單號為：<strong style="color: #9f7944;">#{rfq_dict.get('rfq_number')}</strong>。</p>
                        <p>我們的專業物業顧問團隊將於您勾選的方便時段（<strong>{rfq_dict.get('preferred_contact_time')}</strong>）儘速以電話或 LINE 與您聯繫，為您進行屋況深度剖析與包租代管/裝修改造效益規劃。</p>
                        <div style="background: #f4f1eb; border-left: 4px solid #9f7944; padding: 12px 16px; margin: 20px 0; border-radius: 0 6px 6px 0;">
                            <p style="margin: 0; font-weight: bold; color: #2b2823;">若有任何即時問題，歡迎直接與我們真人顧問聯繫：</p>
                            <p style="margin: 5px 0 0 0; font-size: 14px;">專線電話：<strong>(06) 289-4168</strong> ｜ LINE 官方帳號：<strong>@wooinhome</strong></p>
                        </div>
                    </div>
                    <div style="text-align: center; border-top: 1px solid #eee; padding-top: 15px; font-size: 12px; color: #888;">
                        窩在家物業管理顧問有限公司 ｜ 臺南市中西區公園路56號1樓
                    </div>
                </div>
                """
                _send_email_sync(cust_email, cust_subject, cust_html)
        finally:
            if app:
                ctx.pop()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

def test_smtp_connection(server, port, user, password) -> tuple[bool, str]:
    try:
        with smtplib.SMTP(server, port, timeout=10) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(user, password)
        return True, "SMTP 連線與帳號密碼驗證成功！"
    except Exception as e:
        return False, f"連線失敗: {str(e)}"
