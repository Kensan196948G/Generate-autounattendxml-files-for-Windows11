# ============================================================================
# バックエンド自動診断・修復スクリプト
# エラーを自動検知して修復対応
# ============================================================================

param(
    [switch]$Force,          # 強制修復モード
    [switch]$Verbose,        # 詳細ログ表示
    [int]$MaxRetries = 3     # 最大リトライ回数
)

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ErrorActionPreference = "Continue"

# ============================================================================
# ログ関数
# ============================================================================
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    switch ($Level) {
        "SUCCESS" { Write-Host "[$timestamp] ✅ $Message" -ForegroundColor Green }
        "ERROR"   { Write-Host "[$timestamp] ❌ $Message" -ForegroundColor Red }
        "WARNING" { Write-Host "[$timestamp] ⚠️  $Message" -ForegroundColor Yellow }
        "INFO"    { Write-Host "[$timestamp] ℹ️  $Message" -ForegroundColor Cyan }
        "DEBUG"   { if ($Verbose) { Write-Host "[$timestamp] 🔍 $Message" -ForegroundColor Gray } }
        "FIX"     { Write-Host "[$timestamp] 🔧 $Message" -ForegroundColor Magenta }
    }
}

# ============================================================================
# エラー検知・修復クラス
# ============================================================================
class BackendAutoFixer {
    [string]$BackendPath
    [hashtable]$Errors = @{}
    [int]$RetryCount = 0
    [int]$MaxRetries
    
    BackendAutoFixer([string]$path, [int]$maxRetries) {
        $this.BackendPath = $path
        $this.MaxRetries = $maxRetries
    }
    
    # Python環境チェック
    [bool] CheckPython() {
        Write-Log "Python環境をチェック中..." "INFO"
        
        try {
            $pythonVersion = & python --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Python検出: $pythonVersion" "SUCCESS"
                return $true
            }
        } catch {
            $this.Errors["python"] = "Pythonが見つかりません"
        }
        
        return $false
    }
    
    # Python修復
    [bool] FixPython() {
        Write-Log "Pythonインストールを確認中..." "FIX"
        
        # Python3.9以上を確認
        $pythonPaths = @(
            "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
            "C:\Python39\python.exe",
            "C:\Python310\python.exe",
            "C:\Python311\python.exe",
            "C:\Python312\python.exe"
        )
        
        foreach ($pyPath in $pythonPaths) {
            if (Test-Path $pyPath) {
                Write-Log "Python found at: $pyPath" "SUCCESS"
                # PATHに追加（一時的）
                $env:PATH = (Split-Path $pyPath -Parent) + ";" + $env:PATH
                return $true
            }
        }
        
        Write-Log "Pythonが見つかりません。インストールしてください。" "ERROR"
        Write-Log "推奨: Python 3.9以上 from https://www.python.org/" "INFO"
        return $false
    }
    
    # 仮想環境チェック
    [bool] CheckVenv() {
        Write-Log "仮想環境をチェック中..." "INFO"
        
        $venvPath = Join-Path $this.BackendPath "venv"
        if (Test-Path $venvPath) {
            $venvPython = Join-Path $venvPath "Scripts\python.exe"
            if (Test-Path $venvPython) {
                Write-Log "仮想環境が存在します" "SUCCESS"
                return $true
            }
        }
        
        $this.Errors["venv"] = "仮想環境が不完全または存在しません"
        return $false
    }
    
    # 仮想環境修復
    [bool] FixVenv() {
        Write-Log "仮想環境を作成/修復中..." "FIX"
        
        Push-Location $this.BackendPath
        
        # 既存の仮想環境を削除
        $venvPath = ".\venv"
        if (Test-Path $venvPath) {
            Write-Log "既存の仮想環境を削除中..." "INFO"
            Remove-Item $venvPath -Recurse -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        # 新しい仮想環境を作成
        Write-Log "新しい仮想環境を作成中..." "INFO"
        & python -m venv venv 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0 -and (Test-Path ".\venv\Scripts\python.exe")) {
            Write-Log "仮想環境作成成功" "SUCCESS"
            Pop-Location
            return $true
        }
        
        Pop-Location
        return $false
    }
    
    # 依存関係チェック
    [bool] CheckDependencies() {
        Write-Log "依存関係をチェック中..." "INFO"
        
        Push-Location $this.BackendPath
        
        # requirements.txtの存在確認
        if (-not (Test-Path ".\requirements.txt")) {
            $this.Errors["requirements"] = "requirements.txtが存在しません"
            Pop-Location
            return $false
        }
        
        # 主要パッケージの確認
        $checkScript = @"
import sys
try:
    import fastapi
    import uvicorn
    import lxml
    print('SUCCESS')
except ImportError as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"@
        
        $result = $checkScript | & .\venv\Scripts\python.exe 2>&1
        
        Pop-Location
        
        if ($result -like "*SUCCESS*") {
            Write-Log "主要パッケージ確認OK" "SUCCESS"
            return $true
        }
        
        $this.Errors["dependencies"] = "依存パッケージが不足しています"
        return $false
    }
    
    # 依存関係修復
    [bool] FixDependencies() {
        Write-Log "依存関係をインストール中..." "FIX"
        
        Push-Location $this.BackendPath
        
        # requirements.txtが存在しない場合は作成
        if (-not (Test-Path ".\requirements.txt")) {
            Write-Log "requirements.txtを作成中..." "INFO"
            $requirements = @"
# Windows 11 Sysprep応答ファイル生成システム WebUI版
# バックエンド依存ライブラリ - 安定版

# FastAPI関連（安定版）
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# WebSocket通信
websockets==12.0

# XML処理
lxml==4.9.3

# 設定管理
pydantic==2.5.0

# YAMLサポート
PyYAML==6.0.1

# 非同期処理
aiofiles==23.2.1

# パフォーマンス監視
psutil==5.9.6

# 開発支援（オプション）
python-dotenv==1.0.0
"@
            Set-Content -Path ".\requirements.txt" -Value $requirements -Encoding UTF8
        }
        
        # pipアップグレード
        Write-Log "pipをアップグレード中..." "DEBUG"
        & .\venv\Scripts\python.exe -m pip install --upgrade pip --quiet 2>&1 | Out-Null
        
        # パッケージインストール
        Write-Log "パッケージをインストール中..." "INFO"
        & .\venv\Scripts\pip.exe install -r requirements.txt --quiet 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "依存関係インストール成功" "SUCCESS"
            Pop-Location
            return $true
        }
        
        # 個別インストールを試みる
        Write-Log "個別パッケージインストールを試行中..." "FIX"
        $packages = @(
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "pydantic==2.5.0",
            "lxml==4.9.3",
            "PyYAML==6.0.1",
            "psutil==5.9.6"
        )
        
        foreach ($package in $packages) {
            Write-Log "Installing: $package" "DEBUG"
            & .\venv\Scripts\pip.exe install $package --quiet 2>&1 | Out-Null
        }
        
        Pop-Location
        return $true
    }
    
    # XML生成モジュールチェック
    [bool] CheckXMLGenerator() {
        Write-Log "XML生成モジュールをチェック中..." "INFO"
        
        $xmlGenPath = Join-Path $this.BackendPath "xml_generator.py"
        if (-not (Test-Path $xmlGenPath)) {
            $this.Errors["xml_generator"] = "xml_generator.pyが存在しません"
            return $false
        }
        
        # インポートテスト
        Push-Location $this.BackendPath
        
        $testScript = @"
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from xml_generator import UnattendXMLGenerator, XMLGeneratorSubAgent
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"@
        
        $result = $testScript | & .\venv\Scripts\python.exe 2>&1
        
        Pop-Location
        
        if ($result -like "*SUCCESS*") {
            Write-Log "XML生成モジュール確認OK" "SUCCESS"
            return $true
        }
        
        return $false
    }
    
    # main.pyチェック
    [bool] CheckMainPy() {
        Write-Log "main.pyをチェック中..." "INFO"
        
        $mainPath = Join-Path $this.BackendPath "main.py"
        if (-not (Test-Path $mainPath)) {
            $this.Errors["main"] = "main.pyが存在しません"
            return $false
        }
        
        # シンタックスチェック
        Push-Location $this.BackendPath
        
        $syntaxCheck = & .\venv\Scripts\python.exe -m py_compile main.py 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "main.pyシンタックスOK" "SUCCESS"
            
            # インポートチェック
            $importTest = @"
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import main
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@
            
            $result = $importTest | & .\venv\Scripts\python.exe 2>&1
            
            Pop-Location
            
            if ($result -like "*SUCCESS*") {
                return $true
            } else {
                Write-Log "main.pyインポートエラー" "ERROR"
                Write-Log "$result" "DEBUG"
                $this.Errors["main_import"] = "main.pyのインポートに失敗"
            }
        } else {
            $this.Errors["main_syntax"] = "main.pyに構文エラーがあります"
        }
        
        Pop-Location
        return $false
    }
    
    # バックエンド起動テスト
    [bool] TestBackendStartup() {
        Write-Log "バックエンド起動テスト中..." "INFO"
        
        Push-Location $this.BackendPath
        
        # テスト用起動スクリプト
        $testStartup = @"
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数設定
os.environ['TESTING'] = '1'

try:
    import main
    # アプリケーションオブジェクトの確認
    if hasattr(main, 'app'):
        print('SUCCESS: FastAPI app found')
    else:
        print('ERROR: No app object in main.py')
        sys.exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@
        
        $result = $testStartup | & .\venv\Scripts\python.exe 2>&1
        
        Pop-Location
        
        if ($result -like "*SUCCESS*") {
            Write-Log "バックエンド起動準備OK" "SUCCESS"
            return $true
        }
        
        Write-Log "起動テスト失敗: $result" "ERROR"
        return $false
    }
    
    # 統合診断・修復
    [bool] DiagnoseAndFix() {
        Write-Log "統合診断・修復を開始..." "INFO"
        Write-Log "=" * 70 "DEBUG"
        
        $steps = @(
            @{Check = "CheckPython"; Fix = "FixPython"; Name = "Python環境"},
            @{Check = "CheckVenv"; Fix = "FixVenv"; Name = "仮想環境"},
            @{Check = "CheckDependencies"; Fix = "FixDependencies"; Name = "依存関係"},
            @{Check = "CheckXMLGenerator"; Fix = $null; Name = "XML生成モジュール"},
            @{Check = "CheckMainPy"; Fix = $null; Name = "main.py"},
            @{Check = "TestBackendStartup"; Fix = $null; Name = "起動テスト"}
        )
        
        foreach ($step in $steps) {
            Write-Log "チェック: $($step.Name)" "DEBUG"
            
            $checkResult = & { $this.($step.Check)() }
            
            if (-not $checkResult) {
                if ($step.Fix) {
                    Write-Log "$($step.Name)の問題を修復中..." "FIX"
                    $fixResult = & { $this.($step.Fix)() }
                    
                    if (-not $fixResult) {
                        Write-Log "$($step.Name)の修復に失敗" "ERROR"
                        return $false
                    }
                    
                    # 修復後に再チェック
                    $recheckResult = & { $this.($step.Check)() }
                    if (-not $recheckResult) {
                        Write-Log "$($step.Name)の修復後も問題が残っています" "ERROR"
                        return $false
                    }
                } else {
                    Write-Log "$($step.Name)に問題があります（自動修復不可）" "ERROR"
                    return $false
                }
            }
        }
        
        Write-Log "すべての診断・修復が完了しました" "SUCCESS"
        return $true
    }
}

# ============================================================================
# メイン処理
# ============================================================================

Clear-Host

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              バックエンド自動診断・修復システム                          ║" -ForegroundColor Cyan
Write-Host "║                  エラー自動検知・修復対応                                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$backendPath = Join-Path $ScriptRoot "backend"

if (-not (Test-Path $backendPath)) {
    Write-Log "バックエンドフォルダが見つかりません: $backendPath" "ERROR"
    exit 1
}

# AutoFixerインスタンス作成
$fixer = [BackendAutoFixer]::new($backendPath, $MaxRetries)

# 診断・修復実行
$success = $false
$retryCount = 0

while (-not $success -and $retryCount -lt $MaxRetries) {
    if ($retryCount -gt 0) {
        Write-Log "リトライ $retryCount/$MaxRetries" "WARNING"
    }
    
    $success = $fixer.DiagnoseAndFix()
    
    if (-not $success) {
        $retryCount++
        if ($retryCount -lt $MaxRetries) {
            Write-Log "5秒後に再試行します..." "INFO"
            Start-Sleep -Seconds 5
        }
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if ($success) {
    Write-Log "診断・修復完了！" "SUCCESS"
    Write-Host ""
    Write-Log "バックエンドを起動しています..." "INFO"
    
    # バックエンド起動
    Push-Location $backendPath
    
    # バッチファイル作成
    $startBatch = @"
@echo off
cd /d "$backendPath"
echo ======================================
echo  バックエンドサーバー起動
echo  Context7 + SubAgent(42体)
echo ======================================
echo.
echo URL: http://192.168.3.92:8080
echo API Docs: http://192.168.3.92:8080/api/docs
echo.

if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe main.py
) else (
    python main.py
)
"@
    
    $tempBatch = "$env:TEMP\start-backend-fixed-$(Get-Random).bat"
    Set-Content -Path $tempBatch -Value $startBatch -Encoding UTF8
    
    Write-Log "新しいウィンドウでバックエンドを起動中..." "INFO"
    Start-Process cmd -ArgumentList "/k", $tempBatch -WindowStyle Normal
    
    Pop-Location
    
    # 起動確認
    Write-Log "起動確認中..." "INFO"
    Start-Sleep -Seconds 5
    
    try {
        $response = Invoke-WebRequest -Uri "http://192.168.3.92:8080/api/status" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Log "バックエンドが正常に起動しました！" "SUCCESS"
            Write-Host ""
            Write-Host "📌 アクセスURL:" -ForegroundColor White
            Write-Host "   API: http://192.168.3.92:8080" -ForegroundColor Cyan
            Write-Host "   API Docs: http://192.168.3.92:8080/api/docs" -ForegroundColor Cyan
        }
    } catch {
        Write-Log "バックエンドの起動確認に失敗（手動で確認してください）" "WARNING"
    }
    
} else {
    Write-Log "修復に失敗しました" "ERROR"
    Write-Host ""
    Write-Log "検出されたエラー:" "ERROR"
    foreach ($error in $fixer.Errors.GetEnumerator()) {
        Write-Host "  - $($error.Key): $($error.Value)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Log "手動での対処が必要です:" "WARNING"
    Write-Host "  1. Python 3.9以上がインストールされているか確認" -ForegroundColor Yellow
    Write-Host "  2. backend\venvフォルダを削除して再実行" -ForegroundColor Yellow
    Write-Host "  3. それでも失敗する場合は backend\main.py を確認" -ForegroundColor Yellow
}

Write-Host ""
if (-not $success) {
    Read-Host "Enterキーで終了"
}