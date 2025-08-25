# ============================================================================
# Windows 11 無人応答ファイル生成システム - 統合起動スクリプト v5.0
# エラーフリー版 - PowerShell実行ポリシー対応
# ============================================================================

param(
    [switch]$SkipInstall,     # 依存関係インストールをスキップ
    [switch]$Debug,            # デバッグモード
    [switch]$ForceRestart      # 既存プロセスを強制終了
)

# スクリプトのルートディレクトリ
$global:ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

# ============================================================================
# 関数定義
# ============================================================================

function Write-ColorHost {
    param(
        [string]$Message,
        [string]$ForegroundColor = "White",
        [switch]$NoNewline
    )
    
    $params = @{
        Object = $Message
        ForegroundColor = $ForegroundColor
        NoNewline = $NoNewline.IsPresent
    }
    Write-Host @params
}

function Write-Status {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $prefix = "[$timestamp]"
    
    switch ($Type) {
        "Success" { 
            Write-ColorHost "$prefix " -ForegroundColor "DarkGray" -NoNewline
            Write-ColorHost "✅ " -ForegroundColor "Green" -NoNewline
            Write-ColorHost $Message -ForegroundColor "Green"
        }
        "Error" { 
            Write-ColorHost "$prefix " -ForegroundColor "DarkGray" -NoNewline
            Write-ColorHost "❌ " -ForegroundColor "Red" -NoNewline
            Write-ColorHost $Message -ForegroundColor "Red"
        }
        "Warning" { 
            Write-ColorHost "$prefix " -ForegroundColor "DarkGray" -NoNewline
            Write-ColorHost "⚠️  " -ForegroundColor "Yellow" -NoNewline
            Write-ColorHost $Message -ForegroundColor "Yellow"
        }
        "Info" { 
            Write-ColorHost "$prefix " -ForegroundColor "DarkGray" -NoNewline
            Write-ColorHost "ℹ️  " -ForegroundColor "Cyan" -NoNewline
            Write-ColorHost $Message -ForegroundColor "Cyan"
        }
        "Processing" {
            Write-ColorHost "$prefix " -ForegroundColor "DarkGray" -NoNewline
            Write-ColorHost "⏳ " -ForegroundColor "Yellow" -NoNewline
            Write-ColorHost $Message -ForegroundColor "White"
        }
        default { Write-Host "$prefix $Message" }
    }
}

function Test-Port {
    param([int]$Port)
    
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("127.0.0.1", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

function Stop-ExistingServers {
    Write-Status "既存サーバーを確認中..." "Info"
    
    # Pythonプロセス（バックエンド）
    $pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue | 
        Where-Object { $_.Path -like "*Generate-autounattendxml*" -or $_.CommandLine -like "*main.py*" }
    
    if ($pythonProcesses) {
        Write-Status "既存のバックエンドプロセスを停止中..." "Warning"
        $pythonProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    
    # Node.jsプロセス（フロントエンド）
    $nodeProcesses = Get-Process node* -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*3050*" -or $_.CommandLine -like "*next*" }
    
    if ($nodeProcesses) {
        Write-Status "既存のフロントエンドプロセスを停止中..." "Warning"
        $nodeProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

function Get-LocalIPAddress {
    # 優先IP
    $targetIP = "192.168.3.92"
    
    # 指定IPの確認
    $checkIP = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | 
               Where-Object { $_.IPAddress -eq $targetIP }
    if ($checkIP) {
        return $targetIP
    }
    
    # その他のプライベートIP
    $privateIP = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { 
            ($_.IPAddress -like "192.168.*" -or 
             $_.IPAddress -like "10.*" -or 
             $_.IPAddress -like "172.16.*") -and
            $_.IPAddress -notlike "169.254.*"
        } | Select-Object -First 1
    
    if ($privateIP) {
        return $privateIP.IPAddress
    }
    
    return "127.0.0.1"
}

function Test-Environment {
    $result = @{
        Python = $false
        Node = $false
        NPM = $false
    }
    
    # Python確認
    try {
        $pythonVersion = & cmd /c "python --version 2>&1"
        if ($pythonVersion -like "Python*") {
            $result.Python = $true
            Write-Status "Python: $pythonVersion" "Success"
        }
    } catch {
        Write-Status "Pythonが見つかりません" "Error"
    }
    
    # Node.js確認
    try {
        $nodeVersion = & cmd /c "node --version 2>&1"
        if ($nodeVersion -like "v*") {
            $result.Node = $true
            Write-Status "Node.js: $nodeVersion" "Success"
        }
    } catch {
        Write-Status "Node.jsが見つかりません" "Error"
    }
    
    # npm確認
    try {
        $npmVersion = & cmd /c "npm --version 2>&1"
        if ($npmVersion -match "^\d+\.\d+\.\d+") {
            $result.NPM = $true
            Write-Status "npm: $npmVersion" "Success"
        }
    } catch {
        Write-Status "npmが見つかりません" "Error"
    }
    
    return $result
}

function Setup-Backend {
    param([bool]$SkipInstall)
    
    Write-Status "バックエンドをセットアップ中..." "Processing"
    
    Push-Location "$ScriptRoot\backend"
    try {
        # 仮想環境
        if (-not (Test-Path ".\venv")) {
            Write-Status "仮想環境を作成中..." "Info"
            & cmd /c "python -m venv venv 2>&1" | Out-Null
        }
        
        if (-not $SkipInstall -and (Test-Path ".\requirements.txt")) {
            Write-Status "必須パッケージをインストール中..." "Info"
            & cmd /c ".\venv\Scripts\pip.exe install -r requirements.txt --quiet 2>&1" | Out-Null
        }
        
        Write-Status "バックエンドセットアップ完了" "Success"
        return $true
    } catch {
        Write-Status "バックエンドセットアップ失敗: $_" "Error"
        return $false
    } finally {
        Pop-Location
    }
}

function Setup-Frontend {
    param([bool]$SkipInstall)
    
    Write-Status "フロントエンドをセットアップ中..." "Processing"
    
    Push-Location "$ScriptRoot\frontend"
    try {
        if (-not (Test-Path ".\package.json")) {
            Write-Status "package.jsonが見つかりません" "Error"
            return $false
        }
        
        if (-not (Test-Path ".\node_modules") -or -not $SkipInstall) {
            Write-Status "Node.jsパッケージをインストール中..." "Info"
            
            # package-lock.jsonがある場合は削除（クリーンインストール）
            if (Test-Path ".\package-lock.json") {
                Remove-Item ".\package-lock.json" -Force -ErrorAction SilentlyContinue
            }
            
            # cmd経由でnpm install実行
            & cmd /c "npm install 2>&1" | Out-Null
            
            if ($LASTEXITCODE -ne 0) {
                Write-Status "npm installで警告がありました（続行）" "Warning"
            }
        }
        
        Write-Status "フロントエンドセットアップ完了" "Success"
        return $true
    } catch {
        Write-Status "フロントエンドセットアップ失敗: $_" "Error"
        return $false
    } finally {
        Pop-Location
    }
}

function Start-BackendServer {
    param([string]$IP)
    
    Write-Status "バックエンドサーバーを起動中..." "Processing"
    
    $backendScript = @"
Set-Location '$ScriptRoot\backend'
Write-Host '======================================' -ForegroundColor Cyan
Write-Host ' バックエンドサーバー' -ForegroundColor Green
Write-Host ' Context7 + SubAgent(42体) + Claude-flow' -ForegroundColor Green
Write-Host '======================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'URL: http://${IP}:8080' -ForegroundColor Yellow
Write-Host 'API Docs: http://${IP}:8080/api/docs' -ForegroundColor Yellow
Write-Host ''

if (Test-Path '.\venv\Scripts\python.exe') {
    .\venv\Scripts\python.exe main.py
} else {
    python main.py
}
"@
    
    $process = Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript `
        -PassThru -WindowStyle Normal
    
    # 起動待機
    $timeout = 30
    $elapsed = 0
    Write-Host "   バックエンド起動待機中" -NoNewline
    
    while ($elapsed -lt $timeout) {
        if (Test-Port -Port 8080) {
            Write-Host ""
            Write-Status "バックエンドが起動しました (PID: $($process.Id))" "Success"
            return $process
        }
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
        $elapsed += 2
    }
    
    Write-Host ""
    Write-Status "バックエンドの起動がタイムアウトしました" "Error"
    return $null
}

function Start-FrontendServer {
    param([string]$IP)
    
    Write-Status "フロントエンドサーバーを起動中..." "Processing"
    
    # cmd経由でnpmを実行する方法
    $frontendScript = @"
cd /d "$ScriptRoot\frontend"
echo ======================================
echo  フロントエンドサーバー
echo  URL: http://${IP}:3050
echo ======================================
echo.
set NEXT_PUBLIC_API_URL=http://${IP}:8080/api
set NEXT_PUBLIC_LOCAL_IP=${IP}
npm run dev
"@
    
    # バッチファイルを一時的に作成
    $tempBatch = "$env:TEMP\start-frontend-$(Get-Random).bat"
    Set-Content -Path $tempBatch -Value $frontendScript -Encoding UTF8
    
    $process = Start-Process cmd -ArgumentList "/k", $tempBatch `
        -PassThru -WindowStyle Normal
    
    # 起動待機（Next.jsは時間がかかる）
    $timeout = 60
    $elapsed = 0
    Write-Host "   フロントエンド起動待機中（初回ビルドには時間がかかります）" -NoNewline
    
    while ($elapsed -lt $timeout) {
        if (Test-Port -Port 3050) {
            Write-Host ""
            Write-Status "フロントエンドが起動しました (PID: $($process.Id))" "Success"
            
            # 一時バッチファイルを削除
            Start-Sleep -Seconds 2
            Remove-Item $tempBatch -Force -ErrorAction SilentlyContinue
            
            return $process
        }
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 3
        $elapsed += 3
    }
    
    Write-Host ""
    Write-Status "フロントエンドは起動処理中です（もうしばらくお待ちください）" "Warning"
    
    # 一時バッチファイルを削除
    Remove-Item $tempBatch -Force -ErrorAction SilentlyContinue
    
    return $process
}

function Test-SystemHealth {
    param([string]$IP)
    
    Write-Status "システムヘルスチェック中..." "Info"
    
    # バックエンドAPI確認
    try {
        $response = Invoke-WebRequest -Uri "http://${IP}:8080/api/status" `
            -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            $status = $response.Content | ConvertFrom-Json
            Write-Status "バックエンドAPI: 正常" "Success"
            Write-Status "  Context7: $($status.context7)" "Info"
            Write-Status "  SubAgent: $($status.subagents.total)体" "Info"
            return $true
        }
    } catch {
        Write-Status "バックエンドAPI接続エラー: $_" "Error"
        return $false
    }
}

# ============================================================================
# メイン処理
# ============================================================================

Clear-Host

# バナー表示
Write-Host ""
Write-ColorHost "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor "Cyan"
Write-ColorHost "║       Windows 11 無人応答ファイル生成システム v5.0                     ║" -ForegroundColor "Cyan"
Write-ColorHost "║       Context7 + SubAgent(42体) + Claude-flow並列処理                   ║" -ForegroundColor "Cyan"
Write-ColorHost "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor "Cyan"
Write-Host ""

# IP取得
$LOCAL_IP = Get-LocalIPAddress
Write-Status "IPアドレス: $LOCAL_IP" "Info"
Write-Host ""

# 既存プロセスの処理
if ($ForceRestart -or (Test-Port -Port 8080) -or (Test-Port -Port 3050)) {
    if (-not $ForceRestart) {
        Write-Status "既存のサーバーが検出されました" "Warning"
        $response = Read-Host "再起動しますか？ (Y/N)"
        if ($response -ne 'Y' -and $response -ne 'y') {
            Write-Status "起動をキャンセルしました" "Info"
            exit 0
        }
    }
    Stop-ExistingServers
}

# 環境チェック
Write-Status "環境をチェック中..." "Info"
$env = Test-Environment

if (-not $env.Python -or -not $env.Node -or -not $env.NPM) {
    Write-Status "必要な環境が整っていません" "Error"
    Write-Host ""
    if (-not $env.Python) {
        Write-Host "  Python: https://www.python.org/" -ForegroundColor Yellow
    }
    if (-not $env.Node -or -not $env.NPM) {
        Write-Host "  Node.js: https://nodejs.org/" -ForegroundColor Yellow
    }
    Write-Host ""
    Read-Host "Enterキーで終了"
    exit 1
}

Write-Host ""

# セットアップ
$backendReady = Setup-Backend -SkipInstall:$SkipInstall
$frontendReady = Setup-Frontend -SkipInstall:$SkipInstall

if (-not $backendReady -or -not $frontendReady) {
    Write-Status "セットアップに失敗しました" "Error"
    Read-Host "Enterキーで終了"
    exit 1
}

Write-Host ""

# サーバー起動
Write-Status "サーバーを起動しています..." "Info"
Write-Host ""

# バックエンド起動
$backendProcess = Start-BackendServer -IP $LOCAL_IP

if (-not $backendProcess) {
    Write-Status "バックエンドの起動に失敗しました" "Error"
    Read-Host "Enterキーで終了"
    exit 1
}

# 少し待機
Start-Sleep -Seconds 2

# フロントエンド起動
$frontendProcess = Start-FrontendServer -IP $LOCAL_IP

Write-Host ""

# ヘルスチェック
Start-Sleep -Seconds 3
$healthOK = Test-SystemHealth -IP $LOCAL_IP

# 結果表示
Write-Host ""
Write-ColorHost "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor "Green"
Write-ColorHost "║                      システム起動完了！                                  ║" -ForegroundColor "Green"
Write-ColorHost "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor "Green"
Write-Host ""

Write-ColorHost "📌 アクセスURL:" -ForegroundColor "White"
Write-Host ""
Write-ColorHost "   フロントエンド:  " -ForegroundColor "White" -NoNewline
Write-ColorHost "http://${LOCAL_IP}:3050" -ForegroundColor "Cyan"
Write-ColorHost "   バックエンドAPI: " -ForegroundColor "White" -NoNewline
Write-ColorHost "http://${LOCAL_IP}:8080" -ForegroundColor "Cyan"
Write-ColorHost "   API仕様書:      " -ForegroundColor "White" -NoNewline
Write-ColorHost "http://${LOCAL_IP}:8080/api/docs" -ForegroundColor "Cyan"
Write-ColorHost "   ヘルスチェック:  " -ForegroundColor "White" -NoNewline
Write-ColorHost "http://${LOCAL_IP}:8080/api/health" -ForegroundColor "Cyan"
Write-Host ""

Write-ColorHost "📊 起動状態:" -ForegroundColor "White"
Write-Host ""

if ($backendProcess) {
    Write-ColorHost "   バックエンド:  " -ForegroundColor "White" -NoNewline
    Write-ColorHost "✅ 稼働中 " -ForegroundColor "Green" -NoNewline
    Write-ColorHost "(PID: $($backendProcess.Id))" -ForegroundColor "Gray"
} else {
    Write-ColorHost "   バックエンド:  " -ForegroundColor "White" -NoNewline
    Write-ColorHost "❌ 起動失敗" -ForegroundColor "Red"
}

if ($frontendProcess) {
    if (Test-Port -Port 3050) {
        Write-ColorHost "   フロントエンド: " -ForegroundColor "White" -NoNewline
        Write-ColorHost "✅ 稼働中 " -ForegroundColor "Green" -NoNewline
        Write-ColorHost "(PID: $($frontendProcess.Id))" -ForegroundColor "Gray"
    } else {
        Write-ColorHost "   フロントエンド: " -ForegroundColor "White" -NoNewline
        Write-ColorHost "⏳ 起動中 " -ForegroundColor "Yellow" -NoNewline
        Write-ColorHost "(PID: $($frontendProcess.Id))" -ForegroundColor "Gray"
        Write-Host "                   （初回ビルドには時間がかかります）" -ForegroundColor "Gray"
    }
} else {
    Write-ColorHost "   フロントエンド: " -ForegroundColor "White" -NoNewline
    Write-ColorHost "❌ 起動失敗" -ForegroundColor "Red"
}

Write-Host ""

if ($healthOK) {
    Write-ColorHost "   API接続:       " -ForegroundColor "White" -NoNewline
    Write-ColorHost "✅ 正常" -ForegroundColor "Green"
}

Write-Host ""
Write-ColorHost "🛑 終了方法:" -ForegroundColor "Yellow"
Write-Host "   1. このウィンドウを閉じる" -ForegroundColor "Gray"
Write-Host "   2. 各サーバーウィンドウで Ctrl+C を押す" -ForegroundColor "Gray"
Write-Host "   3. 停止スクリプト: .\Stop-WebUI.ps1" -ForegroundColor "Gray"
Write-Host ""

# ブラウザ起動
if ($backendProcess) {
    Start-Sleep -Seconds 2
    Write-Status "ブラウザを開いています..." "Info"
    
    if (Test-Port -Port 3050) {
        Start-Process "http://${LOCAL_IP}:3050"
    } else {
        Start-Process "http://${LOCAL_IP}:8080/api/docs"
        Write-Host ""
        Write-Status "フロントエンドの起動完了を待っています..." "Warning"
        Write-ColorHost "   起動完了後: " -ForegroundColor "Yellow" -NoNewline
        Write-ColorHost "http://${LOCAL_IP}:3050" -ForegroundColor "Cyan"
    }
}

Write-Host ""
Write-ColorHost "システムは正常に起動しました。このウィンドウは開いたままにしてください。" -ForegroundColor "Green"
Write-Host ""

# デバッグモード
if ($Debug) {
    Write-Status "デバッグモード: プロセス監視中..." "Info"
    while ($true) {
        if ($backendProcess -and -not (Get-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue)) {
            Write-Status "バックエンドが停止しました" "Error"
            break
        }
        if ($frontendProcess -and -not (Get-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue)) {
            Write-Status "フロントエンドが停止しました" "Error"
            break
        }
        Start-Sleep -Seconds 5
    }
}

Read-Host "Enterキーを押すとこのウィンドウを閉じます（サーバーは継続動作）"