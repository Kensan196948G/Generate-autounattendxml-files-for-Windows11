# ============================================================================
# Windows 11 無人応答ファイル生成システム - 優雅な停止スクリプト
# ============================================================================

param(
    [switch]$Force,       # 強制終了
    [int]$Timeout = 10    # タイムアウト（秒）
)

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Status {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    switch ($Type) {
        "Success" { Write-Host "[$timestamp] ✅ $Message" -ForegroundColor Green }
        "Error" { Write-Host "[$timestamp] ❌ $Message" -ForegroundColor Red }
        "Warning" { Write-Host "[$timestamp] ⚠️  $Message" -ForegroundColor Yellow }
        "Info" { Write-Host "[$timestamp] ℹ️  $Message" -ForegroundColor Cyan }
    }
}

function Stop-ServerGracefully {
    param(
        [string]$ProcessName,
        [string]$ServerType,
        [int]$Port,
        [int]$WaitSeconds = 5
    )
    
    Write-Status "$ServerType を停止中..." "Info"
    
    # プロセス検索
    $processes = Get-Process $ProcessName -ErrorAction SilentlyContinue
    
    if ($ProcessName -eq "python*") {
        $processes = $processes | Where-Object { 
            $_.Path -like "*Generate-autounattendxml*" -or 
            $_.CommandLine -like "*main.py*"
        }
    } elseif ($ProcessName -eq "node*") {
        $processes = $processes | Where-Object { 
            $_.CommandLine -like "*3050*" -or
            $_.CommandLine -like "*frontend*"
        }
    }
    
    if (-not $processes) {
        Write-Status "$ServerType プロセスが見つかりません" "Warning"
        return $true
    }
    
    foreach ($proc in $processes) {
        try {
            Write-Host "  PID $($proc.Id) を停止中..." -ForegroundColor Gray
            
            if (-not $Force) {
                # 優雅な停止を試みる（SIGTERM相当）
                $proc.CloseMainWindow() | Out-Null
                
                # 停止待機
                $waited = 0
                while (-not $proc.HasExited -and $waited -lt $WaitSeconds) {
                    Start-Sleep -Seconds 1
                    $waited++
                    Write-Host "." -NoNewline
                }
                Write-Host ""
            }
            
            # まだ実行中なら強制終了
            if (-not $proc.HasExited) {
                Write-Host "  強制終了中..." -ForegroundColor Yellow
                Stop-Process -Id $proc.Id -Force
                Start-Sleep -Seconds 1
            }
            
            Write-Status "  PID $($proc.Id) 停止完了" "Success"
            
        } catch {
            Write-Status "  PID $($proc.Id) 停止失敗: $_" "Error"
            return $false
        }
    }
    
    # ポート解放確認
    Start-Sleep -Seconds 2
    
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("127.0.0.1", $Port)
        $connection.Close()
        Write-Status "$ServerType ポート $Port がまだ使用中です" "Warning"
        return $false
    } catch {
        Write-Status "$ServerType ポート $Port が解放されました" "Success"
        return $true
    }
}

function Send-ShutdownSignal {
    param([string]$IP = "192.168.3.92")
    
    # バックエンドに優雅な停止シグナルを送信
    try {
        $shutdownEndpoint = "http://${IP}:8080/api/shutdown"
        $response = Invoke-WebRequest -Uri $shutdownEndpoint -Method POST `
            -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Status "停止シグナル送信成功" "Success"
            return $true
        }
    } catch {
        # エンドポイントが存在しない場合は通常の停止を続行
        if ($_.Exception.Response.StatusCode -ne 404) {
            Write-Status "停止シグナル送信失敗（通常停止を続行）" "Warning"
        }
    }
    
    return $false
}

function Cleanup-TempFiles {
    Write-Status "一時ファイルをクリーンアップ中..." "Info"
    
    # Next.js一時ファイル
    $nextTempPath = "$ScriptRoot\frontend\.next\cache"
    if (Test-Path $nextTempPath) {
        try {
            Remove-Item "$nextTempPath\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Status "  Next.js キャッシュをクリア" "Success"
        } catch {
            Write-Status "  キャッシュクリア失敗（次回起動時に自動クリア）" "Warning"
        }
    }
    
    # Python __pycache__
    $pycachePaths = Get-ChildItem "$ScriptRoot\backend" -Directory -Filter "__pycache__" -Recurse
    foreach ($path in $pycachePaths) {
        try {
            Remove-Item $path.FullName -Recurse -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    
    Write-Status "クリーンアップ完了" "Success"
}

# ============================================================================
# メイン処理
# ============================================================================

Clear-Host

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║                  WebUIシステム停止スクリプト                            ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
Write-Host ""

$startTime = Get-Date

# 停止シグナル送信（実装されている場合）
if (-not $Force) {
    Send-ShutdownSignal
    Start-Sleep -Seconds 2
}

# 監視プロセスの停止
Write-Status "監視プロセスを確認中..." "Info"
$monitorProcesses = Get-Process powershell -ErrorAction SilentlyContinue | 
    Where-Object { $_.CommandLine -like "*Monitor-Servers.ps1*" }

if ($monitorProcesses) {
    foreach ($proc in $monitorProcesses) {
        Write-Status "監視プロセス (PID: $($proc.Id)) を停止中..." "Info"
        Stop-Process -Id $proc.Id -Force
    }
    Start-Sleep -Seconds 1
}

# フロントエンド停止
$frontendStopped = Stop-ServerGracefully -ProcessName "node*" `
    -ServerType "フロントエンド" -Port 3050 -WaitSeconds $Timeout

# バックエンド停止
$backendStopped = Stop-ServerGracefully -ProcessName "python*" `
    -ServerType "バックエンド" -Port 8080 -WaitSeconds $Timeout

# CMD/PowerShellウィンドウのクリーンアップ
Write-Status "関連ウィンドウを確認中..." "Info"
$relatedWindows = Get-Process cmd, powershell -ErrorAction SilentlyContinue | 
    Where-Object { 
        $_.MainWindowTitle -like "*autounattend*" -or
        $_.MainWindowTitle -like "*WebUI*" -or
        $_.CommandLine -like "*Generate-autounattendxml*"
    }

if ($relatedWindows) {
    Write-Status "関連ウィンドウを閉じています..." "Info"
    $relatedWindows | ForEach-Object {
        try {
            $_.CloseMainWindow() | Out-Null
        } catch {}
    }
}

# 一時ファイルのクリーンアップ
if (-not $Force) {
    Cleanup-TempFiles
}

# 終了サマリー
$endTime = Get-Date
$duration = [math]::Round(($endTime - $startTime).TotalSeconds, 1)

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                         停止処理完了                                    ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📊 停止結果:" -ForegroundColor White
Write-Host "   フロントエンド: $(if($frontendStopped){'✅ 停止完了'}else{'⚠️  停止失敗'})" `
    -ForegroundColor $(if($frontendStopped){"Green"}else{"Yellow"})
Write-Host "   バックエンド:   $(if($backendStopped){'✅ 停止完了'}else{'⚠️  停止失敗'})" `
    -ForegroundColor $(if($backendStopped){"Green"}else{"Yellow"})
Write-Host ""
Write-Host "   処理時間: ${duration}秒" -ForegroundColor Gray
Write-Host ""

# 再起動オプション
Write-Host "🔄 再起動する場合:" -ForegroundColor Cyan
Write-Host "   .\Start-WebUI.ps1" -ForegroundColor White
Write-Host "   .\Start-WebUI-Enhanced.ps1 -AutoMonitor" -ForegroundColor White
Write-Host ""

if (-not $frontendStopped -or -not $backendStopped) {
    Write-Status "一部のプロセスが正常に停止しませんでした" "Warning"
    Write-Host "強制停止する場合: .\Stop-WebUI.ps1 -Force" -ForegroundColor Yellow
    Write-Host ""
}

Read-Host "Enterキーで終了"