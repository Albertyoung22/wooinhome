import re

KNOWLEDGE_BASE = {
    'tax': {
        'keywords': ['稅', '報稅', '減稅', '房屋稅', '地價稅', '所得稅', '免稅', '稅率', 'tax', '税金', '세금'],
        'reply_zh': """【窩在家包租代管 房東專屬租稅優惠說明】
委託窩在家合法包租代管，房東可享有政府法定三重租稅減免：
1. **綜合所得稅免稅額**：每屋每月租金收入最高享有 1.5 萬元免稅額度，超過部分更可扣除 60% 必要費用（一般自租僅可扣除 43%）。
2. **房屋稅優惠**：由一般出租非自住稅率（最高達 4.8%）大幅降為「自用住宅稅率 1.2%」！
3. **地價稅優惠**：由一般千分之十累進稅率，適用自用住宅千分之二優惠稅率！
讓您合法收租兼顧節稅，省下的稅金直接轉換為淨投報率。建議直接填寫線上評估表，由稅務專員為您精算！""",
        'reply_en': """[WOO IN HOME Tax Relief Guide for Property Owners]
Partnering with our certified property management service grants owners three major statutory tax incentives in Taiwan:
1. Income Tax Deduction: Up to NT$15,000 monthly rental income is exempt; remaining portion enjoys a 60% standard expense deduction.
2. House Tax Reduction: Lowered to owner-occupied rate of 1.2% (vs up to 4.8% for standard rentals).
3. Land Value Tax: Reduced to preferential 0.2% rate!
Contact our advisors for a personalized tax optimization report.""",
        'reply_ja': """【窩在家（WOO IN HOME）オーナー様向け税制優遇のご案内】
公認プロパティマネジメントに委託することで、以下の3大税制優遇が適用されます：
1. 所得税控除：月額家賃1.5万NTDまで非課税、超過分も60%の経費控除。
2. 家屋税軽減：一般賃貸税率（最大4.8%）から自己居住優遇税率（1.2%）へ大幅軽減。
3. 地価税優遇：特別優遇税率0.2%が適用可能！""",
        'reply_ko': """[WOO IN HOME 임대인 절세 혜택 안내]
정부 공인 주택임대관리 위탁 시 다음 세제 혜택을 받으실 수 있습니다:
1. 소득세 공제: 월 임대료 최대 15,000 NTD 비과세 및 초과분 60% 경비 공제.
2. 재산세(가옥세) 감면: 일반 임대세율(최대 4.8%)에서 자가 주거용 1.2% 우대세율 적용.
3. 지가세 우대세율 0.2% 적용!"""
    },
    'difference': {
        'keywords': ['差別', '差異', '比較', '包租', '代管', '哪個好', 'difference', 'compare', '違い', '차이'],
        'reply_zh': """【包租代管 vs. 代租代管 該怎麼選？】
🏢 **1. 包租代管 (Manage Host) —「零空置期、穩定淨收」首選**
• 模式：由窩在家與您簽訂 3~5 年包租約，每月固定給付穩定租金給房東，房客是否退租由窩在家全權承擔空置與欠租風險。
• 適合對象：居住外縣市、退休族群、工作忙碌、追求每月固定被動收入不想過問任何雜事的房東。

🤝 **2. 代租代管 (Manage Agent) —「租金報酬最大化」首選**
• 模式：由窩在家替您專業招租、嚴格把關房客信用、代收租金與統籌維護修繕，租金依實際行情入帳，收取月租百分比作為管理費。
• 適合對象：希望保留房屋租賃主控權、物件屋況良好且想獲取市場高檔租金水準的房東。""",
        'reply_en': """[Full Master-Lease vs. Property Management Agency]
1. Full Master-Lease (Manage Host): Guaranteed monthly rent paid directly to you. Zero vacancy or default risk. Ideal for out-of-town owners.
2. Property Agency (Manage Agent): We screen high-caliber tenants, manage daily operations and maintenance. Rent reflects market highs. Ideal for maximizing rental yield.""",
        'reply_ja': """【サブリース（一括借り上げ）と賃貸管理代行の違い】
1. サブリース（包租代管）：空室・滞納リスクなしで毎月安定した家賃収入を保証。
2. 管理代行（代租代管）：厳格な入居者審査から日常管理・修繕まで代行し、市場最高水準の利回りを狙えます。""",
        'reply_ko': """[통임대(마스터리스) vs 일반 위탁관리 비교]
1. 마스터리스(包租代管): 공실/연체 위험 없이 매월 확정 임대료 보장 지급.
2. 위탁관리(代租代管): 임차인 선별부터 유지보수까지 일괄 대행하며 시장 최고 수익률 추구."""
    },
    'renovation': {
        'keywords': ['翻新', '裝修', '改造', '老屋', '裝潢', '坪效', '美學', 'renovate', 'renovation', 'リノベーション', '리모델링'],
        'reply_zh': """【窩在家 空間活化與老宅翻新服務】
我們團隊擁有超過 15 年空間美學與室內工程改造經驗：
• **痛點突破**：傳統 30~50 年台南老宅常面臨壁癌、水電管線老舊、動線不良等問題。
• **精準賦能**：採用日式侘寂與現代極簡設計，著重小額預算創造極致坪效，翻新後租金平均躍升 80%~160%，並能吸引南科工程師與優質白領租客。
• **一站式統包**：現場評估 ➔ 3D 空間規劃 ➔ 嚴格工程監造 ➔ 軟裝陳設 ➔ 專業攝影招租，免除房東監工心力！""",
        'reply_en': """[Space Revitalization & Heritage Renovation]
Specializing in retrofitting 30-50 year heritage townhouses in Tainan into high-yield, aesthetic living spaces:
• Budget-optimized modular design boosting rent by +80% to +160%.
• Full turnkey service: Structural upgrades, pipeline replacement, modern styling, and tenant placement.""",
        'reply_ja': """【古民家再生・空間リノベーション】
台南の築30〜50年の古民家を現代のミニマリズム空間へ再生。賃料は平均80%〜160%アップ！ワンストップで施工から入居者募集まで行います。""",
        'reply_ko': """[노후 주택 재생 및 인테리어 리모델링]
대만 타이난 노후 주택을 모던 미니멀리즘 감성으로 탈바꿈시켜 임대 수익률을 80%~160% 극대화합니다."""
    },
    'process': {
        'keywords': ['流程', '步驟', '如何開始', '簽約', '收費', '費用', 'process', 'flow', '流れ', '절차'],
        'reply_zh': """【窩在家 5 大標準委託流程】
1. **線上諮詢與估價**：填寫官網 RFQ 表單或加 LINE 溝通初步需求。
2. **現場專人屋況評估**：丈量尺寸、勘查採光結構、產出市場租金分析報告。
3. **簽約與公證保障**：法定標準租賃契約，送交地方法院公證處公證，雙方權益最具保障。
4. **空間美化與工程修繕（選配）**：針對老舊管線與屋況提供最具性價比的改造工程。
5. **多通路精準招租與管家駐點維護**：嚴格徵信篩選房客、代收租金，每月固定產出財務報表！""",
        'reply_en': """[5-Step Professional Onboarding Process]
1. Initial RFQ / Consultation
2. On-Site Property & Rental Assessment
3. Notarized Contract Signing for Legal Protection
4. Space Beautification & Upgrade (Optional)
5. Multi-Channel Marketing & Dedicated Butler Maintenance""",
        'reply_ja': """【5つのステップで安心委託】
1. オンラインお問い合わせ
2. 現地調査および家賃査定
3. 法的効力を持つ公正証書契約の締結
4. 内装リノベーション施工（オプション）
5. 入居者募集および日常の管理・家賃送金""",
        'reply_ko': """[5단계 전문 위탁 프로세스]
1. 온라인 상담 접수
2. 현장 실사 및 적정 임대료 분석
3. 법원 공증 계약 체결로 안전성 확보
4. 필요시 맞춤형 리모델링 시공
5. 임차인 선별 입주 및 전담 매니저의 월간 정산 관리"""
    },
    'rentals': {
        'keywords': ['租屋', '找房', '招租', '套房', '想租', '看房', '預約帶看', '租金補貼', '租補', '南科租屋', 'rent', 'rental', 'viewing', '部屋探し', '賃貸', '방구하기'],
        'reply_zh': """【窩在好宅 ｜ 精選優質好宅出租與預約賞屋】
窩在家所有招租房源皆具備「水電安全檢驗、全套一級節能變頻家電、乾濕分離衛浴與法院公證契約保障」，拒絕假房源，全程免仲介費！
🏡 **熱門在架好宅類別**：
1. **南科/永康 獨立露台套房**：月租 13,800 元起，配備獨立洗脫烘與智慧門禁。
2. **善化 LM 特區 高階景觀套房**：騎車 5 分鐘抵達南科，專屬室內機車位。
3. **東區文化中心 侘寂美透天**：4 房天井日光宅，適合家庭或設計團隊。
4. **中西區文創慢活公寓**：日光中島開放廚房，漫步國華神農街。
👉 您可點擊上方導覽列【精選招租】或前往 `/rentals` 瀏覽全景相簿，並直接填表預約專人一對一實地帶看！所有物件均可合法申辦 300 億中央租金補貼。""",
        'reply_en': """[Curated Rentals & Private Viewings]
All WOO IN HOME rental properties are professionally inspected with full appliance setup, legal notarization, and zero broker fees!
Browse our portfolio of suites and apartments in Yungkang, East District, and Shan-Hua (STSP Tech Park) under the 'Rentals' tab. Schedule a viewing online anytime!""",
        'reply_ja': """【厳選賃貸物件・内見のご案内】
当社管理物件はすべて設備完備・安全検査済み・仲介手数料無料！
台南市内および南科（サイエンスパーク）周辺の高品質ワンルーム・ファミリー向けマンションをご用意。メニューの「賃貸物件」よりオンライン内見予約が可能です。""",
        'reply_ko': """[프리미엄 임대 매물 및 현장 방문 안내]
모든 매물은 수전/전기 안전 점검 완료, 풀옵션 가전 완비, 중개수수료 무료!
상단 '임대 매물' 메뉴에서 남과(STSP) 인근 원룸 및 아파트 실사진을 확인하시고 온라인 방문 예약을 신청하세요."""
    }
}

DEFAULT_REPLY = {
    'zh-TW': """您好！我是窩在家的智慧諮詢顧問。
我們是台南深耕多年的專業包租代管與空間活化品牌，累積服務超過百位房東。
請問您今天想要了解哪方面的資訊呢？
1. 【包租代管 vs 代租代管】哪種最適合我？
2. 【租稅優惠】房屋稅/地價稅減免與 1.5 萬免稅額
3. 【老屋翻新改造】預算與租金翻倍試算
4. 【線上即時估價】加入詢價清單或由專人一對一聯繫

您也可以直接點擊「加入詢價清單」或「填寫諮詢表」，專人將在指定時段親自向您說明！""",
    'en': """Hello! I am your WOO IN HOME smart asset advisor.
We specialize in certified property master-leasing, rental agency, and space revitalization in Tainan.
How can I assist you today?
1. Difference between Full Master-Lease and Rental Agency
2. Property Tax Exemption Guidelines (Up to NT$15,000/mo exempt)
3. Space Renovation & Rental Yield Multiplier
4. Request an Instant Quote / RFQ

Feel free to ask a question or submit an RFQ!""",
    'ja': """こんにちは！「窩在家（WOO IN HOME）」AIプロパティアドバイザーです。
台南における不動産一括借り上げ（サブリース）、賃貸管理代行、空間リノベーションの専門ブランドです。
ご質問がございましたら、いつでもお気軽にお申し付けください。""",
    'ko': """안녕하세요! WOO IN HOME 스마트 자산관리 AI 어드바이저입니다.
대만 타이난 전문 임대주택 위탁관리 및 주택 재생 브랜드로서 최고의 수익률과 안정성을 보장해 드립니다."""
}

def get_ai_response(query: str, lang: str = 'zh-TW') -> str:
    """Matches user intent against rich knowledge base or provides structured fallback"""
    if not query or not query.strip():
        return DEFAULT_REPLY.get(lang, DEFAULT_REPLY['zh-TW'])

    query_lower = query.lower()
    
    # 1. Check knowledge base keywords
    for key, data in KNOWLEDGE_BASE.items():
        if any(kw in query_lower for kw in data['keywords']):
            field = f"reply_{lang[:2]}"
            if field in data:
                return data[field]
            return data.get('reply_zh', data['reply_zh'])

    # 2. Check for contact or phone
    if any(k in query_lower for k in ['電話', '地址', '聯絡', '在哪', 'phone', 'address', 'contact', '住所']):
        return """【窩在家 聯絡資訊】
📍 總部地址：臺南市中西區公園路56號1樓 (近民生綠園 / 台南火車站)
📞 諮詢專線：(06) 289-4168
💬 官方 LINE：@wooinhome
⏰ 營業時間：週一至週五 09:00 - 18:00
歡迎填寫線上詢價單或預約專人到府勘查評估！"""

    return DEFAULT_REPLY.get(lang, DEFAULT_REPLY['zh-TW'])

