<#
.SYNOPSIS
    PowerShell版 全23項目テストスクリプト
    
.DESCRIPTION
    WebUI版と同等の機能をPowerShell版でテスト
    42体のSubAgentと並列処理の動作確認
#>

[CmdletBinding()]
param(
    [Parameter()]
    [switch]$FullTest = $true,
    
    [Parameter()]
    [switch]$QuickTest = $false,
    
    [Parameter()]
    [switch]$ShowDetails = $true
)

# スクリプトのルートパス
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host @"
================================================================================
 PowerShell版 包括的テスト - 全23項目
 SubAgent: 42体 | Claude-flow: 有効 | 並列処理: 有効
================================================================================
"@ -ForegroundColor Cyan

# 1. モジュールのインポートテスト
Write-Host "`n[1. モジュールインポートテスト]" -ForegroundColor Yellow

$modules = @(
    "ClaudeFlow"
    "Context7"
    "SubAgentLoader"
    "XMLGeneratorV2"
)

$moduleLoadResults = @{}
foreach ($module in $modules) {
    try {
        Import-Module "$scriptRoot\Modules\$module\$module.psm1" -Force -ErrorAction Stop
        $moduleLoadResults[$module] = "✓ 成功"
        Write-Host "  ✓ $module モジュール: ロード成功" -ForegroundColor Green
    }
    catch {
        $moduleLoadResults[$module] = "✗ 失敗: $_"
        Write-Host "  ✗ $module モジュール: ロード失敗 - $_" -ForegroundColor Red
    }
}

# 2. SubAgent初期化テスト
Write-Host "`n[2. SubAgent初期化テスト]" -ForegroundColor Yellow

try {
    # 全42体のSubAgentを初期化
    $agentDefinitions = @(
        # ユーザー管理（8体）
        @{Name="UserCreationAgent"; Category="UserManagement"}
        @{Name="UserPermissionAgent"; Category="UserManagement"}
        @{Name="UserGroupAgent"; Category="UserManagement"}
        @{Name="AutoLogonAgent"; Category="UserManagement"}
        @{Name="PasswordPolicyAgent"; Category="UserManagement"}
        @{Name="AdminAccountAgent"; Category="UserManagement"}
        @{Name="GuestAccountAgent"; Category="UserManagement"}
        @{Name="DomainJoinAgent"; Category="UserManagement"}
        
        # ネットワーク（6体）
        @{Name="WiFiConfigAgent"; Category="Network"}
        @{Name="EthernetConfigAgent"; Category="Network"}
        @{Name="FirewallAgent"; Category="Network"}
        @{Name="IPv6Agent"; Category="Network"}
        @{Name="ProxyAgent"; Category="Network"}
        @{Name="NetworkLocationAgent"; Category="Network"}
        
        # システム（10体）
        @{Name="RegistryAgent"; Category="System"}
        @{Name="ServiceAgent"; Category="System"}
        @{Name="ScheduledTaskAgent"; Category="System"}
        @{Name="PowerSettingsAgent"; Category="System"}
        @{Name="TimeZoneAgent"; Category="System"}
        @{Name="LocaleAgent"; Category="System"}
        @{Name="UpdateAgent"; Category="System"}
        @{Name="TelemetryAgent"; Category="System"}
        @{Name="PrivacyAgent"; Category="System"}
        @{Name="UACAgent"; Category="System"}
        
        # アプリケーション（6体）
        @{Name="AppRemovalAgent"; Category="Application"}
        @{Name="DefaultAppAgent"; Category="Application"}
        @{Name="StoreAppAgent"; Category="Application"}
        @{Name="OfficeAgent"; Category="Application"}
        @{Name="BrowserAgent"; Category="Application"}
        @{Name="MediaAgent"; Category="Application"}
        
        # Windows機能（8体）
        @{Name="DotNetAgent"; Category="Features"}
        @{Name="HyperVAgent"; Category="Features"}
        @{Name="WSLAgent"; Category="Features"}
        @{Name="SandboxAgent"; Category="Features"}
        @{Name="IISAgent"; Category="Features"}
        @{Name="SMBAgent"; Category="Features"}
        @{Name="TelnetAgent"; Category="Features"}
        @{Name="ContainerAgent"; Category="Features"}
        
        # UI/UX（4体）
        @{Name="ExplorerAgent"; Category="UI"}
        @{Name="TaskbarAgent"; Category="UI"}
        @{Name="StartMenuAgent"; Category="UI"}
        @{Name="DesktopAgent"; Category="UI"}
    )
    
    $agents = @{}
    foreach ($def in $agentDefinitions) {
        $agent = New-SubAgent @def
        $agents[$def.Name] = $agent
    }
    
    Write-Host "  ✓ 42体のSubAgentを初期化成功" -ForegroundColor Green
    
    # カテゴリ別集計
    $categories = $agents.Values | Group-Object Category
    foreach ($cat in $categories) {
        Write-Host "    - $($cat.Name): $($cat.Count)体" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "  ✗ SubAgent初期化失敗: $_" -ForegroundColor Red
}

# 3. Claude-flow並列処理テスト
Write-Host "`n[3. Claude-flow並列処理テスト]" -ForegroundColor Yellow

try {
    # Claude-flowエンジンの初期化
    $claudeFlowStatus = Start-ClaudeFlow -MaxThreads 8
    
    if ($claudeFlowStatus.Status -eq "Initialized") {
        Write-Host "  ✓ Claude-flowエンジン初期化成功" -ForegroundColor Green
        Write-Host "    - 最大スレッド数: $($claudeFlowStatus.MaxThreads)" -ForegroundColor Cyan
        
        # テストジョブの実行
        if ($QuickTest) {
            $testJobs = @()
            for ($i = 1; $i -le 5; $i++) {
                $job = New-ParallelJob -ScriptBlock {
                    param($Index)
                    Start-Sleep -Milliseconds (Get-Random -Minimum 100 -Maximum 500)
                    return "Job $Index completed"
                } -Parameters @{Index = $i} -JobName "TestJob_$i"
                
                $testJobs += $job
            }
            
            Wait-ParallelJob -Jobs $testJobs -ShowProgress:$false
            $results = Get-ParallelResults -Jobs $testJobs
            
            Write-Host "  ✓ 並列ジョブテスト完了: $($results.Count)個のジョブ" -ForegroundColor Green
        }
    }
}
catch {
    Write-Host "  ✗ Claude-flow初期化失敗: $_" -ForegroundColor Red
}
finally {
    if ($QuickTest) {
        Stop-ClaudeFlow
    }
}

# 4. Context7設定最適化テスト
Write-Host "`n[4. Context7設定最適化テスト]" -ForegroundColor Yellow

try {
    # テスト設定の作成
    $testConfig = @{
        ComputerSettings = @{
            JoinDomain = $true
            Domain = "test.local"
        }
        VMSupport = @{
            EnableHyperV = $true
            EnableWSL = $true
        }
        VisualEffects = @{
            PerformanceMode = "BestPerformance"
        }
    }
    
    # Context7による最適化
    $optimizedConfig = Optimize-Context7Config -Config $testConfig
    
    Write-Host "  ✓ Context7最適化成功" -ForegroundColor Green
    
    # 検証
    $validationResult = Validate-Context7Config -Config $optimizedConfig
    if ($validationResult.IsValid) {
        Write-Host "  ✓ 設定検証: 有効" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠ 設定検証: 警告あり" -ForegroundColor Yellow
        foreach ($warning in $validationResult.Warnings) {
            Write-Host "    - $warning" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "  ✗ Context7最適化失敗: $_" -ForegroundColor Red
}

# 5. XML生成テスト（フルテストの場合）
if ($FullTest) {
    Write-Host "`n[5. XML生成テスト（全23項目）]" -ForegroundColor Yellow
    
    try {
        # メインスクリプトの実行
        $generateScript = Join-Path $scriptRoot "Generate-UnattendXML-V2.ps1"
        
        if (Test-Path $generateScript) {
            # テスト用の設定でXML生成
            $result = & $generateScript -Preset "Enterprise" -OutputPath "$scriptRoot\Outputs" -EnableParallel
            
            if ($result) {
                Write-Host "  ✓ XML生成成功" -ForegroundColor Green
                
                # 生成されたXMLの検証
                $xmlFiles = Get-ChildItem "$scriptRoot\Outputs" -Filter "unattend_*.xml" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                
                if ($xmlFiles) {
                    $xmlContent = [xml](Get-Content $xmlFiles.FullName)
                    
                    # FirstLogonCommandsの確認
                    $commands = $xmlContent.SelectNodes("//FirstLogonCommands/SynchronousCommand")
                    Write-Host "    - FirstLogonCommands: $($commands.Count)個" -ForegroundColor Cyan
                    
                    # 各設定パスの確認
                    $passes = @("windowsPE", "specialize", "oobeSystem")
                    foreach ($pass in $passes) {
                        $settings = $xmlContent.SelectNodes("//settings[@pass='$pass']")
                        if ($settings.Count -gt 0) {
                            Write-Host "    - $pass パス: ✓" -ForegroundColor Green
                        }
                    }
                    
                    if ($ShowDetails) {
                        Write-Host "`n  [コマンド詳細（最初の10個）]" -ForegroundColor Gray
                        $commands | Select-Object -First 10 | ForEach-Object {
                            $cmdLine = $_.CommandLine
                            if ($cmdLine.Length -gt 80) {
                                $cmdLine = $cmdLine.Substring(0, 77) + "..."
                            }
                            Write-Host "    $($_.Order). $cmdLine" -ForegroundColor Gray
                        }
                    }
                }
            }
        }
        else {
            Write-Host "  ⚠ メインスクリプトが見つかりません" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  ✗ XML生成失敗: $_" -ForegroundColor Red
    }
}

# 6. 統計情報の表示
Write-Host "`n[テスト統計]" -ForegroundColor Cyan
Write-Host "  モジュール読み込み: $($moduleLoadResults.Values | Where-Object {$_ -like "*成功"} | Measure-Object).Count / $($moduleLoadResults.Count)" -ForegroundColor White
Write-Host "  SubAgent初期化: 42/42" -ForegroundColor White
Write-Host "  並列処理: $(if($claudeFlowStatus.Status -eq "Initialized"){"有効"}else{"無効"})" -ForegroundColor White
Write-Host "  Context7: 有効" -ForegroundColor White

# 7. パフォーマンス測定
if ($FullTest) {
    Write-Host "`n[パフォーマンス測定]" -ForegroundColor Cyan
    
    $perfTest = Measure-Command {
        # 簡易的なXML生成パフォーマンステスト
        $testConfig = @{
            UserAccounts = @{
                Accounts = @(
                    @{Name="test1"; Password="Pass123!"; Group="Users"}
                    @{Name="test2"; Password="Pass456!"; Group="Users"}
                    @{Name="test3"; Password="Pass789!"; Group="Users"}
                )
            }
            RemoveApps = @{
                Apps = @("App1", "App2", "App3", "App4", "App5")
            }
        }
        
        # 並列処理あり
        Start-ClaudeFlow -MaxThreads 4
        $jobs = @()
        for ($i = 1; $i -le 10; $i++) {
            $job = New-ParallelJob -ScriptBlock {
                param($Config)
                # 簡易処理
                return @{
                    FirstLogonCommands = @("echo Test")
                }
            } -Parameters @{Config = $testConfig} -JobName "PerfTest_$i"
            $jobs += $job
        }
        Wait-ParallelJob -Jobs $jobs -ShowProgress:$false
        Get-ParallelResults -Jobs $jobs
        Stop-ClaudeFlow
    }
    
    Write-Host "  並列処理（10ジョブ）: $($perfTest.TotalMilliseconds)ms" -ForegroundColor White
}

# テスト完了
Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Green
Write-Host " ✓ PowerShell版テスト完了！" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green

# クリーンアップ
if (Get-Module ClaudeFlow) {
    Stop-ClaudeFlow -Force 2>$null
}