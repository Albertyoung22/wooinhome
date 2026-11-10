# ==============================================================================
# 窩在家 (WOO IN HOME) - 一鍵推送至 GitHub 輔助腳本
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  窩在家物業管理平台 - GitHub 推送與 Render 部署準備精靈" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Check Git
$gitCheck = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCheck) {
    Write-Host "[錯誤] 您的電腦尚未安裝 Git，請先至 https://git-scm.com/ 下載安裝！" -ForegroundColor Red
    exit 1
}

# Check Current Branch
$currentBranch = (git branch --show-current).Trim()
Write-Host "[1/3] 目前本地 Git 分支: $currentBranch" -ForegroundColor Green

# Check Remote Origin
$remoteOrigin = (git remote get-url origin 2>$null)

if (-not $remoteOrigin) {
    Write-Host ""
    Write-Host "請輸入您的 GitHub 儲存庫網址 (HTTPS 格式)：" -ForegroundColor Yellow
    Write-Host "範例：https://github.com/您的帳號/wooinhome.git" -ForegroundColor DarkGray
    $repoUrl = Read-Host "請貼上 GitHub Repository URL"

    if ([string]::IsNullOrWhiteSpace($repoUrl)) {
        Write-Host "[取消] 未輸入網址，操作中止。" -ForegroundColor Red
        exit 1
    }

    git remote add origin $repoUrl.Trim()
    Write-Host "[✓] 已成功綁定遠端儲存庫: $repoUrl" -ForegroundColor Green
} else {
    Write-Host "[1/3] 已綁定遠端儲存庫: $remoteOrigin" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/3] 正在確保所有修改均已提交..." -ForegroundColor Yellow
git add .
$status = git status --porcelain
if ($status) {
    git commit -m "chore: prepare for Render deployment"
}

Write-Host ""
Write-Host "[3/3] 正在推送至 GitHub (main 分支)..." -ForegroundColor Yellow
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "  🎉 恭喜！專案已成功推送到 GitHub！" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步：在 Render 部署" -ForegroundColor Cyan
    Write-Host "1. 前往 https://render.com/ 登入"
    Write-Host "2. 點擊「New +」 ➔ 選擇「Web Service」"
    Write-Host "3. 連接您的 GitHub 專案"
    Write-Host "4. Render 會自動讀取 render.yaml 與 Procfile，點擊「Create Web Service」即可！"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[提示] 推送時若出現驗證錯誤，請確認：" -ForegroundColor Yellow
    Write-Host "1. GitHub 是否已建立該 Repository"
    Write-Host "2. 您的 GitHub 帳號密碼或 Personal Access Token 是否具有寫入權限"
}
