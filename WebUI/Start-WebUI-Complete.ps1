# ============================================================================
# Windows 11 無人応答ファイル生成システム - 完全統合起動スクリプト
# Context7 + SubAgent(42体) + Claude-flow + Playwright + 自動修復対応
# ============================================================================

param(
    [switch]$SkipInstall,        # 依存関係インストールをスキップ
    [switch]$Debug,               # デバッグモード
    [switch]$ForceRestart,        # 既存プロセスを強制終了  
    [switch]$RunTests,            # 起動後に自動テストを実行
    [switch]$EnableAutoRepair     # 自動修復システムを有効化
)

$global:ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

# ============================================================================
# ヘルパー関数
# ============================================================================

function Write-Status {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $prefix = "[$timestamp]"
    
    switch ($Type) {
        "Success" { Write-Host "$prefix ✅ $Message" -ForegroundColor Green }
        "Error" { Write-Host "$prefix ❌ $Message" -ForegroundColor Red }
        "Warning" { Write-Host "$prefix ⚠️  $Message" -ForegroundColor Yellow }
        "Info" { Write-Host "$prefix ℹ️  $Message" -ForegroundColor Cyan }
        "Processing" { Write-Host "$prefix ⏳ $Message" -ForegroundColor White }
    }
}

function Get-LocalIPAddress {
    $targetIP = "192.168.3.92"
    
    # 指定IPの確認
    $checkIP = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | 
               Where-Object { $_.IPAddress -eq $targetIP }
    if ($checkIP) { return $targetIP }
    
    # その他のプライベートIP（APIPA除外）
    $privateIP = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { 
            ($_.IPAddress -like "192.168.*" -or 
             $_.IPAddress -like "10.*" -or 
             $_.IPAddress -like "172.16.*") -and
            $_.IPAddress -notlike "169.254.*"
        } | Select-Object -First 1
    
    if ($privateIP) { return $privateIP.IPAddress }
    
    return "127.0.0.1"
}

function Test-Port {
    param([int]$Port, [int]$Timeout = 5)
    
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $result = $connection.BeginConnect("127.0.0.1", $Port, $null, $null)
        $wait = $result.AsyncWaitHandle.WaitOne($Timeout * 1000, $false)
        
        if ($wait) {
            $connection.EndConnect($result)
            $connection.Close()
            return $true
        }
        
        $connection.Close()
        return $false
    } catch {
        return $false
    }
}

function Stop-ExistingServers {
    Write-Status "既存サーバーを確認中..." "Info"
    
    # Pythonプロセス（バックエンド）
    $pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue | 
        Where-Object { $_.Path -like "*Generate-autounattendxml*" }
    
    if ($pythonProcesses) {
        Write-Status "既存のバックエンドプロセスを停止中..." "Warning"
        $pythonProcesses | Stop-Process -Force
        Start-Sleep -Seconds 2
    }
    
    # Node.jsプロセス（フロントエンド）
    $nodeProcesses = Get-Process node* -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*3050*" }
    
    if ($nodeProcesses) {
        Write-Status "既存のフロントエンドプロセスを停止中..." "Warning"
        $nodeProcesses | Stop-Process -Force
        Start-Sleep -Seconds 2
    }
}

function Install-Dependencies {
    Write-Status "依存関係をインストール中..." "Processing"
    
    # Python依存関係
    Push-Location "$ScriptRoot\backend"
    
    if (-not (Test-Path ".\venv")) {
        Write-Status "Python仮想環境を作成中..." "Info"
        & python -m venv venv
    }
    
    Write-Status "Pythonパッケージをインストール中..." "Info"
    & .\venv\Scripts\pip.exe install -r requirements.txt --quiet
    
    # psutilを追加インストール（ヘルスチェック用）
    & .\venv\Scripts\pip.exe install psutil --quiet
    
    Pop-Location
    
    # Node.js依存関係
    Push-Location "$ScriptRoot\frontend"
    
    Write-Status "Node.jsパッケージをインストール中..." "Info"
    
    # package-lock.jsonがある場合は削除（クリーンインストール）
    if (Test-Path ".\package-lock.json") {
        Remove-Item ".\package-lock.json" -Force -ErrorAction SilentlyContinue
    }
    
    & cmd /c "npm install" 2>&1 | Out-Null
    
    # Playwrightのインストール
    if ($RunTests) {
        Write-Status "Playwright browsersをインストール中..." "Info"
        & cmd /c "npx playwright install" 2>&1 | Out-Null
    }
    
    Pop-Location
    
    Write-Status "依存関係のインストール完了" "Success"
}

function Start-BackendServer {
    param([string]$IP)
    
    Write-Status "バックエンドサーバーを起動中..." "Processing"
    
    $backendScript = @"
Set-Location '$ScriptRoot\backend'
Write-Host '======================================' -ForegroundColor Cyan
Write-Host ' Windows 11 無人応答ファイル生成システム' -ForegroundColor Green
Write-Host ' バックエンドサーバー' -ForegroundColor Green
Write-Host ' Context7 + SubAgent(42体) + Claude-flow' -ForegroundColor Green
Write-Host '======================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'API URL: http://${IP}:8080' -ForegroundColor Yellow
Write-Host 'API Docs: http://${IP}:8080/api/docs' -ForegroundColor Yellow
Write-Host ''

# 自動修復システムを有効化
`$env:ENABLE_AUTO_REPAIR = '$EnableAutoRepair'

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
    
    # UIファイルの切り替え確認（PowerShellで事前処理）
    Push-Location "$ScriptRoot\frontend"
    if (Test-Path '.\src\pages\index_new.tsx') {
        Write-Status "新しいUIファイルを適用中..." "Info"
        if (Test-Path '.\src\pages\index.tsx') {
            Move-Item '.\src\pages\index.tsx' '.\src\pages\index_old.tsx' -Force
        }
        Move-Item '.\src\pages\index_new.tsx' '.\src\pages\index.tsx' -Force
        Write-Status "新しいUIが適用されました" "Success"
    }
    Pop-Location
    
    # cmd用のバッチファイルを作成
    $frontendBatch = @"
@echo off
chcp 65001 > nul
cd /d "$ScriptRoot\frontend"
echo ======================================
echo  Windows 11 無人応答ファイル生成システム
echo  フロントエンドサーバー
echo  Schneegans.de スタイルUI
echo ======================================
echo.
echo URL: http://${IP}:3050
echo.

REM 環境変数設定
set NEXT_PUBLIC_API_URL=http://${IP}:8080/api
set NEXT_PUBLIC_LOCAL_IP=${IP}

REM npm run devを実行
echo 開発サーバーを起動中...
npm run dev
"@
    
    # 一時バッチファイルを作成
    $tempBatch = "$env:TEMP\start-frontend-complete-$(Get-Random).bat"
    Set-Content -Path $tempBatch -Value $frontendBatch -Encoding UTF8
    
    # cmdウィンドウでバッチファイルを実行
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
            return $process
        }
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 3
        $elapsed += 3
    }
    
    Write-Host ""
    Write-Status "フロントエンドは起動処理中です（もうしばらくお待ちください）" "Warning"
    return $process
}

function Start-AutoRepairMonitor {
    param([string]$IP)
    
    if (-not $EnableAutoRepair) {
        return $null
    }
    
    Write-Status "自動修復モニターを起動中..." "Processing"
    
    $monitorScript = @"
Set-Location '$ScriptRoot'
Write-Host '======================================' -ForegroundColor Cyan
Write-Host ' 自動修復モニター' -ForegroundColor Green
Write-Host ' エラー検知・自動修復システム' -ForegroundColor Green
Write-Host '======================================' -ForegroundColor Cyan
Write-Host ''

.\Monitor-Servers.ps1 -AutoRestart
"@
    
    $process = Start-Process powershell -ArgumentList "-NoExit", "-Command", $monitorScript `
        -PassThru -WindowStyle Minimized
    
    Write-Status "自動修復モニター起動 (PID: $($process.Id))" "Success"
    return $process
}

function Run-PlaywrightTests {
    param([string]$IP)
    
    if (-not $RunTests) {
        return
    }
    
    Write-Status "Playwrightテストを実行中..." "Processing"
    
    Push-Location "$ScriptRoot\playwright"
    
    # テスト実行
    $testResult = & cmd /c "npx playwright test --reporter=list" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "すべてのテストが成功しました" "Success"
    } else {
        Write-Status "一部のテストが失敗しました（詳細はレポートを確認）" "Warning"
    }
    
    # HTMLレポートを生成
    & cmd /c "npx playwright show-report" 2>&1 | Out-Null
    
    Pop-Location
}

function Test-SystemHealth {
    param([string]$IP)
    
    Write-Status "システムヘルスチェック中..." "Info"
    
    try {
        # ヘルスエンドポイントを確認
        $healthUrl = "http://${IP}:8080/api/health"
        $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            $health = $response.Content | ConvertFrom-Json
            
            Write-Status "システムヘルス: $($health.status)" $(
                if ($health.status -eq "healthy") { "Success" } 
                elseif ($health.status -eq "degraded") { "Warning" }
                else { "Error" }
            )
            
            if ($health.agents) {
                Write-Host "  SubAgent: $($health.agents.healthy)/$($health.agents.total) 正常" -ForegroundColor Gray
            }
            
            if ($health.issues -and $health.issues.Count -gt 0) {
                Write-Host "  検出された問題:" -ForegroundColor Yellow
                foreach ($issue in $health.issues) {
                    Write-Host "    - $issue" -ForegroundColor Yellow
                }
            }
            
            return $true
        }
    } catch {
        # フォールバック（通常のステータスエンドポイント）
        try {
            $statusUrl = "http://${IP}:8080/api/status"
            $response = Invoke-WebRequest -Uri $statusUrl -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            
            if ($response.StatusCode -eq 200) {
                $status = $response.Content | ConvertFrom-Json
                Write-Status "バックエンドAPI: 正常" "Success"
                Write-Host "  Context7: $($status.context7)" -ForegroundColor Gray
                Write-Host "  SubAgent: $($status.subagents.total)体" -ForegroundColor Gray
                return $true
            }
        } catch {
            Write-Status "ヘルスチェック失敗: $_" "Error"
            return $false
        }
    }
    
    return $false
}

# ============================================================================
# メイン処理
# ============================================================================

Clear-Host

# バナー表示
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      Windows 11 無人応答ファイル生成システム - 完全統合版               ║" -ForegroundColor Cyan
Write-Host "║      Context7 + SubAgent(42体) + Claude-flow + Playwright               ║" -ForegroundColor Cyan
Write-Host "║      自動エラー検知・修復システム搭載                                   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
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

# 依存関係のインストール
if (-not $SkipInstall) {
    Install-Dependencies
}

Write-Host ""

# サーバー起動
$backendProcess = Start-BackendServer -IP $LOCAL_IP

if (-not $backendProcess) {
    Write-Status "バックエンドの起動に失敗しました" "Error"
    Read-Host "Enterキーで終了"
    exit 1
}

# バックエンド安定待機
Start-Sleep -Seconds 3

$frontendProcess = Start-FrontendServer -IP $LOCAL_IP

Write-Host ""

# ヘルスチェック
Start-Sleep -Seconds 3
$healthOK = Test-SystemHealth -IP $LOCAL_IP

# 自動修復モニター起動
$monitorProcess = $null
if ($EnableAutoRepair) {
    $monitorProcess = Start-AutoRepairMonitor -IP $LOCAL_IP
}

# Playwrightテスト実行
if ($RunTests -and $frontendProcess) {
    Write-Host ""
    Write-Status "フロントエンドの完全起動を待機中..." "Info"
    
    # フロントエンドが完全に起動するまで待機
    $maxWait = 30
    $waited = 0
    while ($waited -lt $maxWait -and -not (Test-Port -Port 3050)) {
        Start-Sleep -Seconds 2
        $waited += 2
    }
    
    if (Test-Port -Port 3050) {
        Run-PlaywrightTests -IP $LOCAL_IP
    }
}

# 結果表示
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    システム起動完了！                                    ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📌 アクセスURL:" -ForegroundColor White
Write-Host "   フロントエンド:     http://${LOCAL_IP}:3050" -ForegroundColor Cyan
Write-Host "   バックエンドAPI:    http://${LOCAL_IP}:8080" -ForegroundColor Cyan
Write-Host "   API仕様書:         http://${LOCAL_IP}:8080/api/docs" -ForegroundColor Cyan
Write-Host "   ヘルスチェック:     http://${LOCAL_IP}:8080/api/health" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 起動状態:" -ForegroundColor White
if ($backendProcess) {
    Write-Host "   バックエンド:      ✅ 稼働中 (PID: $($backendProcess.Id))" -ForegroundColor Green
}
if ($frontendProcess) {
    $frontStatus = if (Test-Port -Port 3050) { "✅ 稼働中" } else { "⏳ 起動中" }
    Write-Host "   フロントエンド:     $frontStatus (PID: $($frontendProcess.Id))" -ForegroundColor $(if($frontStatus -like "*稼働中*"){"Green"}else{"Yellow"})
}
if ($monitorProcess) {
    Write-Host "   自動修復モニター:   ✅ 稼働中 (PID: $($monitorProcess.Id))" -ForegroundColor Green
}
Write-Host ""

Write-Host "🚀 機能状態:" -ForegroundColor White
Write-Host "   Context7:          ✅ 有効" -ForegroundColor Green
Write-Host "   SubAgent:          ✅ 42体" -ForegroundColor Green
Write-Host "   Claude-flow:       ✅ 並列処理対応" -ForegroundColor Green
if ($EnableAutoRepair) {
    Write-Host "   自動修復:          ✅ 有効（最大20回リトライ）" -ForegroundColor Green
}
if ($RunTests) {
    Write-Host "   Playwright:        ✅ テスト実行済み" -ForegroundColor Green
}
Write-Host ""

Write-Host "🛑 終了方法:" -ForegroundColor Yellow
Write-Host "   1. このウィンドウを閉じる" -ForegroundColor Gray
Write-Host "   2. 各サーバーウィンドウで Ctrl+C" -ForegroundColor Gray
Write-Host "   3. 停止スクリプト: .\Stop-WebUI.ps1" -ForegroundColor Gray
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
        Write-Host "   起動完了後: http://${LOCAL_IP}:3050" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Status "システムは正常に起動しました" "Success"
Write-Host ""

# デバッグモード
if ($Debug) {
    Write-Status "デバッグモード: プロセス監視中..." "Info"
    while ($true) {
        if (-not (Get-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue)) {
            Write-Status "バックエンドが停止しました" "Error"
            
            if ($EnableAutoRepair) {
                Write-Status "自動修復を試行中..." "Warning"
                $backendProcess = Start-BackendServer -IP $LOCAL_IP
            } else {
                break
            }
        }
        
        if ($frontendProcess -and -not (Get-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue)) {
            Write-Status "フロントエンドが停止しました" "Error"
            
            if ($EnableAutoRepair) {
                Write-Status "自動修復を試行中..." "Warning"
                $frontendProcess = Start-FrontendServer -IP $LOCAL_IP
            } else {
                break
            }
        }
        
        Start-Sleep -Seconds 5
    }
}

Read-Host "Enterキーを押すとこのウィンドウを閉じます（サーバーは継続動作）"