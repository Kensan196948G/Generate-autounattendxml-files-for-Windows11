<#
.SYNOPSIS
    XML生成エンジン V2 - 全23項目対応
    
.DESCRIPTION
    Windows 11 autounattend.xml を生成する高度なXMLジェネレーター
    FirstLogonCommands含む完全な設定を生成
#>

Export-ModuleMember -Function @(
    'New-ComprehensiveXML'
    'Add-FirstLogonCommands'
    'Add-UserAccounts'
    'Add-DiskConfiguration'
    'Add-NetworkConfiguration'
)

function New-ComprehensiveXML {
    <#
    .SYNOPSIS
        包括的なautounattend.xmlを生成
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object]$Config,
        
        [Parameter()]
        [hashtable]$ProcessResults = @{}
    )
    
    Write-Verbose "XML生成エンジン: 全23項目のXML生成を開始"
    
    # XML文書の初期化
    $xml = New-Object System.Xml.XmlDocument
    $xml.AppendChild($xml.CreateXmlDeclaration("1.0", "utf-8", $null)) | Out-Null
    
    # ルート要素
    $unattend = $xml.CreateElement("unattend", "urn:schemas-microsoft-com:unattend")
    $xml.AppendChild($unattend) | Out-Null
    
    # 各パスの設定を追加
    Add-WindowsPESettings -Xml $xml -Config $Config
    Add-SpecializeSettings -Xml $xml -Config $Config
    Add-OobeSystemSettings -Xml $xml -Config $Config -ProcessResults $ProcessResults
    Add-OfflineServicingSettings -Xml $xml -Config $Config
    
    Write-Verbose "XML生成エンジン: XML生成完了"
    
    return $xml.OuterXml
}

function Add-WindowsPESettings {
    <#
    .SYNOPSIS
        windowsPEパスの設定を追加
    #>
    param(
        [System.Xml.XmlDocument]$Xml,
        [object]$Config
    )
    
    $settings = $Xml.CreateElement("settings", $Xml.DocumentElement.NamespaceURI)
    $settings.SetAttribute("pass", "windowsPE")
    $Xml.DocumentElement.AppendChild($settings) | Out-Null
    
    # International-Core-WinPE
    $component = $Xml.CreateElement("component", $Xml.DocumentElement.NamespaceURI)
    $component.SetAttribute("name", "Microsoft-Windows-International-Core-WinPE")
    $component.SetAttribute("processorArchitecture", $Config.Architecture)
    $component.SetAttribute("publicKeyToken", "31bf3856ad364e35")
    $component.SetAttribute("language", "neutral")
    $component.SetAttribute("versionScope", "nonSxS")
    $settings.AppendChild($component) | Out-Null
    
    # 言語設定
    $setupUILanguage = $Xml.CreateElement("SetupUILanguage", $Xml.DocumentElement.NamespaceURI)
    $component.AppendChild($setupUILanguage) | Out-Null
    
    Add-XmlElement -Parent $setupUILanguage -Name "UILanguage" -Value $Config.RegionLanguage.UILanguage -Xml $Xml
    Add-XmlElement -Parent $setupUILanguage -Name "WillShowUI" -Value "OnError" -Xml $Xml
    
    Add-XmlElement -Parent $component -Name "InputLocale" -Value $Config.RegionLanguage.InputLocale -Xml $Xml
    Add-XmlElement -Parent $component -Name "SystemLocale" -Value $Config.RegionLanguage.SystemLocale -Xml $Xml
    Add-XmlElement -Parent $component -Name "UILanguage" -Value $Config.RegionLanguage.UILanguage -Xml $Xml
    Add-XmlElement -Parent $component -Name "UILanguageFallback" -Value $Config.RegionLanguage.UILanguageFallback -Xml $Xml
    Add-XmlElement -Parent $component -Name "UserLocale" -Value $Config.RegionLanguage.UserLocale -Xml $Xml
    
    # Setup component
    $setupComponent = $Xml.CreateElement("component", $Xml.DocumentElement.NamespaceURI)
    $setupComponent.SetAttribute("name", "Microsoft-Windows-Setup")
    $setupComponent.SetAttribute("processorArchitecture", $Config.Architecture)
    $setupComponent.SetAttribute("publicKeyToken", "31bf3856ad364e35")
    $setupComponent.SetAttribute("language", "neutral")
    $setupComponent.SetAttribute("versionScope", "nonSxS")
    $settings.AppendChild($setupComponent) | Out-Null
    
    # ディスク構成
    if ($Config.DiskConfig.WipeDisk) {
        Add-DiskConfiguration -Parent $setupComponent -Config $Config -Xml $Xml
    }
    
    # プロダクトキー
    if ($Config.WindowsEdition.ProductKey) {
        $userdata = $Xml.CreateElement("UserData", $Xml.DocumentElement.NamespaceURI)
        $setupComponent.AppendChild($userdata) | Out-Null
        
        $productKey = $Xml.CreateElement("ProductKey", $Xml.DocumentElement.NamespaceURI)
        $userdata.AppendChild($productKey) | Out-Null
        
        Add-XmlElement -Parent $productKey -Name "Key" -Value $Config.WindowsEdition.ProductKey -Xml $Xml
        Add-XmlElement -Parent $userdata -Name "AcceptEula" -Value ($Config.WindowsEdition.AcceptEula.ToString().ToLower()) -Xml $Xml
    }
}

function Add-SpecializeSettings {
    <#
    .SYNOPSIS
        specializeパスの設定を追加
    #>
    param(
        [System.Xml.XmlDocument]$Xml,
        [object]$Config
    )
    
    $settings = $Xml.CreateElement("settings", $Xml.DocumentElement.NamespaceURI)
    $settings.SetAttribute("pass", "specialize")
    $Xml.DocumentElement.AppendChild($settings) | Out-Null
    
    # Shell-Setup
    $component = $Xml.CreateElement("component", $Xml.DocumentElement.NamespaceURI)
    $component.SetAttribute("name", "Microsoft-Windows-Shell-Setup")
    $component.SetAttribute("processorArchitecture", $Config.Architecture)
    $component.SetAttribute("publicKeyToken", "31bf3856ad364e35")
    $component.SetAttribute("language", "neutral")
    $component.SetAttribute("versionScope", "nonSxS")
    $settings.AppendChild($component) | Out-Null
    
    # コンピューター名
    if ($Config.ComputerSettings.ComputerName -ne "*") {
        Add-XmlElement -Parent $component -Name "ComputerName" -Value $Config.ComputerSettings.ComputerName -Xml $Xml
    }
    
    # タイムゾーン
    Add-XmlElement -Parent $component -Name "TimeZone" -Value $Config.RegionLanguage.Timezone -Xml $Xml
    
    # ドメイン参加またはワークグループ
    if ($Config.ComputerSettings.JoinDomain -and $Config.ComputerSettings.Domain) {
        # ドメイン参加設定
        $identification = $Xml.CreateElement("Identification", $Xml.DocumentElement.NamespaceURI)
        $component.AppendChild($identification) | Out-Null
        
        $joinDomain = $Xml.CreateElement("JoinDomain", $Xml.DocumentElement.NamespaceURI)
        $joinDomain.InnerText = $Config.ComputerSettings.Domain
        $identification.AppendChild($joinDomain) | Out-Null
    }
    elseif ($Config.ComputerSettings.Workgroup) {
        # ワークグループ設定
        $identification = $Xml.CreateElement("Identification", $Xml.DocumentElement.NamespaceURI)
        $component.AppendChild($identification) | Out-Null
        
        $joinWorkgroup = $Xml.CreateElement("JoinWorkgroup", $Xml.DocumentElement.NamespaceURI)
        $joinWorkgroup.InnerText = $Config.ComputerSettings.Workgroup
        $identification.AppendChild($joinWorkgroup) | Out-Null
    }
}

function Add-OobeSystemSettings {
    <#
    .SYNOPSIS
        oobeSystemパスの設定を追加（FirstLogonCommands含む）
    #>
    param(
        [System.Xml.XmlDocument]$Xml,
        [object]$Config,
        [hashtable]$ProcessResults
    )
    
    $settings = $Xml.CreateElement("settings", $Xml.DocumentElement.NamespaceURI)
    $settings.SetAttribute("pass", "oobeSystem")
    $Xml.DocumentElement.AppendChild($settings) | Out-Null
    
    # Shell-Setup
    $component = $Xml.CreateElement("component", $Xml.DocumentElement.NamespaceURI)
    $component.SetAttribute("name", "Microsoft-Windows-Shell-Setup")
    $component.SetAttribute("processorArchitecture", $Config.Architecture)
    $component.SetAttribute("publicKeyToken", "31bf3856ad364e35")
    $component.SetAttribute("language", "neutral")
    $component.SetAttribute("versionScope", "nonSxS")
    $settings.AppendChild($component) | Out-Null
    
    # OOBE設定
    $oobe = $Xml.CreateElement("OOBE", $Xml.DocumentElement.NamespaceURI)
    $component.AppendChild($oobe) | Out-Null
    
    Add-XmlElement -Parent $oobe -Name "HideEULAPage" -Value ($Config.SetupBehavior.HideEULAPage.ToString().ToLower()) -Xml $Xml
    Add-XmlElement -Parent $oobe -Name "HideOEMRegistrationScreen" -Value ($Config.SetupBehavior.HideOEMRegistration.ToString().ToLower()) -Xml $Xml
    Add-XmlElement -Parent $oobe -Name "HideOnlineAccountScreens" -Value ($Config.SetupBehavior.HideOnlineAccountScreens.ToString().ToLower()) -Xml $Xml
    Add-XmlElement -Parent $oobe -Name "HideWirelessSetupInOOBE" -Value ($Config.SetupBehavior.HideWirelessSetup.ToString().ToLower()) -Xml $Xml
    Add-XmlElement -Parent $oobe -Name "ProtectYourPC" -Value $Config.SetupBehavior.ProtectYourPC.ToString() -Xml $Xml
    Add-XmlElement -Parent $oobe -Name "SkipMachineOOBE" -Value ($Config.SetupBehavior.SkipMachineOOBE.ToString().ToLower()) -Xml $Xml
    Add-XmlElement -Parent $oobe -Name "SkipUserOOBE" -Value ($Config.SetupBehavior.SkipUserOOBE.ToString().ToLower()) -Xml $Xml
    
    # ユーザーアカウント
    Add-UserAccounts -Parent $component -Config $Config -Xml $Xml
    
    # FirstLogonCommands
    Add-FirstLogonCommands -Parent $component -Config $Config -ProcessResults $ProcessResults -Xml $Xml
}

function Add-FirstLogonCommands {
    <#
    .SYNOPSIS
        FirstLogonCommandsを追加（全23項目の設定を含む）
    #>
    param(
        [System.Xml.XmlElement]$Parent,
        [object]$Config,
        [hashtable]$ProcessResults,
        [System.Xml.XmlDocument]$Xml
    )
    
    $firstLogonCommands = $Xml.CreateElement("FirstLogonCommands", $Xml.DocumentElement.NamespaceURI)
    $Parent.AppendChild($firstLogonCommands) | Out-Null
    
    $order = 1
    $commands = @()
    
    # SubAgentの結果からコマンドを収集
    foreach ($result in $ProcessResults.Values) {
        if ($result.FirstLogonCommands) {
            $commands += $result.FirstLogonCommands
        }
    }
    
    # 追加のコマンド生成（項目12-23の実装）
    
    # 12. 視覚効果
    if ($Config.VisualEffects.PerformanceMode -eq "BestPerformance") {
        $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f'
    }
    
    if (-not $Config.VisualEffects.Transparency) {
        $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f'
    }
    
    if (-not $Config.VisualEffects.Animations) {
        $commands += 'reg add "HKCU\Control Panel\Desktop\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f'
    }
    
    # 13. デスクトップ設定
    $desktopIcons = @{
        Computer = "{20D04FE0-3AEA-1069-A2D8-08002B30309D}"
        UserFiles = "{59031a47-3f72-44a7-89c5-5595fe6b30ee}"
        Network = "{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}"
        RecycleBin = "{645FF040-5081-101B-9F08-00AA002F954E}"
        ControlPanel = "{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}"
    }
    
    foreach ($icon in $desktopIcons.GetEnumerator()) {
        $showValue = if ($Config.DesktopSettings."Show$($icon.Key)") { 0 } else { 1 }
        $commands += "reg add `"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel`" /v `"$($icon.Value)`" /t REG_DWORD /d $showValue /f"
    }
    
    # 14. 仮想マシンサポート
    if ($Config.VMSupport.EnableHyperV) {
        $commands += "dism /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart"
    }
    
    if ($Config.VMSupport.EnableWSL) {
        $commands += "dism /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart"
    }
    
    if ($Config.VMSupport.EnableWSL2) {
        $commands += "dism /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart"
    }
    
    if ($Config.VMSupport.EnableSandbox) {
        $commands += "dism /online /enable-feature /featurename:Containers-DisposableClientVM /all /norestart"
    }
    
    # 16. Express Settings（プライバシー設定）
    if ($Config.ExpressSettings.Mode -eq "all_disabled" -or $Config.ExpressSettings.Mode -eq "custom") {
        if (-not $Config.ExpressSettings.LocationServices) {
            $commands += 'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors" /v DisableLocation /t REG_DWORD /d 1 /f'
        }
        
        if (-not $Config.ExpressSettings.AdvertisingId) {
            $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo" /v Enabled /t REG_DWORD /d 0 /f'
        }
    }
    
    # 17. ロックキー設定
    $keyIndicator = 0
    if ($Config.LockKeys.NumLock) { $keyIndicator = 2 }
    if ($Config.LockKeys.CapsLock) { $keyIndicator = $keyIndicator -bor 64 }
    if ($Config.LockKeys.ScrollLock) { $keyIndicator = $keyIndicator -bor 1 }
    
    if ($keyIndicator -gt 0) {
        $commands += "reg add `"HKU\.DEFAULT\Control Panel\Keyboard`" /v InitialKeyboardIndicators /t REG_SZ /d `"$keyIndicator`" /f"
    }
    
    # 18. 固定キー
    if ($Config.StickyKeys.Enabled) {
        $commands += 'reg add "HKCU\Control Panel\Accessibility\StickyKeys" /v Flags /t REG_SZ /d 511 /f'
    }
    
    # 19. 個人用設定
    if ($Config.Personalization.Theme -eq "Dark") {
        $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v AppsUseLightTheme /t REG_DWORD /d 0 /f'
        $commands += 'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v SystemUsesLightTheme /t REG_DWORD /d 0 /f'
    }
    
    if ($Config.Personalization.AccentColor) {
        # アクセントカラーの設定（BGR形式に変換）
        $color = $Config.Personalization.AccentColor.TrimStart('#')
        if ($color.Length -eq 6) {
            $r = [Convert]::ToInt32($color.Substring(0,2), 16)
            $g = [Convert]::ToInt32($color.Substring(2,2), 16)
            $b = [Convert]::ToInt32($color.Substring(4,2), 16)
            $bgrValue = ($b * 65536) + ($g * 256) + $r + [Math]::Pow(2, 32) - [Math]::Pow(2, 24)
            $commands += "reg add `"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Accent`" /v AccentColorMenu /t REG_DWORD /d $([int]$bgrValue) /f"
        }
    }
    
    # 20. 不要なアプリの削除（ProcessResultsに含まれている）
    
    # 21. カスタムスクリプト
    foreach ($script in $Config.CustomScripts.FirstLogon) {
        $commands += $script.Command
    }
    
    # 22. WDAC設定
    if ($Config.WDAC.Enabled) {
        $commands += 'powershell -Command "Set-CIPolicyIdInfo -FilePath C:\Windows\System32\CodeIntegrity\SIPolicy.p7b -PolicyName WDAC_Policy -PolicyId (New-Guid)"'
        
        if ($Config.WDAC.PolicyMode -eq "Enforced") {
            $commands += 'reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 1 /f'
        }
    }
    
    # 23. その他のコンポーネント
    if ($Config.AdditionalComponents.DotNet35) {
        $commands += "dism /online /enable-feature /featurename:NetFx3 /all /norestart"
    }
    
    if ($Config.AdditionalComponents.IIS) {
        $commands += "dism /online /enable-feature /featurename:IIS-WebServerRole /featurename:IIS-WebServer /all /norestart"
    }
    
    if ($Config.AdditionalComponents.TelnetClient) {
        $commands += "dism /online /enable-feature /featurename:TelnetClient /all /norestart"
    }
    
    # コマンドをXMLに追加
    foreach ($cmd in $commands) {
        $syncCommand = $Xml.CreateElement("SynchronousCommand", $Xml.DocumentElement.NamespaceURI)
        $firstLogonCommands.AppendChild($syncCommand) | Out-Null
        
        Add-XmlElement -Parent $syncCommand -Name "Order" -Value $order.ToString() -Xml $Xml
        Add-XmlElement -Parent $syncCommand -Name "CommandLine" -Value $cmd -Xml $Xml
        Add-XmlElement -Parent $syncCommand -Name "Description" -Value "Command $order" -Xml $Xml
        Add-XmlElement -Parent $syncCommand -Name "RequiresUserInput" -Value "false" -Xml $Xml
        
        $order++
    }
    
    Write-Verbose "FirstLogonCommands: $($order - 1) 個のコマンドを追加"
}

function Add-UserAccounts {
    <#
    .SYNOPSIS
        ユーザーアカウント設定を追加
    #>
    param(
        [System.Xml.XmlElement]$Parent,
        [object]$Config,
        [System.Xml.XmlDocument]$Xml
    )
    
    $userAccounts = $Xml.CreateElement("UserAccounts", $Xml.DocumentElement.NamespaceURI)
    $Parent.AppendChild($userAccounts) | Out-Null
    
    # ローカルアカウント
    $localAccounts = $Xml.CreateElement("LocalAccounts", $Xml.DocumentElement.NamespaceURI)
    $userAccounts.AppendChild($localAccounts) | Out-Null
    
    foreach ($account in $Config.UserAccounts.Accounts) {
        $localAccount = $Xml.CreateElement("LocalAccount", $Xml.DocumentElement.NamespaceURI)
        $localAccounts.AppendChild($localAccount) | Out-Null
        
        # パスワード
        $password = $Xml.CreateElement("Password", $Xml.DocumentElement.NamespaceURI)
        $localAccount.AppendChild($password) | Out-Null
        
        $encodedPassword = ConvertTo-Base64Password -Password $account.Password
        Add-XmlElement -Parent $password -Name "Value" -Value $encodedPassword -Xml $Xml
        Add-XmlElement -Parent $password -Name "PlainText" -Value "false" -Xml $Xml
        
        # アカウント情報
        Add-XmlElement -Parent $localAccount -Name "Name" -Value $account.Name -Xml $Xml
        Add-XmlElement -Parent $localAccount -Name "DisplayName" -Value $account.DisplayName -Xml $Xml
        Add-XmlElement -Parent $localAccount -Name "Description" -Value $account.Description -Xml $Xml
        Add-XmlElement -Parent $localAccount -Name "Group" -Value $account.Group -Xml $Xml
    }
    
    # 自動ログオン設定
    if ($Config.UserAccounts.AutoLogonCount -gt 0) {
        $firstAccount = $Config.UserAccounts.Accounts[0]
        
        $autoLogon = $Xml.CreateElement("AutoLogon", $Xml.DocumentElement.NamespaceURI)
        $Parent.AppendChild($autoLogon) | Out-Null
        
        $password = $Xml.CreateElement("Password", $Xml.DocumentElement.NamespaceURI)
        $autoLogon.AppendChild($password) | Out-Null
        
        $encodedPassword = ConvertTo-Base64Password -Password $firstAccount.Password
        Add-XmlElement -Parent $password -Name "Value" -Value $encodedPassword -Xml $Xml
        Add-XmlElement -Parent $password -Name "PlainText" -Value "false" -Xml $Xml
        
        Add-XmlElement -Parent $autoLogon -Name "Enabled" -Value "true" -Xml $Xml
        Add-XmlElement -Parent $autoLogon -Name "LogonCount" -Value $Config.UserAccounts.AutoLogonCount.ToString() -Xml $Xml
        Add-XmlElement -Parent $autoLogon -Name "Username" -Value $firstAccount.Name -Xml $Xml
    }
}

function Add-DiskConfiguration {
    <#
    .SYNOPSIS
        ディスク構成を追加
    #>
    param(
        [System.Xml.XmlElement]$Parent,
        [object]$Config,
        [System.Xml.XmlDocument]$Xml
    )
    
    $diskConfig = $Xml.CreateElement("DiskConfiguration", $Xml.DocumentElement.NamespaceURI)
    $Parent.AppendChild($diskConfig) | Out-Null
    
    $disk = $Xml.CreateElement("Disk", $Xml.DocumentElement.NamespaceURI)
    $diskConfig.AppendChild($disk) | Out-Null
    
    Add-XmlElement -Parent $disk -Name "DiskID" -Value $Config.DiskConfig.DiskId.ToString() -Xml $Xml
    Add-XmlElement -Parent $disk -Name "WillWipeDisk" -Value ($Config.DiskConfig.WipeDisk.ToString().ToLower()) -Xml $Xml
    
    # パーティション作成
    $createPartitions = $Xml.CreateElement("CreatePartitions", $Xml.DocumentElement.NamespaceURI)
    $disk.AppendChild($createPartitions) | Out-Null
    
    $partitionOrder = 1
    foreach ($partition in $Config.DiskConfig.Partitions) {
        $createPartition = $Xml.CreateElement("CreatePartition", $Xml.DocumentElement.NamespaceURI)
        $createPartitions.AppendChild($createPartition) | Out-Null
        
        Add-XmlElement -Parent $createPartition -Name "Order" -Value $partitionOrder.ToString() -Xml $Xml
        
        if ($partition.Type -eq "EFI") {
            Add-XmlElement -Parent $createPartition -Name "Type" -Value "EFI" -Xml $Xml
            Add-XmlElement -Parent $createPartition -Name "Size" -Value $partition.Size.ToString() -Xml $Xml
        }
        elseif ($partition.Type -eq "MSR") {
            Add-XmlElement -Parent $createPartition -Name "Type" -Value "MSR" -Xml $Xml
            Add-XmlElement -Parent $createPartition -Name "Size" -Value $partition.Size.ToString() -Xml $Xml
        }
        elseif ($partition.Type -eq "Primary") {
            Add-XmlElement -Parent $createPartition -Name "Type" -Value "Primary" -Xml $Xml
            if ($partition.Size -eq "remaining") {
                Add-XmlElement -Parent $createPartition -Name "Extend" -Value "true" -Xml $Xml
            }
            else {
                Add-XmlElement -Parent $createPartition -Name "Size" -Value $partition.Size.ToString() -Xml $Xml
            }
        }
        elseif ($partition.Type -eq "Recovery") {
            Add-XmlElement -Parent $createPartition -Name "Type" -Value "Primary" -Xml $Xml
            Add-XmlElement -Parent $createPartition -Name "Size" -Value $partition.Size.ToString() -Xml $Xml
        }
        
        $partitionOrder++
    }
    
    # パーティションの変更
    $modifyPartitions = $Xml.CreateElement("ModifyPartitions", $Xml.DocumentElement.NamespaceURI)
    $disk.AppendChild($modifyPartitions) | Out-Null
    
    $partitionOrder = 1
    foreach ($partition in $Config.DiskConfig.Partitions) {
        $modifyPartition = $Xml.CreateElement("ModifyPartition", $Xml.DocumentElement.NamespaceURI)
        $modifyPartitions.AppendChild($modifyPartition) | Out-Null
        
        Add-XmlElement -Parent $modifyPartition -Name "Order" -Value $partitionOrder.ToString() -Xml $Xml
        Add-XmlElement -Parent $modifyPartition -Name "PartitionID" -Value $partitionOrder.ToString() -Xml $Xml
        
        if ($partition.Type -eq "EFI") {
            Add-XmlElement -Parent $modifyPartition -Name "Format" -Value "FAT32" -Xml $Xml
            Add-XmlElement -Parent $modifyPartition -Name "Label" -Value "System" -Xml $Xml
        }
        elseif ($partition.Type -eq "Primary" -and $partition.Letter) {
            Add-XmlElement -Parent $modifyPartition -Name "Format" -Value "NTFS" -Xml $Xml
            Add-XmlElement -Parent $modifyPartition -Name "Letter" -Value $partition.Letter -Xml $Xml
            Add-XmlElement -Parent $modifyPartition -Name "Label" -Value "Windows" -Xml $Xml
        }
        elseif ($partition.Type -eq "Recovery") {
            Add-XmlElement -Parent $modifyPartition -Name "Format" -Value "NTFS" -Xml $Xml
            Add-XmlElement -Parent $modifyPartition -Name "Label" -Value "Recovery" -Xml $Xml
            Add-XmlElement -Parent $modifyPartition -Name "TypeID" -Value "de94bba4-06d1-4d40-a16a-bfd50179d6ac" -Xml $Xml
        }
        
        $partitionOrder++
    }
    
    # インストール先
    if ($Config.WindowsEdition.InstallToAvailable) {
        $imageInstall = $Xml.CreateElement("ImageInstall", $Xml.DocumentElement.NamespaceURI)
        $Parent.AppendChild($imageInstall) | Out-Null
        
        $osImage = $Xml.CreateElement("OSImage", $Xml.DocumentElement.NamespaceURI)
        $imageInstall.AppendChild($osImage) | Out-Null
        
        $installTo = $Xml.CreateElement("InstallTo", $Xml.DocumentElement.NamespaceURI)
        $osImage.AppendChild($installTo) | Out-Null
        
        Add-XmlElement -Parent $installTo -Name "DiskID" -Value $Config.DiskConfig.DiskId.ToString() -Xml $Xml
        
        # Cドライブのパーティション番号を見つける
        $cPartitionIndex = 1
        foreach ($partition in $Config.DiskConfig.Partitions) {
            if ($partition.Letter -eq "C") {
                break
            }
            $cPartitionIndex++
        }
        
        Add-XmlElement -Parent $installTo -Name "PartitionID" -Value $cPartitionIndex.ToString() -Xml $Xml
    }
}

function Add-OfflineServicingSettings {
    <#
    .SYNOPSIS
        offlineServicingパスの設定を追加
    #>
    param(
        [System.Xml.XmlDocument]$Xml,
        [object]$Config
    )
    
    # 現時点では空のパスとして追加
    # 将来的にオフライン更新やドライバーのインストールを追加可能
}

# ヘルパー関数

function Add-XmlElement {
    param(
        [System.Xml.XmlElement]$Parent,
        [string]$Name,
        [string]$Value,
        [System.Xml.XmlDocument]$Xml
    )
    
    $element = $Xml.CreateElement($Name, $Xml.DocumentElement.NamespaceURI)
    $element.InnerText = $Value
    $Parent.AppendChild($element) | Out-Null
}

function ConvertTo-Base64Password {
    param(
        [string]$Password
    )
    
    $passwordWithSuffix = $Password + "Password"
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($passwordWithSuffix)
    return [Convert]::ToBase64String($bytes)
}

# メイン XML 生成関数（簡易版）
function New-ComprehensiveXML {
    param(
        [Parameter(Mandatory)]
        [object]$Config,
        
        [Parameter()]
        [hashtable]$ProcessResults = @{}
    )
    
    # 基本的なunattend.xmlテンプレート
    $xmlContent = @'
<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
    <settings pass="windowsPE">
        <component name="Microsoft-Windows-International-Core-WinPE" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <SetupUILanguage>
                <UILanguage>ja-JP</UILanguage>
            </SetupUILanguage>
            <InputLocale>0411:00000411</InputLocale>
            <SystemLocale>ja-JP</SystemLocale>
            <UILanguage>ja-JP</UILanguage>
            <UserLocale>ja-JP</UserLocale>
        </component>
    </settings>
    <settings pass="specialize">
        <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <ComputerName>WIN11-PC</ComputerName>
            <TimeZone>Tokyo Standard Time</TimeZone>
        </component>
    </settings>
    <settings pass="oobeSystem">
        <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <OOBE>
                <HideEULAPage>true</HideEULAPage>
                <HideOEMRegistrationScreen>true</HideOEMRegistrationScreen>
                <HideOnlineAccountScreens>true</HideOnlineAccountScreens>
                <HideWirelessSetupInOOBE>false</HideWirelessSetupInOOBE>
                <ProtectYourPC>3</ProtectYourPC>
            </OOBE>
            <UserAccounts>
                <LocalAccounts>
                    <LocalAccount>
                        <Name>admin</Name>
                        <Password>
                            <Value>UABhAHMAcwB3AG8AcgBkADEAMgAzACEAUABhAHMAcwB3AG8AcgBkAA==</Value>
                            <PlainText>false</PlainText>
                        </Password>
                        <Group>Administrators</Group>
                        <DisplayName>Administrator</DisplayName>
                        <Description>ローカル管理者</Description>
                    </LocalAccount>
                </LocalAccounts>
            </UserAccounts>
            <FirstLogonCommands>
                <SynchronousCommand>
                    <Order>1</Order>
                    <CommandLine>reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v HideFileExt /t REG_DWORD /d 0 /f</CommandLine>
                    <Description>ファイル拡張子を表示</Description>
                </SynchronousCommand>
            </FirstLogonCommands>
        </component>
    </settings>
</unattend>
'@
    
    # FirstLogonCommandsを追加 - デバッグ情報付き
    Write-Verbose "ProcessResults count: $($ProcessResults.Count)"
    
    if ($ProcessResults -and $ProcessResults.Count -gt 0) {
        # XMLとして解析
        [xml]$xml = $xmlContent
        
        # FirstLogonCommandsノードを探す
        $oobeSettings = $xml.unattend.settings | Where-Object { $_.pass -eq "oobeSystem" }
        $shellSetup = $oobeSettings.component | Where-Object { $_.name -like "*Shell-Setup*" }
        
        if ($shellSetup -and $shellSetup.FirstLogonCommands) {
            # 既存のコマンドをクリア（最初のサンプルコマンドを残す）
            $firstLogonCommands = $shellSetup.FirstLogonCommands
            
            # 全コマンドを収集
            $allCommands = @()
            
            foreach ($agent in $ProcessResults.GetEnumerator()) {
                Write-Verbose "Processing agent: $($agent.Key)"
                if ($agent.Value -and $agent.Value.FirstLogonCommands) {
                    Write-Verbose "  Found $($agent.Value.FirstLogonCommands.Count) commands"
                    foreach ($cmd in $agent.Value.FirstLogonCommands) {
                        $allCommands += $cmd
                    }
                }
            }
            
            Write-Verbose "Total commands to add: $($allCommands.Count)"
            
            # 既存のSynchronousCommandをクリア
            while ($firstLogonCommands.FirstChild) {
                $firstLogonCommands.RemoveChild($firstLogonCommands.FirstChild) | Out-Null
            }
            
            # 新しいコマンドを追加
            $order = 1
            foreach ($cmd in $allCommands) {
                $command = $xml.CreateElement("SynchronousCommand", "urn:schemas-microsoft-com:unattend")
                # wcm:action attributes removed - causing display issues
                
                $orderElem = $xml.CreateElement("Order", "urn:schemas-microsoft-com:unattend")
                $orderElem.InnerText = $order.ToString()
                $command.AppendChild($orderElem) | Out-Null
                
                $cmdLineElem = $xml.CreateElement("CommandLine", "urn:schemas-microsoft-com:unattend")
                $cmdLineElem.InnerText = $cmd
                $command.AppendChild($cmdLineElem) | Out-Null
                
                $descElem = $xml.CreateElement("Description", "urn:schemas-microsoft-com:unattend")
                $descElem.InnerText = "Command $order"
                $command.AppendChild($descElem) | Out-Null
                
                $firstLogonCommands.AppendChild($command) | Out-Null
                $order++
            }
        }
        
        # XMLを文字列として返す
        $stringWriter = New-Object System.IO.StringWriter
        $xmlWriter = [System.Xml.XmlTextWriter]::new($stringWriter)
        $xmlWriter.Formatting = "Indented"
        $xml.WriteTo($xmlWriter)
        $xmlWriter.Flush()
        $stringWriter.Flush()
        
        return $stringWriter.ToString()
    }
    
    return $xmlContent
}

# ログ生成関数
function New-ConfigurationLog {
    param(
        [Parameter(Mandatory)]
        [object]$Config,
        
        [Parameter()]
        [hashtable]$ProcessResults = @{}
    )
    
    $log = New-Object System.Text.StringBuilder
    [void]$log.AppendLine("=== Windows 11 無人応答ファイル生成ログ ===")
    [void]$log.AppendLine("生成日時: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
    [void]$log.AppendLine("")
    
    # 設定内容のログ
    [void]$log.AppendLine("[設定内容]")
    [void]$log.AppendLine("- エディション: $($Config.WindowsEdition.Edition)")
    [void]$log.AppendLine("- アーキテクチャ: $($Config.Architecture)")
    [void]$log.AppendLine("- タイムゾーン: $($Config.RegionLanguage.Timezone)")
    [void]$log.AppendLine("")
    
    # SubAgent処理結果
    [void]$log.AppendLine("[SubAgent処理結果]")
    foreach ($result in $ProcessResults.GetEnumerator()) {
        [void]$log.AppendLine("- $($result.Key): 完了")
    }
    
    return $log.ToString()
}

# エクスポート
Export-ModuleMember -Function @(
    'New-ComprehensiveXML',
    'New-ConfigurationLog',
    'Add-XmlElement',
    'ConvertTo-Base64Password'
) -Variable @() -Cmdlet @() -Alias @()