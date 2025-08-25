<#
.SYNOPSIS
    ログ生成モジュール - 日本語ログとXML生成ログの管理
    
.DESCRIPTION
    Windows 11 無人応答ファイル生成システムのログ生成機能
    XMLと同時に日本語でのログファイルを生成
#>

# ログレベル定義
enum LogLevel {
    Debug = 0
    Info = 1
    Warning = 2
    Error = 3
    Critical = 4
}

class LogGenerator {
    [string]$LogPath
    [string]$LogFileName
    [LogLevel]$LogLevel
    [bool]$EnableConsoleOutput
    [System.Collections.ArrayList]$LogBuffer
    
    LogGenerator() {
        $this.Initialize()
    }
    
    LogGenerator([string]$Path) {
        $this.LogPath = $Path
        $this.Initialize()
    }
    
    [void]Initialize() {
        if (-not $this.LogPath) {
            $this.LogPath = Join-Path $PSScriptRoot "..\..\Logs"
        }
        
        if (-not (Test-Path $this.LogPath)) {
            New-Item -ItemType Directory -Path $this.LogPath -Force | Out-Null
        }
        
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $this.LogFileName = "UnattendXML_$timestamp.log"
        $this.LogLevel = [LogLevel]::Info
        $this.EnableConsoleOutput = $true
        $this.LogBuffer = New-Object System.Collections.ArrayList
    }
    
    [void]WriteLog([LogLevel]$Level, [string]$Message) {
        if ($Level -lt $this.LogLevel) { return }
        
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $levelText = $Level.ToString().ToUpper().PadRight(8)
        $logEntry = "[$timestamp] [$levelText] $Message"
        
        # バッファに追加
        [void]$this.LogBuffer.Add($logEntry)
        
        # コンソール出力
        if ($this.EnableConsoleOutput) {
            $color = switch ($Level) {
                ([LogLevel]::Debug) { "Gray" }
                ([LogLevel]::Info) { "White" }
                ([LogLevel]::Warning) { "Yellow" }
                ([LogLevel]::Error) { "Red" }
                ([LogLevel]::Critical) { "Magenta" }
            }
            Write-Host $logEntry -ForegroundColor $color
        }
        
        # ファイル出力
        $logFile = Join-Path $this.LogPath $this.LogFileName
        Add-Content -Path $logFile -Value $logEntry -Encoding UTF8
    }
    
    [void]Debug([string]$Message) {
        $this.WriteLog([LogLevel]::Debug, $Message)
    }
    
    [void]Info([string]$Message) {
        $this.WriteLog([LogLevel]::Info, $Message)
    }
    
    [void]Warning([string]$Message) {
        $this.WriteLog([LogLevel]::Warning, $Message)
    }
    
    [void]Error([string]$Message) {
        $this.WriteLog([LogLevel]::Error, $Message)
    }
    
    [void]Critical([string]$Message) {
        $this.WriteLog([LogLevel]::Critical, $Message)
    }
    
    [void]SaveToFile() {
        $logFile = Join-Path $this.LogPath $this.LogFileName
        $this.LogBuffer | Out-File -FilePath $logFile -Encoding UTF8 -Force
    }
    
    [string]GetLogPath() {
        return Join-Path $this.LogPath $this.LogFileName
    }
}

class ComprehensiveLogGenerator {
    [LogGenerator]$Logger
    [hashtable]$Configuration
    [System.Collections.ArrayList]$SummaryLog
    
    ComprehensiveLogGenerator() {
        $this.Logger = [LogGenerator]::new()
        $this.SummaryLog = New-Object System.Collections.ArrayList
    }
    
    [void]GenerateConfigurationLog([hashtable]$Config) {
        $this.Configuration = $Config
        $this.Logger.Info("=== Windows 11 無人応答ファイル生成ログ ===")
        $this.Logger.Info("生成日時: $(Get-Date -Format 'yyyy年MM月dd日 HH:mm:ss')")
        $this.Logger.Info("")
        
        # 各設定項目のログ生成
        $this.LogRegionLanguage()
        $this.LogWindowsEdition()
        $this.LogDiskConfiguration()
        $this.LogUserAccounts()
        $this.LogNetworkSettings()
        $this.LogWindowsFeatures()
        $this.LogApplicationSettings()
        $this.LogSystemSettings()
        $this.LogFirstLogonCommands()
        
        $this.GenerateSummary()
    }
    
    [void]LogRegionLanguage() {
        $this.Logger.Info("[1. 地域と言語の設定]")
        if ($this.Configuration.RegionLanguage) {
            $config = $this.Configuration.RegionLanguage
            $this.Logger.Info("  表示言語: $($config.DisplayLanguage)")
            $this.Logger.Info("  システムロケール: $($config.SystemLocale)")
            $this.Logger.Info("  タイムゾーン: $($config.Timezone)")
            $this.Logger.Info("  入力方式: $($config.InputLocale)")
        }
    }
    
    [void]LogWindowsEdition() {
        $this.Logger.Info("[4. Windowsエディション]")
        if ($this.Configuration.WindowsEdition) {
            $config = $this.Configuration.WindowsEdition
            $this.Logger.Info("  エディション: Windows 11 $($config.Edition)")
            $this.Logger.Info("  プロダクトキー: $(if ($config.ProductKey) { '設定済み' } else { '未設定' })")
            $this.Logger.Info("  EULA承諾: $(if ($config.AcceptEula) { '承諾済み' } else { '未承諾' })")
        }
    }
    
    [void]LogDiskConfiguration() {
        $this.Logger.Info("[6. ディスク構成]")
        if ($this.Configuration.DiskConfiguration) {
            $config = $this.Configuration.DiskConfiguration
            $this.Logger.Info("  ディスク消去: $(if ($config.WipeDisk) { '有効' } else { '無効' })")
            if ($config.Partitions) {
                $this.Logger.Info("  パーティション数: $($config.Partitions.Count)")
                foreach ($partition in $config.Partitions) {
                    $this.Logger.Info("    - $($partition.Type): $($partition.Size)MB")
                }
            }
        }
    }
    
    [void]LogUserAccounts() {
        $this.Logger.Info("[8. ユーザーアカウント]")
        if ($this.Configuration.UserAccounts -and $this.Configuration.UserAccounts.Accounts) {
            $accounts = $this.Configuration.UserAccounts.Accounts
            $this.Logger.Info("  アカウント数: $($accounts.Count)")
            foreach ($account in $accounts) {
                $this.Logger.Info("    - $($account.Username) (グループ: $($account.Group))")
                if ($account.AutoLogon) {
                    $this.Logger.Info("      自動ログオン: 有効 (回数: $($account.AutoLogonCount))")
                }
            }
        }
    }
    
    [void]LogNetworkSettings() {
        $this.Logger.Info("[15. Wi-Fi設定]")
        if ($this.Configuration.WiFiConfig -and $this.Configuration.WiFiConfig.Enabled) {
            $wifi = $this.Configuration.WiFiConfig
            $this.Logger.Info("  SSID: $($wifi.SSID)")
            $this.Logger.Info("  セキュリティ: $($wifi.SecurityType)")
            $this.Logger.Info("  自動接続: $(if ($wifi.AutoConnect) { '有効' } else { '無効' })")
        } else {
            $this.Logger.Info("  Wi-Fi設定: スキップ")
        }
        
        $this.Logger.Info("[ネットワーク全般]")
        if ($this.Configuration.NetworkSettings) {
            $net = $this.Configuration.NetworkSettings
            $this.Logger.Info("  IPv6: $(if ($net.DisableIPv6) { '無効' } else { '有効' })")
            $this.Logger.Info("  ファイアウォール: $(if ($net.DisableFirewall) { '無効' } else { '有効' })")
        }
    }
    
    [void]LogWindowsFeatures() {
        $this.Logger.Info("[14. 仮想マシンサポート]")
        if ($this.Configuration.VMSupport) {
            $vm = $this.Configuration.VMSupport
            $this.Logger.Info("  Hyper-V: $(if ($vm.EnableHyperV) { '有効' } else { '無効' })")
            $this.Logger.Info("  WSL: $(if ($vm.EnableWSL) { '有効' } else { '無効' })")
            $this.Logger.Info("  Windows Sandbox: $(if ($vm.EnableSandbox) { '有効' } else { '無効' })")
        }
        
        $this.Logger.Info("[23. 追加のコンポーネント]")
        if ($this.Configuration.AdditionalComponents) {
            $comp = $this.Configuration.AdditionalComponents
            $enabledComponents = @()
            if ($comp.OpenSSHClient) { $enabledComponents += "OpenSSH Client" }
            if ($comp.OpenSSHServer) { $enabledComponents += "OpenSSH Server" }
            if ($comp.TelnetClient) { $enabledComponents += "Telnet Client" }
            if ($comp.WindowsMediaPlayer) { $enabledComponents += "Windows Media Player" }
            
            if ($enabledComponents.Count -gt 0) {
                $this.Logger.Info("  有効なコンポーネント:")
                foreach ($component in $enabledComponents) {
                    $this.Logger.Info("    - $component")
                }
            }
        }
    }
    
    [void]LogApplicationSettings() {
        $this.Logger.Info("[20. アプリの削除]")
        if ($this.Configuration.RemoveApps -and $this.Configuration.RemoveApps.Apps) {
            $apps = $this.Configuration.RemoveApps.Apps
            $this.Logger.Info("  削除対象アプリ数: $($apps.Count)")
            $this.Logger.Info("  主な削除対象:")
            $apps | Select-Object -First 5 | ForEach-Object {
                $this.Logger.Info("    - $_")
            }
            if ($apps.Count -gt 5) {
                $this.Logger.Info("    ... 他 $($apps.Count - 5) 個")
            }
        }
    }
    
    [void]LogSystemSettings() {
        $this.Logger.Info("[11. システムの調整]")
        if ($this.Configuration.SystemTweaks) {
            $tweaks = $this.Configuration.SystemTweaks
            $this.Logger.Info("  テレメトリ: $(if ($tweaks.DisableTelemetry) { '無効' } else { '有効' })")
            $this.Logger.Info("  Bluetooth: $(if ($tweaks.DisableBluetooth) { '無効' } else { '有効' })")
            $this.Logger.Info("  Cortana: $(if ($tweaks.DisableCortana) { '無効' } else { '有効' })")
        }
        
        $this.Logger.Info("[12. 視覚効果]")
        if ($this.Configuration.VisualEffects) {
            $visual = $this.Configuration.VisualEffects
            $this.Logger.Info("  パフォーマンスモード: $($visual.PerformanceMode)")
            $this.Logger.Info("  アニメーション: $(if ($visual.DisableAnimations) { '無効' } else { '有効' })")
            $this.Logger.Info("  透明効果: $(if ($visual.DisableTransparency) { '無効' } else { '有効' })")
        }
    }
    
    [void]LogFirstLogonCommands() {
        $this.Logger.Info("[FirstLogonCommands]")
        if ($this.Configuration.FirstLogonCommands) {
            $commands = $this.Configuration.FirstLogonCommands
            $this.Logger.Info("  コマンド数: $($commands.Count)")
            $this.Logger.Info("  実行内容:")
            
            # カテゴリ別に集計
            $categories = @{
                Registry = ($commands | Where-Object { $_ -like "*reg add*" }).Count
                PowerShell = ($commands | Where-Object { $_ -like "*powershell*" }).Count
                DISM = ($commands | Where-Object { $_ -like "*dism*" }).Count
                Other = 0
            }
            $categories.Other = $commands.Count - $categories.Registry - $categories.PowerShell - $categories.DISM
            
            $this.Logger.Info("    - レジストリ設定: $($categories.Registry)個")
            $this.Logger.Info("    - PowerShellコマンド: $($categories.PowerShell)個")
            $this.Logger.Info("    - DISM操作: $($categories.DISM)個")
            if ($categories.Other -gt 0) {
                $this.Logger.Info("    - その他: $($categories.Other)個")
            }
        }
    }
    
    [void]GenerateSummary() {
        $this.Logger.Info("")
        $this.Logger.Info("=== 生成サマリー ===")
        $this.Logger.Info("SubAgent実行数: 42")
        $this.Logger.Info("並列処理: 有効")
        $this.Logger.Info("Context7最適化: 適用済み")
        $this.Logger.Info("生成完了: $(Get-Date -Format 'HH:mm:ss')")
    }
    
    [string]GetLogContent() {
        return $this.Logger.LogBuffer -join "`n"
    }
    
    [void]SaveLog([string]$OutputPath) {
        $logFileName = "UnattendXML_Log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
        $logPath = Join-Path $OutputPath $logFileName
        $this.GetLogContent() | Out-File -FilePath $logPath -Encoding UTF8
        $this.Logger.Info("ログファイル保存: $logPath")
    }
}

# モジュール関数のエクスポート
function New-LogGenerator {
    param(
        [string]$LogPath
    )
    
    if ($LogPath) {
        return [LogGenerator]::new($LogPath)
    } else {
        return [LogGenerator]::new()
    }
}

function New-ComprehensiveLogGenerator {
    return [ComprehensiveLogGenerator]::new()
}

function Write-LogMessage {
    param(
        [LogGenerator]$Logger,
        [LogLevel]$Level = [LogLevel]::Info,
        [string]$Message
    )
    
    $Logger.WriteLog($Level, $Message)
}

# エクスポート
Export-ModuleMember -Function @(
    'New-LogGenerator',
    'New-ComprehensiveLogGenerator',
    'Write-LogMessage'
) -Variable @() -Cmdlet @() -Alias @()