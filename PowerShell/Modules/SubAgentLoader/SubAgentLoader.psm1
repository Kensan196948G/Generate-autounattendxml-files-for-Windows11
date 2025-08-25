<#
.SYNOPSIS
    SubAgentローダー - 42体のエージェント管理システム
    
.DESCRIPTION
    各機能別のSubAgentを動的にロード・管理するシステム
#>

Export-ModuleMember -Function @(
    'New-SubAgent'
    'Invoke-SubAgent'
    'Get-SubAgentStatus'
    'Register-SubAgentHandler'
)

# SubAgentレジストリ
$script:SubAgentRegistry = @{}
$script:SubAgentHandlers = @{}

function New-SubAgent {
    <#
    .SYNOPSIS
        新しいSubAgentを作成
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name,
        
        [Parameter(Mandatory)]
        [ValidateSet("UserManagement", "Network", "System", "Application", "Features", "UI")]
        [string]$Category,
        
        [Parameter()]
        [scriptblock]$ProcessBlock,
        
        [Parameter()]
        [hashtable]$Properties = @{}
    )
    
    # デフォルトの処理ブロック
    if (-not $ProcessBlock) {
        $ProcessBlock = Get-DefaultProcessBlock -Name $Name -Category $Category
    }
    
    $agent = [PSCustomObject]@{
        Name = $Name
        Category = $Category
        Process = $ProcessBlock
        Properties = $Properties
        Status = "Ready"
        LastRun = $null
        LastResult = $null
    }
    
    # レジストリに登録
    $script:SubAgentRegistry[$Name] = $agent
    
    Write-Verbose "SubAgent '$Name' (カテゴリ: $Category) を作成"
    
    return $agent
}

function Get-DefaultProcessBlock {
    <#
    .SYNOPSIS
        エージェント別のデフォルト処理ブロックを取得
    #>
    param(
        [string]$Name,
        [string]$Category
    )
    
    switch ($Name) {
        # ユーザー管理エージェント群
        "UserCreationAgent" {
            return {
                param($Config)
                $results = @()
                foreach ($account in $Config.UserAccounts.Accounts) {
                    $results += @{
                        Type = "UserAccount"
                        Name = $account.Name
                        Password = ConvertTo-Base64Password $account.Password
                        Group = $account.Group
                        Commands = @(
                            "net user `"$($account.Name)`" /add"
                            "net localgroup `"$($account.Group)`" `"$($account.Name)`" /add"
                        )
                    }
                }
                return $results
            }
        }
        
        "WiFiConfigAgent" {
            return {
                param($Config)
                if ($Config.WiFiSettings.SetupMode -eq "configure") {
                    return @{
                        Type = "WiFiProfile"
                        SSID = $Config.WiFiSettings.SSID
                        Password = $Config.WiFiSettings.Password
                        Authentication = $Config.WiFiSettings.AuthType
                        Encryption = $Config.WiFiSettings.Encryption
                        AutoConnect = $Config.WiFiSettings.ConnectAutomatically
                    }
                }
                return $null
            }
        }
        
        "RegistryAgent" {
            return {
                param($Config)
                $commands = @()
                
                # エクスプローラー設定
                if ($Config.ExplorerSettings.ShowFileExtensions) {
                    $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v HideFileExt /t REG_DWORD /d 0 /f'
                }
                
                # タスクバー設定
                if ($Config.StartTaskbar.TaskbarAlignment -eq "Left") {
                    $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v TaskbarAl /t REG_DWORD /d 0 /f'
                }
                
                # テレメトリ無効化
                if ($Config.SystemTweaks.DisableTelemetry) {
                    $commands += 'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f'
                }
                
                return @{
                    Type = "Registry"
                    FirstLogonCommands = $commands
                }
            }
        }
        
        "AppRemovalAgent" {
            return {
                param($Config)
                $commands = @()
                foreach ($app in $Config.RemoveApps.Apps) {
                    $commands += "powershell -Command `"Get-AppxPackage *$app* | Remove-AppxPackage`""
                }
                return @{
                    Type = "AppRemoval"
                    FirstLogonCommands = $commands
                }
            }
        }
        
        "HyperVAgent" {
            return {
                param($Config)
                $commands = @()
                if ($Config.VMSupport.EnableHyperV) {
                    $commands += "dism /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart"
                }
                if ($Config.VMSupport.EnableWSL) {
                    $commands += "dism /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart"
                }
                if ($Config.VMSupport.EnableWSL2) {
                    $commands += "dism /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart"
                }
                return @{
                    Type = "WindowsFeatures"
                    FirstLogonCommands = $commands
                }
            }
        }
        
        "ExplorerAgent" {
            return {
                param($Config)
                $commands = @()
                $settings = $Config.ExplorerSettings
                
                if ($settings.ShowHiddenFiles) {
                    $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v Hidden /t REG_DWORD /d 1 /f'
                }
                
                if ($settings.ShowProtectedOSFiles) {
                    $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v ShowSuperHidden /t REG_DWORD /d 1 /f'
                }
                
                if ($settings.LaunchTo -eq "ThisPC") {
                    $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v LaunchTo /t REG_DWORD /d 1 /f'
                }
                
                return @{
                    Type = "ExplorerSettings"
                    FirstLogonCommands = $commands
                }
            }
        }
        
        "TaskbarAgent" {
            return {
                param($Config)
                $commands = @()
                $settings = $Config.StartTaskbar
                
                # タスクバー位置
                $alignValue = if ($settings.TaskbarAlignment -eq "Left") { 0 } else { 1 }
                $commands += "reg add `"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced`" /v TaskbarAl /t REG_DWORD /d $alignValue /f"
                
                # 検索ボタン
                $searchValue = switch ($settings.TaskbarSearch) {
                    "Hidden" { 0 }
                    "Icon" { 1 }
                    "Box" { 2 }
                    default { 1 }
                }
                $commands += "reg add `"HKCU\Software\Microsoft\Windows\CurrentVersion\Search`" /v SearchboxTaskbarMode /t REG_DWORD /d $searchValue /f"
                
                # ウィジェット
                if (-not $settings.TaskbarWidgets) {
                    $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v TaskbarDa /t REG_DWORD /d 0 /f'
                }
                
                # チャット
                if (-not $settings.TaskbarChat) {
                    $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v TaskbarMn /t REG_DWORD /d 0 /f'
                }
                
                return @{
                    Type = "TaskbarSettings"
                    FirstLogonCommands = $commands
                }
            }
        }
        
        "DesktopAgent" {
            return {
                param($Config)
                $commands = @()
                $settings = $Config.DesktopSettings
                
                # デスクトップアイコン
                $icons = @{
                    Computer = "{20D04FE0-3AEA-1069-A2D8-08002B30309D}"
                    UserFiles = "{59031a47-3f72-44a7-89c5-5595fe6b30ee}"
                    Network = "{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}"
                    RecycleBin = "{645FF040-5081-101B-9F08-00AA002F954E}"
                    ControlPanel = "{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}"
                }
                
                foreach ($icon in $icons.GetEnumerator()) {
                    $showValue = if ($settings."Show$($icon.Key)") { 0 } else { 1 }
                    $commands += "reg add `"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel`" /v `"$($icon.Value)`" /t REG_DWORD /d $showValue /f"
                }
                
                # 視覚効果
                if ($Config.VisualEffects.PerformanceMode -eq "BestPerformance") {
                    $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f'
                }
                
                # 透明効果
                if (-not $Config.VisualEffects.Transparency) {
                    $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f'
                }
                
                # アニメーション
                if (-not $Config.VisualEffects.Animations) {
                    $commands += 'reg add "HKCU\Control Panel\Desktop\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f'
                }
                
                return @{
                    Type = "DesktopSettings"
                    FirstLogonCommands = $commands
                }
            }
        }
        
        default {
            # デフォルトの処理ブロック
            return {
                param($Config)
                return @{
                    Type = "Default"
                    Agent = $Name
                    Category = $Category
                    Status = "NotImplemented"
                }
            }
        }
    }
}

function Invoke-SubAgent {
    <#
    .SYNOPSIS
        SubAgentを実行
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name,
        
        [Parameter(Mandatory)]
        [object]$Config,
        
        [Parameter()]
        [hashtable]$AdditionalParams = @{}
    )
    
    $agent = $script:SubAgentRegistry[$Name]
    
    if (-not $agent) {
        throw "SubAgent '$Name' が見つかりません"
    }
    
    try {
        $agent.Status = "Running"
        $agent.LastRun = Get-Date
        
        # 処理の実行
        $result = & $agent.Process -Config $Config @AdditionalParams
        
        $agent.Status = "Completed"
        $agent.LastResult = $result
        
        return $result
    }
    catch {
        $agent.Status = "Failed"
        $agent.LastResult = @{
            Error = $_.Exception.Message
        }
        throw
    }
}

function Get-SubAgentStatus {
    <#
    .SYNOPSIS
        全SubAgentの状態を取得
    #>
    [CmdletBinding()]
    param(
        [Parameter()]
        [string]$Category
    )
    
    $agents = $script:SubAgentRegistry.Values
    
    if ($Category) {
        $agents = $agents | Where-Object { $_.Category -eq $Category }
    }
    
    $status = @{
        Total = $agents.Count
        Ready = ($agents | Where-Object { $_.Status -eq "Ready" }).Count
        Running = ($agents | Where-Object { $_.Status -eq "Running" }).Count
        Completed = ($agents | Where-Object { $_.Status -eq "Completed" }).Count
        Failed = ($agents | Where-Object { $_.Status -eq "Failed" }).Count
        Agents = $agents | Select-Object Name, Category, Status, LastRun
    }
    
    return $status
}

function Register-SubAgentHandler {
    <#
    .SYNOPSIS
        カスタムSubAgentハンドラーを登録
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name,
        
        [Parameter(Mandatory)]
        [scriptblock]$Handler
    )
    
    $script:SubAgentHandlers[$Name] = $Handler
    Write-Verbose "SubAgentハンドラー '$Name' を登録"
}

# ユーティリティ関数

function ConvertTo-Base64Password {
    <#
    .SYNOPSIS
        パスワードをWindows用にBase64エンコード
    #>
    param(
        [string]$Password
    )
    
    $passwordWithSuffix = $Password + "Password"
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($passwordWithSuffix)
    return [Convert]::ToBase64String($bytes)
}

function Initialize-AllSubAgents {
    <#
    .SYNOPSIS
        全42体のSubAgentを初期化
    #>
    [CmdletBinding()]
    param()
    
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
    
    foreach ($def in $agentDefinitions) {
        New-SubAgent @def
    }
    
    Write-Information "42体のSubAgentを初期化完了" -InformationAction Continue
}

# エクスポート
Export-ModuleMember -Function @(
    'New-SubAgent',
    'Get-SubAgentProcessBlock',
    'Initialize-AllSubAgents'
) -Variable @() -Cmdlet @() -Alias @()