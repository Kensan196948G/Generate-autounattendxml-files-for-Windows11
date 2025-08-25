# ============================================================================
# サーバー監視・自動復旧スクリプト
# ============================================================================

param(
    [int]$CheckInterval = 10,  # チェック間隔（秒）
    [switch]$AutoRestart       # 自動再起動を有効化
)

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Status {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $prefix = "[$timestamp]"
    
    switch ($Type) {
        "Success" { 
            Write-Host "$prefix ✅ $Message" -ForegroundColor Green
        }
        "Error" { 
            Write-Host "$prefix ❌ $Message" -ForegroundColor Red
        }
        "Warning" { 
            Write-Host "$prefix ⚠️  $Message" -ForegroundColor Yellow
        }
        "Info" { 
            Write-Host "$prefix ℹ️  $Message" -ForegroundColor Cyan
        }
    }
}

function Test-ServerHealth {
    param(
        [string]$ServerType,
        [int]$Port,
        [string]$HealthEndpoint = $null
    )
    
    # ポート確認
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("127.0.0.1", $Port)
        $connection.Close()
        
        # HTTPヘルスチェック
        if ($HealthEndpoint) {
            try {
                $response = Invoke-WebRequest -Uri $HealthEndpoint -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    return @{
                        Status = "Healthy"
                        Message = "正常稼働中"
                    }
                }
            } catch {
                return @{
                    Status = "Degraded"
                    Message = "ポート開放済み、APIレスポンスなし"
                }
            }
        }
        
        return @{
            Status = "Running"
            Message = "ポート開放済み"
        }
    } catch {
        return @{
            Status = "Down"
            Message = "サーバー停止"
        }
    }
}

function Restart-Server {
    param(
        [string]$ServerType,
        [string]$ScriptPath
    )
    
    Write-Status "$ServerType を再起動中..." "Warning"
    
    $IP = "192.168.3.92"
    
    switch ($ServerType) {
        "Backend" {
            # Pythonプロセスを停止
            Get-Process python* -ErrorAction SilentlyContinue | 
                Where-Object { $_.Path -like "*Generate-autounattendxml*" } |
                Stop-Process -Force
            
            Start-Sleep -Seconds 2
            
            # バックエンドを再起動
            $backendScript = @"
cd /d "$ScriptPath\backend"
echo ======================================
echo  バックエンドサーバー再起動
echo  Context7 + SubAgent(42体)
echo ======================================
echo.

if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe main.py
) else (
    python main.py
)
"@
            
            $tempBatch = "$env:TEMP\restart-backend-$(Get-Random).bat"
            Set-Content -Path $tempBatch -Value $backendScript -Encoding UTF8
            Start-Process cmd -ArgumentList "/k", $tempBatch -WindowStyle Normal
        }
        "Frontend" {
            # Node.jsプロセスを停止
            Get-Process node* -ErrorAction SilentlyContinue | 
                Where-Object { $_.CommandLine -like "*3050*" } |
                Stop-Process -Force
            
            Start-Sleep -Seconds 2
            
            # フロントエンドを再起動（バッチファイル経由）
            $frontendScript = @"
@echo off
chcp 65001 > nul
cd /d "$ScriptPath\frontend"
echo ======================================
echo  フロントエンドサーバー再起動
echo ======================================
echo.

REM 環境変数設定
set NEXT_PUBLIC_API_URL=http://${IP}:8080/api
set NEXT_PUBLIC_LOCAL_IP=${IP}

REM npm run devを実行
npm run dev
"@
            
            $tempBatch = "$env:TEMP\restart-frontend-$(Get-Random).bat"
            Set-Content -Path $tempBatch -Value $frontendScript -Encoding UTF8
            Start-Process cmd -ArgumentList "/k", $tempBatch -WindowStyle Normal
        }
    }
}

# ============================================================================
# メインループ
# ============================================================================

Clear-Host
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                     サーバー監視モニター                                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$IP = "192.168.3.92"
$backendUrl = "http://${IP}:8080/api/status"
$frontendUrl = "http://${IP}:3050"

Write-Status "監視を開始しました (間隔: ${CheckInterval}秒)" "Info"
if ($AutoRestart) {
    Write-Status "自動再起動: 有効" "Warning"
}
Write-Host ""

$consecutiveFailures = @{
    Backend = 0
    Frontend = 0
}

while ($true) {
    # バックエンドチェック
    $backendHealth = Test-ServerHealth -ServerType "Backend" -Port 8080 -HealthEndpoint $backendUrl
    
    switch ($backendHealth.Status) {
        "Healthy" {
            Write-Status "Backend API: $($backendHealth.Message)" "Success"
            $consecutiveFailures.Backend = 0
        }
        "Degraded" {
            Write-Status "Backend API: $($backendHealth.Message)" "Warning"
            $consecutiveFailures.Backend++
        }
        "Down" {
            Write-Status "Backend API: $($backendHealth.Message)" "Error"
            $consecutiveFailures.Backend++
            
            if ($AutoRestart -and $consecutiveFailures.Backend -ge 3) {
                Restart-Server -ServerType "Backend" -ScriptPath $ScriptRoot
                $consecutiveFailures.Backend = 0
            }
        }
    }
    
    # フロントエンドチェック
    $frontendHealth = Test-ServerHealth -ServerType "Frontend" -Port 3050
    
    switch ($frontendHealth.Status) {
        "Running" {
            Write-Status "Frontend: $($frontendHealth.Message)" "Success"
            $consecutiveFailures.Frontend = 0
        }
        "Down" {
            Write-Status "Frontend: $($frontendHealth.Message)" "Error"
            $consecutiveFailures.Frontend++
            
            if ($AutoRestart -and $consecutiveFailures.Frontend -ge 3) {
                Restart-Server -ServerType "Frontend" -ScriptPath $ScriptRoot
                $consecutiveFailures.Frontend = 0
            }
        }
    }
    
    # API詳細情報取得
    if ($backendHealth.Status -eq "Healthy") {
        try {
            $response = Invoke-WebRequest -Uri $backendUrl -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            $status = $response.Content | ConvertFrom-Json
            Write-Host "  └─ Context7: $($status.context7) | SubAgents: $($status.subagents.total)体" -ForegroundColor Gray
        } catch {}
    }
    
    Write-Host ""
    
    # スリープ
    Start-Sleep -Seconds $CheckInterval
    
    # キー入力チェック（終了用）
    if ([Console]::KeyAvailable) {
        $key = [Console]::ReadKey($true)
        if ($key.Key -eq [ConsoleKey]::Q) {
            Write-Status "監視を終了します" "Info"
            break
        }
    }
}