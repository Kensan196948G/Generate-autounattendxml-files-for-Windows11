#Requires -Version 5.0

<#
.SYNOPSIS
    デスクトップとスタートメニュー設定管理モジュール

.DESCRIPTION
    Windows 11のデスクトップアイコン表示とスタートメニューフォルダ表示を管理するモジュール。
    レジストリ設定とXML生成の両方をサポート。

.VERSION
    1.0.0
#>

# モジュールスコープ変数
$Script:ModuleName = "DesktopConfig"
$Script:ConfigDefaults = @{
    DesktopIcons = @{
        ShowThisPC = $true
        ShowUserFiles = $true
        ShowNetwork = $false
        ShowRecycleBin = $true
        ShowControlPanel = $false
    }
    StartMenu = @{
        ShowDocuments = $true
        ShowDownloads = $true
        ShowMusic = $false
        ShowPictures = $true
        ShowVideos = $false
        ShowNetwork = $false
        ShowPersonalFolder = $true
        ShowFileExplorer = $true
        ShowSettings = $true
        ShowRecentlyAddedApps = $true
        ShowMostUsedApps = $true
        ShowSuggestions = $false
    }
}

class DesktopIconSettings {
    [bool]$ShowThisPC = $true
    [bool]$ShowUserFiles = $true
    [bool]$ShowNetwork = $false
    [bool]$ShowRecycleBin = $true
    [bool]$ShowControlPanel = $false
    
    DesktopIconSettings() {
        # デフォルト値は上記のとおり
    }
    
    DesktopIconSettings([hashtable]$Config) {
        if ($Config.ContainsKey('ShowThisPC')) { $this.ShowThisPC = $Config.ShowThisPC }
        if ($Config.ContainsKey('ShowUserFiles')) { $this.ShowUserFiles = $Config.ShowUserFiles }
        if ($Config.ContainsKey('ShowNetwork')) { $this.ShowNetwork = $Config.ShowNetwork }
        if ($Config.ContainsKey('ShowRecycleBin')) { $this.ShowRecycleBin = $Config.ShowRecycleBin }
        if ($Config.ContainsKey('ShowControlPanel')) { $this.ShowControlPanel = $Config.ShowControlPanel }
    }
    
    [hashtable] ToHashtable() {
        return @{
            ShowThisPC = $this.ShowThisPC
            ShowUserFiles = $this.ShowUserFiles
            ShowNetwork = $this.ShowNetwork
            ShowRecycleBin = $this.ShowRecycleBin
            ShowControlPanel = $this.ShowControlPanel
        }
    }
}

class StartMenuSettings {
    [bool]$ShowDocuments = $true
    [bool]$ShowDownloads = $true
    [bool]$ShowMusic = $false
    [bool]$ShowPictures = $true
    [bool]$ShowVideos = $false
    [bool]$ShowNetwork = $false
    [bool]$ShowPersonalFolder = $true
    [bool]$ShowFileExplorer = $true
    [bool]$ShowSettings = $true
    [bool]$ShowRecentlyAddedApps = $true
    [bool]$ShowMostUsedApps = $true
    [bool]$ShowSuggestions = $false
    
    StartMenuSettings() {
        # デフォルト値は上記のとおり
    }
    
    StartMenuSettings([hashtable]$Config) {
        if ($Config.ContainsKey('ShowDocuments')) { $this.ShowDocuments = $Config.ShowDocuments }
        if ($Config.ContainsKey('ShowDownloads')) { $this.ShowDownloads = $Config.ShowDownloads }
        if ($Config.ContainsKey('ShowMusic')) { $this.ShowMusic = $Config.ShowMusic }
        if ($Config.ContainsKey('ShowPictures')) { $this.ShowPictures = $Config.ShowPictures }
        if ($Config.ContainsKey('ShowVideos')) { $this.ShowVideos = $Config.ShowVideos }
        if ($Config.ContainsKey('ShowNetwork')) { $this.ShowNetwork = $Config.ShowNetwork }
        if ($Config.ContainsKey('ShowPersonalFolder')) { $this.ShowPersonalFolder = $Config.ShowPersonalFolder }
        if ($Config.ContainsKey('ShowFileExplorer')) { $this.ShowFileExplorer = $Config.ShowFileExplorer }
        if ($Config.ContainsKey('ShowSettings')) { $this.ShowSettings = $Config.ShowSettings }
        if ($Config.ContainsKey('ShowRecentlyAddedApps')) { $this.ShowRecentlyAddedApps = $Config.ShowRecentlyAddedApps }
        if ($Config.ContainsKey('ShowMostUsedApps')) { $this.ShowMostUsedApps = $Config.ShowMostUsedApps }
        if ($Config.ContainsKey('ShowSuggestions')) { $this.ShowSuggestions = $Config.ShowSuggestions }
    }
    
    [hashtable] ToHashtable() {
        return @{
            ShowDocuments = $this.ShowDocuments
            ShowDownloads = $this.ShowDownloads
            ShowMusic = $this.ShowMusic
            ShowPictures = $this.ShowPictures
            ShowVideos = $this.ShowVideos
            ShowNetwork = $this.ShowNetwork
            ShowPersonalFolder = $this.ShowPersonalFolder
            ShowFileExplorer = $this.ShowFileExplorer
            ShowSettings = $this.ShowSettings
            ShowRecentlyAddedApps = $this.ShowRecentlyAddedApps
            ShowMostUsedApps = $this.ShowMostUsedApps
            ShowSuggestions = $this.ShowSuggestions
        }
    }
}

function New-DesktopConfig {
    <#
    .SYNOPSIS
        新しいデスクトップ設定を作成
    #>
    param(
        [Parameter(Mandatory = $false)]
        [hashtable]$DesktopIcons = @{},
        
        [Parameter(Mandatory = $false)]
        [hashtable]$StartMenu = @{}
    )
    
    $config = @{
        DesktopIcons = [DesktopIconSettings]::new($DesktopIcons)
        StartMenu = [StartMenuSettings]::new($StartMenu)
    }
    
    return $config
}

function Get-DesktopIconCommands {
    <#
    .SYNOPSIS
        デスクトップアイコン設定用のレジストリコマンドを生成
    #>
    param(
        [Parameter(Mandatory = $true)]
        [DesktopIconSettings]$Settings
    )
    
    $commands = @()
    $basePath = "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel"
    
    # GUIDマッピング
    $iconGuids = @{
        ThisPC = "{20D04FE0-3AEA-1069-A2D8-08002B30309D}"
        UserFiles = "{59031a47-3f72-44a7-89c5-5595fe6b30ee}"
        Network = "{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}"
        RecycleBin = "{645FF040-5081-101B-9F08-00AA002F954E}"
        ControlPanel = "{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}"
    }
    
    # デスクトップアイコンの表示/非表示設定
    # 注意: レジストリ値が0で表示、1で非表示
    if ($Settings.ShowThisPC) {
        $commands += "reg add `"$basePath`" /v `"$($iconGuids.ThisPC)`" /t REG_DWORD /d 0 /f"
    } else {
        $commands += "reg add `"$basePath`" /v `"$($iconGuids.ThisPC)`" /t REG_DWORD /d 1 /f"
    }
    
    if ($Settings.ShowUserFiles) {
        $commands += "reg add `"$basePath`" /v `"$($iconGuids.UserFiles)`" /t REG_DWORD /d 0 /f"
    } else {
        $commands += "reg add `"$basePath`" /v `"$($iconGuids.UserFiles)`" /t REG_DWORD /d 1 /f"
    }
    
    if ($Settings.ShowNetwork) {
        $commands += "reg add `"$basePath`" /v `"$($iconGuids.Network)`" /t REG_DWORD /d 0 /f"
    } else {
        $commands += "reg add `"$basePath`" /v `"$($iconGuids.Network)`" /t REG_DWORD /d 1 /f"
    }
    
    if ($Settings.ShowRecycleBin) {
        $commands += "reg add `"$basePath`" /v `"$($iconGuids.RecycleBin)`" /t REG_DWORD /d 0 /f"
    } else {
        $commands += "reg add `"$basePath`" /v `"$($iconGuids.RecycleBin)`" /t REG_DWORD /d 1 /f"
    }
    
    if ($Settings.ShowControlPanel) {
        $commands += "reg add `"$basePath`" /v `"$($iconGuids.ControlPanel)`" /t REG_DWORD /d 0 /f"
    } else {
        $commands += "reg add `"$basePath`" /v `"$($iconGuids.ControlPanel)`" /t REG_DWORD /d 1 /f"
    }
    
    # デスクトップアイコンを表示する設定
    $commands += "reg add `"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced`" /v `"HideIcons`" /t REG_DWORD /d 0 /f"
    
    return $commands
}

function Get-StartMenuCommands {
    <#
    .SYNOPSIS
        スタートメニュー設定用のレジストリコマンドを生成
    #>
    param(
        [Parameter(Mandatory = $true)]
        [StartMenuSettings]$Settings
    )
    
    $commands = @()
    $basePath = "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    
    # スタートメニューフォルダ設定
    $commands += "reg add `"$basePath`" /v `"Start_ShowDocuments`" /t REG_DWORD /d $(if($Settings.ShowDocuments){1}else{0}) /f"
    $commands += "reg add `"$basePath`" /v `"Start_ShowDownloads`" /t REG_DWORD /d $(if($Settings.ShowDownloads){1}else{0}) /f"
    $commands += "reg add `"$basePath`" /v `"Start_ShowMusic`" /t REG_DWORD /d $(if($Settings.ShowMusic){1}else{0}) /f"
    $commands += "reg add `"$basePath`" /v `"Start_ShowPictures`" /t REG_DWORD /d $(if($Settings.ShowPictures){1}else{0}) /f"
    $commands += "reg add `"$basePath`" /v `"Start_ShowVideos`" /t REG_DWORD /d $(if($Settings.ShowVideos){1}else{0}) /f"
    $commands += "reg add `"$basePath`" /v `"Start_ShowNetwork`" /t REG_DWORD /d $(if($Settings.ShowNetwork){1}else{0}) /f"
    $commands += "reg add `"$basePath`" /v `"Start_ShowUser`" /t REG_DWORD /d $(if($Settings.ShowPersonalFolder){1}else{0}) /f"
    $commands += "reg add `"$basePath`" /v `"Start_ShowMyComputer`" /t REG_DWORD /d $(if($Settings.ShowFileExplorer){1}else{0}) /f"
    $commands += "reg add `"$basePath`" /v `"Start_ShowControlPanel`" /t REG_DWORD /d $(if($Settings.ShowSettings){1}else{0}) /f"
    
    # 追加のスタートメニュー設定
    $commands += "reg add `"$basePath`" /v `"Start_ShowRecentDocs`" /t REG_DWORD /d $(if($Settings.ShowRecentlyAddedApps){1}else{0}) /f"
    $commands += "reg add `"$basePath`" /v `"Start_ShowFrequentlyUsedPrograms`" /t REG_DWORD /d $(if($Settings.ShowMostUsedApps){1}else{0}) /f"
    
    # おすすめの無効化（ShowSuggestionsがfalseの場合に無効化）
    if (!$Settings.ShowSuggestions) {
        $commands += "reg add `"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager`" /v `"SubscribedContent-338388Enabled`" /t REG_DWORD /d 0 /f"
        $commands += "reg add `"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager`" /v `"SubscribedContent-338389Enabled`" /t REG_DWORD /d 0 /f"
    }
    
    return $commands
}

function Add-DesktopConfigToXML {
    <#
    .SYNOPSIS
        デスクトップ設定をXMLに追加
    #>
    param(
        [Parameter(Mandatory = $true)]
        [System.Xml.XmlDocument]$XmlDocument,
        
        [Parameter(Mandatory = $true)]
        [hashtable]$Config
    )
    
    Write-Verbose "デスクトップ設定をXMLに追加中..."
    
    # FirstLogonCommandsセクションを取得または作成
    $oobeSettings = $XmlDocument.unattend.settings | Where-Object { $_.pass -eq "oobeSystem" }
    if (!$oobeSettings) {
        throw "oobeSystemセクションが見つかりません"
    }
    
    $shellSetup = $oobeSettings.component | Where-Object { $_.name -eq "Microsoft-Windows-Shell-Setup" }
    if (!$shellSetup) {
        throw "Microsoft-Windows-Shell-Setupコンポーネントが見つかりません"
    }
    
    $firstLogonCommands = $shellSetup.FirstLogonCommands
    if (!$firstLogonCommands) {
        $firstLogonCommands = $XmlDocument.CreateElement("FirstLogonCommands", $XmlDocument.DocumentElement.NamespaceURI)
        $shellSetup.AppendChild($firstLogonCommands) | Out-Null
    }
    
    # 現在のコマンド数を取得
    $currentOrder = ($firstLogonCommands.SynchronousCommand | Measure-Object).Count + 1
    
    # デスクトップアイコン設定コマンドを追加
    $desktopCommands = Get-DesktopIconCommands -Settings $Config.DesktopIcons
    foreach ($cmd in $desktopCommands) {
        $syncCommand = $XmlDocument.CreateElement("SynchronousCommand", $XmlDocument.DocumentElement.NamespaceURI)
        
        $order = $XmlDocument.CreateElement("Order", $XmlDocument.DocumentElement.NamespaceURI)
        $order.InnerText = $currentOrder.ToString()
        $syncCommand.AppendChild($order) | Out-Null
        
        $commandLine = $XmlDocument.CreateElement("CommandLine", $XmlDocument.DocumentElement.NamespaceURI)
        $commandLine.InnerText = "cmd /c $cmd"
        $syncCommand.AppendChild($commandLine) | Out-Null
        
        $description = $XmlDocument.CreateElement("Description", $XmlDocument.DocumentElement.NamespaceURI)
        $description.InnerText = "Configure desktop icon"
        $syncCommand.AppendChild($description) | Out-Null
        
        $requiresUserInput = $XmlDocument.CreateElement("RequiresUserInput", $XmlDocument.DocumentElement.NamespaceURI)
        $requiresUserInput.InnerText = "false"
        $syncCommand.AppendChild($requiresUserInput) | Out-Null
        
        $firstLogonCommands.AppendChild($syncCommand) | Out-Null
        $currentOrder++
    }
    
    # スタートメニュー設定コマンドを追加
    $startMenuCommands = Get-StartMenuCommands -Settings $Config.StartMenu
    foreach ($cmd in $startMenuCommands) {
        $syncCommand = $XmlDocument.CreateElement("SynchronousCommand", $XmlDocument.DocumentElement.NamespaceURI)
        
        $order = $XmlDocument.CreateElement("Order", $XmlDocument.DocumentElement.NamespaceURI)
        $order.InnerText = $currentOrder.ToString()
        $syncCommand.AppendChild($order) | Out-Null
        
        $commandLine = $XmlDocument.CreateElement("CommandLine", $XmlDocument.DocumentElement.NamespaceURI)
        $commandLine.InnerText = "cmd /c $cmd"
        $syncCommand.AppendChild($commandLine) | Out-Null
        
        $description = $XmlDocument.CreateElement("Description", $XmlDocument.DocumentElement.NamespaceURI)
        $description.InnerText = "Configure start menu"
        $syncCommand.AppendChild($description) | Out-Null
        
        $requiresUserInput = $XmlDocument.CreateElement("RequiresUserInput", $XmlDocument.DocumentElement.NamespaceURI)
        $requiresUserInput.InnerText = "false"
        $syncCommand.AppendChild($requiresUserInput) | Out-Null
        
        $firstLogonCommands.AppendChild($syncCommand) | Out-Null
        $currentOrder++
    }
    
    Write-Verbose "デスクトップ設定をXMLに追加完了"
    
    return $XmlDocument
}

function Get-DesktopConfigPreset {
    <#
    .SYNOPSIS
        プリセット設定を取得
    #>
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("Minimal", "Standard", "Full")]
        [string]$PresetName
    )
    
    switch ($PresetName) {
        "Minimal" {
            return @{
                DesktopIcons = @{
                    ShowThisPC = $true
                    ShowUserFiles = $false
                    ShowNetwork = $false
                    ShowRecycleBin = $true
                    ShowControlPanel = $false
                }
                StartMenu = @{
                    ShowDocuments = $false
                    ShowDownloads = $false
                    ShowMusic = $false
                    ShowPictures = $false
                    ShowVideos = $false
                    ShowNetwork = $false
                    ShowPersonalFolder = $false
                    ShowFileExplorer = $true
                    ShowSettings = $true
                    ShowRecentlyAddedApps = $false
                    ShowMostUsedApps = $false
                    ShowSuggestions = $false
                }
            }
        }
        "Standard" {
            return @{
                DesktopIcons = @{
                    ShowThisPC = $true
                    ShowUserFiles = $true
                    ShowNetwork = $false
                    ShowRecycleBin = $true
                    ShowControlPanel = $false
                }
                StartMenu = @{
                    ShowDocuments = $true
                    ShowDownloads = $true
                    ShowMusic = $false
                    ShowPictures = $true
                    ShowVideos = $false
                    ShowNetwork = $false
                    ShowPersonalFolder = $true
                    ShowFileExplorer = $true
                    ShowSettings = $true
                    ShowRecentlyAddedApps = $true
                    ShowMostUsedApps = $true
                    ShowSuggestions = $false
                }
            }
        }
        "Full" {
            return @{
                DesktopIcons = @{
                    ShowThisPC = $true
                    ShowUserFiles = $true
                    ShowNetwork = $true
                    ShowRecycleBin = $true
                    ShowControlPanel = $true
                }
                StartMenu = @{
                    ShowDocuments = $true
                    ShowDownloads = $true
                    ShowMusic = $true
                    ShowPictures = $true
                    ShowVideos = $true
                    ShowNetwork = $true
                    ShowPersonalFolder = $true
                    ShowFileExplorer = $true
                    ShowSettings = $true
                    ShowRecentlyAddedApps = $true
                    ShowMostUsedApps = $true
                    ShowSuggestions = $false
                }
            }
        }
    }
}

# エクスポート
Export-ModuleMember -Function @(
    'New-DesktopConfig',
    'Get-DesktopIconCommands',
    'Get-StartMenuCommands',
    'Add-DesktopConfigToXML',
    'Get-DesktopConfigPreset'
) -Variable @(
    'ConfigDefaults'
)