# SubAgentリファレンス - 42体の自律型エージェント詳細仕様

## 目次
1. [SubAgentシステム概要](#subagentシステム概要)
2. [ユーザー管理エージェント（8体）](#ユーザー管理エージェント8体)
3. [ネットワークエージェント（6体）](#ネットワークエージェント6体)
4. [システムエージェント（10体）](#システムエージェント10体)
5. [アプリケーションエージェント（6体）](#アプリケーションエージェント6体)
6. [Windows機能エージェント（8体）](#windows機能エージェント8体)
7. [UI/UXエージェント（4体）](#uiuxエージェント4体)
8. [エージェント間連携](#エージェント間連携)
9. [カスタムエージェント開発](#カスタムエージェント開発)

---

## SubAgentシステム概要

### アーキテクチャ
```
┌─────────────────────────────────────────┐
│         SubAgent Orchestrator           │
│            (中央制御)                    │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼───┐   ┌───▼───┐   ┌───▼───┐
│User   │   │Network│   │System │
│Agents │   │Agents │   │Agents │
│(8体)   │   │(6体)   │   │(10体)  │
└────────┘   └────────┘   └────────┘
    │            │            │
┌───▼───┐   ┌───▼───┐   ┌───▼───┐
│App    │   │Feature│   │UI/UX  │
│Agents │   │Agents │   │Agents │
│(6体)   │   │(8体)   │   │(4体)   │
└────────┘   └────────┘   └────────┘
```

### 基本クラス構造
```powershell
class SubAgent {
    [string]$Name
    [string]$Category
    [string]$Description
    [hashtable]$Configuration
    [ScriptBlock]$ProcessBlock
    [string]$Status
    [object]$Result
    
    [void]Execute([hashtable]$Config) {
        # エージェント実行ロジック
    }
    
    [object]GetResult() {
        return $this.Result
    }
}
```

---

## ユーザー管理エージェント（8体）

### 1. UserCreationAgent
**責務:** ユーザーアカウントの作成と初期設定

```powershell
@{
    Name = "UserCreationAgent"
    Category = "UserManagement"
    Description = "ローカルユーザーアカウントの作成"
    
    InputParameters = @{
        Username = [string]    # ユーザー名
        Password = [string]    # パスワード
        FullName = [string]    # フルネーム
        Description = [string] # 説明
    }
    
    OutputFormat = @{
        UserAccounts = @{
            LocalAccounts = @{
                LocalAccount = @{
                    Name = $Username
                    Password = @{
                        Value = $EncodedPassword
                    }
                    DisplayName = $FullName
                    Description = $Description
                }
            }
        }
    }
    
    Commands = @(
        "net user $Username $Password /add",
        "net user $Username /fullname:`"$FullName`"",
        "wmic useraccount where name='$Username' set Description='$Description'"
    )
}
```

### 2. UserPermissionAgent
**責務:** ユーザー権限の設定と管理

```powershell
@{
    Name = "UserPermissionAgent"
    Category = "UserManagement"
    Description = "ユーザー権限とアクセス制御の設定"
    
    InputParameters = @{
        Username = [string]
        Permissions = [array]  # 権限リスト
        DenyPermissions = [array]  # 拒否権限リスト
    }
    
    Capabilities = @(
        "ローカルログオン権限",
        "リモートデスクトップ権限",
        "ファイル共有アクセス権限",
        "レジストリアクセス権限",
        "サービス管理権限"
    )
    
    RegistryKeys = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
        "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server"
    )
}
```

### 3. UserGroupAgent
**責務:** グループメンバーシップの管理

```powershell
@{
    Name = "UserGroupAgent"
    Category = "UserManagement"
    Description = "ユーザーグループの割り当てと管理"
    
    InputParameters = @{
        Username = [string]
        Groups = [array]  # グループリスト
    }
    
    SupportedGroups = @(
        "Administrators",
        "Users",
        "Power Users",
        "Remote Desktop Users",
        "Backup Operators",
        "Network Configuration Operators"
    )
    
    Commands = @(
        "net localgroup `"$GroupName`" $Username /add"
    )
}
```

### 4. AutoLogonAgent
**責務:** 自動ログオンの設定

```powershell
@{
    Name = "AutoLogonAgent"
    Category = "UserManagement"
    Description = "Windows自動ログオンの構成"
    
    InputParameters = @{
        Username = [string]
        Password = [string]
        Domain = [string]
        AutoLogonCount = [int]
    }
    
    RegistrySettings = @{
        "DefaultUserName" = $Username
        "DefaultPassword" = $Password
        "DefaultDomainName" = $Domain
        "AutoAdminLogon" = "1"
        "AutoLogonCount" = $AutoLogonCount
    }
    
    SecurityNote = "パスワードはLSA Secretsに保存推奨"
}
```

### 5. PasswordPolicyAgent
**責務:** パスワードポリシーの設定

```powershell
@{
    Name = "PasswordPolicyAgent"
    Category = "UserManagement"
    Description = "パスワードポリシーとアカウントロックアウトポリシー"
    
    InputParameters = @{
        MinPasswordLength = [int]
        PasswordComplexity = [bool]
        MaxPasswordAge = [int]
        PasswordHistoryCount = [int]
        LockoutThreshold = [int]
    }
    
    Commands = @(
        "net accounts /minpwlen:$MinPasswordLength",
        "net accounts /maxpwage:$MaxPasswordAge",
        "net accounts /uniquepw:$PasswordHistoryCount"
    )
}
```

### 6. AdminAccountAgent
**責務:** 管理者アカウントの管理

```powershell
@{
    Name = "AdminAccountAgent"
    Category = "UserManagement"
    Description = "ビルトインAdministratorアカウントの管理"
    
    InputParameters = @{
        DisableAdministrator = [bool]
        RenameAdministrator = [string]
        SetAdminPassword = [string]
    }
    
    SecurityFeatures = @(
        "Administratorアカウント無効化",
        "アカウント名変更によるセキュリティ向上",
        "強力なパスワード設定"
    )
}
```

### 7. GuestAccountAgent
**責務:** ゲストアカウントの管理

```powershell
@{
    Name = "GuestAccountAgent"
    Category = "UserManagement"
    Description = "ゲストアカウントのセキュリティ設定"
    
    InputParameters = @{
        DisableGuest = [bool]
        RenameGuest = [string]
    }
    
    DefaultAction = "Disable"  # セキュリティベストプラクティス
}
```

### 8. DomainJoinAgent
**責務:** Active Directoryドメイン参加

```powershell
@{
    Name = "DomainJoinAgent"
    Category = "UserManagement"
    Description = "Active Directoryドメインへの参加設定"
    
    InputParameters = @{
        DomainName = [string]
        DomainOU = [string]
        DomainAdmin = [string]
        DomainPassword = [string]
        ComputerName = [string]
    }
    
    PreRequisites = @(
        "DNSサーバー設定",
        "ネットワーク接続",
        "時刻同期"
    )
    
    Commands = @(
        "netdom join $ComputerName /Domain:$DomainName /OU:$DomainOU /UserD:$DomainAdmin /PasswordD:$DomainPassword"
    )
}
```

---

## ネットワークエージェント（6体）

### 1. WiFiConfigAgent
**責務:** Wi-Fi設定と管理

```powershell
@{
    Name = "WiFiConfigAgent"
    Category = "Network"
    Description = "Wi-Fiプロファイルの作成と管理"
    
    InputParameters = @{
        SSID = [string]
        Password = [string]
        SecurityType = [string]
        AutoConnect = [bool]
        Priority = [int]
    }
    
    XMLTemplate = @'
<WLANProfile>
    <name>{SSID}</name>
    <SSIDConfig>
        <SSID>
            <name>{SSID}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>{ConnectionMode}</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>{Authentication}</authentication>
                <encryption>{Encryption}</encryption>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{Password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>
'@
}
```

### 2. EthernetConfigAgent
**責務:** イーサネット設定

```powershell
@{
    Name = "EthernetConfigAgent"
    Category = "Network"
    Description = "イーサネットアダプターの設定"
    
    InputParameters = @{
        AdapterName = [string]
        IPAddress = [string]
        SubnetMask = [string]
        Gateway = [string]
        DNS = [array]
        DHCP = [bool]
    }
    
    Commands = @{
        Static = "netsh interface ip set address `"$AdapterName`" static $IPAddress $SubnetMask $Gateway"
        DHCP = "netsh interface ip set address `"$AdapterName`" dhcp"
        DNS = "netsh interface ip set dns `"$AdapterName`" static $PrimaryDNS"
    }
}
```

### 3. FirewallAgent
**責務:** Windows Defenderファイアウォール設定

```powershell
@{
    Name = "FirewallAgent"
    Category = "Network"
    Description = "ファイアウォールルールとプロファイル設定"
    
    InputParameters = @{
        EnableFirewall = [bool]
        Profiles = [array]  # Domain, Private, Public
        InboundRules = [array]
        OutboundRules = [array]
    }
    
    Profiles = @{
        Domain = @{
            Enabled = $true
            DefaultInboundAction = "Block"
            DefaultOutboundAction = "Allow"
        }
        Private = @{
            Enabled = $true
            DefaultInboundAction = "Block"
            DefaultOutboundAction = "Allow"
        }
        Public = @{
            Enabled = $true
            DefaultInboundAction = "Block"
            DefaultOutboundAction = "Allow"
        }
    }
}
```

### 4. IPv6Agent
**責務:** IPv6プロトコル設定

```powershell
@{
    Name = "IPv6Agent"
    Category = "Network"
    Description = "IPv6プロトコルの有効化/無効化"
    
    InputParameters = @{
        DisableIPv6 = [bool]
        DisableIPv6Components = [int]  # ビットマスク
    }
    
    RegistryPath = "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters"
    DisableComponents = @{
        0x01 = "Disable IPv6 on all tunnel interfaces"
        0x10 = "Disable IPv6 on all nontunnel interfaces"
        0x11 = "Disable IPv6 on all interfaces except loopback"
        0x20 = "Prefer IPv4 over IPv6"
        0xFF = "Disable IPv6 completely"
    }
}
```

### 5. ProxyAgent
**責務:** プロキシサーバー設定

```powershell
@{
    Name = "ProxyAgent"
    Category = "Network"
    Description = "システムプロキシとWinHTTPプロキシ設定"
    
    InputParameters = @{
        ProxyServer = [string]
        ProxyPort = [int]
        ProxyBypass = [array]
        AutoConfigURL = [string]
        UseAutoConfig = [bool]
    }
    
    Commands = @{
        SystemProxy = "netsh winhttp set proxy $ProxyServer:$ProxyPort"
        AutoConfig = "netsh winhttp set proxy proxy-server=`"$ProxyServer`" bypass-list=`"$BypassList`""
        Reset = "netsh winhttp reset proxy"
    }
}
```

### 6. NetworkLocationAgent
**責務:** ネットワーク場所の設定

```powershell
@{
    Name = "NetworkLocationAgent"
    Category = "Network"
    Description = "ネットワークプロファイルと場所の設定"
    
    InputParameters = @{
        NetworkCategory = [string]  # Private, Public, Domain
        NetworkName = [string]
    }
    
    Commands = @(
        "Set-NetConnectionProfile -InterfaceAlias `"$InterfaceName`" -NetworkCategory $NetworkCategory"
    )
}
```

---

## システムエージェント（10体）

### 1. RegistryAgent
**責務:** レジストリの設定と管理

```powershell
@{
    Name = "RegistryAgent"
    Category = "System"
    Description = "レジストリキーと値の管理"
    
    InputParameters = @{
        RegistryPath = [string]
        ValueName = [string]
        ValueData = [object]
        ValueType = [string]  # REG_SZ, REG_DWORD, etc.
    }
    
    Operations = @{
        Create = "New-ItemProperty"
        Modify = "Set-ItemProperty"
        Delete = "Remove-ItemProperty"
        Query = "Get-ItemProperty"
    }
    
    CommonPaths = @(
        "HKLM:\SOFTWARE\Policies",
        "HKLM:\SYSTEM\CurrentControlSet",
        "HKCU:\Software\Microsoft\Windows\CurrentVersion"
    )
}
```

### 2. ServiceAgent
**責務:** Windowsサービスの管理

```powershell
@{
    Name = "ServiceAgent"
    Category = "System"
    Description = "Windowsサービスの設定と制御"
    
    InputParameters = @{
        ServiceName = [string]
        StartupType = [string]  # Automatic, Manual, Disabled
        ServiceAction = [string]  # Start, Stop, Restart
    }
    
    CommonServices = @{
        "Windows Update" = "wuauserv"
        "Windows Defender" = "WinDefend"
        "Windows Search" = "WSearch"
        "Print Spooler" = "Spooler"
        "Remote Desktop" = "TermService"
    }
}
```

### 3. ScheduledTaskAgent
**責務:** スケジュールタスクの管理

```powershell
@{
    Name = "ScheduledTaskAgent"
    Category = "System"
    Description = "スケジュールタスクの作成と管理"
    
    InputParameters = @{
        TaskName = [string]
        TaskPath = [string]
        Action = [scriptblock]
        Trigger = [hashtable]
        Principal = [hashtable]
    }
    
    TriggerTypes = @(
        "AtStartup",
        "AtLogon",
        "Daily",
        "Weekly",
        "Monthly",
        "OnIdle"
    )
}
```

### 4. PowerSettingsAgent
**責務:** 電源設定の管理

```powershell
@{
    Name = "PowerSettingsAgent"
    Category = "System"
    Description = "電源プランと設定の管理"
    
    InputParameters = @{
        PowerPlan = [string]  # Balanced, High Performance, Power Saver
        MonitorTimeout = [int]
        DiskTimeout = [int]
        SleepTimeout = [int]
        HibernateEnabled = [bool]
    }
    
    PowerSchemes = @{
        Balanced = "381b4222-f694-41f0-9685-ff5bb260df2e"
        HighPerformance = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
        PowerSaver = "a1841308-3541-4fab-bc81-f71556f20b4a"
    }
}
```

### 5. TimeZoneAgent
**責務:** タイムゾーンと時刻設定

```powershell
@{
    Name = "TimeZoneAgent"
    Category = "System"
    Description = "タイムゾーンとNTP設定"
    
    InputParameters = @{
        TimeZone = [string]
        NTPServer = [string]
        AutoTimeSync = [bool]
    }
    
    TimeZones = @{
        "Tokyo" = "Tokyo Standard Time"
        "PST" = "Pacific Standard Time"
        "EST" = "Eastern Standard Time"
        "UTC" = "UTC"
    }
}
```

### 6. LocaleAgent
**責務:** 地域と言語設定

```powershell
@{
    Name = "LocaleAgent"
    Category = "System"
    Description = "システムロケールと地域設定"
    
    InputParameters = @{
        SystemLocale = [string]
        UserLocale = [string]
        InputMethod = [string]
        DisplayLanguage = [string]
    }
    
    LocaleIDs = @{
        "Japanese" = "ja-JP"
        "English-US" = "en-US"
        "Chinese-Simplified" = "zh-CN"
        "Korean" = "ko-KR"
    }
}
```

### 7. UpdateAgent
**責務:** Windows Update設定

```powershell
@{
    Name = "UpdateAgent"
    Category = "System"
    Description = "Windows Update設定と制御"
    
    InputParameters = @{
        UpdateBehavior = [string]  # Automatic, Notify, Disabled
        ActiveHours = [hashtable]
        DeferFeatureUpdates = [int]
        DeferQualityUpdates = [int]
    }
    
    RegistrySettings = @{
        "NoAutoUpdate" = 0  # 0=Auto, 1=Disabled
        "AUOptions" = 4  # 2=Notify, 3=Download, 4=Automatic
        "ScheduledInstallDay" = 0  # 0=Every day
        "ScheduledInstallTime" = 3  # 3=3AM
    }
}
```

### 8. TelemetryAgent
**責務:** テレメトリとプライバシー設定

```powershell
@{
    Name = "TelemetryAgent"
    Category = "System"
    Description = "診断データとテレメトリ設定"
    
    InputParameters = @{
        TelemetryLevel = [string]  # Security, Basic, Enhanced, Full
        DisableAdvertisingID = [bool]
        DisableLocationTracking = [bool]
        DisableFeedback = [bool]
    }
    
    TelemetryLevels = @{
        0 = "Security (Enterprise only)"
        1 = "Basic"
        2 = "Enhanced"
        3 = "Full"
    }
    
    Services = @(
        "DiagTrack",
        "dmwappushservice",
        "diagnosticshub.standardcollector.service"
    )
}
```

### 9. PrivacyAgent
**責務:** プライバシー設定の管理

```powershell
@{
    Name = "PrivacyAgent"
    Category = "System"
    Description = "プライバシー設定とアプリ権限"
    
    InputParameters = @{
        CameraAccess = [bool]
        MicrophoneAccess = [bool]
        LocationAccess = [bool]
        ContactsAccess = [bool]
        CalendarAccess = [bool]
    }
    
    AppPermissions = @(
        "Camera",
        "Microphone",
        "Location",
        "Contacts",
        "Calendar",
        "PhoneCall",
        "Notifications",
        "AccountInfo",
        "BackgroundApps"
    )
}
```

### 10. UACAgent
**責務:** ユーザーアカウント制御（UAC）設定

```powershell
@{
    Name = "UACAgent"
    Category = "System"
    Description = "UAC設定とセキュリティレベル"
    
    InputParameters = @{
        UACLevel = [int]  # 0-4
        AdminApprovalMode = [bool]
        ConsentPromptBehavior = [int]
    }
    
    UACLevels = @{
        0 = "Never notify (disabled)"
        1 = "Notify only when apps try to make changes (do not dim)"
        2 = "Notify only when apps try to make changes (default)"
        3 = "Always notify"
        4 = "Always notify and require credentials"
    }
}
```

---

## アプリケーションエージェント（6体）

### 1. AppRemovalAgent
**責務:** プリインストールアプリの削除

```powershell
@{
    Name = "AppRemovalAgent"
    Category = "Application"
    Description = "不要なプリインストールアプリの削除"
    
    InputParameters = @{
        AppsToRemove = [array]
        RemoveForAllUsers = [bool]
        RemoveProvisionedApps = [bool]
    }
    
    CommonAppsToRemove = @(
        "Microsoft.BingNews",
        "Microsoft.BingWeather",
        "Microsoft.XboxApp",
        "Microsoft.SkypeApp",
        "Microsoft.YourPhone",
        "Microsoft.MixedReality.Portal"
    )
    
    Commands = @{
        RemoveApp = "Get-AppxPackage -Name $AppName | Remove-AppxPackage"
        RemoveProvisioned = "Get-AppxProvisionedPackage -Online | Where-Object {$_.PackageName -like '*$AppName*'} | Remove-AppxProvisionedPackage -Online"
    }
}
```

### 2. DefaultAppAgent
**責務:** 既定のアプリケーション設定

```powershell
@{
    Name = "DefaultAppAgent"
    Category = "Application"
    Description = "既定のアプリケーション関連付け"
    
    InputParameters = @{
        DefaultBrowser = [string]
        DefaultMailClient = [string]
        DefaultPDFReader = [string]
        DefaultMediaPlayer = [string]
    }
    
    FileAssociations = @{
        ".html" = "ChromeHTML"
        ".pdf" = "AcroExch.Document"
        ".mp3" = "WMP11.AssocFile.MP3"
        ".jpg" = "PhotoViewer.FileAssoc.Jpeg"
    }
    
    ProtocolAssociations = @{
        "http" = "ChromeHTML"
        "https" = "ChromeHTML"
        "mailto" = "Outlook.URL.mailto.15"
    }
}
```

### 3. StoreAppAgent
**責務:** Microsoft Store設定

```powershell
@{
    Name = "StoreAppAgent"
    Category = "Application"
    Description = "Microsoft Storeとアプリ更新設定"
    
    InputParameters = @{
        DisableStore = [bool]
        DisableAutoUpdate = [bool]
        RequirePrivateStore = [bool]
    }
    
    PolicySettings = @{
        "RemoveWindowsStore" = 1
        "DisableStoreApps" = 1
        "AutoDownload" = 2
        "RequirePrivateStoreOnly" = 1
    }
}
```

### 4. OfficeAgent
**責務:** Microsoft Office設定

```powershell
@{
    Name = "OfficeAgent"
    Category = "Application"
    Description = "Microsoft Office初期設定と最適化"
    
    InputParameters = @{
        AcceptEULA = [bool]
        DisableFirstRun = [bool]
        DefaultSaveLocation = [string]
        UpdateChannel = [string]
    }
    
    RegistrySettings = @{
        "AcceptAllEulas" = 1
        "DisableFirstRunMovie" = 1
        "DisableOfficeStart" = 1
        "UpdateBranch" = "Current"
    }
    
    UpdateChannels = @{
        "Current" = "Current Channel"
        "Monthly" = "Monthly Enterprise Channel"
        "SemiAnnual" = "Semi-Annual Enterprise Channel"
    }
}
```

### 5. BrowserAgent
**責務:** Webブラウザー設定

```powershell
@{
    Name = "BrowserAgent"
    Category = "Application"
    Description = "Webブラウザーの設定と最適化"
    
    InputParameters = @{
        Browser = [string]  # Edge, Chrome, Firefox
        HomePage = [string]
        SearchEngine = [string]
        DisablePasswordManager = [bool]
    }
    
    EdgeSettings = @{
        "HomepageLocation" = "https://www.company.com"
        "DefaultSearchProviderEnabled" = 1
        "DefaultSearchProviderName" = "Google"
        "PasswordManagerEnabled" = 0
    }
}
```

### 6. MediaAgent
**責務:** メディアアプリケーション設定

```powershell
@{
    Name = "MediaAgent"
    Category = "Application"
    Description = "メディアプレーヤーとコーデック設定"
    
    InputParameters = @{
        DefaultVideoPlayer = [string]
        DefaultAudioPlayer = [string]
        InstallCodecs = [bool]
    }
    
    MediaExtensions = @{
        Video = @(".mp4", ".avi", ".mkv", ".mov")
        Audio = @(".mp3", ".wav", ".flac", ".aac")
        Image = @(".jpg", ".png", ".gif", ".bmp")
    }
}
```

---

## Windows機能エージェント（8体）

### 1. DotNetAgent
**責務:** .NET Framework設定

```powershell
@{
    Name = "DotNetAgent"
    Category = "Features"
    Description = ".NET Frameworkのインストールと設定"
    
    InputParameters = @{
        EnableDotNet35 = [bool]
        EnableDotNet48 = [bool]
        EnableASPNET = [bool]
    }
    
    Features = @{
        "NetFx3" = ".NET Framework 3.5"
        "NetFx4-AdvSrvs" = ".NET Framework 4.8 Advanced Services"
        "IIS-NetFxExtensibility45" = "IIS .NET Extensibility 4.5"
        "IIS-ASPNET45" = "IIS ASP.NET 4.5"
    }
    
    Commands = @(
        "DISM /Online /Enable-Feature /FeatureName:NetFx3 /All",
        "Enable-WindowsOptionalFeature -Online -FeatureName NetFx3"
    )
}
```

### 2. HyperVAgent
**責務:** Hyper-V仮想化機能

```powershell
@{
    Name = "HyperVAgent"
    Category = "Features"
    Description = "Hyper-V仮想化プラットフォーム設定"
    
    InputParameters = @{
        EnableHyperV = [bool]
        EnableManagementTools = [bool]
        DefaultVMPath = [string]
        DefaultVHDPath = [string]
    }
    
    Features = @(
        "Microsoft-Hyper-V",
        "Microsoft-Hyper-V-Management-PowerShell",
        "Microsoft-Hyper-V-Management-Clients"
    )
    
    Requirements = @{
        CPU = "64-bit processor with SLAT"
        Memory = "4GB minimum"
        BIOS = "Virtualization enabled"
    }
}
```

### 3. WSLAgent
**責務:** Windows Subsystem for Linux

```powershell
@{
    Name = "WSLAgent"
    Category = "Features"
    Description = "WSL/WSL2の有効化と設定"
    
    InputParameters = @{
        EnableWSL = [bool]
        EnableWSL2 = [bool]
        DefaultDistribution = [string]
        DefaultVersion = [int]
    }
    
    Features = @(
        "Microsoft-Windows-Subsystem-Linux",
        "VirtualMachinePlatform"
    )
    
    Commands = @(
        "wsl --set-default-version 2",
        "wsl --install -d Ubuntu"
    )
}
```

### 4. SandboxAgent
**責務:** Windows Sandbox設定

```powershell
@{
    Name = "SandboxAgent"
    Category = "Features"
    Description = "Windows Sandboxの有効化"
    
    InputParameters = @{
        EnableSandbox = [bool]
        vGPU = [bool]
        Networking = [bool]
        AudioInput = [bool]
    }
    
    Requirements = @{
        Edition = "Windows 11 Pro/Enterprise"
        CPU = "64-bit with virtualization"
        Memory = "4GB minimum"
    }
}
```

### 5. IISAgent
**責務:** Internet Information Services

```powershell
@{
    Name = "IISAgent"
    Category = "Features"
    Description = "IIS Webサーバーの設定"
    
    InputParameters = @{
        EnableIIS = [bool]
        EnableASPNET = [bool]
        EnablePHP = [bool]
        DefaultSite = [hashtable]
    }
    
    Features = @(
        "IIS-WebServerRole",
        "IIS-WebServer",
        "IIS-CommonHttpFeatures",
        "IIS-Security",
        "IIS-RequestFiltering",
        "IIS-ASPNET45"
    )
}
```

### 6. SMBAgent
**責務:** SMBファイル共有設定

```powershell
@{
    Name = "SMBAgent"
    Category = "Features"
    Description = "SMBプロトコルとファイル共有設定"
    
    InputParameters = @{
        EnableSMBv1 = [bool]
        EnableSMBv2 = [bool]
        EnableSMBv3 = [bool]
        EnableGuestAccess = [bool]
    }
    
    SecuritySettings = @{
        "RequireSecuritySignature" = $true
        "EnableSecuritySignature" = $true
        "EncryptData" = $true
    }
}
```

### 7. TelnetAgent
**責務:** Telnetクライアント設定

```powershell
@{
    Name = "TelnetAgent"
    Category = "Features"
    Description = "Telnetクライアントの有効化"
    
    InputParameters = @{
        EnableTelnetClient = [bool]
    }
    
    Feature = "TelnetClient"
    SecurityNote = "セキュリティリスクのため本番環境では非推奨"
}
```

### 8. ContainerAgent
**責務:** Windowsコンテナー機能

```powershell
@{
    Name = "ContainerAgent"
    Category = "Features"
    Description = "Windowsコンテナーとdocker設定"
    
    InputParameters = @{
        EnableContainers = [bool]
        ContainerType = [string]  # Windows, Linux
        DockerDesktop = [bool]
    }
    
    Features = @(
        "Containers",
        "Microsoft-Hyper-V",
        "Containers-DisposableClientVM"
    )
}
```

---

## UI/UXエージェント（4体）

### 1. ExplorerAgent
**責務:** エクスプローラー設定

```powershell
@{
    Name = "ExplorerAgent"
    Category = "UI"
    Description = "Windowsエクスプローラーのカスタマイズ"
    
    InputParameters = @{
        ShowFileExtensions = [bool]
        ShowHiddenFiles = [bool]
        ShowFullPath = [bool]
        QuickAccessPins = [array]
    }
    
    RegistrySettings = @{
        "HideFileExt" = 0
        "Hidden" = 1
        "ShowSuperHidden" = 1
        "FullPath" = 1
    }
}
```

### 2. TaskbarAgent
**責務:** タスクバー設定

```powershell
@{
    Name = "TaskbarAgent"
    Category = "UI"
    Description = "タスクバーのカスタマイズ"
    
    InputParameters = @{
        TaskbarAlignment = [string]
        ShowSearchButton = [bool]
        ShowTaskViewButton = [bool]
        ShowWidgetsButton = [bool]
        CombineButtons = [string]
    }
    
    Windows11Settings = @{
        "TaskbarAl" = 0  # 0=Left, 1=Center
        "ShowTaskViewButton" = 0
        "ShowWidgetsButton" = 0
    }
}
```

### 3. StartMenuAgent
**責務:** スタートメニュー設定

```powershell
@{
    Name = "StartMenuAgent"
    Category = "UI"
    Description = "スタートメニューのカスタマイズ"
    
    InputParameters = @{
        StartLayout = [string]
        ShowRecentlyAdded = [bool]
        ShowMostUsed = [bool]
        PinnedApps = [array]
    }
    
    LayoutFile = "LayoutModification.xml"
    PolicyPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Explorer"
}
```

### 4. DesktopAgent
**責務:** デスクトップ設定

```powershell
@{
    Name = "DesktopAgent"
    Category = "UI"
    Description = "デスクトップ環境のカスタマイズ"
    
    InputParameters = @{
        ShowDesktopIcons = [hashtable]
        Wallpaper = [string]
        Theme = [string]
        IconSize = [int]
    }
    
    DesktopIcons = @{
        "ThisPC" = "{20D04FE0-3AEA-1069-A2D8-08002B30309D}"
        "UserFiles" = "{59031a47-3f72-44a7-89c5-5595fe6b30ee}"
        "Network" = "{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}"
        "RecycleBin" = "{645FF040-5081-101B-9F08-00AA002F954E}"
        "ControlPanel" = "{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}"
    }
}
```

---

## エージェント間連携

### 依存関係マップ
```powershell
$AgentDependencies = @{
    "DomainJoinAgent" = @("NetworkConfigAgent", "TimeZoneAgent")
    "HyperVAgent" = @("MemoryAgent", "CPUAgent")
    "WSLAgent" = @("HyperVAgent", "VirtualMachinePlatformAgent")
    "OfficeAgent" = @("DotNetAgent", "RegistryAgent")
}
```

### 実行順序制御
```powershell
$ExecutionOrder = @(
    # Phase 1: 基本設定
    @("TimeZoneAgent", "LocaleAgent"),
    
    # Phase 2: ネットワーク
    @("EthernetConfigAgent", "WiFiConfigAgent", "FirewallAgent"),
    
    # Phase 3: ユーザー
    @("UserCreationAgent", "UserGroupAgent", "UserPermissionAgent"),
    
    # Phase 4: 機能
    @("DotNetAgent", "HyperVAgent", "WSLAgent"),
    
    # Phase 5: アプリケーション
    @("AppRemovalAgent", "OfficeAgent", "DefaultAppAgent")
)
```

### メッセージング
```powershell
class AgentMessage {
    [string]$From
    [string]$To
    [string]$Type  # Request, Response, Notification
    [hashtable]$Data
    [datetime]$Timestamp
}
```

---

## カスタムエージェント開発

### テンプレート
```powershell
class CustomAgent : SubAgent {
    CustomAgent() {
        $this.Name = "CustomAgent"
        $this.Category = "Custom"
        $this.Description = "カスタムエージェントの説明"
    }
    
    [void]Initialize([hashtable]$Config) {
        # 初期化処理
        $this.Configuration = $Config
    }
    
    [void]Execute([hashtable]$Config) {
        try {
            $this.Status = "Running"
            
            # メイン処理ロジック
            # ...
            
            $this.Result = @{
                Success = $true
                Data = @{}
            }
            $this.Status = "Completed"
        }
        catch {
            $this.Status = "Failed"
            $this.Result = @{
                Success = $false
                Error = $_.Exception.Message
            }
        }
    }
    
    [void]Validate() {
        # 設定検証ロジック
        if (-not $this.Configuration) {
            throw "Configuration is required"
        }
    }
    
    [hashtable]GetOutput() {
        # XML生成用の出力フォーマット
        return @{
            Commands = @()
            RegistryKeys = @()
            Files = @()
        }
    }
}
```

### 登録方法
```powershell
# カスタムエージェントの登録
Register-SubAgent -Agent (New-Object CustomAgent) -Category "Custom"

# エージェントローダーへの追加
$loader = Get-SubAgentLoader
$loader.RegisterAgent("CustomAgent", $customAgentDefinition)
```

### デバッグ
```powershell
# エージェントのデバッグ実行
$agent = New-Object CustomAgent
$agent.Initialize(@{Debug = $true})
$agent.Execute(@{TestParam = "TestValue"})

# 結果確認
$agent.GetResult() | ConvertTo-Json -Depth 5
```

---

## パフォーマンス最適化

### 並列実行設定
```powershell
$ParallelConfig = @{
    MaxConcurrentAgents = 8
    TimeoutSeconds = 300
    RetryCount = 3
    RetryDelaySeconds = 5
}
```

### キャッシング
```powershell
$CacheConfig = @{
    EnableCache = $true
    CacheDurationMinutes = 30
    CacheLocation = ".\Cache\Agents"
}
```

### リソース管理
```powershell
$ResourceLimits = @{
    MaxMemoryMB = 512
    MaxCPUPercent = 75
    MaxDiskIOMBps = 100
}
```

---

## 次のステップ

1. **[トラブルシューティングガイド_v2.md](./トラブルシューティングガイド_v2.md)** - エージェント関連の問題解決
2. **[開発完了報告書.md](./開発完了報告書.md)** - v2.0開発完了報告
3. **[詳細利用手順書_v2.md](./詳細利用手順書_v2.md)** - 実際の使用方法

---

*最終更新: 2024年8月24日 | バージョン: 2.0.0*