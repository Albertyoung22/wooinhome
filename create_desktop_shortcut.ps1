# ==============================================================================
# 建立「窩在家 (WOO IN HOME)」桌面與工作列捷徑腳本
# ==============================================================================

$targetDir = "D:\PythonTest\wooinhome"
$pythonExe = "C:\Users\ALBERT\AppData\Local/Programs\Python\Python312\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python.exe"
}

$iconPath = Join-Path $targetDir "app_icon.ico"
$scriptPath = Join-Path $targetDir "desktop.py"

# Desktop Path
$desktopFolder = [Environment]::GetFolderPath("Desktop")
$shortcutFile = Join-Path $desktopFolder "窩在家包租代管.lnk"

# WScript.Shell
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutFile)
$shortcut.TargetPath = $pythonExe
$shortcut.Arguments = "`"$scriptPath`""
$shortcut.WorkingDirectory = $targetDir
$shortcut.IconLocation = "$iconPath, 0"
$shortcut.Description = "窩在家包租代管 ｜ 企業級形象官網暨智慧詢價管理系統"
$shortcut.Save()

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  🎉 桌面專屬圖標捷徑已成功建立！" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "捷徑位置：$shortcutFile" -ForegroundColor Cyan
Write-Host "圖標來源：$iconPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示：您現在可以直接在桌面雙擊「窩在家包租代管」啟動，" -ForegroundColor Yellow
Write-Host "也可以「按右鍵 ➔ 釘選到工作列 (Pin to taskbar)」！" -ForegroundColor Yellow
