import os
import json
from app import app, db
from models import CaseStudy, Article

with open('data/wooinhome_crawled_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with app.app_context():
    # 1. Clear placeholder cases and insert real ones
    CaseStudy.query.delete()

    # Case 1: 永康機能升級宅
    c1_imgs = data['cases'][0]['images'] if len(data['cases']) > 0 else []
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
    c2_imgs = data['cases'][1]['images'] if len(data['cases']) > 1 else []
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
    c3_imgs = data['cases'][2]['images'] if len(data['cases']) > 2 else []
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

    # 2. Clear placeholder articles and insert all 8 real articles
    Article.query.delete()

    for idx, art_data in enumerate(data['articles'], 1):
        cover_img = art_data['images'][0] if art_data['images'] else '/static/images/hero_living_cozy.jpg'
        new_art = Article(
            slug=art_data['slug'],
            title=art_data['title'],
            cover_image=cover_img,
            category='法規與稅務' if '稅' in art_data['title'] or '法規' in art_data['title'] else '包租代管實務',
            author='窩在家資產管理團隊',
            date_published=art_data['date'] or '2026-03-01',
            read_time='5 分鐘閱讀',
            summary=art_data['summary'],
            content=art_data['content'],
            tags='台南包租代管,房東稅務,合法收租,老屋翻新'
        )
        db.session.add(new_art)

    db.session.commit()
    print("Database populated with authentic cases and articles successfully!")
