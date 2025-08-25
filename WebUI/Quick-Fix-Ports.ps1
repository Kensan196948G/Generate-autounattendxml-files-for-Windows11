#Requires -Version 5.0
<#
.SYNOPSIS
    WebUIポート問題の即座解決スクリプト
.DESCRIPTION
    ポート8080でバックエンド、3050でフロントエンドを確実に起動
#>

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  WebUI ポート問題解決 & 起動" -ForegroundColor Cyan  
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: すべてのプロセスを終了
Write-Host "[1/4] 既存プロセスをクリーンアップ中..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "✅ クリーンアップ完了" -ForegroundColor Green

# Step 2: 環境変数ファイルを更新（ポート8080）
Write-Host ""
Write-Host "[2/4] 環境設定を更新中..." -ForegroundColor Yellow
$envFile = Join-Path $PSScriptRoot "frontend\.env.local"
$envContent = @"
# WebUI Frontend Environment Variables
NEXT_PUBLIC_API_URL=http://192.168.3.92:8080/api
NEXT_PUBLIC_LOCAL_IP=192.168.3.92
"@
Set-Content -Path $envFile -Value $envContent -Encoding UTF8
Write-Host "✅ 環境設定更新完了（API: ポート8080）" -ForegroundColor Green

# Step 3: バックエンドを起動（ポート8080）
Write-Host ""
Write-Host "[3/4] バックエンドサーバーを起動中..." -ForegroundColor Yellow
$backendPath = Join-Path $PSScriptRoot "backend"
$backendScript = @"
cd '$backendPath'
Write-Host ''
Write-Host '====================================' -ForegroundColor Green
Write-Host ' バックエンドサーバー起動' -ForegroundColor Green
Write-Host ' ポート: 8080' -ForegroundColor Green
Write-Host ' URL: http://192.168.3.92:8080' -ForegroundColor Green
Write-Host '====================================' -ForegroundColor Green
Write-Host ''

# main.pyを修正してポート8080を使用
`$mainPy = Get-Content main.py -Raw
`$mainPy = `$mainPy -replace 'port=\d+', 'port=8080'
Set-Content main.py `$mainPy

# 起動
python main.py
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript -WindowStyle Normal
Start-Sleep -Seconds 5
Write-Host "✅ バックエンド起動（ポート8080）" -ForegroundColor Green

# Step 4: フロントエンドを起動（ポート3050）
Write-Host ""
Write-Host "[4/4] フロントエンドサーバーを起動中..." -ForegroundColor Yellow
$frontendPath = Join-Path $PSScriptRoot "frontend"
$frontendScript = @"
cd '$frontendPath'
Write-Host ''
Write-Host '====================================' -ForegroundColor Cyan
Write-Host ' フロントエンドサーバー起動' -ForegroundColor Cyan
Write-Host ' ポート: 3050' -ForegroundColor Cyan
Write-Host ' URL: http://192.168.3.92:3050' -ForegroundColor Cyan
Write-Host '====================================' -ForegroundColor Cyan
Write-Host ''
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript -WindowStyle Normal
Start-Sleep -Seconds 5
Write-Host "✅ フロントエンド起動（ポート3050）" -ForegroundColor Green

# 完了メッセージ
Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "    ✅ WebUI起動完了！" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "📌 アクセスURL:" -ForegroundColor Yellow
Write-Host "   WebUI: http://192.168.3.92:3050" -ForegroundColor White
Write-Host "   API: http://192.168.3.92:8080/api" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  注意: ポート設定を統一しました" -ForegroundColor Yellow
Write-Host "   バックエンド: 8080" -ForegroundColor Gray
Write-Host "   フロントエンド: 3050" -ForegroundColor Gray
Write-Host ""
Write-Host "停止する場合は各ウィンドウで Ctrl+C" -ForegroundColor Gray

# ブラウザを開く
Start-Sleep -Seconds 3
Start-Process "http://192.168.3.92:3050"