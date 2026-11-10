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
from models import db, RFQQuotation, RFQItem, AdminNote, SystemSetting, CaseStudy, Article, RentalListing, RentalViewingBooking
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

            # If no rental listings, populate 6 authentic high-quality listings
            if RentalListing.query.count() == 0:
                r1 = RentalListing(
                    code='WOO-YK101',
                    title='南科新貴首選 ｜ 永康機能升級宅 ｜ 獨立露台採光套房',
                    category='suite',
                    district='永康區',
                    address_summary='台南市永康區中華路商圈 (近南科園區、奇美醫院)',
                    rent_price=13800,
                    management_fee=800,
                    deposit_months=2,
                    area_ping=12.5,
                    floor_info='3F / 5F',
                    layout='1房 1衛 1獨立景觀露台',
                    status='available',
                    cover_image='/static/images/original/b69b8c178e35c3f16221d53195f625c28.jpg',
                    gallery=json.dumps([
                        '/static/images/original/b69b8c178e35c3f16221d53195f625c28.jpg',
                        '/static/images/original/bd954293a7422fd744b19c0cd24376239.jpg',
                        '/static/images/original/be5236ed9c89f9637f229c4931044fe8b.jpg',
                        '/static/images/original/b6eee3cf4698cde4ffcd1fbf60ed5ccc0.jpg'
                    ], ensure_ascii=False),
                    features='獨立陽台,乾濕分離,獨立洗脫烘,智慧門禁密碼鎖,一級變頻冷暖,代收垃圾,可申請租金補貼',
                    description='全室全新日式侘寂與現代機能美學裝修。配置大面採光氣密窗、獨立洗脫烘滾筒洗衣機、瞬熱式儲熱水器，附高速光纖網路。近南科通勤 15 分鐘，生活機能極佳！',
                    traffic_surroundings='步行 3 分鐘至全聯、7-11，騎車 5 分鐘抵達大橋火車站，南科通勤便利。',
                    is_featured=True
                )

                r2 = RentalListing(
                    code='WOO-ES202',
                    title='東區老屋新生 ｜ 文化中心侘寂美透天 ｜ 整棟日光天井庭院宅',
                    category='townhouse',
                    district='東區',
                    address_summary='台南市東區崇德路商圈 (近台南文化中心、巴克禮公園)',
                    rent_price=48000,
                    management_fee=0,
                    deposit_months=2,
                    area_ping=56.0,
                    floor_info='整棟 1~3F',
                    layout='4房 2廳 3衛 1日光天井茶席 1露天庭院',
                    status='available',
                    cover_image='/static/images/original/b6694bcd77359edcec0766d1462a91c02.jpg',
                    gallery=json.dumps([
                        '/static/images/original/b6694bcd77359edcec0766d1462a91c02.jpg',
                        '/static/images/original/bf81634c6c30eb1fd6df99bb34fcd4641.jpg',
                        '/static/images/original/b664b3850084a32e25dda11913749fafc.jpg',
                        '/static/images/original/b57eccb9bfda2751aa3f9c72bb06b8d81.jpg'
                    ], ensure_ascii=False),
                    features='整棟透天,私有採光天井,日式侘寂茶席,全新水電管線,衛浴防水48H保固,可開伙,附平面車位',
                    description='40 年老宅經窩在家建築團隊結構補強與風格活化。保留老台南天井光影與經典磨石子地坪，注入現代極簡軟裝。極適合追求生活美學之外商主管、設計建築團隊或自住家庭。',
                    traffic_surroundings='鄰近文化中心、崇德黃昏市場，步行可達市立醫院與德安商圈，靜巷清幽不吵雜。',
                    is_featured=True
                )

                r3 = RentalListing(
                    code='WOO-ES303',
                    title='東區林森路商圈 ｜ 綠憩景觀家庭宅 ｜ 24H物業保全景觀3房',
                    category='apartment',
                    district='東區',
                    address_summary='台南市東區林森路二段 (近成功大學、南紡購物中心)',
                    rent_price=32000,
                    management_fee=2400,
                    deposit_months=2,
                    area_ping=38.0,
                    floor_info='9F / 14F',
                    layout='3房 2廳 2衛 2景觀陽台',
                    status='available',
                    cover_image='/static/images/original/bc854558e56f8590a1fa540c083fdcba9.jpg',
                    gallery=json.dumps([
                        '/static/images/original/bc854558e56f8590a1fa540c083fdcba9.jpg',
                        '/static/images/original/bd0220ee78bfb2d77252bd14be0fcde41.jpg',
                        '/static/images/original/b83485bea10e9f346148c79c2178f1afb.jpg'
                    ], ensure_ascii=False),
                    features='24H物業保全,子母車垃圾集中,平面汽車位,乾濕分離,超大客餐廳,可開伙,可寵物友善',
                    description='東區核心地段景觀電梯大樓，高樓層通風採光極佳。客廳開闊大面落地窗，全室配備日立變頻冷暖空調與林內三口瓦斯爐，適合南科高階家庭或成大公教人員。',
                    traffic_surroundings='車程 3 分鐘抵達南紡購物中心、成大校區，下樓即是林森路綠園道，機能無懈可擊。',
                    is_featured=True
                )

                r4 = RentalListing(
                    code='WOO-CW404',
                    title='中西區文創慢活 ｜ 國華神農生活圈 ｜ 日光挑高設計一房一廳',
                    category='apartment',
                    district='中西區',
                    address_summary='台南市中西區中正路商圈 (近神農街、國華街商圈)',
                    rent_price=18500,
                    management_fee=1000,
                    deposit_months=2,
                    area_ping=18.0,
                    floor_info='2F / 4F',
                    layout='1房 1廳 1衛 1開放式中島廚房',
                    status='available',
                    cover_image='/static/images/original/bad4aea4a3454db46874dc931a96bf1bb.jpg',
                    gallery=json.dumps([
                        '/static/images/original/bad4aea4a3454db46874dc931a96bf1bb.jpg',
                        '/static/images/original/b14a3b522cd675ff4d257390eef0c2104.jpg',
                        '/static/images/original/b708bb1991d4afcabde7b376254c10056.jpg'
                    ], ensure_ascii=False),
                    features='開放式中島廚房,可開伙,微型客廳,智慧電子鎖,變頻冷暖,近文創美食商圈,台南漫步首選',
                    description='步入古都心臟地帶，挑高 3 米 2 現代日式小公寓。配備實木餐飲中島吧台、全套烘碗洗滌廚具與乾濕分離明亮衛浴，享受台南最道地的慢活時光。',
                    traffic_surroundings='下樓步行 3 分鐘到國華街美食聚落，海安商圈散步即達，假日生活精彩豐富。',
                    is_featured=False
                )

                r5 = RentalListing(
                    code='WOO-SH505',
                    title='善化南科LM特區 ｜ 台積工程師首選 ｜ 北歐簡約飯店式陽台套房',
                    category='suite',
                    district='善化區',
                    address_summary='台南市善化區蓮潭北路 (LM特區核心、近善化火車站)',
                    rent_price=14500,
                    management_fee=600,
                    deposit_months=2,
                    area_ping=11.5,
                    floor_info='4F / 6F',
                    layout='1房 1衛 1景觀獨立陽台',
                    status='available',
                    cover_image='/static/images/original/b6eee3cf4698cde4ffcd1fbf60ed5ccc0.jpg',
                    gallery=json.dumps([
                        '/static/images/original/b6eee3cf4698cde4ffcd1fbf60ed5ccc0.jpg',
                        '/static/images/original/bffb07e17f69ae1a798860ee39e840549.jpg',
                        '/static/images/original/bdf689d5b1cc740f907da4c021d920db4.jpg'
                    ], ensure_ascii=False),
                    features='電梯大樓,機車專屬室內車位,子母車垃圾集中,代收包裹,獨立洗衣機,南科園區通勤5分',
                    description='LM 特區全新景觀住宅。飯店式感應磁卡進出、垃圾專人清理，配備降噪雙層氣密窗與五星級獨立筒乳膠床墊，專為南科高壓工程師打造的極致好眠宅。',
                    traffic_surroundings='騎車 5 分鐘抵達台積電晶圓廠區、善化火車站，生活機能純住宅高綠覆。',
                    is_featured=True
                )

                r6 = RentalListing(
                    code='WOO-NO606',
                    title='北區鄭子寮重劃區 ｜ 公園首排 ｜ 輕奢簡約2房景觀電梯宅',
                    category='apartment',
                    district='北區',
                    address_summary='台南市北區文成路 (近花園夜市、小北商圈)',
                    rent_price=26000,
                    management_fee=1800,
                    deposit_months=2,
                    area_ping=26.5,
                    floor_info='7F / 12F',
                    layout='2房 1廳 1衛 1獨立曬衣陽台',
                    status='available',
                    cover_image='/static/images/original/b0258c0719a0aaef27ae724f64e6edb39.jpg',
                    gallery=json.dumps([
                        '/static/images/original/b0258c0719a0aaef27ae724f64e6edb39.jpg',
                        '/static/images/original/bde807cc872a5d658e6b1c47f4d79e083.jpg',
                        '/static/images/original/b73a38e2161ab4b013e247e35d99eb50a.jpg'
                    ], ensure_ascii=False),
                    features='24H物業保全,健身房交誼廳,室內專屬機車位,乾濕分離日式浴缸,可開伙,全套系統收納櫃',
                    description='北區高級住宅聚落鄭子寮，綠意環繞棟距開闊。格局方正樑柱外推，衛浴開窗配備日式深型浴缸與暖風機，採光滿分。',
                    traffic_surroundings='步行 5 分鐘到文元國小與千坪公園，車程 3 分鐘到小北觀光夜市與星巴克。',
                    is_featured=False
                )

                db.session.add_all([r1, r2, r3, r4, r5, r6])

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

@app.route('/rentals')
def rentals():
    district = request.args.get('district', '')
    category = request.args.get('category', '')
    max_price = request.args.get('max_price', type=int)
    
    query = RentalListing.query
    if district:
        query = query.filter_by(district=district)
    if category:
        query = query.filter_by(category=category)
    if max_price:
        query = query.filter(RentalListing.rent_price <= max_price)
        
    listings = query.order_by(RentalListing.is_featured.desc(), RentalListing.id.desc()).all()
    return render_hybrid(
        'rentals.html',
        {'listings': listings, 'current_district': district, 'current_category': category, 'current_max_price': max_price},
        '精選招租 ｜ 窩在好宅 ｜ 台南南科套房、家庭宅、質感透天出租 ｜ 窩在家'
    )

@app.route('/rentals/<identifier>')
def rental_detail(identifier):
    if identifier.isdigit():
        listing = RentalListing.query.get_or_404(int(identifier))
    else:
        listing = RentalListing.query.filter_by(code=identifier).first_or_404()
    return render_hybrid(
        'rental_detail.html',
        {'listing': listing},
        f'{listing.title} ｜ 窩在家精選招租'
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

@app.route('/api/rentals')
def api_rentals():
    listings = RentalListing.query.order_by(RentalListing.is_featured.desc(), RentalListing.id.desc()).all()
    return jsonify([l.to_dict() for l in listings])

@app.route('/api/rentals/booking', methods=['POST'])
def api_rental_booking():
    data = request.get_json() or request.form
    renter_name = (data.get('renter_name') or '').strip()
    renter_phone = (data.get('renter_phone') or '').strip()
    if not renter_name or not renter_phone:
        return jsonify({'success': False, 'message': '請填寫姓名與聯絡電話！'}), 400

    rental_id = data.get('rental_id')
    rental = RentalListing.query.get(rental_id) if rental_id else None

    booking = RentalViewingBooking(
        rental_id=rental.id if rental else None,
        rental_code=rental.code if rental else data.get('rental_code'),
        rental_title=rental.title if rental else data.get('rental_title'),
        renter_name=renter_name,
        renter_phone=renter_phone,
        renter_line_id=data.get('renter_line_id'),
        preferred_datetime=data.get('preferred_datetime'),
        renter_occupation=data.get('renter_occupation'),
        notes=data.get('notes'),
        status='pending'
    )
    db.session.add(booking)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'預約帶看成功！窩在家房務管家將於 24 小時內以電話或 LINE 確認看屋時段。',
        'booking_id': booking.id
    })

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
        'signed': RFQQuotation.query.filter_by(status='signed').count(),
        'rental_bookings': RentalViewingBooking.query.count(),
        'available_rentals': RentalListing.query.filter_by(status='available').count()
    }

    # Fetch recent rental bookings and listings
    bookings = RentalViewingBooking.query.order_by(RentalViewingBooking.created_at.desc()).limit(20).all()
    rentals = RentalListing.query.order_by(RentalListing.id.desc()).all()

    return render_template(
        'admin/dashboard.html',
        rfqs=rfqs,
        stats=stats,
        search_query=search_q,
        status_filter=status_filter,
        bookings=bookings,
        rentals=rentals
    )

@app.route('/admin/booking/<int:booking_id>/status', methods=['POST'])
@login_required
def admin_booking_status(booking_id):
    booking = RentalViewingBooking.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    if new_status:
        booking.status = new_status
        db.session.commit()
    return redirect(url_for('admin_dashboard') + '#bookings-tab')

@app.route('/admin/rental/<int:rental_id>/toggle-status', methods=['POST'])
@login_required
def admin_rental_toggle_status(rental_id):
    rental = RentalListing.query.get_or_404(rental_id)
    if rental.status == 'available':
        rental.status = 'rented'
    else:
        rental.status = 'available'
    db.session.commit()
    return redirect(url_for('admin_dashboard') + '#rentals-tab')

@app.route('/admin/rentals')
@login_required
def admin_rentals():
    rentals = RentalListing.query.order_by(RentalListing.id.desc()).all()
    bookings = RentalViewingBooking.query.order_by(RentalViewingBooking.created_at.desc()).all()
    active_count = RentalListing.query.filter_by(status='available').count()
    rented_count = RentalListing.query.filter_by(status='rented').count()
    pending_bookings = RentalViewingBooking.query.filter_by(status='pending').count()

    return render_template(
        'admin/rentals.html',
        rentals=rentals,
        bookings=bookings,
        active_count=active_count,
        rented_count=rented_count,
        pending_bookings=pending_bookings
    )

@app.route('/admin/rentals/add', methods=['POST'])
@login_required
def admin_rentals_add():
    code = request.form.get('code', '').strip()
    title = request.form.get('title', '').strip()
    rent_price = int(request.form.get('rent_price', 0))
    if not code or not title or not rent_price:
        return redirect(url_for('admin_rentals'))

    cover_img = request.form.get('cover_image', '').strip() or '/static/images/original/b69b8c178e35c3f16221d53195f625c28.jpg'
    new_rental = RentalListing(
        code=code,
        title=title,
        district=request.form.get('district', '永康區'),
        category=request.form.get('category', 'suite'),
        rent_price=rent_price,
        management_fee=int(request.form.get('management_fee') or 0),
        area_ping=float(request.form.get('area_ping') or 12.0),
        floor_info=request.form.get('floor_info', '3F/5F'),
        layout=request.form.get('layout', '1房1衛'),
        address_summary=request.form.get('address_summary', ''),
        cover_image=cover_img,
        gallery=json.dumps([cover_img]),
        features=request.form.get('features', '獨立陽台,乾濕分離,洗脫烘,變頻冷暖'),
        description=request.form.get('description', ''),
        traffic_surroundings=request.form.get('traffic_surroundings', ''),
        status='available'
    )
    db.session.add(new_rental)
    db.session.commit()
    return redirect(url_for('admin_rentals'))

@app.route('/admin/rentals/edit/<int:rental_id>', methods=['POST'])
@login_required
def admin_rentals_edit(rental_id):
    rental = RentalListing.query.get_or_404(rental_id)
    rental.code = request.form.get('code', rental.code).strip()
    rental.title = request.form.get('title', rental.title).strip()
    rental.district = request.form.get('district', rental.district)
    rental.category = request.form.get('category', rental.category)
    rental.rent_price = int(request.form.get('rent_price') or rental.rent_price)
    rental.management_fee = int(request.form.get('management_fee') or rental.management_fee)
    rental.area_ping = float(request.form.get('area_ping') or rental.area_ping)
    rental.floor_info = request.form.get('floor_info', rental.floor_info)
    rental.layout = request.form.get('layout', rental.layout)
    rental.address_summary = request.form.get('address_summary', rental.address_summary)
    
    cover_image = request.form.get('cover_image', '').strip()
    if cover_image:
        rental.cover_image = cover_image
        gallery = json.loads(rental.gallery) if rental.gallery else []
        if cover_image not in gallery:
            gallery.insert(0, cover_image)
        rental.gallery = json.dumps(gallery)
        
    rental.features = request.form.get('features', rental.features)
    rental.description = request.form.get('description', rental.description)
    rental.traffic_surroundings = request.form.get('traffic_surroundings', rental.traffic_surroundings)
    status_val = request.form.get('status')
    if status_val in ['available', 'reserved', 'rented']:
        rental.status = status_val

    db.session.commit()
    return redirect(url_for('admin_rentals'))

@app.route('/admin/rentals/status/<int:rental_id>', methods=['POST'])
@login_required
def admin_rentals_update_status(rental_id):
    rental = RentalListing.query.get_or_404(rental_id)
    new_status = request.form.get('status')
    if new_status in ['available', 'reserved', 'rented']:
        rental.status = new_status
        db.session.commit()
    return redirect(url_for('admin_rentals'))

@app.route('/admin/rentals/delete/<int:rental_id>', methods=['POST'])
@login_required
def admin_rentals_delete(rental_id):
    rental = RentalListing.query.get_or_404(rental_id)
    db.session.delete(rental)
    db.session.commit()
    return redirect(url_for('admin_rentals'))

@app.route('/admin/bookings/status/<int:booking_id>', methods=['POST'])
@login_required
def admin_bookings_update_status(booking_id):
    booking = RentalViewingBooking.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    if new_status:
        booking.status = new_status
        db.session.commit()
    return redirect(url_for('admin_rentals'))

@app.route('/admin/bookings/delete/<int:booking_id>', methods=['POST'])
@login_required
def admin_bookings_delete(booking_id):
    booking = RentalViewingBooking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    return redirect(url_for('admin_rentals'))

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
