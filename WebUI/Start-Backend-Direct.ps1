# バックエンド直接起動スクリプト（デバッグ用）
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║               バックエンドサーバー直接起動（デバッグモード）             ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Push-Location "$ScriptRoot\backend"

# requirements.txtの確認・作成
if (-not (Test-Path ".\requirements.txt")) {
    Write-Host "📝 requirements.txtを作成中..." -ForegroundColor Yellow
    $requirements = @"
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pyyaml==6.0.1
psutil==5.9.6
python-multipart==0.0.6
websockets==12.0
lxml==4.9.3
"@
    Set-Content -Path ".\requirements.txt" -Value $requirements -Encoding UTF8
}

# 仮想環境の確認・作成
if (-not (Test-Path ".\venv")) {
    Write-Host "🔧 仮想環境を作成中..." -ForegroundColor Yellow
    & python -m venv venv
    
    Write-Host "📦 パッケージをインストール中..." -ForegroundColor Yellow
    & .\venv\Scripts\pip.exe install -r requirements.txt
}

Write-Host ""
Write-Host "🚀 バックエンドサーバーを起動します..." -ForegroundColor Green
Write-Host "   URL: http://192.168.3.92:8080" -ForegroundColor Cyan
Write-Host "   API Docs: http://192.168.3.92:8080/api/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "停止するには Ctrl+C を押してください" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# main.pyを直接実行
if (Test-Path ".\venv\Scripts\python.exe") {
    & .\venv\Scripts\python.exe main.py
} else {
    & python main.py
}

Pop-Location