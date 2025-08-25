# ============================================================================
# フロントエンド＋バックエンド 統合自動診断・修復スクリプト（シンプル版）
# Windows 11 無人応答ファイル生成システム
# バージョン: 2.0 - 全23項目完全対応版
# ============================================================================

param(
    [switch]$Verbose,        # 詳細ログ表示モード
    [switch]$Force,          # 強制修復モード
    [int]$MaxRetries = 3     # リトライ回数指定
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
        "FIX"     { Write-Host "[$timestamp] 🔧 $Message" -ForegroundColor Magenta }
        "DEBUG"   { if ($Verbose) { Write-Host "[$timestamp] 🔍 $Message" -ForegroundColor Gray } }
    }
}

# ============================================================================
# バックエンド診断・修復
# ============================================================================
function Fix-Backend {
    param([string]$Path)
    
    Write-Log "バックエンド診断開始..." "INFO"
    $success = $true
    
    # Python確認
    Write-Log "Python環境を確認中..." "DEBUG"
    try {
        $pythonVersion = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Python OK: $pythonVersion" "SUCCESS"
        } else {
            throw "Python not found"
        }
    } catch {
        Write-Log "Pythonが見つかりません" "ERROR"
        Write-Log "https://www.python.org/ からPython 3.9以上をインストールしてください" "INFO"
        return $false
    }
    
    Push-Location $Path
    
    # requirements.txt確認・作成
    if (-not (Test-Path ".\requirements.txt")) {
        Write-Log "requirements.txtを作成中..." "FIX"
        $requirements = @"
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
websockets==12.0
lxml==4.9.3
pydantic==2.5.0
PyYAML==6.0.1
aiofiles==23.2.1
psutil==5.9.6
python-dotenv==1.0.0
"@
        Set-Content -Path ".\requirements.txt" -Value $requirements -Encoding UTF8
    }
    
    # 仮想環境確認・作成
    if ($Force -or -not (Test-Path ".\venv\Scripts\python.exe")) {
        Write-Log "仮想環境を作成中..." "FIX"
        
        if (Test-Path ".\venv") {
            Remove-Item ".\venv" -Recurse -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        & python -m venv venv 2>&1 | Out-Null
        
        if (-not (Test-Path ".\venv\Scripts\python.exe")) {
            Write-Log "仮想環境の作成に失敗" "ERROR"
            Pop-Location
            return $false
        }
    }
    
    # パッケージインストール
    Write-Log "依存パッケージを確認中..." "DEBUG"
    
    $checkScript = @"
import sys
try:
    import fastapi
    import uvicorn
    import lxml
    print('OK')
except ImportError as e:
    print(f'MISSING: {e}')
    sys.exit(1)
"@
    
    $result = $checkScript | & .\venv\Scripts\python.exe 2>&1
    
    if ($result -notlike "*OK*") {
        Write-Log "パッケージをインストール中..." "FIX"
        & .\venv\Scripts\pip.exe install --upgrade pip --quiet 2>&1 | Out-Null
        & .\venv\Scripts\pip.exe install -r requirements.txt --quiet 2>&1 | Out-Null
        
        # 再確認
        $result = $checkScript | & .\venv\Scripts\python.exe 2>&1
        if ($result -notlike "*OK*") {
            Write-Log "パッケージインストールに失敗" "ERROR"
            Pop-Location
            return $false
        }
    }
    
    Write-Log "バックエンド診断完了" "SUCCESS"
    Pop-Location
    return $true
}

# ============================================================================
# フロントエンド診断・修復
# ============================================================================
function Fix-Frontend {
    param([string]$Path)
    
    Write-Log "フロントエンド診断開始..." "INFO"
    
    # Node.js確認
    Write-Log "Node.js環境を確認中..." "DEBUG"
    try {
        $nodeVersion = & node --version 2>&1
        $npmVersion = & npm --version 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Node.js OK: $nodeVersion / npm $npmVersion" "SUCCESS"
        } else {
            throw "Node not found"
        }
    } catch {
        Write-Log "Node.jsが見つかりません" "ERROR"
        Write-Log "https://nodejs.org/ からNode.js 18以上をインストールしてください" "INFO"
        return $false
    }
    
    Push-Location $Path
    
    # package.json確認
    if (-not (Test-Path ".\package.json")) {
        Write-Log "package.jsonを作成中..." "FIX"
        $packageJson = @{
            name = "windows11-unattend-generator"
            version = "1.0.0"
            private = $true
            scripts = @{
                dev = "next dev -p 3050"
                build = "next build"
                start = "next start -p 3050"
            }
            dependencies = @{
                next = "14.0.4"
                react = "18.2.0"
                "react-dom" = "18.2.0"
                typescript = "5.3.3"
            }
        }
        $packageJson | ConvertTo-Json -Depth 10 | Set-Content -Path ".\package.json" -Encoding UTF8
    }
    
    # node_modules確認
    if ($Force -or -not (Test-Path ".\node_modules\next")) {
        Write-Log "Node.jsパッケージをインストール中..." "FIX"
        
        if (Test-Path ".\node_modules") {
            Remove-Item ".\node_modules" -Recurse -Force -ErrorAction SilentlyContinue
        }
        
        if (Test-Path ".\package-lock.json") {
            Remove-Item ".\package-lock.json" -Force -ErrorAction SilentlyContinue
        }
        
        & cmd /c "npm install" 2>&1 | Out-Null
        
        if (-not (Test-Path ".\node_modules\next")) {
            Write-Log "パッケージインストールに失敗" "ERROR"
            Pop-Location
            return $false
        }
    }
    
    # next.config.js確認
    if (-not (Test-Path ".\next.config.js")) {
        Write-Log "Next.js設定を作成中..." "FIX"
        $config = @"
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
}

module.exports = nextConfig
"@
        Set-Content -Path ".\next.config.js" -Value $config -Encoding UTF8
    }
    
    Write-Log "フロントエンド診断完了" "SUCCESS"
    Pop-Location
    return $true
}

# ============================================================================
# サーバー起動
# ============================================================================
function Start-Servers {
    param(
        [string]$BackendPath,
        [string]$FrontendPath
    )
    
    $IP = "192.168.3.92"
    
    # バックエンド起動
    Write-Log "バックエンドサーバーを起動中..." "INFO"
    
    $backendScript = @"
@echo off
cd /d "$BackendPath"
echo Starting Backend Server...
echo URL: http://$IP:8081
echo API Docs: http://$IP:8081/api/docs
echo.
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe main.py
) else (
    python main.py
)
"@
    
    $tempBackend = "$env:TEMP\start-backend-$(Get-Random).bat"
    Set-Content -Path $tempBackend -Value $backendScript -Encoding UTF8
    
    Start-Process cmd -ArgumentList "/k", $tempBackend -WindowStyle Minimized
    
    # 起動待機
    Write-Host -NoNewline "   待機中"
    $timeout = 30
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-Host -NoNewline "."
        
        try {
            $response = Invoke-WebRequest -Uri "http://$IP:8081/api/status" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host ""
                Write-Log "バックエンド起動成功" "SUCCESS"
                break
            }
        } catch {}
    }
    
    if ($elapsed -ge $timeout) {
        Write-Host ""
        Write-Log "バックエンド起動タイムアウト（処理は継続）" "WARNING"
    }
    
    # バックエンド安定待機
    Start-Sleep -Seconds 3
    
    # フロントエンド起動
    Write-Log "フロントエンドサーバーを起動中..." "INFO"
    
    $frontendScript = @"
@echo off
chcp 65001 > nul
cd /d "$FrontendPath"
echo Starting Frontend Server...
echo URL: http://$IP:3050
echo.
set NEXT_PUBLIC_API_URL=http://$IP:8081/api
set NEXT_PUBLIC_LOCAL_IP=$IP
npm run dev
"@
    
    $tempFrontend = "$env:TEMP\start-frontend-$(Get-Random).bat"
    Set-Content -Path $tempFrontend -Value $frontendScript -Encoding UTF8
    
    Start-Process cmd -ArgumentList "/k", $tempFrontend -WindowStyle Minimized
    
    Write-Log "フロントエンド起動処理開始（ビルドに時間がかかります）" "INFO"
}

# ============================================================================
# メイン処理
# ============================================================================

Clear-Host

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         フロントエンド＋バックエンド 統合自動診断・修復システム          ║" -ForegroundColor Cyan
Write-Host "║                  Windows 11 無人応答ファイル生成システム                 ║" -ForegroundColor Cyan
Write-Host "║                         全23項目完全対応版 v2.0                          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# オプション表示
Write-Log "実行オプション:" "INFO"
Write-Host "  詳細ログ: $(if($Verbose){'ON'}else{'OFF'})" -ForegroundColor Gray
Write-Host "  強制修復: $(if($Force){'ON'}else{'OFF'})" -ForegroundColor Gray
Write-Host "  最大リトライ: $MaxRetries" -ForegroundColor Gray
Write-Host ""

# パス設定
$backendPath = Join-Path $ScriptRoot "backend"
$frontendPath = Join-Path $ScriptRoot "frontend"

# 既存プロセスの確認と停止
Write-Log "既存プロセスを確認中..." "INFO"

$pythonProcs = Get-Process python* -ErrorAction SilentlyContinue | 
    Where-Object { $_.Path -like "*Generate-autounattendxml*" }

$nodeProcs = Get-Process node* -ErrorAction SilentlyContinue | 
    Where-Object { $_.CommandLine -like "*3050*" }

if ($pythonProcs -or $nodeProcs) {
    if (-not $Force) {
        $response = Read-Host "既存のサーバーが検出されました。再起動しますか？ (Y/N)"
        if ($response -ne 'Y' -and $response -ne 'y') {
            Write-Log "処理をキャンセルしました" "INFO"
            exit 0
        }
    }
    
    Write-Log "既存プロセスを停止中..." "WARNING"
    $pythonProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    $nodeProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "INFO"
Write-Host ""

# 診断・修復実行
$backendOK = $false
$frontendOK = $false

# バックエンド診断・修復
$retries = 0
while ($retries -lt $MaxRetries) {
    if ($retries -gt 0) {
        Write-Log "バックエンド診断リトライ ($retries/$MaxRetries)..." "WARNING"
    }
    
    if (Fix-Backend -Path $backendPath) {
        $backendOK = $true
        break
    }
    
    $retries++
    if ($retries -lt $MaxRetries) {
        Start-Sleep -Seconds 3
    }
}

Write-Host ""

# フロントエンド診断・修復
$retries = 0
while ($retries -lt $MaxRetries) {
    if ($retries -gt 0) {
        Write-Log "フロントエンド診断リトライ ($retries/$MaxRetries)..." "WARNING"
    }
    
    if (Fix-Frontend -Path $frontendPath) {
        $frontendOK = $true
        break
    }
    
    $retries++
    if ($retries -lt $MaxRetries) {
        Start-Sleep -Seconds 3
    }
}

Write-Host ""
Write-Log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "INFO"
Write-Host ""

# レポート表示
Write-Host "【診断結果】" -ForegroundColor Yellow
if ($backendOK) {
    Write-Host "  バックエンド:   ✅ 正常" -ForegroundColor Green
} else {
    Write-Host "  バックエンド:   ❌ 問題あり" -ForegroundColor Red
}

if ($frontendOK) {
    Write-Host "  フロントエンド: ✅ 正常" -ForegroundColor Green
} else {
    Write-Host "  フロントエンド: ❌ 問題あり" -ForegroundColor Red
}

Write-Host ""

# サーバー起動
if ($backendOK -and $frontendOK) {
    Write-Log "サーバーを起動します..." "INFO"
    Write-Host ""
    
    Start-Servers -BackendPath $backendPath -FrontendPath $frontendPath
    
    Start-Sleep -Seconds 3
    
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                      システム起動完了！                                  ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "📌 アクセスURL:" -ForegroundColor White
    Write-Host "   フロントエンド:  http://192.168.3.92:3050" -ForegroundColor Cyan
    Write-Host "   バックエンドAPI: http://192.168.3.92:8081" -ForegroundColor Cyan
    Write-Host "   API仕様書:      http://192.168.3.92:8081/api/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🛑 停止方法:" -ForegroundColor Yellow
    Write-Host "   各サーバーウィンドウで Ctrl+C" -ForegroundColor Gray
    Write-Host "   または .\Stop-WebUI.ps1 を実行" -ForegroundColor Gray
    Write-Host ""
    
    # ブラウザ起動
    Start-Sleep -Seconds 2
    Start-Process "http://192.168.3.92:3050"
    
} else {
    Write-Log "診断・修復に失敗しました" "ERROR"
    Write-Host ""
    
    if (-not $backendOK) {
        Write-Host "【バックエンドの対処法】" -ForegroundColor Yellow
        Write-Host "  1. Python 3.9以上をインストール" -ForegroundColor Gray
        Write-Host "  2. backend\venvフォルダを削除" -ForegroundColor Gray
        Write-Host "  3. このスクリプトを再実行" -ForegroundColor Gray
    }
    
    if (-not $frontendOK) {
        Write-Host ""
        Write-Host "【フロントエンドの対処法】" -ForegroundColor Yellow
        Write-Host "  1. Node.js 18以上をインストール" -ForegroundColor Gray
        Write-Host "  2. frontend\node_modulesフォルダを削除" -ForegroundColor Gray
        Write-Host "  3. このスクリプトを再実行" -ForegroundColor Gray
    }
}

Write-Host ""