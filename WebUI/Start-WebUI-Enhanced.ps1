# ============================================================================
# Windows 11 無人応答ファイル生成システム - 拡張起動スクリプト v5.0
# 自動リトライ・ヘルスモニタリング対応版
# ============================================================================

param(
    [switch]$SkipInstall,     # 依存関係インストールをスキップ
    [switch]$Debug,            # デバッグモード
    [switch]$ForceRestart,     # 既存プロセスを強制終了
    [switch]$AutoMonitor,      # 自動監視モード
    [int]$MaxRetries = 3       # 最大リトライ回数
)

$global:ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

# ============================================================================
# 関数定義
# ============================================================================

function Write-Status {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $prefix = "[$timestamp]"
    
    switch ($Type) {
        "Success" { Write-Host "$prefix [OK] $Message" -ForegroundColor Green }
        "Error" { Write-Host "$prefix [ERROR] $Message" -ForegroundColor Red }
        "Warning" { Write-Host "$prefix [WARN] $Message" -ForegroundColor Yellow }
        "Info" { Write-Host "$prefix [INFO] $Message" -ForegroundColor Cyan }
        "Processing" { Write-Host "$prefix [PROC] $Message" -ForegroundColor White }
    }
}

function Test-PortWithRetry {
    param(
        [int]$Port,
        [int]$MaxAttempts = 10,
        [int]$DelaySeconds = 3
    )
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $connection = New-Object System.Net.Sockets.TcpClient
            $connection.Connect("127.0.0.1", $Port)
            $connection.Close()
            return $true
        } catch {
            if ($i -lt $MaxAttempts) {
                Write-Host "." -NoNewline
                Start-Sleep -Seconds $DelaySeconds
            }
        }
    }
    return $false
}

function Start-ServerWithRetry {
    param(
        [string]$ServerType,
        [string]$IP,
        [int]$Port,
        [scriptblock]$StartScript,
        [int]$MaxRetries = 3
    )
    
    $retryCount = 0
    $process = $null
    
    while ($retryCount -lt $MaxRetries) {
        $retryCount++
        Write-Status "$ServerType 起動試行 $retryCount/$MaxRetries" "Processing"
        
        # サーバー起動
        $process = & $StartScript
        
        if ($process) {
            Write-Host "   ポート $Port の応答待機中" -NoNewline
            
            if (Test-PortWithRetry -Port $Port) {
                Write-Host ""
                Write-Status "$ServerType 起動成功 (PID: $($process.Id))" "Success"
                return $process
            }
            
            Write-Host ""
            Write-Status "$ServerType 起動タイムアウト (試行 $retryCount)" "Warning"
            
            # プロセス停止
            if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
                Stop-Process -Id $process.Id -Force
                Start-Sleep -Seconds 2
            }
        }
    }
    
    Write-Status "$ServerType の起動に失敗しました（全試行失敗）" "Error"
    return $null
}

function Test-APIHealth {
    param([string]$IP)
    
    $healthEndpoint = "http://${IP}:8080/api/health"
    $maxAttempts = 5
    
    for ($i = 1; $i -le $maxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $healthEndpoint -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            $health = $response.Content | ConvertFrom-Json
            
            Write-Status "API ヘルスチェック完了" "Success"
            Write-Host "  状態: $($health.status)" -ForegroundColor $(
                switch($health.status) {
                    "healthy" { "Green" }
                    "degraded" { "Yellow" }
                    default { "Red" }
                }
            )
            
            if ($health.system) {
                Write-Host "  CPU: $([math]::Round($health.system.cpu_percent, 1))%" -ForegroundColor Gray
                Write-Host "  メモリ: $([math]::Round($health.system.memory.percent, 1))%" -ForegroundColor Gray
            }
            
            if ($health.agents) {
                Write-Host "  エージェント: $($health.agents.healthy)/$($health.agents.total) 正常" -ForegroundColor Gray
            }
            
            if ($health.issues -and $health.issues.Count -gt 0) {
                Write-Host "  問題:" -ForegroundColor Yellow
                foreach ($issue in $health.issues) {
                    Write-Host "    - $issue" -ForegroundColor Yellow
                }
            }
            
            return $health.status -eq "healthy" -or $health.status -eq "degraded"
            
        } catch {
            if ($i -lt $maxAttempts) {
                Write-Host "   ヘルスチェック再試行 ($i/$maxAttempts)..." -ForegroundColor Yellow
                Start-Sleep -Seconds 2
            }
        }
    }
    
    return $false
}

function Start-BackendServerEnhanced {
    param([string]$IP)
    
    $startScript = {
        $backendCmd = @"
Set-Location '$ScriptRoot\backend'
Write-Host '======================================'
Write-Host ' バックエンドサーバー (拡張版)'
Write-Host '======================================'
if (Test-Path '.\venv\Scripts\python.exe') {
    # psutilインストール確認
    .\venv\Scripts\pip.exe show psutil 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'psutilをインストール中...'
        .\venv\Scripts\pip.exe install psutil --quiet
    }
    .\venv\Scripts\python.exe main.py
} else {
    python main.py
}
"@
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -PassThru -WindowStyle Normal
    }
    
    return Start-ServerWithRetry -ServerType "バックエンド" -IP $IP -Port 8080 -StartScript $startScript -MaxRetries $MaxRetries
}

function Start-FrontendServerEnhanced {
    param([string]$IP)
    
    $startScript = {
        $frontendCmd = @"
cd /d $ScriptRoot\frontend
echo ======================================
echo  フロントエンドサーバー (拡張版)
echo ======================================
set NEXT_PUBLIC_API_URL=http://${IP}:8080/api
set NEXT_PUBLIC_LOCAL_IP=${IP}
npm run dev
"@
        Start-Process cmd -ArgumentList "/k", $frontendCmd -PassThru -WindowStyle Normal
    }
    
    return Start-ServerWithRetry -ServerType "フロントエンド" -IP $IP -Port 3050 -StartScript $startScript -MaxRetries $MaxRetries
}

function Start-MonitorProcess {
    param([string]$IP)
    
    Write-Status "監視プロセスを起動中..." "Info"
    
    $monitorScript = @"
Set-Location '$ScriptRoot'
.\Monitor-Servers.ps1 -AutoRestart
"@
    
    $process = Start-Process powershell -ArgumentList "-NoExit", "-Command", $monitorScript -PassThru -WindowStyle Minimized
    
    Write-Status "監視プロセス起動 (PID: $($process.Id))" "Success"
    return $process
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

# ============================================================================
# メイン処理
# ============================================================================

Clear-Host

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Windows 11 無人応答ファイル生成システム WebUI v5.0 (拡張版)        ║" -ForegroundColor Cyan
Write-Host "║     自動リトライ・ヘルスモニタリング対応                                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# IP取得
$LOCAL_IP = Get-LocalIPAddress
Write-Status "IPアドレス: $LOCAL_IP" "Info"

# 既存プロセスの停止
if ($ForceRestart) {
    Write-Status "既存サーバーを停止中..." "Warning"
    Get-Process python*, node* -ErrorAction SilentlyContinue | 
        Where-Object { $_.Path -like "*Generate-autounattendxml*" } |
        Stop-Process -Force
    Start-Sleep -Seconds 2
}

Write-Host ""

# バックエンド起動（リトライ付き）
$backendProcess = Start-BackendServerEnhanced -IP $LOCAL_IP

if (-not $backendProcess) {
    Write-Status "バックエンドの起動に失敗しました" "Error"
    Read-Host "Press Enter to exit"
    exit 1
}

# バックエンドの安定待機
Start-Sleep -Seconds 3

# フロントエンド起動（リトライ付き）
$frontendProcess = Start-FrontendServerEnhanced -IP $LOCAL_IP

Write-Host ""

# ヘルスチェック実行
$healthOK = Test-APIHealth -IP $LOCAL_IP

# 監視プロセス起動（オプション）
$monitorProcess = $null
if ($AutoMonitor -and $backendProcess) {
    $monitorProcess = Start-MonitorProcess -IP $LOCAL_IP
}

# 結果表示
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    システム起動完了（拡張版）                           ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "[URL] アクセスURL:" -ForegroundColor White
Write-Host "   フロントエンド:  http://${LOCAL_IP}:3050" -ForegroundColor Cyan
Write-Host "   バックエンドAPI: http://${LOCAL_IP}:8080" -ForegroundColor Cyan
Write-Host "   API仕様書:      http://${LOCAL_IP}:8080/api/docs" -ForegroundColor Cyan
Write-Host "   ヘルスチェック:  http://${LOCAL_IP}:8080/api/health" -ForegroundColor Cyan
Write-Host ""

Write-Host "[STATUS] 起動状態:" -ForegroundColor White
if ($backendProcess) {
    Write-Host "   バックエンド:   [OK] 稼働中 (PID: $($backendProcess.Id))" -ForegroundColor Green
}
if ($frontendProcess) {
    $frontStatus = if (Test-PortWithRetry -Port 3050 -MaxAttempts 1) { "[OK] 稼働中" } else { "[WAIT] 起動中" }
    Write-Host "   フロントエンド:  $frontStatus (PID: $($frontendProcess.Id))" -ForegroundColor $(if($frontStatus -like "*稼働中*"){"Green"}else{"Yellow"})
}
if ($monitorProcess) {
    Write-Host "   監視プロセス:    [OK] 稼働中 (PID: $($monitorProcess.Id))" -ForegroundColor Green
}
Write-Host ""

if ($healthOK) {
    Write-Host "   ヘルスステータス: [OK] 正常" -ForegroundColor Green
} else {
    Write-Host "   ヘルスステータス: [WAIT] 確認中" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[STOP] 終了方法:" -ForegroundColor Yellow
Write-Host "   1. このウィンドウを閉じる" -ForegroundColor Gray
Write-Host "   2. 各サーバーウィンドウで Ctrl+C" -ForegroundColor Gray
Write-Host ""

# ブラウザ起動
if ($backendProcess) {
    Start-Sleep -Seconds 2
    if (Test-PortWithRetry -Port 3050 -MaxAttempts 1) {
        Start-Process "http://${LOCAL_IP}:3050"
    } else {
        Start-Process "http://${LOCAL_IP}:8080/api/docs"
    }
}

Write-Host ""
Write-Status "システムは正常に起動しました" "Success"
Write-Host ""

if ($Debug) {
    Write-Status "デバッグモード: 継続監視中..." "Info"
    while ($true) {
        if (-not (Get-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue)) {
            Write-Status "バックエンドが停止しました" "Error"
            break
        }
        Start-Sleep -Seconds 5
    }
}

Read-Host "Press Enter to exit"