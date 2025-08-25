#Requires -Version 5.0
<#
.SYNOPSIS
    WebUI完全起動スクリプト（バックエンド + フロントエンド）
.DESCRIPTION
    Windows 11 Sysprep応答ファイル生成システムのWebUIを完全に起動します
#>

param(
    [switch]$Debug,
    [switch]$NoOpen
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Windows 11 Sysprep WebUI 起動" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# パス設定
$BackendPath = Join-Path $PSScriptRoot "backend"
$FrontendPath = Join-Path $PSScriptRoot "frontend"

# バックエンド起動（新しいウィンドウ）
Write-Host "🚀 バックエンドサーバーを起動中..." -ForegroundColor Yellow
$backendScript = @"
cd '$BackendPath'
Write-Host 'Backend Server Starting on port 8081...' -ForegroundColor Cyan
python main.py
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript -WindowStyle Normal

# バックエンド起動待機
Write-Host "⏳ バックエンドの起動を待機中..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# バックエンド疎通確認
$maxRetries = 10
$retryCount = 0
$backendReady = $false

while ($retryCount -lt $maxRetries -and -not $backendReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8081/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            Write-Host "✅ バックエンドサーバー起動確認" -ForegroundColor Green
        }
    } catch {
        $retryCount++
        Write-Host "   再試行 $retryCount/$maxRetries..." -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if (-not $backendReady) {
    Write-Host "⚠️  バックエンドサーバーの起動確認ができませんでした" -ForegroundColor Yellow
    Write-Host "   手動で http://localhost:8081/docs を確認してください" -ForegroundColor Yellow
}

# フロントエンド起動（新しいウィンドウ）
Write-Host ""
Write-Host "🚀 フロントエンドサーバーを起動中..." -ForegroundColor Yellow

$frontendScript = @"
cd '$FrontendPath'
Write-Host 'Frontend Server Starting on port 3050...' -ForegroundColor Cyan
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript -WindowStyle Normal

# フロントエンド起動待機
Write-Host "⏳ フロントエンドの起動を待機中..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ WebUI起動完了" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 フロントエンド: http://192.168.3.92:3050" -ForegroundColor Green
Write-Host "📚 バックエンドAPI: http://localhost:8081/docs" -ForegroundColor Green
Write-Host ""
Write-Host "終了するには、各ウィンドウで Ctrl+C を押してください" -ForegroundColor Gray
Write-Host "================================================" -ForegroundColor Cyan

# ブラウザを開く
if (-not $NoOpen) {
    Start-Sleep -Seconds 2
    Start-Process "http://192.168.3.92:3050"
}

# このウィンドウは開いたままにする
Write-Host ""
Write-Host "このウィンドウは閉じても問題ありません" -ForegroundColor Gray
Write-Host "サーバーは別ウィンドウで実行中です" -ForegroundColor Gray