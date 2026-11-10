# 窩在家 (WOO IN HOME) ｜ 企業級高質感形象官網暨智慧詢價管理平台

> **深耕台南 15 年 ｜ 專業包租代管 ｜ 代租代管 ｜ 老屋空間活化與租稅顧問**

本專案為「窩在家物業管理顧問有限公司」量身打造之企業級品牌官網與智慧詢價 CRM 管理平台。融合現代侘寂美學設計與高擴充性全端技術，具備 **SSR + SPA 混合路由**、**4國語言即時國際化 (i18n)**、**Microsoft Edge-TTS 神經語音導覽**、**空間活化與租金增值試算機**、**智慧 RFQ 詢價購物車**、**AI 智慧客服助手** 以及 **Admin CRM 業務管理後台**。

針對雲端平台（如 Render）重啟或重新部署清空本機硬碟的特性，系統獨家實作「**GitHub 專屬備份分支 (`cloud-backup`) 自動備份與啟動還原機制**」（帶有 `[skip ci]` 避免無限循環構建），並相容外部 PostgreSQL 與 Google Sheets，確保客戶詢價與資料永久保存！

---

## 🌟 核心功能規格

1. **前後端技術棧**：
   - 後端採用 Python Flask，搭配 Gunicorn 支援高併發雲端部署；支援透過 `pywebview` 一鍵封裝為桌面原生應用程式（`desktop.py`）。
   - 前端採用 **SSR + SPA 混合路由引擎**：每個分頁具備完整獨立 URL、優化 SEO Meta、OpenGraph、Twitter Cards 與 JSON-LD 結構化資料，站內導覽使用 History API 無刷新流暢切換。
   - 頂級現代響應式（RWD）工藝美學：日式侘寂與現代建築極簡風格，完美適配電腦、平板與各型手機。

2. **核心功能模組**：
   - **產品與規格檢索中心**：支援整棟透天、公寓大樓、獨立套房、商圈店面多維度篩選。
   - **空間活化與租金增值試算機**：動態演算翻新後租金躍升潛力、年收租金增加額、工程 CapEx 回本期與法定租稅減免效益。
   - **智慧詢價清單 (RFQ Cart)**：浮動抽屜購物車，可一鍵將試算結果、推薦方案加入清單並匯入詢價單。
   - **四國語言即時切換 (i18n)**：支援繁體中文 (`zh-TW`)、英文 (`en`)、日文 (`ja`)、韓文 (`ko`)，靜態與動態訊息無延遲切換。
   - **Edge-TTS 神經語音導覽**：整合微軟 Edge-TTS，提供高擬真語音解說，具備本地音訊快取。
   - **右下角 AI 智慧顧問助手**：內建台南在地物業法規、租稅優惠（1.5萬免稅額、房屋稅1.2%）與常見問題知識庫。
   - **線上 RFQ 詢價單與檔案上傳**：支援多項目委託與客戶房屋圖資/PDF 上傳，兼顧資料隱私。

3. **業務管理後台 (Admin CRM) 與雲端防遺失機制**：
   - **密碼保護 (HMAC 安全驗證)**：預設帳號 `admin`，密碼 `admin888`。
   - 詢價單全生命週期管理：狀態追蹤（待處理、聯繫中、已報價、已簽約、已結案）、內部業務備註、客戶附件下載。
   - **一鍵匯出 CSV 報表**：內建 UTF-8 BOM，相容繁體中文 Microsoft Excel。
   - **自動化郵件通知**：非同步執行緒發送美化 HTML 通知信給主管，並寄發預約回執信給客戶。
   - **GitHub 專屬分支自動備份與還原 (`cloud-backup`)**：定時或收到詢價時將資料庫快照自動推送到 GitHub，啟動時自動檢測還原，徹底解決 Render 磁碟清空問題。
   - **內建 `/api/health` 與背景防休眠 (Keep-Alive)**：定期自我呼叫避免 Render 免費執行個體休眠。

---

## 🚀 部署至 Render 執行步驟指南

本專案已完全設定好 `render.yaml`、`Procfile`、`runtime.txt` 與 `requirements.txt`，請依照下列步驟上傳 GitHub 並部署：

### 第一步：在本地初始化 Git 並上傳至 GitHub

在終端機中執行：

```bash
# 1. 初始化 Git 儲存庫
git init

# 2. 加入所有檔案
git add .

# 3. 建立初始 Commit
git commit -m "feat: initial commit for wooinhome enterprise platform"

# 4. 在 GitHub 上建立一個新的公開或私有 Repository（例如：wooinhome-web）
# 5. 綁定 GitHub 遠端儲存庫並推送主分支
git remote add origin https://github.com/<您的GitHub帳號>/<您的專案名稱>.git
git branch -M main
git push -u origin main
```

---

### 第二步：在 Render 建立 Web Service（一鍵部署）

1. 登入 [Render 官方網站](https://render.com/)。
2. 點擊右上角 **「New +」** ➔ 選擇 **「Web Service」**。
3. 選擇 **「Build and deploy from a Git repository」**，連接您的 GitHub 帳號並選取剛才建立的專案。
4. 設定基本參數（Render 通常會根據專案自動偵測）：
   - **Name**: `wooinhome-web`
   - **Region**: `Singapore (Southeast Asia)` (離台灣最近，延遲最低)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type**: `Free`
5. 設定環境變數（**Environment Variables**，可選）：
   - `ADMIN_USERNAME`: 管理員後台帳號（預設 `admin`）
   - `ADMIN_PASSWORD`: 管理員後台密碼（預設 `admin888`）
   - `SECRET_KEY`: 自訂一組隨機安全金鑰
   - `KEEP_ALIVE_URL`: 填入您的 Render 網址（例如：`https://wooinhome-web.onrender.com/api/health`），即可啟動防休眠！
   - `GITHUB_TOKEN` *(可選)*: 您的 GitHub Personal Access Token (需具備 repo 權限)
   - `GITHUB_REPO` *(可選)*: 您的備份儲存庫 (例如 `yourname/wooinhome-backup`)
6. 點擊 **「Create Web Service」**，Render 將在約 1~2 分鐘內自動建置完成並提供一個專屬的 HTTPS 網址！

---

## 💻 本地端運行與桌面應用程式啟動

### 1. 本地 Web 伺服器啟動
```bash
# 安裝相依套件
pip install -r requirements.txt

# 啟動 Flask 開發伺服器
python app.py
```
瀏覽器造訪：`http://127.0.0.1:5000`

### 2. 封裝桌面原生視窗啟動 (PyWebView)
```bash
python desktop.py
```
系統將自動尋找閒置通訊埠並以獨立的高質感原生桌面應用程式視窗啟動！

---

## 🔐 後台 CRM 登入資訊
- **後台登入路徑**：`/admin/login`
- **預設帳號**：`admin`
- **預設密碼**：`admin888`
- 可在登入後的「系統參數與雲端備份」頁面中直接線上配置 SMTP 郵件通知與 GitHub 備份權杖。

---

## 📁 專案架構目錄說明

```
wooinhome/
│
├── app.py                      # Flask 主伺服器、SSR + SPA 雙模引擎、RESTful API
├── desktop.py                  # PyWebView 桌面版封裝入口
├── config.py                   # 系統配置與安全雜湊設定
├── models.py                   # SQLAlchemy ORM 資料庫模型與預設種子資料
├── render.yaml                 # Render Blueprint 雲端一鍵部署規範
├── Procfile                    # 雲端行程啟動指令 (Gunicorn)
├── runtime.txt                 # 指定 Python 執行版本 (3.11.9)
├── requirements.txt            # Python 相依套件清單
│
├── services/
│   ├── tts_service.py          # Microsoft Edge-TTS 語音生成與本機快取
│   ├── email_service.py        # 非同步多執行緒郵件通知 (管理員+客戶)
│   ├── backup_service.py       # GitHub cloud-backup 分支自動持久化備份/還原 & Keep-Alive
│   └── ai_agent_service.py     # AI 智慧顧問意圖辨識與物業知識庫
│
├── static/
│   ├── css/
│   │   ├── style.css           # 侘寂日式工藝與極簡建築美學樣式庫
│   │   └── admin.css           # CRM 後台專屬響應式管理介面樣式
│   ├── js/
│   │   ├── i18n.js             # 繁中、英、日、韓四國語言即時國際化引擎
│   │   ├── router.js           # SSR + SPA 混合路由引擎 (History API)
│   │   ├── rfq_cart.js         # 詢價清單抽屜購物車 (LocalStorage)
│   │   ├── calculator.js       # 空間活化與租金增值試算工具
│   │   ├── tts_player.js       # 語音朗讀播放器控制
│   │   ├── ai_chat.js          # 右下角智慧客服懸浮面板
│   │   └── app.js              # 主站互動、Toast 通知、表單驗證
│   ├── audio_cache/            # Edge-TTS 生成音訊快取目錄
│   └── uploads/                # 客戶上傳物件照片與圖資檔案
│
└── templates/
    ├── base.html               # 頂層 HTML 骨架 (SEO Meta, Header, Footer, AI, RFQ Drawer)
    ├── index.html              # 首頁
    ├── manage_host.html        # 包租代管專頁
    ├── manage_agent.html       # 代租代管專頁
    ├── spatial_renovation.html # 老屋空間活化改造專頁
    ├── works.html              # 實績案例展示庫
    ├── calculator.html         # 空間活化與租金收益增值試算中心
    ├── blog.html               # 物管與法規專欄
    ├── faq.html                # 常見問題 Q&A
    ├── contact.html            # 線上詢價與專人委託 RFQ 表單
    └── admin/
        ├── login.html          # CRM 管理後台安全登入
        ├── dashboard.html      # CRM 儀表板與詢價單清單
        ├── rfq_detail.html     # 詢價單詳情與備註追蹤
        └── settings.html       # 郵件通知與 GitHub 備份持久化設定
```
