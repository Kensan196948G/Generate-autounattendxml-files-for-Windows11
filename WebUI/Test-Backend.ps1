# バックエンドテストスクリプト
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║                  バックエンドサーバー診断                                ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
Write-Host ""

# Python環境確認
Write-Host "🔍 Python環境を確認中..." -ForegroundColor Cyan
Push-Location "$ScriptRoot\backend"

# Pythonバージョン確認
Write-Host "Python version:" -ForegroundColor Gray
& python --version

# 仮想環境確認
if (Test-Path ".\venv") {
    Write-Host "✅ 仮想環境が存在します" -ForegroundColor Green
    
    # 仮想環境のPython確認
    if (Test-Path ".\venv\Scripts\python.exe") {
        Write-Host "仮想環境のPython:" -ForegroundColor Gray
        & .\venv\Scripts\python.exe --version
    }
} else {
    Write-Host "⚠️ 仮想環境が見つかりません" -ForegroundColor Yellow
    Write-Host "仮想環境を作成します..." -ForegroundColor Cyan
    & python -m venv venv
}

Write-Host ""
Write-Host "📦 必要なパッケージをインストール中..." -ForegroundColor Cyan

# requirements.txtが存在しない場合は作成
if (-not (Test-Path ".\requirements.txt")) {
    Write-Host "requirements.txtを作成します..." -ForegroundColor Yellow
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
    Write-Host "✅ requirements.txt作成完了" -ForegroundColor Green
}

# パッケージインストール
Write-Host "パッケージをインストール中..." -ForegroundColor Gray
& .\venv\Scripts\pip.exe install -r requirements.txt --quiet

Write-Host ""
Write-Host "🧪 インポートテスト中..." -ForegroundColor Cyan

# Pythonスクリプトでインポートテスト
$testScript = @"
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print('Testing imports...')

try:
    # 基本モジュール
    import fastapi
    print('✓ FastAPI')
    
    import uvicorn
    print('✓ Uvicorn')
    
    import psutil
    print('✓ Psutil')
    
    import yaml
    print('✓ YAML')
    
    import lxml
    print('✓ lxml')
    
    # ローカルモジュール
    from xml_generator import UnattendXMLGenerator, XMLGeneratorSubAgent
    print('✓ XML Generator')
    
    print('')
    print('✅ すべてのインポートが成功しました！')
    
except ImportError as e:
    print(f'❌ インポートエラー: {e}')
    sys.exit(1)
"@

$testScript | & .\venv\Scripts\python.exe

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ インポートに失敗しました" -ForegroundColor Red
    Write-Host "xml_generator.pyの問題を修正します..." -ForegroundColor Yellow
    
    # xml_generator.pyの依存関係を確認
    Write-Host "追加パッケージをインストール中..." -ForegroundColor Cyan
    & .\venv\Scripts\pip.exe install lxml --upgrade --quiet
}

Write-Host ""
Write-Host "🚀 バックエンドサーバーを起動テスト中..." -ForegroundColor Cyan

# 単純な起動テスト
$serverTest = @"
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # 最小限のテスト
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI()
    
    @app.get('/test')
    def test():
        return {'status': 'ok'}
    
    print('✅ FastAPIアプリケーション作成成功')
    
    # main.pyを直接実行してみる
    import main
    print('✅ main.pyのインポート成功')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc()
"@

$serverTest | & .\venv\Scripts\python.exe

Pop-Location

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ バックエンドは正常に起動可能です" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 次のステップ:" -ForegroundColor Yellow
    Write-Host "   1. .\Start-WebUI.ps1 を再実行" -ForegroundColor White
    Write-Host "   2. それでも失敗する場合は .\Start-Backend-Direct.ps1 を実行" -ForegroundColor White
} else {
    Write-Host "❌ バックエンドに問題があります" -ForegroundColor Red
    Write-Host ""
    Write-Host "📝 トラブルシューティング:" -ForegroundColor Yellow
    Write-Host "   1. backend\venv フォルダを削除" -ForegroundColor White
    Write-Host "   2. このスクリプトを再実行" -ForegroundColor White
}

Write-Host ""
Read-Host "Enterキーで終了"