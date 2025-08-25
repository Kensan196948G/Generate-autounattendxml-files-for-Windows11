#Requires -Version 5.0

<#
.SYNOPSIS
    Windows 11 UnattendXML ネットワーク設定モジュール

.DESCRIPTION
    Sysprep応答ファイルでのネットワーク設定を管理するPowerShellモジュール
    - IPv6無効化設定
    - Windows Firewall無効化
    - Bluetooth無効化
    - グループポリシー設定
    - ネットワークプロファイル設定

.VERSION
    1.0.0

.AUTHOR
    Windows 11 Sysprep Automation Team

.COPYRIGHT
    Copyright (c) 2025. All rights reserved.
#>

# .NET Framework アセンブリの読み込み
Add-Type -AssemblyName System.Xml
Add-Type -AssemblyName System.Net.NetworkInformation

# ネットワーク設定列挙型
enum NetworkProfileType {
    Public = 0
    Private = 1
    Domain = 2
}

enum FirewallProfile {
    Domain = 0
    Private = 1
    Public = 2
    All = 3
}

# ネットワーク設定クラス
class NetworkConfiguration {
    [bool]$DisableIPv6
    [bool]$DisableFirewall
    [bool]$DisableBluetooth
    [bool]$MuteAudio
    [NetworkProfileType]$DefaultNetworkProfile
    [FirewallProfile[]]$DisabledFirewallProfiles
    [hashtable]$GroupPolicySettings
    [hashtable]$RegistrySettings
    [hashtable]$ServiceSettings
    
    # コンストラクタ
    NetworkConfiguration() {
        $this.DisableIPv6 = $true
        $this.DisableFirewall = $true
        $this.DisableBluetooth = $true
        $this.MuteAudio = $true
        $this.DefaultNetworkProfile = [NetworkProfileType]::Private
        $this.DisabledFirewallProfiles = @([FirewallProfile]::All)
        $this.GroupPolicySettings = @{}
        $this.RegistrySettings = @{}
        $this.ServiceSettings = @{}
        
        # デフォルト設定の初期化
        $this.InitializeDefaultSettings()
    }
    
    # デフォルト設定初期化
    [void] InitializeDefaultSettings() {
        # IPv6無効化用レジストリ設定
        if ($this.DisableIPv6) {
            $this.RegistrySettings["HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters"] = @{
                "DisabledComponents" = @{
                    Type = "REG_DWORD"
                    Value = 0xffffffff
                }
            }
        }
        
        # Bluetooth無効化用レジストリ設定
        if ($this.DisableBluetooth) {
            $this.RegistrySettings["HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters"] = @{
                "BluetoothEnabled" = @{
                    Type = "REG_DWORD"
                    Value = 0
                }
            }
            
            # Bluetoothサービス無効化
            $this.ServiceSettings["BTHSERV"] = @{
                StartMode = "Disabled"
                Description = "Bluetooth Support Service"
            }
            $this.ServiceSettings["BthAvrcpTg"] = @{
                StartMode = "Disabled"
                Description = "AVRCP Transport"
            }
            $this.ServiceSettings["BthHFSrv"] = @{
                StartMode = "Disabled"
                Description = "Bluetooth Handsfree Service"
            }
        }
        
        # 音源ミュート設定
        if ($this.MuteAudio) {
            $this.RegistrySettings["HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Audio"] = @{
                "DisableProtectedAudioDG" = @{
                    Type = "REG_DWORD"
                    Value = 1
                }
            }
        }
        
        # グループポリシー設定
        $this.GroupPolicySettings = @{
            # 安全でないゲストログオンの有効化
            "Computer Configuration\Administrative Templates\Network\Lanman Workstation" = @{
                "Enable insecure guest logons" = "Enabled"
            }
            
            # ネットワーク探索の有効化
            "Computer Configuration\Administrative Templates\Network\Network Connections" = @{
                "Turn on mapper I/O (LLTDIO) driver" = "Enabled"
                "Turn on Responder (RSPNDR) driver" = "Enabled"
            }
            
            # SMB設定
            "Computer Configuration\Administrative Templates\Network\Lanman Server" = @{
                "Require case insensitivity for non-Windows SMB clients" = "Disabled"
                "Require security signature for SMB2/3 connections" = "Disabled"
            }
        }
    }
}

# ネットワーク設定XMLジェネレーター
class UnattendNetworkXMLGenerator {
    [System.Xml.XmlDocument]$XmlDocument
    [NetworkConfiguration]$Config
    [System.Xml.XmlNamespaceManager]$NamespaceManager
    
    # コンストラクタ
    UnattendNetworkXMLGenerator([System.Xml.XmlDocument]$xmlDoc, [NetworkConfiguration]$config) {
        $this.XmlDocument = $xmlDoc
        $this.Config = $config
        $this.NamespaceManager = New-Object System.Xml.XmlNamespaceManager($xmlDoc.NameTable)
        $this.NamespaceManager.AddNamespace("un", "urn:schemas-microsoft-com:unattend")
    }
    
    # ネットワーク設定XML生成
    [System.Xml.XmlElement] GenerateNetworkConfigurationXML() {
        Write-Verbose "ネットワーク設定XML生成開始"
        
        $unattendRoot = $this.XmlDocument.DocumentElement
        
        # specialize パスでの設定
        $this.AddSpecializeSettings($unattendRoot)
        
        # oobeSystem パスでの設定
        $this.AddOobeSystemSettings($unattendRoot)
        
        Write-Verbose "ネットワーク設定XML生成完了"
        return $unattendRoot
    }
    
    # Specialize パス設定追加
    [void] AddSpecializeSettings([System.Xml.XmlElement]$unattendRoot) {
        Write-Verbose "Specialize パス設定追加開始"
        
        $settingsElement = $this.GetOrCreateSettingsElement($unattendRoot, "specialize")
        
        # レジストリ設定
        $this.AddRegistrySettings($settingsElement)
        
        # サービス設定
        $this.AddServiceSettings($settingsElement)
        
        # Firewall設定
        $this.AddFirewallSettings($settingsElement)
        
        Write-Verbose "Specialize パス設定追加完了"
    }
    
    # OOBE System パス設定追加
    [void] AddOobeSystemSettings([System.Xml.XmlElement]$unattendRoot) {
        Write-Verbose "OOBE System パス設定追加開始"
        
        $settingsElement = $this.GetOrCreateSettingsElement($unattendRoot, "oobeSystem")
        
        # ネットワークロケーション設定
        $this.AddNetworkLocationSettings($settingsElement)
        
        Write-Verbose "OOBE System パス設定追加完了"
    }
    
    # レジストリ設定追加
    [void] AddRegistrySettings([System.Xml.XmlElement]$settingsElement) {
        Write-Verbose "レジストリ設定追加開始"
        
        if ($this.Config.RegistrySettings.Count -eq 0) {
            return
        }
        
        # Microsoft-Windows-Shell-Setup コンポーネント
        $shellSetupComponent = $this.GetOrCreateComponent($settingsElement, "Microsoft-Windows-Shell-Setup")
        
        # FirstLogonCommands要素
        $firstLogonCommandsElement = $this.XmlDocument.CreateElement("FirstLogonCommands", $shellSetupComponent.NamespaceURI)
        $shellSetupComponent.AppendChild($firstLogonCommandsElement) | Out-Null
        
        $commandOrder = 1
        
        foreach ($registryPath in $this.Config.RegistrySettings.Keys) {
            $registryValues = $this.Config.RegistrySettings[$registryPath]
            
            foreach ($valueName in $registryValues.Keys) {
                $valueData = $registryValues[$valueName]
                
                # SynchronousCommand要素
                $synchronousCommandElement = $this.XmlDocument.CreateElement("SynchronousCommand", $firstLogonCommandsElement.NamespaceURI)
                $synchronousCommandElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
                $firstLogonCommandsElement.AppendChild($synchronousCommandElement) | Out-Null
                
                # Order要素
                $orderElement = $this.XmlDocument.CreateElement("Order", $synchronousCommandElement.NamespaceURI)
                $orderElement.InnerText = $commandOrder.ToString()
                $synchronousCommandElement.AppendChild($orderElement) | Out-Null
                
                # CommandLine要素
                $commandLineElement = $this.XmlDocument.CreateElement("CommandLine", $synchronousCommandElement.NamespaceURI)
                
                if ($valueData.Type -eq "REG_DWORD") {
                    $commandLineElement.InnerText = "reg add `"$registryPath`" /v `"$valueName`" /t REG_DWORD /d $($valueData.Value) /f"
                } elseif ($valueData.Type -eq "REG_SZ") {
                    $commandLineElement.InnerText = "reg add `"$registryPath`" /v `"$valueName`" /t REG_SZ /d `"$($valueData.Value)`" /f"
                }
                
                $synchronousCommandElement.AppendChild($commandLineElement) | Out-Null
                
                # Description要素
                $descriptionElement = $this.XmlDocument.CreateElement("Description", $synchronousCommandElement.NamespaceURI)
                $descriptionElement.InnerText = "Registry Setting: $registryPath\$valueName"
                $synchronousCommandElement.AppendChild($descriptionElement) | Out-Null
                
                $commandOrder++
            }
        }
        
        Write-Verbose "レジストリ設定追加完了"
    }
    
    # サービス設定追加
    [void] AddServiceSettings([System.Xml.XmlElement]$settingsElement) {
        Write-Verbose "サービス設定追加開始"
        
        if ($this.Config.ServiceSettings.Count -eq 0) {
            return
        }
        
        $shellSetupComponent = $this.GetOrCreateComponent($settingsElement, "Microsoft-Windows-Shell-Setup")
        
        # FirstLogonCommands取得（レジストリ設定で作成済みの場合）
        $firstLogonCommandsElement = $shellSetupComponent.SelectSingleNode("un:FirstLogonCommands", $this.NamespaceManager)
        if ($firstLogonCommandsElement -eq $null) {
            $firstLogonCommandsElement = $this.XmlDocument.CreateElement("FirstLogonCommands", $shellSetupComponent.NamespaceURI)
            $shellSetupComponent.AppendChild($firstLogonCommandsElement) | Out-Null
        }
        
        # 既存コマンド数を取得
        $existingCommands = $firstLogonCommandsElement.SelectNodes("un:SynchronousCommand", $this.NamespaceManager)
        $commandOrder = $existingCommands.Count + 1
        
        foreach ($serviceName in $this.Config.ServiceSettings.Keys) {
            $serviceConfig = $this.Config.ServiceSettings[$serviceName]
            
            # SynchronousCommand要素
            $synchronousCommandElement = $this.XmlDocument.CreateElement("SynchronousCommand", $firstLogonCommandsElement.NamespaceURI)
            $synchronousCommandElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $firstLogonCommandsElement.AppendChild($synchronousCommandElement) | Out-Null
            
            # Order要素
            $orderElement = $this.XmlDocument.CreateElement("Order", $synchronousCommandElement.NamespaceURI)
            $orderElement.InnerText = $commandOrder.ToString()
            $synchronousCommandElement.AppendChild($orderElement) | Out-Null
            
            # CommandLine要素
            $commandLineElement = $this.XmlDocument.CreateElement("CommandLine", $synchronousCommandElement.NamespaceURI)
            $commandLineElement.InnerText = "sc config `"$serviceName`" start= disabled"
            $synchronousCommandElement.AppendChild($commandLineElement) | Out-Null
            
            # Description要素
            $descriptionElement = $this.XmlDocument.CreateElement("Description", $synchronousCommandElement.NamespaceURI)
            $descriptionElement.InnerText = "Disable Service: $serviceName ($($serviceConfig.Description))"
            $synchronousCommandElement.AppendChild($descriptionElement) | Out-Null
            
            $commandOrder++
        }
        
        Write-Verbose "サービス設定追加完了"
    }
    
    # Firewall設定追加
    [void] AddFirewallSettings([System.Xml.XmlElement]$settingsElement) {
        Write-Verbose "Firewall設定追加開始"
        
        if (!$this.Config.DisableFirewall) {
            return
        }
        
        $shellSetupComponent = $this.GetOrCreateComponent($settingsElement, "Microsoft-Windows-Shell-Setup")
        
        # FirstLogonCommands取得
        $firstLogonCommandsElement = $shellSetupComponent.SelectSingleNode("un:FirstLogonCommands", $this.NamespaceManager)
        if ($firstLogonCommandsElement -eq $null) {
            $firstLogonCommandsElement = $this.XmlDocument.CreateElement("FirstLogonCommands", $shellSetupComponent.NamespaceURI)
            $shellSetupComponent.AppendChild($firstLogonCommandsElement) | Out-Null
        }
        
        # 既存コマンド数を取得
        $existingCommands = $firstLogonCommandsElement.SelectNodes("un:SynchronousCommand", $this.NamespaceManager)
        $commandOrder = $existingCommands.Count + 1
        
        # Firewallプロファイルごとに無効化コマンド追加
        foreach ($profile in $this.Config.DisabledFirewallProfiles) {
            $profileName = switch ($profile) {
                ([FirewallProfile]::Domain) { "domainprofile" }
                ([FirewallProfile]::Private) { "privateprofile" }
                ([FirewallProfile]::Public) { "publicprofile" }
                ([FirewallProfile]::All) { "allprofiles" }
            }
            
            # SynchronousCommand要素
            $synchronousCommandElement = $this.XmlDocument.CreateElement("SynchronousCommand", $firstLogonCommandsElement.NamespaceURI)
            $synchronousCommandElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $firstLogonCommandsElement.AppendChild($synchronousCommandElement) | Out-Null
            
            # Order要素
            $orderElement = $this.XmlDocument.CreateElement("Order", $synchronousCommandElement.NamespaceURI)
            $orderElement.InnerText = $commandOrder.ToString()
            $synchronousCommandElement.AppendChild($orderElement) | Out-Null
            
            # CommandLine要素
            $commandLineElement = $this.XmlDocument.CreateElement("CommandLine", $synchronousCommandElement.NamespaceURI)
            $commandLineElement.InnerText = "netsh advfirewall set $profileName state off"
            $synchronousCommandElement.AppendChild($commandLineElement) | Out-Null
            
            # Description要素
            $descriptionElement = $this.XmlDocument.CreateElement("Description", $synchronousCommandElement.NamespaceURI)
            $descriptionElement.InnerText = "Disable Windows Firewall: $profile Profile"
            $synchronousCommandElement.AppendChild($descriptionElement) | Out-Null
            
            $commandOrder++
        }
        
        Write-Verbose "Firewall設定追加完了"
    }
    
    # ネットワークロケーション設定追加
    [void] AddNetworkLocationSettings([System.Xml.XmlElement]$settingsElement) {
        Write-Verbose "ネットワークロケーション設定追加開始"
        
        $shellSetupComponent = $this.GetOrCreateComponent($settingsElement, "Microsoft-Windows-Shell-Setup")
        
        # NetworkLocation要素
        $networkLocationElement = $this.XmlDocument.CreateElement("NetworkLocation", $shellSetupComponent.NamespaceURI)
        $shellSetupComponent.AppendChild($networkLocationElement) | Out-Null
        
        # ネットワークプロファイル設定
        $profileValue = switch ($this.Config.DefaultNetworkProfile) {
            ([NetworkProfileType]::Public) { "Public" }
            ([NetworkProfileType]::Private) { "Home" }  # Unattend.xmlでは"Home"を使用
            ([NetworkProfileType]::Domain) { "Work" }
            default { "Home" }
        }
        
        $networkLocationElement.InnerText = $profileValue
        
        Write-Verbose "ネットワークロケーション設定追加完了"
    }
    
    # Settings要素の取得または作成
    [System.Xml.XmlElement] GetOrCreateSettingsElement([System.Xml.XmlElement]$parent, [string]$pass) {
        $xpath = "un:settings[@pass='$pass']"
        $settingsElement = $parent.SelectSingleNode($xpath, $this.NamespaceManager)
        
        if ($settingsElement -eq $null) {
            $settingsElement = $this.XmlDocument.CreateElement("settings", $parent.NamespaceURI)
            $settingsElement.SetAttribute("pass", $pass)
            $parent.AppendChild($settingsElement) | Out-Null
        }
        
        return $settingsElement
    }
    
    # Component要素の取得または作成
    [System.Xml.XmlElement] GetOrCreateComponent([System.Xml.XmlElement]$parent, [string]$name) {
        $xpath = "un:component[@name='$name']"
        $componentElement = $parent.SelectSingleNode($xpath, $this.NamespaceManager)
        
        if ($componentElement -eq $null) {
            $componentElement = $this.XmlDocument.CreateElement("component", $parent.NamespaceURI)
            $componentElement.SetAttribute("name", $name)
            $componentElement.SetAttribute("processorArchitecture", "amd64")
            $componentElement.SetAttribute("publicKeyToken", "31bf3856ad364e35")
            $componentElement.SetAttribute("language", "neutral")
            $componentElement.SetAttribute("versionScope", "nonSxS")
            $componentElement.SetAttribute("xmlns:wcm", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $componentElement.SetAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
            $parent.AppendChild($componentElement) | Out-Null
        }
        
        return $componentElement
    }
}

# ネットワーク設定検証クラス
class NetworkConfigValidator {
    [NetworkConfiguration]$Config
    [string[]]$ValidationErrors
    [string[]]$ValidationWarnings
    
    # コンストラクタ
    NetworkConfigValidator([NetworkConfiguration]$config) {
        $this.Config = $config
        $this.ValidationErrors = @()
        $this.ValidationWarnings = @()
    }
    
    # 設定検証実行
    [bool] ValidateConfiguration() {
        Write-Verbose "ネットワーク設定検証開始"
        
        $this.ValidationErrors = @()
        $this.ValidationWarnings = @()
        
        # 基本検証
        $this.ValidateFirewallSettings()
        $this.ValidateRegistrySettings()
        $this.ValidateServiceSettings()
        $this.ValidateSecurityImplications()
        
        # 結果出力
        foreach ($warning in $this.ValidationWarnings) {
            Write-Warning $warning
        }
        
        foreach ($error in $this.ValidationErrors) {
            Write-Error $error
        }
        
        $isValid = $this.ValidationErrors.Count -eq 0
        Write-Verbose "ネットワーク設定検証完了 (Valid: $isValid)"
        
        return $isValid
    }
    
    # Firewall設定検証
    [void] ValidateFirewallSettings() {
        if ($this.Config.DisableFirewall) {
            $this.ValidationWarnings += "Windows Firewallが無効化されています（セキュリティリスク）"
            
            if ($this.Config.DisabledFirewallProfiles -contains [FirewallProfile]::All) {
                $this.ValidationWarnings += "すべてのFirewallプロファイルが無効化されています"
            }
        }
    }
    
    # レジストリ設定検証
    [void] ValidateRegistrySettings() {
        foreach ($registryPath in $this.Config.RegistrySettings.Keys) {
            # 重要なレジストリパスの変更警告
            if ($registryPath -like "*\Security\*" -or $registryPath -like "*\Policies\*") {
                $this.ValidationWarnings += "セキュリティ関連のレジストリ設定が変更されています: $registryPath"
            }
            
            # IPv6無効化の確認
            if ($registryPath -like "*Tcpip6*" -and $this.Config.DisableIPv6) {
                $this.ValidationWarnings += "IPv6が完全に無効化されます（一部アプリケーションで問題が発生する可能性があります）"
            }
        }
    }
    
    # サービス設定検証
    [void] ValidateServiceSettings() {
        $criticalServices = @("BTHSERV", "Themes", "AudioSrv", "AudioEndpointBuilder")
        
        foreach ($serviceName in $this.Config.ServiceSettings.Keys) {
            $serviceConfig = $this.Config.ServiceSettings[$serviceName]
            
            if ($serviceConfig.StartMode -eq "Disabled" -and $serviceName -in $criticalServices) {
                $this.ValidationWarnings += "重要なサービスが無効化されています: $serviceName ($($serviceConfig.Description))"
            }
        }
    }
    
    # セキュリティへの影響検証
    [void] ValidateSecurityImplications() {
        $securityIssues = @()
        
        if ($this.Config.DisableFirewall) {
            $securityIssues += "Firewall無効化"
        }
        
        if ($this.Config.GroupPolicySettings.ContainsKey("Computer Configuration\Administrative Templates\Network\Lanman Workstation")) {
            $lanmanSettings = $this.Config.GroupPolicySettings["Computer Configuration\Administrative Templates\Network\Lanman Workstation"]
            if ($lanmanSettings.ContainsKey("Enable insecure guest logons") -and $lanmanSettings["Enable insecure guest logons"] -eq "Enabled") {
                $securityIssues += "安全でないゲストログオンの有効化"
            }
        }
        
        if ($securityIssues.Count -gt 0) {
            $this.ValidationWarnings += "セキュリティに影響する設定が含まれています: $($securityIssues -join ', ')"
        }
    }
}

# メイン関数：UnattendXMLネットワーク設定生成
function New-UnattendNetworkConfiguration {
    <#
    .SYNOPSIS
        UnattendXMLファイルのネットワーク設定を生成する
    
    .PARAMETER Config
        メイン設定オブジェクト
    
    .PARAMETER XmlDocument
        XML文書オブジェクト
    
    .PARAMETER NetworkConfig
        ネットワーク設定（省略時はデフォルト設定）
    
    .EXAMPLE
        New-UnattendNetworkConfiguration -Config $config -XmlDocument $xmlDoc
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [object]$Config,
        
        [Parameter(Mandatory = $true)]
        [System.Xml.XmlDocument]$XmlDocument,
        
        [Parameter(Mandatory = $false)]
        [NetworkConfiguration]$NetworkConfig
    )
    
    try {
        Write-Verbose "UnattendXML ネットワーク設定生成開始"
        
        # ネットワーク設定の準備
        if ($NetworkConfig -eq $null) {
            $NetworkConfig = [NetworkConfiguration]::new()
            
            # メイン設定からの値適用
            if ($Config.PSObject.Properties.Name -contains "System") {
                if ($Config.System.PSObject.Properties.Name -contains "DisableIPv6") {
                    $NetworkConfig.DisableIPv6 = $Config.System.DisableIPv6
                }
                if ($Config.System.PSObject.Properties.Name -contains "DisableFirewall") {
                    $NetworkConfig.DisableFirewall = $Config.System.DisableFirewall
                }
                if ($Config.System.PSObject.Properties.Name -contains "DisableBluetooth") {
                    $NetworkConfig.DisableBluetooth = $Config.System.DisableBluetooth
                }
                if ($Config.System.PSObject.Properties.Name -contains "MuteAudio") {
                    $NetworkConfig.MuteAudio = $Config.System.MuteAudio
                }
            }
            
            # 設定に基づいてデフォルト設定を再初期化
            $NetworkConfig.InitializeDefaultSettings()
        }
        
        # 設定検証
        $validator = [NetworkConfigValidator]::new($NetworkConfig)
        if (!$validator.ValidateConfiguration()) {
            throw "ネットワーク設定の検証に失敗しました"
        }
        
        # XML生成
        $xmlGenerator = [UnattendNetworkXMLGenerator]::new($XmlDocument, $NetworkConfig)
        $result = $xmlGenerator.GenerateNetworkConfigurationXML()
        
        Write-Verbose "UnattendXML ネットワーク設定生成完了"
        return @{
            Success = $true
            Message = "ネットワーク設定生成完了"
            DisableIPv6 = $NetworkConfig.DisableIPv6
            DisableFirewall = $NetworkConfig.DisableFirewall
            DisableBluetooth = $NetworkConfig.DisableBluetooth
            RegistrySettings = $NetworkConfig.RegistrySettings.Count
            ServiceSettings = $NetworkConfig.ServiceSettings.Count
        }
    }
    catch {
        Write-Error "ネットワーク設定生成エラー: $_"
        return @{
            Success = $false
            Message = "ネットワーク設定生成エラー: $_"
            Error = $_
        }
    }
}

# ネットワーク診断関数
function Test-NetworkConfiguration {
    <#
    .SYNOPSIS
        現在のシステムのネットワーク設定を診断する
    
    .EXAMPLE
        Test-NetworkConfiguration
    #>
    [CmdletBinding()]
    param()
    
    $result = @{
        IPv6Status = $null
        FirewallStatus = $null
        BluetoothStatus = $null
        NetworkProfile = $null
        Recommendations = @()
    }
    
    try {
        # IPv6ステータス確認
        try {
            $ipv6Adapters = Get-NetAdapter | Get-NetAdapterBinding -ComponentID ms_tcpip6 | Where-Object { $_.Enabled }
            $result.IPv6Status = @{
                Enabled = $ipv6Adapters.Count -gt 0
                AdapterCount = $ipv6Adapters.Count
            }
            
            if ($ipv6Adapters.Count -gt 0) {
                $result.Recommendations += "IPv6が有効になっています。企業環境では無効化を検討してください。"
            }
        }
        catch {
            $result.IPv6Status = @{ Error = $_.Exception.Message }
        }
        
        # Firewallステータス確認
        try {
            $firewallProfiles = Get-NetFirewallProfile
            $result.FirewallStatus = @{
                Domain = ($firewallProfiles | Where-Object { $_.Name -eq "Domain" }).Enabled
                Private = ($firewallProfiles | Where-Object { $_.Name -eq "Private" }).Enabled
                Public = ($firewallProfiles | Where-Object { $_.Name -eq "Public" }).Enabled
            }
            
            $enabledProfiles = @($result.FirewallStatus.GetEnumerator() | Where-Object { $_.Value }).Count
            if ($enabledProfiles -eq 0) {
                $result.Recommendations += "すべてのFirewallプロファイルが無効になっています。"
            }
        }
        catch {
            $result.FirewallStatus = @{ Error = $_.Exception.Message }
        }
        
        # Bluetoothステータス確認
        try {
            $bluetoothServices = Get-Service -Name "BTHSERV", "BthAvrcpTg", "BthHFSrv" -ErrorAction SilentlyContinue
            $result.BluetoothStatus = @{
                Services = $bluetoothServices | ForEach-Object { 
                    @{ Name = $_.Name; Status = $_.Status; StartType = $_.StartType }
                }
                IsEnabled = ($bluetoothServices | Where-Object { $_.Status -eq "Running" }).Count -gt 0
            }
            
            if ($result.BluetoothStatus.IsEnabled) {
                $result.Recommendations += "Bluetoothサービスが実行中です。不要な場合は無効化を検討してください。"
            }
        }
        catch {
            $result.BluetoothStatus = @{ Error = $_.Exception.Message }
        }
        
        # ネットワークプロファイル確認
        try {
            $networkProfiles = Get-NetConnectionProfile
            $result.NetworkProfile = $networkProfiles | ForEach-Object {
                @{
                    InterfaceAlias = $_.InterfaceAlias
                    NetworkCategory = $_.NetworkCategory
                    IPv4Connectivity = $_.IPv4Connectivity
                    IPv6Connectivity = $_.IPv6Connectivity
                }
            }
        }
        catch {
            $result.NetworkProfile = @{ Error = $_.Exception.Message }
        }
        
        Write-Host "ネットワーク診断結果:" -ForegroundColor Cyan
        Write-Host ($result | ConvertTo-Json -Depth 3)
        
        return $result
    }
    catch {
        Write-Error "ネットワーク診断エラー: $_"
        return $result
    }
}

# エクスポートするメンバー
Export-ModuleMember -Function @(
    'New-UnattendNetworkConfiguration',
    'Test-NetworkConfiguration'
) -Class @(
    'NetworkConfiguration',
    'UnattendNetworkXMLGenerator',
    'NetworkConfigValidator'
) -Variable @(
    'NetworkProfileType',
    'FirewallProfile'
)