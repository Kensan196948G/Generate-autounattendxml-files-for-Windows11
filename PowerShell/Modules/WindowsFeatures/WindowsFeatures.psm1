#Requires -Version 5.0

<#
.SYNOPSIS
    Windows 11 UnattendXML Windows機能モジュール

.DESCRIPTION
    Sysprep応答ファイルでのWindows機能設定を管理するPowerShellモジュール
    - .NET Framework 3.5有効化
    - DISMコマンドレット使用
    - Windows Capabilityサービス管理
    - オプション機能の管理

.VERSION
    1.0.0

.AUTHOR
    Windows 11 Sysprep Automation Team

.COPYRIGHT
    Copyright (c) 2025. All rights reserved.
#>

# .NET Framework アセンブリの読み込み
Add-Type -AssemblyName System.Xml
Add-Type -AssemblyName Microsoft.Management.Infrastructure

# Windows機能状態列挙型
enum WindowsFeatureState {
    Disabled = 0
    Enabled = 1
    EnablePending = 2
    DisablePending = 3
}

enum InstallMethod {
    DISM = 0
    PowerShell = 1
    Registry = 2
}

# Windows機能設定クラス
class WindowsFeature {
    [string]$Name
    [string]$DisplayName
    [string]$Description
    [WindowsFeatureState]$TargetState
    [InstallMethod]$InstallMethod
    [string[]]$Dependencies
    [bool]$RestartRequired
    [hashtable]$CustomSettings
    
    # コンストラクタ
    WindowsFeature([string]$name, [WindowsFeatureState]$targetState) {
        $this.Name = $name
        $this.DisplayName = $name
        $this.Description = ""
        $this.TargetState = $targetState
        $this.InstallMethod = [InstallMethod]::DISM
        $this.Dependencies = @()
        $this.RestartRequired = $false
        $this.CustomSettings = @{}
    }
    
    # 詳細コンストラクタ
    WindowsFeature([string]$name, [string]$displayName, [WindowsFeatureState]$targetState, [InstallMethod]$installMethod) {
        $this.Name = $name
        $this.DisplayName = $displayName
        $this.Description = ""
        $this.TargetState = $targetState
        $this.InstallMethod = $installMethod
        $this.Dependencies = @()
        $this.RestartRequired = $false
        $this.CustomSettings = @{}
    }
}

# Windows機能設定管理クラス
class WindowsFeaturesConfig {
    [WindowsFeature[]]$Features
    [bool]$EnableDotNet35
    [bool]$EnableHyperV
    [bool]$EnableWSL
    [bool]$EnableWindowsSandbox
    [bool]$DisableCortana
    [bool]$DisableWindowsSearch
    [hashtable]$OptionalFeatures
    [hashtable]$Capabilities
    
    # コンストラクタ
    WindowsFeaturesConfig() {
        $this.Features = @()
        $this.EnableDotNet35 = $true
        $this.EnableHyperV = $false
        $this.EnableWSL = $false
        $this.EnableWindowsSandbox = $false
        $this.DisableCortana = $true
        $this.DisableWindowsSearch = $false
        $this.OptionalFeatures = @{}
        $this.Capabilities = @{}
        
        # デフォルト機能設定の初期化
        $this.InitializeDefaultFeatures()
    }
    
    # デフォルト機能設定初期化
    [void] InitializeDefaultFeatures() {
        # .NET Framework 3.5
        if ($this.EnableDotNet35) {
            $dotNet35 = [WindowsFeature]::new("NetFx3", ".NET Framework 3.5", [WindowsFeatureState]::Enabled, [InstallMethod]::DISM)
            $dotNet35.Description = ".NET Framework 3.5 (レガシーアプリケーション互換性)"
            $dotNet35.RestartRequired = $true
            $this.Features += $dotNet35
        }
        
        # Hyper-V
        if ($this.EnableHyperV) {
            $hyperV = [WindowsFeature]::new("Microsoft-Hyper-V-All", "Hyper-V", [WindowsFeatureState]::Enabled, [InstallMethod]::DISM)
            $hyperV.Description = "Hyper-V 仮想化プラットフォーム"
            $hyperV.RestartRequired = $true
            $hyperV.Dependencies = @("Microsoft-Hyper-V", "Microsoft-Hyper-V-Management-PowerShell")
            $this.Features += $hyperV
        }
        
        # WSL (Windows Subsystem for Linux)
        if ($this.EnableWSL) {
            $wsl = [WindowsFeature]::new("Microsoft-Windows-Subsystem-Linux", "Windows Subsystem for Linux", [WindowsFeatureState]::Enabled, [InstallMethod]::DISM)
            $wsl.Description = "Linux用Windowsサブシステム"
            $wsl.RestartRequired = $true
            $this.Features += $wsl
            
            # Virtual Machine Platform (WSL2用)
            $vmPlatform = [WindowsFeature]::new("VirtualMachinePlatform", "Virtual Machine Platform", [WindowsFeatureState]::Enabled, [InstallMethod]::DISM)
            $vmPlatform.Description = "仮想マシンプラットフォーム (WSL2用)"
            $vmPlatform.RestartRequired = $true
            $this.Features += $vmPlatform
        }
        
        # Windows Sandbox
        if ($this.EnableWindowsSandbox) {
            $sandbox = [WindowsFeature]::new("Containers-DisposableClientVM", "Windows Sandbox", [WindowsFeatureState]::Enabled, [InstallMethod]::DISM)
            $sandbox.Description = "Windows サンドボックス"
            $sandbox.RestartRequired = $true
            $this.Features += $sandbox
        }
        
        # オプション機能設定
        $this.OptionalFeatures = @{
            "TelnetClient" = @{
                State = [WindowsFeatureState]::Disabled
                Description = "Telnet クライアント"
            }
            "TFTP" = @{
                State = [WindowsFeatureState]::Disabled
                Description = "TFTP クライアント"
            }
            "SimpleTCP" = @{
                State = [WindowsFeatureState]::Disabled
                Description = "Simple TCP/IP Services"
            }
            "WorkFolders-Client" = @{
                State = [WindowsFeatureState]::Enabled
                Description = "Work Folders クライアント"
            }
        }
        
        # Windows Capability設定
        $this.Capabilities = @{
            "OpenSSH.Client~~~~0.0.1.0" = @{
                State = [WindowsFeatureState]::Enabled
                Description = "OpenSSH クライアント"
            }
            "OpenSSH.Server~~~~0.0.1.0" = @{
                State = [WindowsFeatureState]::Disabled
                Description = "OpenSSH サーバー"
            }
            "Microsoft.Windows.PowerShell.ISE~~~~0.0.1.0" = @{
                State = [WindowsFeatureState]::Enabled
                Description = "PowerShell ISE"
            }
        }
    }
    
    # 機能追加
    [void] AddFeature([WindowsFeature]$feature) {
        $this.Features += $feature
    }
    
    # 機能検索
    [WindowsFeature] GetFeature([string]$name) {
        return $this.Features | Where-Object { $_.Name -eq $name }
    }
}

# Windows機能XML生成クラス
class UnattendWindowsFeaturesXMLGenerator {
    [System.Xml.XmlDocument]$XmlDocument
    [WindowsFeaturesConfig]$Config
    [System.Xml.XmlNamespaceManager]$NamespaceManager
    
    # コンストラクタ
    UnattendWindowsFeaturesXMLGenerator([System.Xml.XmlDocument]$xmlDoc, [WindowsFeaturesConfig]$config) {
        $this.XmlDocument = $xmlDoc
        $this.Config = $config
        $this.NamespaceManager = New-Object System.Xml.XmlNamespaceManager($xmlDoc.NameTable)
        $this.NamespaceManager.AddNamespace("un", "urn:schemas-microsoft-com:unattend")
    }
    
    # Windows機能設定XML生成
    [System.Xml.XmlElement] GenerateWindowsFeaturesXML() {
        Write-Verbose "Windows機能設定XML生成開始"
        
        $unattendRoot = $this.XmlDocument.DocumentElement
        
        # offlineServicing パスでの機能インストール
        $this.AddOfflineServicingSettings($unattendRoot)
        
        # specialize パスでの追加設定
        $this.AddSpecializeSettings($unattendRoot)
        
        Write-Verbose "Windows機能設定XML生成完了"
        return $unattendRoot
    }
    
    # Offline Servicing パス設定追加
    [void] AddOfflineServicingSettings([System.Xml.XmlElement]$unattendRoot) {
        Write-Verbose "Offline Servicing パス設定追加開始"
        
        $settingsElement = $this.GetOrCreateSettingsElement($unattendRoot, "offlineServicing")
        
        # Microsoft-Windows-PnpCustomizationsNonWinPE コンポーネント
        $pnpComponent = $this.GetOrCreateComponent($settingsElement, "Microsoft-Windows-PnpCustomizationsNonWinPE")
        
        # DriverPaths要素（必要に応じて）
        # $this.AddDriverPaths($pnpComponent)
        
        # Windows機能の有効化/無効化
        $this.AddWindowsFeatures($settingsElement)
        
        Write-Verbose "Offline Servicing パス設定追加完了"
    }
    
    # Specialize パス設定追加
    [void] AddSpecializeSettings([System.Xml.XmlElement]$unattendRoot) {
        Write-Verbose "Specialize パス設定追加開始"
        
        $settingsElement = $this.GetOrCreateSettingsElement($unattendRoot, "specialize")
        
        # 追加のPowerShellコマンド実行
        $this.AddPowerShellFeatureCommands($settingsElement)
        
        # Windows Capability設定
        $this.AddWindowsCapabilities($settingsElement)
        
        Write-Verbose "Specialize パス設定追加完了"
    }
    
    # Windows機能追加
    [void] AddWindowsFeatures([System.Xml.XmlElement]$settingsElement) {
        Write-Verbose "Windows機能追加開始"
        
        if ($this.Config.Features.Count -eq 0) {
            return
        }
        
        # Microsoft-Windows-ServerManager-SvrMgrNc コンポーネント
        $serverManagerComponent = $this.GetOrCreateComponent($settingsElement, "Microsoft-Windows-ServerManager-SvrMgrNc")
        
        # WindowsFeatures要素
        $windowsFeaturesElement = $this.XmlDocument.CreateElement("WindowsFeatures", $serverManagerComponent.NamespaceURI)
        $serverManagerComponent.AppendChild($windowsFeaturesElement) | Out-Null
        
        foreach ($feature in $this.Config.Features) {
            if ($feature.TargetState -eq [WindowsFeatureState]::Enabled) {
                # Feature要素
                $featureElement = $this.XmlDocument.CreateElement("Feature", $windowsFeaturesElement.NamespaceURI)
                $featureElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
                $windowsFeaturesElement.AppendChild($featureElement) | Out-Null
                
                # Name要素
                $nameElement = $this.XmlDocument.CreateElement("Name", $featureElement.NamespaceURI)
                $nameElement.InnerText = $feature.Name
                $featureElement.AppendChild($nameElement) | Out-Null
                
                Write-Verbose "Windows機能追加: $($feature.Name)"
            }
        }
        
        Write-Verbose "Windows機能追加完了"
    }
    
    # PowerShell機能コマンド追加
    [void] AddPowerShellFeatureCommands([System.Xml.XmlElement]$settingsElement) {
        Write-Verbose "PowerShell機能コマンド追加開始"
        
        $shellSetupComponent = $this.GetOrCreateComponent($settingsElement, "Microsoft-Windows-Shell-Setup")
        
        # FirstLogonCommands要素取得または作成
        $firstLogonCommandsElement = $shellSetupComponent.SelectSingleNode("un:FirstLogonCommands", $this.NamespaceManager)
        if ($firstLogonCommandsElement -eq $null) {
            $firstLogonCommandsElement = $this.XmlDocument.CreateElement("FirstLogonCommands", $shellSetupComponent.NamespaceURI)
            $shellSetupComponent.AppendChild($firstLogonCommandsElement) | Out-Null
        }
        
        # 既存コマンド数を取得
        $existingCommands = $firstLogonCommandsElement.SelectNodes("un:SynchronousCommand", $this.NamespaceManager)
        $commandOrder = $existingCommands.Count + 1
        
        # .NET Framework 3.5 の DISM コマンド
        if ($this.Config.EnableDotNet35) {
            $synchronousCommandElement = $this.XmlDocument.CreateElement("SynchronousCommand", $firstLogonCommandsElement.NamespaceURI)
            $synchronousCommandElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $firstLogonCommandsElement.AppendChild($synchronousCommandElement) | Out-Null
            
            $orderElement = $this.XmlDocument.CreateElement("Order", $synchronousCommandElement.NamespaceURI)
            $orderElement.InnerText = $commandOrder.ToString()
            $synchronousCommandElement.AppendChild($orderElement) | Out-Null
            
            $commandLineElement = $this.XmlDocument.CreateElement("CommandLine", $synchronousCommandElement.NamespaceURI)
            $commandLineElement.InnerText = "dism /online /enable-feature /featurename:NetFx3 /all /norestart"
            $synchronousCommandElement.AppendChild($commandLineElement) | Out-Null
            
            $descriptionElement = $this.XmlDocument.CreateElement("Description", $synchronousCommandElement.NamespaceURI)
            $descriptionElement.InnerText = "Enable .NET Framework 3.5"
            $synchronousCommandElement.AppendChild($descriptionElement) | Out-Null
            
            $commandOrder++
        }
        
        # オプション機能の設定
        foreach ($featureName in $this.Config.OptionalFeatures.Keys) {
            $featureConfig = $this.Config.OptionalFeatures[$featureName]
            
            $synchronousCommandElement = $this.XmlDocument.CreateElement("SynchronousCommand", $firstLogonCommandsElement.NamespaceURI)
            $synchronousCommandElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $firstLogonCommandsElement.AppendChild($synchronousCommandElement) | Out-Null
            
            $orderElement = $this.XmlDocument.CreateElement("Order", $synchronousCommandElement.NamespaceURI)
            $orderElement.InnerText = $commandOrder.ToString()
            $synchronousCommandElement.AppendChild($orderElement) | Out-Null
            
            $commandLineElement = $this.XmlDocument.CreateElement("CommandLine", $synchronousCommandElement.NamespaceURI)
            if ($featureConfig.State -eq [WindowsFeatureState]::Enabled) {
                $commandLineElement.InnerText = "dism /online /enable-feature /featurename:$featureName /all /norestart"
            } else {
                $commandLineElement.InnerText = "dism /online /disable-feature /featurename:$featureName /norestart"
            }
            $synchronousCommandElement.AppendChild($commandLineElement) | Out-Null
            
            $descriptionElement = $this.XmlDocument.CreateElement("Description", $synchronousCommandElement.NamespaceURI)
            $descriptionElement.InnerText = "Configure Feature: $featureName ($($featureConfig.Description))"
            $synchronousCommandElement.AppendChild($descriptionElement) | Out-Null
            
            $commandOrder++
        }
        
        Write-Verbose "PowerShell機能コマンド追加完了"
    }
    
    # Windows Capability設定追加
    [void] AddWindowsCapabilities([System.Xml.XmlElement]$settingsElement) {
        Write-Verbose "Windows Capability設定追加開始"
        
        if ($this.Config.Capabilities.Count -eq 0) {
            return
        }
        
        $shellSetupComponent = $this.GetOrCreateComponent($settingsElement, "Microsoft-Windows-Shell-Setup")
        
        # FirstLogonCommands要素取得
        $firstLogonCommandsElement = $shellSetupComponent.SelectSingleNode("un:FirstLogonCommands", $this.NamespaceManager)
        if ($firstLogonCommandsElement -eq $null) {
            $firstLogonCommandsElement = $this.XmlDocument.CreateElement("FirstLogonCommands", $shellSetupComponent.NamespaceURI)
            $shellSetupComponent.AppendChild($firstLogonCommandsElement) | Out-Null
        }
        
        # 既存コマンド数を取得
        $existingCommands = $firstLogonCommandsElement.SelectNodes("un:SynchronousCommand", $this.NamespaceManager)
        $commandOrder = $existingCommands.Count + 1
        
        foreach ($capabilityName in $this.Config.Capabilities.Keys) {
            $capabilityConfig = $this.Config.Capabilities[$capabilityName]
            
            $synchronousCommandElement = $this.XmlDocument.CreateElement("SynchronousCommand", $firstLogonCommandsElement.NamespaceURI)
            $synchronousCommandElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $firstLogonCommandsElement.AppendChild($synchronousCommandElement) | Out-Null
            
            $orderElement = $this.XmlDocument.CreateElement("Order", $synchronousCommandElement.NamespaceURI)
            $orderElement.InnerText = $commandOrder.ToString()
            $synchronousCommandElement.AppendChild($orderElement) | Out-Null
            
            $commandLineElement = $this.XmlDocument.CreateElement("CommandLine", $synchronousCommandElement.NamespaceURI)
            if ($capabilityConfig.State -eq [WindowsFeatureState]::Enabled) {
                $commandLineElement.InnerText = "powershell.exe -Command `"Add-WindowsCapability -Online -Name '$capabilityName'`""
            } else {
                $commandLineElement.InnerText = "powershell.exe -Command `"Remove-WindowsCapability -Online -Name '$capabilityName'`""
            }
            $synchronousCommandElement.AppendChild($commandLineElement) | Out-Null
            
            $descriptionElement = $this.XmlDocument.CreateElement("Description", $synchronousCommandElement.NamespaceURI)
            $descriptionElement.InnerText = "Configure Capability: $capabilityName ($($capabilityConfig.Description))"
            $synchronousCommandElement.AppendChild($descriptionElement) | Out-Null
            
            $commandOrder++
        }
        
        Write-Verbose "Windows Capability設定追加完了"
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

# Windows機能設定検証クラス
class WindowsFeaturesValidator {
    [WindowsFeaturesConfig]$Config
    [string[]]$ValidationErrors
    [string[]]$ValidationWarnings
    
    # コンストラクタ
    WindowsFeaturesValidator([WindowsFeaturesConfig]$config) {
        $this.Config = $config
        $this.ValidationErrors = @()
        $this.ValidationWarnings = @()
    }
    
    # 設定検証実行
    [bool] ValidateConfiguration() {
        Write-Verbose "Windows機能設定検証開始"
        
        $this.ValidationErrors = @()
        $this.ValidationWarnings = @()
        
        # 基本検証
        $this.ValidateFeatureDependencies()
        $this.ValidateSystemRequirements()
        $this.ValidateCompatibility()
        $this.ValidateSecurityImplications()
        
        # 結果出力
        foreach ($warning in $this.ValidationWarnings) {
            Write-Warning $warning
        }
        
        foreach ($error in $this.ValidationErrors) {
            Write-Error $error
        }
        
        $isValid = $this.ValidationErrors.Count -eq 0
        Write-Verbose "Windows機能設定検証完了 (Valid: $isValid)"
        
        return $isValid
    }
    
    # 機能依存関係検証
    [void] ValidateFeatureDependencies() {
        foreach ($feature in $this.Config.Features) {
            if ($feature.TargetState -eq [WindowsFeatureState]::Enabled -and $feature.Dependencies.Count -gt 0) {
                foreach ($dependency in $feature.Dependencies) {
                    $dependentFeature = $this.Config.GetFeature($dependency)
                    if ($dependentFeature -eq $null -or $dependentFeature.TargetState -ne [WindowsFeatureState]::Enabled) {
                        $this.ValidationWarnings += "機能 '$($feature.Name)' の依存関係 '$dependency' が有効になっていません"
                    }
                }
            }
        }
        
        # Hyper-V 特別チェック
        if ($this.Config.EnableHyperV) {
            $hyperVFeature = $this.Config.GetFeature("Microsoft-Hyper-V-All")
            if ($hyperVFeature -ne $null -and $hyperVFeature.Dependencies.Count -eq 0) {
                $this.ValidationWarnings += "Hyper-V機能の依存関係が正しく設定されていない可能性があります"
            }
        }
    }
    
    # システム要件検証
    [void] ValidateSystemRequirements() {
        # Hyper-V システム要件
        if ($this.Config.EnableHyperV) {
            $this.ValidationWarnings += "Hyper-V有効化: システムがハードウェア仮想化をサポートしている必要があります"
        }
        
        # WSL システム要件
        if ($this.Config.EnableWSL) {
            $this.ValidationWarnings += "WSL有効化: Windows 10 バージョン 1903 以降が必要です"
        }
        
        # Windows Sandbox システム要件
        if ($this.Config.EnableWindowsSandbox) {
            $this.ValidationWarnings += "Windows Sandbox有効化: Pro/Enterprise エディションが必要です"
        }
    }
    
    # 互換性検証
    [void] ValidateCompatibility() {
        # .NET Framework バージョン競合チェック
        if ($this.Config.EnableDotNet35) {
            $this.ValidationWarnings += ".NET Framework 3.5有効化: 新しい.NETバージョンとの互換性を確認してください"
        }
        
        # 機能競合チェック
        $conflictingFeatures = @()
        
        if ($this.Config.EnableHyperV -and $this.Config.EnableWindowsSandbox) {
            $conflictingFeatures += "Hyper-V と Windows Sandbox"
        }
        
        if ($conflictingFeatures.Count -gt 0) {
            $this.ValidationWarnings += "機能競合の可能性: $($conflictingFeatures -join ', ')"
        }
    }
    
    # セキュリティへの影響検証
    [void] ValidateSecurityImplications() {
        $securityRisks = @()
        
        # Telnet クライアント
        if ($this.Config.OptionalFeatures.ContainsKey("TelnetClient")) {
            $telnetConfig = $this.Config.OptionalFeatures["TelnetClient"]
            if ($telnetConfig.State -eq [WindowsFeatureState]::Enabled) {
                $securityRisks += "Telnet クライアントの有効化（セキュリティリスク）"
            }
        }
        
        # OpenSSH サーバー
        if ($this.Config.Capabilities.ContainsKey("OpenSSH.Server~~~~0.0.1.0")) {
            $sshConfig = $this.Config.Capabilities["OpenSSH.Server~~~~0.0.1.0"]
            if ($sshConfig.State -eq [WindowsFeatureState]::Enabled) {
                $securityRisks += "OpenSSH サーバーの有効化（適切な設定が必要）"
            }
        }
        
        if ($securityRisks.Count -gt 0) {
            $this.ValidationWarnings += "セキュリティに影響する機能: $($securityRisks -join ', ')"
        }
    }
}

# メイン関数：UnattendXML Windows機能設定生成
function New-UnattendWindowsFeatures {
    <#
    .SYNOPSIS
        UnattendXMLファイルのWindows機能設定を生成する
    
    .PARAMETER Config
        メイン設定オブジェクト
    
    .PARAMETER XmlDocument
        XML文書オブジェクト
    
    .PARAMETER FeaturesConfig
        Windows機能設定（省略時はデフォルト設定）
    
    .EXAMPLE
        New-UnattendWindowsFeatures -Config $config -XmlDocument $xmlDoc
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [object]$Config,
        
        [Parameter(Mandatory = $true)]
        [System.Xml.XmlDocument]$XmlDocument,
        
        [Parameter(Mandatory = $false)]
        [WindowsFeaturesConfig]$FeaturesConfig
    )
    
    try {
        Write-Verbose "UnattendXML Windows機能設定生成開始"
        
        # Windows機能設定の準備
        if ($FeaturesConfig -eq $null) {
            $FeaturesConfig = [WindowsFeaturesConfig]::new()
            
            # メイン設定からの値適用
            if ($Config.PSObject.Properties.Name -contains "Applications") {
                if ($Config.Applications.PSObject.Properties.Name -contains "EnableDotNet35") {
                    $FeaturesConfig.EnableDotNet35 = $Config.Applications.EnableDotNet35
                }
            }
        }
        
        # 設定検証
        $validator = [WindowsFeaturesValidator]::new($FeaturesConfig)
        if (!$validator.ValidateConfiguration()) {
            throw "Windows機能設定の検証に失敗しました"
        }
        
        # XML生成
        $xmlGenerator = [UnattendWindowsFeaturesXMLGenerator]::new($XmlDocument, $FeaturesConfig)
        $result = $xmlGenerator.GenerateWindowsFeaturesXML()
        
        Write-Verbose "UnattendXML Windows機能設定生成完了"
        return @{
            Success = $true
            Message = "Windows機能設定生成完了"
            EnabledFeatures = ($FeaturesConfig.Features | Where-Object { $_.TargetState -eq [WindowsFeatureState]::Enabled }).Count
            EnableDotNet35 = $FeaturesConfig.EnableDotNet35
            OptionalFeatures = $FeaturesConfig.OptionalFeatures.Count
            Capabilities = $FeaturesConfig.Capabilities.Count
        }
    }
    catch {
        Write-Error "Windows機能設定生成エラー: $_"
        return @{
            Success = $false
            Message = "Windows機能設定生成エラー: $_"
            Error = $_
        }
    }
}

# Windows機能診断関数
function Test-WindowsFeatureStatus {
    <#
    .SYNOPSIS
        現在のシステムのWindows機能状態を診断する
    
    .EXAMPLE
        Test-WindowsFeatureStatus
    #>
    [CmdletBinding()]
    param()
    
    $result = @{
        InstalledFeatures = @()
        AvailableFeatures = @()
        Capabilities = @()
        DotNet35Status = $null
        Recommendations = @()
    }
    
    try {
        Write-Host "Windows機能状態診断中..." -ForegroundColor Yellow
        
        # インストール済み機能確認
        try {
            $installedFeatures = Get-WindowsOptionalFeature -Online | Where-Object { $_.State -eq "Enabled" }
            $result.InstalledFeatures = $installedFeatures | ForEach-Object {
                @{
                    FeatureName = $_.FeatureName
                    DisplayName = $_.DisplayName
                    State = $_.State
                    RestartRequired = $_.RestartRequired
                }
            }
        }
        catch {
            $result.InstalledFeatures = @{ Error = $_.Exception.Message }
        }
        
        # 利用可能機能確認
        try {
            $availableFeatures = Get-WindowsOptionalFeature -Online | Where-Object { $_.State -eq "Disabled" } | Select-Object -First 10
            $result.AvailableFeatures = $availableFeatures | ForEach-Object {
                @{
                    FeatureName = $_.FeatureName
                    DisplayName = $_.DisplayName
                }
            }
        }
        catch {
            $result.AvailableFeatures = @{ Error = $_.Exception.Message }
        }
        
        # .NET Framework 3.5 状態確認
        try {
            $dotNet35 = Get-WindowsOptionalFeature -Online -FeatureName "NetFx3" -ErrorAction SilentlyContinue
            $result.DotNet35Status = @{
                Installed = $dotNet35.State -eq "Enabled"
                State = $dotNet35.State
                RestartRequired = $dotNet35.RestartRequired
            }
            
            if ($dotNet35.State -ne "Enabled") {
                $result.Recommendations += ".NET Framework 3.5が無効になっています。レガシーアプリケーション用に有効化を検討してください。"
            }
        }
        catch {
            $result.DotNet35Status = @{ Error = $_.Exception.Message }
        }
        
        # Windows Capability確認
        try {
            $capabilities = Get-WindowsCapability -Online | Where-Object { $_.State -eq "Installed" } | Select-Object -First 10
            $result.Capabilities = $capabilities | ForEach-Object {
                @{
                    Name = $_.Name
                    DisplayName = $_.DisplayName
                    State = $_.State
                }
            }
        }
        catch {
            $result.Capabilities = @{ Error = $_.Exception.Message }
        }
        
        Write-Host "Windows機能診断結果:" -ForegroundColor Cyan
        Write-Host "インストール済み機能数: $($result.InstalledFeatures.Count)" -ForegroundColor Green
        Write-Host "利用可能機能数: $($result.AvailableFeatures.Count)" -ForegroundColor Green
        Write-Host ".NET Framework 3.5: $(if ($result.DotNet35Status.Installed) { '有効' } else { '無効' })" -ForegroundColor $(if ($result.DotNet35Status.Installed) { 'Green' } else { 'Yellow' })
        
        return $result
    }
    catch {
        Write-Error "Windows機能診断エラー: $_"
        return $result
    }
}

# エクスポートするメンバー
Export-ModuleMember -Function @(
    'New-UnattendWindowsFeatures',
    'Test-WindowsFeatureStatus'
) -Class @(
    'WindowsFeature',
    'WindowsFeaturesConfig',
    'UnattendWindowsFeaturesXMLGenerator',
    'WindowsFeaturesValidator'
) -Variable @(
    'WindowsFeatureState',
    'InstallMethod'
)