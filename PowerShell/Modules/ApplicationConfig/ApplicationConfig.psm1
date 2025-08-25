#Requires -Version 5.0

<#
.SYNOPSIS
    Windows 11 UnattendXML アプリケーション設定モジュール

.DESCRIPTION
    Sysprep応答ファイルでのアプリケーション設定を管理するPowerShellモジュール
    - 既定のアプリケーション設定（ブラウザ、メール、PDF）
    - Office初回起動設定
    - タスクバー設定
    - スタートメニューカスタマイズ

.VERSION
    1.0.0

.AUTHOR
    Windows 11 Sysprep Automation Team

.COPYRIGHT
    Copyright (c) 2025. All rights reserved.
#>

# .NET Framework アセンブリの読み込み
Add-Type -AssemblyName System.Xml
Add-Type -AssemblyName System.Management.Automation

# アプリケーション種別列挙型
enum ApplicationType {
    Browser = 0
    Email = 1
    PDF = 2
    Media = 3
    TextEditor = 4
    Archive = 5
}

enum OfficeVersion {
    Office365 = 0
    Office2021 = 1
    Office2019 = 2
    Office2016 = 3
}

# アプリケーション設定クラス
class ApplicationSetting {
    [string]$Name
    [ApplicationType]$Type
    [string]$ExecutablePath
    [string]$ProgId
    [hashtable]$Extensions
    [hashtable]$RegistrySettings
    [bool]$IsDefault
    
    # コンストラクタ
    ApplicationSetting([string]$name, [ApplicationType]$type) {
        $this.Name = $name
        $this.Type = $type
        $this.ExecutablePath = ""
        $this.ProgId = ""
        $this.Extensions = @{}
        $this.RegistrySettings = @{}
        $this.IsDefault = $false
    }
    
    # 詳細コンストラクタ
    ApplicationSetting([string]$name, [ApplicationType]$type, [string]$progId, [string]$executablePath) {
        $this.Name = $name
        $this.Type = $type
        $this.ExecutablePath = $executablePath
        $this.ProgId = $progId
        $this.Extensions = @{}
        $this.RegistrySettings = @{}
        $this.IsDefault = $false
    }
}

# Office設定クラス
class OfficeConfiguration {
    [OfficeVersion]$Version
    [bool]$SkipFirstRun
    [bool]$AcceptEula
    [bool]$DisableTelemetry
    [bool]$DisableUpdates
    [bool]$EnableMacros
    [hashtable]$CustomSettings
    [string[]]$DisabledFeatures
    [string[]]$EnabledFeatures
    
    # コンストラクタ
    OfficeConfiguration() {
        $this.Version = [OfficeVersion]::Office365
        $this.SkipFirstRun = $true
        $this.AcceptEula = $true
        $this.DisableTelemetry = $true
        $this.DisableUpdates = $false
        $this.EnableMacros = $false
        $this.CustomSettings = @{}
        $this.DisabledFeatures = @()
        $this.EnabledFeatures = @()
        
        # デフォルト無効化機能
        $this.DisabledFeatures = @(
            "Microsoft Office Telemetry Agent",
            "Microsoft Office ClickToRun",
            "Office Software Protection Platform",
            "Microsoft Office Web Apps Service"
        )
    }
}

# アプリケーション設定管理クラス
class ApplicationConfig {
    [ApplicationSetting[]]$Applications
    [OfficeConfiguration]$OfficeConfig
    [string]$DefaultBrowser
    [string]$DefaultEmailClient
    [string]$DefaultPDFReader
    [hashtable]$TaskbarSettings
    [hashtable]$StartMenuSettings
    [hashtable]$FileAssociations
    [hashtable]$UrlAssociations
    
    # コンストラクタ
    ApplicationConfig() {
        $this.Applications = @()
        $this.OfficeConfig = [OfficeConfiguration]::new()
        $this.DefaultBrowser = "MSEdgeHTM"
        $this.DefaultEmailClient = "OUTLOOK.EXE"
        $this.DefaultPDFReader = "AcroExch.Document"
        $this.TaskbarSettings = @{}
        $this.StartMenuSettings = @{}
        $this.FileAssociations = @{}
        $this.UrlAssociations = @{}
        
        # デフォルト設定初期化
        $this.InitializeDefaultApplications()
        $this.InitializeDefaultSettings()
    }
    
    # デフォルトアプリケーション初期化
    [void] InitializeDefaultApplications() {
        # Microsoft Edge（ブラウザ）
        $edge = [ApplicationSetting]::new("Microsoft Edge", [ApplicationType]::Browser, "MSEdgeHTM", "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe")
        $edge.Extensions = @{
            ".htm" = "MSEdgeHTM"
            ".html" = "MSEdgeHTM"
            ".pdf" = "MSEdgeHTM"  # デフォルトでPDFも処理
        }
        $edge.IsDefault = $true
        $this.Applications += $edge
        
        # Google Chrome（ブラウザ）
        $chrome = [ApplicationSetting]::new("Google Chrome", [ApplicationType]::Browser, "ChromeHTML", "%ProgramFiles%\Google\Chrome\Application\chrome.exe")
        $chrome.Extensions = @{
            ".htm" = "ChromeHTML"
            ".html" = "ChromeHTML"
        }
        $this.Applications += $chrome
        
        # Outlook（メール）
        $outlook = [ApplicationSetting]::new("Microsoft Outlook", [ApplicationType]::Email, "Outlook.File.msg.15", "%ProgramFiles%\Microsoft Office\root\Office16\OUTLOOK.EXE")
        $outlook.Extensions = @{
            ".msg" = "Outlook.File.msg.15"
            ".eml" = "Outlook.File.eml.15"
        }
        $outlook.IsDefault = $true
        $this.Applications += $outlook
        
        # Adobe Acrobat Reader（PDF）
        $adobeReader = [ApplicationSetting]::new("Adobe Acrobat Reader DC", [ApplicationType]::PDF, "AcroExch.Document", "%ProgramFiles%\Adobe\Acrobat DC\Acrobat\Acrobat.exe")
        $adobeReader.Extensions = @{
            ".pdf" = "AcroExch.Document"
        }
        $adobeReader.IsDefault = $true
        $this.Applications += $adobeReader
        
        # Windows Media Player（メディア）
        $mediaPlayer = [ApplicationSetting]::new("Windows Media Player", [ApplicationType]::Media, "WMP11.AssocFile.MP3", "%ProgramFiles%\Windows Media Player\wmplayer.exe")
        $mediaPlayer.Extensions = @{
            ".mp3" = "WMP11.AssocFile.MP3"
            ".mp4" = "WMP11.AssocFile.MP4"
            ".avi" = "WMP11.AssocFile.AVI"
        }
        $this.Applications += $mediaPlayer
        
        # Notepad++（テキストエディタ）
        $notepadPlusPlus = [ApplicationSetting]::new("Notepad++", [ApplicationType]::TextEditor, "Notepad++_file", "%ProgramFiles%\Notepad++\notepad++.exe")
        $notepadPlusPlus.Extensions = @{
            ".txt" = "Notepad++_file"
            ".log" = "Notepad++_file"
            ".ini" = "Notepad++_file"
            ".cfg" = "Notepad++_file"
        }
        $this.Applications += $notepadPlusPlus
    }
    
    # デフォルト設定初期化
    [void] InitializeDefaultSettings() {
        # タスクバー設定
        $this.TaskbarSettings = @{
            # 検索ボックスを非表示
            "ShowSearchBox" = 0
            # Cortanaボタンを非表示
            "ShowCortanaButton" = 0
            # タスクビューボタンを非表示
            "ShowTaskViewButton" = 0
            # ニュースと関心事項を無効
            "TaskbarDa" = 0
            # 小さいタスクバーボタン
            "TaskbarSi" = 1
            # タスクバーを左下に固定
            "TaskbarAlignment" = 0
        }
        
        # スタートメニュー設定
        $this.StartMenuSettings = @{
            # Web検索を無効
            "BingSearchEnabled" = 0
            # おすすめを無効
            "Start_IrisRecommendations" = 0
            # 最近使用したファイルを表示しない
            "Start_TrackDocs" = 0
            # ジャンプリストを無効
            "Start_JumpListItems" = 0
        }
        
        # ファイル関連付け
        $this.FileAssociations = @{
            ".txt" = "Notepad++_file"
            ".log" = "Notepad++_file"
            ".pdf" = "AcroExch.Document"
            ".htm" = "MSEdgeHTM"
            ".html" = "MSEdgeHTM"
            ".msg" = "Outlook.File.msg.15"
            ".eml" = "Outlook.File.eml.15"
        }
        
        # URL関連付け
        $this.UrlAssociations = @{
            "http" = "MSEdgeHTM"
            "https" = "MSEdgeHTM"
            "ftp" = "MSEdgeHTM"
            "mailto" = "Outlook.Url.mailto.15"
        }
    }
    
    # アプリケーション追加
    [void] AddApplication([ApplicationSetting]$application) {
        $this.Applications += $application
    }
    
    # アプリケーション検索
    [ApplicationSetting] GetApplication([string]$name) {
        return $this.Applications | Where-Object { $_.Name -eq $name }
    }
    
    # デフォルトアプリケーション検索
    [ApplicationSetting[]] GetDefaultApplications() {
        return $this.Applications | Where-Object { $_.IsDefault }
    }
}

# アプリケーション設定XML生成クラス
class UnattendApplicationXMLGenerator {
    [System.Xml.XmlDocument]$XmlDocument
    [ApplicationConfig]$Config
    [System.Xml.XmlNamespaceManager]$NamespaceManager
    
    # コンストラクタ
    UnattendApplicationXMLGenerator([System.Xml.XmlDocument]$xmlDoc, [ApplicationConfig]$config) {
        $this.XmlDocument = $xmlDoc
        $this.Config = $config
        $this.NamespaceManager = New-Object System.Xml.XmlNamespaceManager($xmlDoc.NameTable)
        $this.NamespaceManager.AddNamespace("un", "urn:schemas-microsoft-com:unattend")
    }
    
    # アプリケーション設定XML生成
    [System.Xml.XmlElement] GenerateApplicationConfigXML() {
        Write-Verbose "アプリケーション設定XML生成開始"
        
        $unattendRoot = $this.XmlDocument.DocumentElement
        
        # oobeSystem パスでの設定
        $this.AddOobeSystemSettings($unattendRoot)
        
        # specialize パスでの設定
        $this.AddSpecializeSettings($unattendRoot)
        
        Write-Verbose "アプリケーション設定XML生成完了"
        return $unattendRoot
    }
    
    # OOBE System パス設定追加
    [void] AddOobeSystemSettings([System.Xml.XmlElement]$unattendRoot) {
        Write-Verbose "OOBE System パス設定追加開始"
        
        $settingsElement = $this.GetOrCreateSettingsElement($unattendRoot, "oobeSystem")
        
        # デフォルトアプリケーション設定
        $this.AddDefaultApplicationSettings($settingsElement)
        
        Write-Verbose "OOBE System パス設定追加完了"
    }
    
    # Specialize パス設定追加
    [void] AddSpecializeSettings([System.Xml.XmlElement]$unattendRoot) {
        Write-Verbose "Specialize パス設定追加開始"
        
        $settingsElement = $this.GetOrCreateSettingsElement($unattendRoot, "specialize")
        
        # レジストリ設定（タスクバー、スタートメニュー等）
        $this.AddRegistrySettings($settingsElement)
        
        # Office設定
        $this.AddOfficeSettings($settingsElement)
        
        # ファイル関連付け設定
        $this.AddFileAssociationSettings($settingsElement)
        
        Write-Verbose "Specialize パス設定追加完了"
    }
    
    # デフォルトアプリケーション設定追加
    [void] AddDefaultApplicationSettings([System.Xml.XmlElement]$settingsElement) {
        Write-Verbose "デフォルトアプリケーション設定追加開始"
        
        $shellSetupComponent = $this.GetOrCreateComponent($settingsElement, "Microsoft-Windows-Shell-Setup")
        
        # DefaultApplications要素
        $defaultApplicationsElement = $this.XmlDocument.CreateElement("DefaultApplications", $shellSetupComponent.NamespaceURI)
        $shellSetupComponent.AppendChild($defaultApplicationsElement) | Out-Null
        
        # ブラウザ設定
        if (![string]::IsNullOrWhiteSpace($this.Config.DefaultBrowser)) {
            $associationElement = $this.XmlDocument.CreateElement("Association", $defaultApplicationsElement.NamespaceURI)
            $associationElement.SetAttribute("Identifier", "http")
            $associationElement.SetAttribute("ProgId", $this.Config.DefaultBrowser)
            $associationElement.SetAttribute("ApplicationName", "Web Browser")
            $defaultApplicationsElement.AppendChild($associationElement) | Out-Null
            
            $associationElement = $this.XmlDocument.CreateElement("Association", $defaultApplicationsElement.NamespaceURI)
            $associationElement.SetAttribute("Identifier", "https")
            $associationElement.SetAttribute("ProgId", $this.Config.DefaultBrowser)
            $associationElement.SetAttribute("ApplicationName", "Web Browser")
            $defaultApplicationsElement.AppendChild($associationElement) | Out-Null
        }
        
        # メールクライアント設定
        if (![string]::IsNullOrWhiteSpace($this.Config.DefaultEmailClient)) {
            $associationElement = $this.XmlDocument.CreateElement("Association", $defaultApplicationsElement.NamespaceURI)
            $associationElement.SetAttribute("Identifier", "mailto")
            $associationElement.SetAttribute("ProgId", $this.Config.DefaultEmailClient)
            $associationElement.SetAttribute("ApplicationName", "Mail Client")
            $defaultApplicationsElement.AppendChild($associationElement) | Out-Null
        }
        
        # PDF Reader設定
        if (![string]::IsNullOrWhiteSpace($this.Config.DefaultPDFReader)) {
            $associationElement = $this.XmlDocument.CreateElement("Association", $defaultApplicationsElement.NamespaceURI)
            $associationElement.SetAttribute("Identifier", ".pdf")
            $associationElement.SetAttribute("ProgId", $this.Config.DefaultPDFReader)
            $associationElement.SetAttribute("ApplicationName", "PDF Reader")
            $defaultApplicationsElement.AppendChild($associationElement) | Out-Null
        }
        
        Write-Verbose "デフォルトアプリケーション設定追加完了"
    }
    
    # レジストリ設定追加
    [void] AddRegistrySettings([System.Xml.XmlElement]$settingsElement) {
        Write-Verbose "レジストリ設定追加開始"
        
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
        
        # タスクバー設定
        foreach ($settingName in $this.Config.TaskbarSettings.Keys) {
            $settingValue = $this.Config.TaskbarSettings[$settingName]
            
            $synchronousCommandElement = $this.XmlDocument.CreateElement("SynchronousCommand", $firstLogonCommandsElement.NamespaceURI)
            $synchronousCommandElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $firstLogonCommandsElement.AppendChild($synchronousCommandElement) | Out-Null
            
            $orderElement = $this.XmlDocument.CreateElement("Order", $synchronousCommandElement.NamespaceURI)
            $orderElement.InnerText = $commandOrder.ToString()
            $synchronousCommandElement.AppendChild($orderElement) | Out-Null
            
            $commandLineElement = $this.XmlDocument.CreateElement("CommandLine", $synchronousCommandElement.NamespaceURI)
            $commandLineElement.InnerText = "reg add `"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced`" /v `"$settingName`" /t REG_DWORD /d $settingValue /f"
            $synchronousCommandElement.AppendChild($commandLineElement) | Out-Null
            
            $descriptionElement = $this.XmlDocument.CreateElement("Description", $synchronousCommandElement.NamespaceURI)
            $descriptionElement.InnerText = "Taskbar Setting: $settingName = $settingValue"
            $synchronousCommandElement.AppendChild($descriptionElement) | Out-Null
            
            $commandOrder++
        }
        
        # スタートメニュー設定
        foreach ($settingName in $this.Config.StartMenuSettings.Keys) {
            $settingValue = $this.Config.StartMenuSettings[$settingName]
            
            $synchronousCommandElement = $this.XmlDocument.CreateElement("SynchronousCommand", $firstLogonCommandsElement.NamespaceURI)
            $synchronousCommandElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $firstLogonCommandsElement.AppendChild($synchronousCommandElement) | Out-Null
            
            $orderElement = $this.XmlDocument.CreateElement("Order", $synchronousCommandElement.NamespaceURI)
            $orderElement.InnerText = $commandOrder.ToString()
            $synchronousCommandElement.AppendChild($orderElement) | Out-Null
            
            $commandLineElement = $this.XmlDocument.CreateElement("CommandLine", $synchronousCommandElement.NamespaceURI)
            
            $registryPath = switch ($settingName) {
                "BingSearchEnabled" { "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" }
                "Start_IrisRecommendations" { "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" }
                "Start_TrackDocs" { "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" }
                "Start_JumpListItems" { "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" }
                default { "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" }
            }
            
            $commandLineElement.InnerText = "reg add `"$registryPath`" /v `"$settingName`" /t REG_DWORD /d $settingValue /f"
            $synchronousCommandElement.AppendChild($commandLineElement) | Out-Null
            
            $descriptionElement = $this.XmlDocument.CreateElement("Description", $synchronousCommandElement.NamespaceURI)
            $descriptionElement.InnerText = "Start Menu Setting: $settingName = $settingValue"
            $synchronousCommandElement.AppendChild($descriptionElement) | Out-Null
            
            $commandOrder++
        }
        
        Write-Verbose "レジストリ設定追加完了"
    }
    
    # Office設定追加
    [void] AddOfficeSettings([System.Xml.XmlElement]$settingsElement) {
        Write-Verbose "Office設定追加開始"
        
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
        
        # Office初回実行スキップ
        if ($this.Config.OfficeConfig.SkipFirstRun) {
            $synchronousCommandElement = $this.XmlDocument.CreateElement("SynchronousCommand", $firstLogonCommandsElement.NamespaceURI)
            $synchronousCommandElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $firstLogonCommandsElement.AppendChild($synchronousCommandElement) | Out-Null
            
            $orderElement = $this.XmlDocument.CreateElement("Order", $synchronousCommandElement.NamespaceURI)
            $orderElement.InnerText = $commandOrder.ToString()
            $synchronousCommandElement.AppendChild($orderElement) | Out-Null
            
            $commandLineElement = $this.XmlDocument.CreateElement("CommandLine", $synchronousCommandElement.NamespaceURI)
            $commandLineElement.InnerText = "reg add `"HKCU\Software\Microsoft\Office\16.0\Common\General`" /v `"ShownFirstRunOptin`" /t REG_DWORD /d 1 /f"
            $synchronousCommandElement.AppendChild($commandLineElement) | Out-Null
            
            $descriptionElement = $this.XmlDocument.CreateElement("Description", $synchronousCommandElement.NamespaceURI)
            $descriptionElement.InnerText = "Office: Skip First Run Experience"
            $synchronousCommandElement.AppendChild($descriptionElement) | Out-Null
            
            $commandOrder++
        }
        
        # Office EULA自動承諾
        if ($this.Config.OfficeConfig.AcceptEula) {
            $synchronousCommandElement = $this.XmlDocument.CreateElement("SynchronousCommand", $firstLogonCommandsElement.NamespaceURI)
            $synchronousCommandElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $firstLogonCommandsElement.AppendChild($synchronousCommandElement) | Out-Null
            
            $orderElement = $this.XmlDocument.CreateElement("Order", $synchronousCommandElement.NamespaceURI)
            $orderElement.InnerText = $commandOrder.ToString()
            $synchronousCommandElement.AppendChild($orderElement) | Out-Null
            
            $commandLineElement = $this.XmlDocument.CreateElement("CommandLine", $synchronousCommandElement.NamespaceURI)
            $commandLineElement.InnerText = "reg add `"HKCU\Software\Microsoft\Office\16.0\Registration`" /v `"AcceptAllEulas`" /t REG_DWORD /d 1 /f"
            $synchronousCommandElement.AppendChild($commandLineElement) | Out-Null
            
            $descriptionElement = $this.XmlDocument.CreateElement("Description", $synchronousCommandElement.NamespaceURI)
            $descriptionElement.InnerText = "Office: Accept EULA Automatically"
            $synchronousCommandElement.AppendChild($descriptionElement) | Out-Null
            
            $commandOrder++
        }
        
        # Officeテレメトリ無効化
        if ($this.Config.OfficeConfig.DisableTelemetry) {
            $synchronousCommandElement = $this.XmlDocument.CreateElement("SynchronousCommand", $firstLogonCommandsElement.NamespaceURI)
            $synchronousCommandElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $firstLogonCommandsElement.AppendChild($synchronousCommandElement) | Out-Null
            
            $orderElement = $this.XmlDocument.CreateElement("Order", $synchronousCommandElement.NamespaceURI)
            $orderElement.InnerText = $commandOrder.ToString()
            $synchronousCommandElement.AppendChild($orderElement) | Out-Null
            
            $commandLineElement = $this.XmlDocument.CreateElement("CommandLine", $synchronousCommandElement.NamespaceURI)
            $commandLineElement.InnerText = "reg add `"HKCU\Software\Policies\Microsoft\Office\16.0\Common\ClientTelemetry`" /v `"DisableTelemetry`" /t REG_DWORD /d 1 /f"
            $synchronousCommandElement.AppendChild($commandLineElement) | Out-Null
            
            $descriptionElement = $this.XmlDocument.CreateElement("Description", $synchronousCommandElement.NamespaceURI)
            $descriptionElement.InnerText = "Office: Disable Telemetry"
            $synchronousCommandElement.AppendChild($descriptionElement) | Out-Null
            
            $commandOrder++
        }
        
        Write-Verbose "Office設定追加完了"
    }
    
    # ファイル関連付け設定追加
    [void] AddFileAssociationSettings([System.Xml.XmlElement]$settingsElement) {
        Write-Verbose "ファイル関連付け設定追加開始"
        
        if ($this.Config.FileAssociations.Count -eq 0) {
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
        
        foreach ($extension in $this.Config.FileAssociations.Keys) {
            $progId = $this.Config.FileAssociations[$extension]
            
            $synchronousCommandElement = $this.XmlDocument.CreateElement("SynchronousCommand", $firstLogonCommandsElement.NamespaceURI)
            $synchronousCommandElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $firstLogonCommandsElement.AppendChild($synchronousCommandElement) | Out-Null
            
            $orderElement = $this.XmlDocument.CreateElement("Order", $synchronousCommandElement.NamespaceURI)
            $orderElement.InnerText = $commandOrder.ToString()
            $synchronousCommandElement.AppendChild($orderElement) | Out-Null
            
            $commandLineElement = $this.XmlDocument.CreateElement("CommandLine", $synchronousCommandElement.NamespaceURI)
            $commandLineElement.InnerText = "assoc $extension=$progId"
            $synchronousCommandElement.AppendChild($commandLineElement) | Out-Null
            
            $descriptionElement = $this.XmlDocument.CreateElement("Description", $synchronousCommandElement.NamespaceURI)
            $descriptionElement.InnerText = "File Association: $extension = $progId"
            $synchronousCommandElement.AppendChild($descriptionElement) | Out-Null
            
            $commandOrder++
        }
        
        Write-Verbose "ファイル関連付け設定追加完了"
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

# アプリケーション設定検証クラス
class ApplicationConfigValidator {
    [ApplicationConfig]$Config
    [string[]]$ValidationErrors
    [string[]]$ValidationWarnings
    
    # コンストラクタ
    ApplicationConfigValidator([ApplicationConfig]$config) {
        $this.Config = $config
        $this.ValidationErrors = @()
        $this.ValidationWarnings = @()
    }
    
    # 設定検証実行
    [bool] ValidateConfiguration() {
        Write-Verbose "アプリケーション設定検証開始"
        
        $this.ValidationErrors = @()
        $this.ValidationWarnings = @()
        
        # 基本検証
        $this.ValidateDefaultApplications()
        $this.ValidateFileAssociations()
        $this.ValidateOfficeSettings()
        $this.ValidateApplicationPaths()
        
        # 結果出力
        foreach ($warning in $this.ValidationWarnings) {
            Write-Warning $warning
        }
        
        foreach ($error in $this.ValidationErrors) {
            Write-Error $error
        }
        
        $isValid = $this.ValidationErrors.Count -eq 0
        Write-Verbose "アプリケーション設定検証完了 (Valid: $isValid)"
        
        return $isValid
    }
    
    # デフォルトアプリケーション検証
    [void] ValidateDefaultApplications() {
        # ブラウザ設定検証
        if ([string]::IsNullOrWhiteSpace($this.Config.DefaultBrowser)) {
            $this.ValidationWarnings += "デフォルトブラウザが設定されていません"
        }
        
        # メールクライアント検証
        if ([string]::IsNullOrWhiteSpace($this.Config.DefaultEmailClient)) {
            $this.ValidationWarnings += "デフォルトメールクライアントが設定されていません"
        }
        
        # PDFリーダー検証
        if ([string]::IsNullOrWhiteSpace($this.Config.DefaultPDFReader)) {
            $this.ValidationWarnings += "デフォルトPDFリーダーが設定されていません"
        }
        
        # 重複ProgId検証
        $progIds = $this.Config.Applications | Where-Object { ![string]::IsNullOrWhiteSpace($_.ProgId) } | ForEach-Object { $_.ProgId }
        $duplicates = $progIds | Group-Object | Where-Object { $_.Count -gt 1 } | Select-Object -ExpandProperty Name
        
        if ($duplicates.Count -gt 0) {
            $this.ValidationWarnings += "重複するProgIDが存在します: $($duplicates -join ', ')"
        }
    }
    
    # ファイル関連付け検証
    [void] ValidateFileAssociations() {
        foreach ($extension in $this.Config.FileAssociations.Keys) {
            $progId = $this.Config.FileAssociations[$extension]
            
            # 拡張子形式検証
            if (!$extension.StartsWith(".")) {
                $this.ValidationErrors += "無効な拡張子形式: $extension (ドットで始まる必要があります)"
            }
            
            # ProgId存在確認
            $application = $this.Config.Applications | Where-Object { $_.ProgId -eq $progId }
            if ($application -eq $null) {
                $this.ValidationWarnings += "ファイル関連付け '$extension' のProgID '$progId' に対応するアプリケーションが見つかりません"
            }
        }
    }
    
    # Office設定検証
    [void] ValidateOfficeSettings() {
        if ($this.Config.OfficeConfig.DisableTelemetry -and !$this.Config.OfficeConfig.AcceptEula) {
            $this.ValidationWarnings += "Officeテレメトリ無効化時はEULA自動承諾を推奨します"
        }
        
        if ($this.Config.OfficeConfig.EnableMacros) {
            $this.ValidationWarnings += "Officeマクロが有効化されています（セキュリティリスク）"
        }
        
        # Office バージョン確認
        switch ($this.Config.OfficeConfig.Version) {
            ([OfficeVersion]::Office2016) {
                $this.ValidationWarnings += "Office 2016はサポート終了が近づいています"
            }
            ([OfficeVersion]::Office2019) {
                $this.ValidationWarnings += "Office 2019の代わりにOffice 365の使用を検討してください"
            }
        }
    }
    
    # アプリケーションパス検証
    [void] ValidateApplicationPaths() {
        foreach ($application in $this.Config.Applications) {
            if (![string]::IsNullOrWhiteSpace($application.ExecutablePath)) {
                # 環境変数展開チェック
                if ($application.ExecutablePath -match '%.*%' -and $application.ExecutablePath -notmatch '%ProgramFiles%|%ProgramFiles\(x86\)%|%LOCALAPPDATA%|%APPDATA%') {
                    $this.ValidationWarnings += "アプリケーション '$($application.Name)' のパスに未知の環境変数が含まれています: $($application.ExecutablePath)"
                }
                
                # 一般的なパス形式検証
                if (!($application.ExecutablePath -match '\.exe$|%.*%.*\.exe$')) {
                    $this.ValidationWarnings += "アプリケーション '$($application.Name)' のパスが実行ファイルを指していない可能性があります: $($application.ExecutablePath)"
                }
            }
        }
    }
}

# メイン関数：UnattendXMLアプリケーション設定生成
function New-UnattendApplicationConfiguration {
    <#
    .SYNOPSIS
        UnattendXMLファイルのアプリケーション設定を生成する
    
    .PARAMETER Config
        メイン設定オブジェクト
    
    .PARAMETER XmlDocument
        XML文書オブジェクト
    
    .PARAMETER ApplicationConfig
        アプリケーション設定（省略時はデフォルト設定）
    
    .EXAMPLE
        New-UnattendApplicationConfiguration -Config $config -XmlDocument $xmlDoc
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [object]$Config,
        
        [Parameter(Mandatory = $true)]
        [System.Xml.XmlDocument]$XmlDocument,
        
        [Parameter(Mandatory = $false)]
        [ApplicationConfig]$ApplicationConfig
    )
    
    try {
        Write-Verbose "UnattendXML アプリケーション設定生成開始"
        
        # アプリケーション設定の準備
        if ($ApplicationConfig -eq $null) {
            $ApplicationConfig = [ApplicationConfig]::new()
            
            # メイン設定からの値適用
            if ($Config.PSObject.Properties.Name -contains "Applications") {
                if ($Config.Applications.PSObject.Properties.Name -contains "DefaultBrowser") {
                    $ApplicationConfig.DefaultBrowser = $Config.Applications.DefaultBrowser
                }
                if ($Config.Applications.PSObject.Properties.Name -contains "DefaultMailClient") {
                    $ApplicationConfig.DefaultEmailClient = $Config.Applications.DefaultMailClient
                }
                if ($Config.Applications.PSObject.Properties.Name -contains "DefaultPDFReader") {
                    $ApplicationConfig.DefaultPDFReader = $Config.Applications.DefaultPDFReader
                }
                if ($Config.Applications.PSObject.Properties.Name -contains "OfficeSettings") {
                    $officeSettings = $Config.Applications.OfficeSettings
                    foreach ($setting in $officeSettings.Keys) {
                        if ($ApplicationConfig.OfficeConfig.PSObject.Properties.Name -contains $setting) {
                            $ApplicationConfig.OfficeConfig.$setting = $officeSettings[$setting]
                        }
                    }
                }
            }
        }
        
        # 設定検証
        $validator = [ApplicationConfigValidator]::new($ApplicationConfig)
        if (!$validator.ValidateConfiguration()) {
            throw "アプリケーション設定の検証に失敗しました"
        }
        
        # XML生成
        $xmlGenerator = [UnattendApplicationXMLGenerator]::new($XmlDocument, $ApplicationConfig)
        $result = $xmlGenerator.GenerateApplicationConfigXML()
        
        Write-Verbose "UnattendXML アプリケーション設定生成完了"
        return @{
            Success = $true
            Message = "アプリケーション設定生成完了"
            DefaultBrowser = $ApplicationConfig.DefaultBrowser
            DefaultEmailClient = $ApplicationConfig.DefaultEmailClient
            DefaultPDFReader = $ApplicationConfig.DefaultPDFReader
            ApplicationsCount = $ApplicationConfig.Applications.Count
            FileAssociations = $ApplicationConfig.FileAssociations.Count
        }
    }
    catch {
        Write-Error "アプリケーション設定生成エラー: $_"
        return @{
            Success = $false
            Message = "アプリケーション設定生成エラー: $_"
            Error = $_
        }
    }
}

# エクスポートするメンバー
Export-ModuleMember -Function @(
    'New-UnattendApplicationConfiguration'
) -Class @(
    'ApplicationSetting',
    'OfficeConfiguration',
    'ApplicationConfig',
    'UnattendApplicationXMLGenerator',
    'ApplicationConfigValidator'
) -Variable @(
    'ApplicationType',
    'OfficeVersion'
)