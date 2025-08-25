#Requires -Version 5.0

<#
.SYNOPSIS
    Windows 11 Sysprep応答ファイル自動生成システム - メインモジュール

.DESCRIPTION
    Windows 11のSysprep実行時に使用する応答ファイル（unattend.xml）を自動生成するPowerShellモジュール
    PowerShell 5.xのクラス機能とRunspacePoolを活用して高性能な並列処理を実現

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

# モジュール内部変数
$Script:ModuleRoot = $PSScriptRoot
$Script:LogPath = Join-Path $ModuleRoot "Logs"
$Script:OutputPath = Join-Path $ModuleRoot "Outputs"
$Script:ConfigPath = Join-Path $ModuleRoot "Configs"

# ログ出力レベル
enum LogLevel {
    Debug = 0
    Info = 1
    Warning = 2
    Error = 3
    Critical = 4
}

# システム設定クラス
class UnattendSystemConfig {
    [string]$HostName
    [string]$TimeZone
    [bool]$DisableIPv6
    [bool]$DisableFirewall
    [bool]$DisableBluetooth
    [bool]$MuteAudio
    
    # コンストラクタ
    UnattendSystemConfig() {
        $this.HostName = "WIN11-PC"
        $this.TimeZone = "Tokyo Standard Time"
        $this.DisableIPv6 = $true
        $this.DisableFirewall = $true
        $this.DisableBluetooth = $true
        $this.MuteAudio = $true
    }
}

# ユーザー設定クラス
class UnattendUserConfig {
    [string]$Name
    [securestring]$Password
    [string[]]$Groups
    [bool]$IsEnabled
    [bool]$IsBuiltIn
    
    # コンストラクタ
    UnattendUserConfig([string]$name, [securestring]$password, [string[]]$groups) {
        $this.Name = $name
        $this.Password = $password
        $this.Groups = $groups
        $this.IsEnabled = $true
        $this.IsBuiltIn = $false
    }
    
    # Built-in アカウント用コンストラクタ
    UnattendUserConfig([string]$name, [bool]$isEnabled) {
        $this.Name = $name
        $this.IsEnabled = $isEnabled
        $this.IsBuiltIn = $true
        $this.Groups = @()
    }
}

# アプリケーション設定クラス
class UnattendApplicationConfig {
    [bool]$EnableDotNet35
    [string]$DefaultBrowser
    [string]$DefaultMailClient
    [string]$DefaultPDFReader
    [hashtable]$OfficeSettings
    
    # コンストラクタ
    UnattendApplicationConfig() {
        $this.EnableDotNet35 = $true
        $this.DefaultBrowser = "msedge"
        $this.DefaultMailClient = "outlook"
        $this.DefaultPDFReader = "AcroExch.Document"
        $this.OfficeSettings = @{
            SkipFirstRun = $true
            AcceptEula = $true
            DisableTelemetry = $true
        }
    }
}

# UnattendXML生成設定クラス
class UnattendGeneratorConfig {
    [UnattendSystemConfig]$System
    [UnattendUserConfig[]]$Users
    [UnattendApplicationConfig]$Applications
    [hashtable]$CustomSettings
    
    # コンストラクタ
    UnattendGeneratorConfig() {
        $this.System = [UnattendSystemConfig]::new()
        $this.Users = @()
        $this.Applications = [UnattendApplicationConfig]::new()
        $this.CustomSettings = @{}
    }
    
    # ユーザー追加メソッド
    [void] AddUser([UnattendUserConfig]$user) {
        $this.Users += $user
    }
    
    # デフォルトユーザー設定
    [void] SetupDefaultUsers() {
        # Administrator無効化
        $adminUser = [UnattendUserConfig]::new("Administrator", $false)
        $this.AddUser($adminUser)
        
        # mirai-user作成
        $miraiPassword = ConvertTo-SecureString "MiraiUser2025!" -AsPlainText -Force
        $miraiUser = [UnattendUserConfig]::new("mirai-user", $miraiPassword, @("Administrators", "Users"))
        $this.AddUser($miraiUser)
        
        # l-admin作成
        $ladminPassword = ConvertTo-SecureString "LAdmin2025!" -AsPlainText -Force
        $ladminUser = [UnattendUserConfig]::new("l-admin", $ladminPassword, @("Administrators", "Users"))
        $this.AddUser($ladminUser)
    }
}

# 並列処理用ジョブクラス
class UnattendGenerationJob {
    [string]$Id
    [string]$Name
    [scriptblock]$Script
    [hashtable]$Parameters
    [System.Management.Automation.PowerShell]$PowerShell
    [System.IAsyncResult]$AsyncResult
    [datetime]$StartTime
    
    # コンストラクタ
    UnattendGenerationJob([string]$name, [scriptblock]$script, [hashtable]$parameters) {
        $this.Id = [System.Guid]::NewGuid().ToString()
        $this.Name = $name
        $this.Script = $script
        $this.Parameters = $parameters
        $this.StartTime = Get-Date
    }
}

# メインUnattendXML生成クラス
class UnattendXMLGenerator {
    [UnattendGeneratorConfig]$Config
    [System.Xml.XmlDocument]$XmlDocument
    [System.Management.Automation.Runspaces.RunspacePool]$RunspacePool
    [System.Collections.Generic.List[UnattendGenerationJob]]$Jobs
    [string]$LogFile
    
    # コンストラクタ
    UnattendXMLGenerator([UnattendGeneratorConfig]$config) {
        $this.Config = $config
        $this.XmlDocument = New-Object System.Xml.XmlDocument
        $this.Jobs = [System.Collections.Generic.List[UnattendGenerationJob]]::new()
        $this.LogFile = Join-Path $Script:LogPath "UnattendGeneration_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
        
        # RunspacePoolの初期化
        $this.InitializeRunspacePool()
    }
    
    # RunspacePool初期化
    [void] InitializeRunspacePool() {
        $minRunspaces = 1
        $maxRunspaces = [Environment]::ProcessorCount
        
        $this.RunspacePool = [System.Management.Automation.Runspaces.RunspaceFactory]::CreateRunspacePool($minRunspaces, $maxRunspaces)
        $this.RunspacePool.Open()
        
        $this.WriteLog([LogLevel]::Info, "RunspacePool初期化完了 (Min: $minRunspaces, Max: $maxRunspaces)")
    }
    
    # ログ出力メソッド
    [void] WriteLog([LogLevel]$level, [string]$message) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$timestamp] [$level] $message"
        
        # コンソール出力
        switch ($level) {
            ([LogLevel]::Error) { Write-Error $message }
            ([LogLevel]::Warning) { Write-Warning $message }
            ([LogLevel]::Debug) { Write-Debug $message }
            default { Write-Host $logEntry -ForegroundColor Green }
        }
        
        # ファイル出力
        try {
            if (!(Test-Path $Script:LogPath)) {
                New-Item -Path $Script:LogPath -ItemType Directory -Force | Out-Null
            }
            Add-Content -Path $this.LogFile -Value $logEntry -Encoding UTF8
        }
        catch {
            Write-Warning "ログファイルへの書き込みに失敗しました: $_"
        }
    }
    
    # 並列ジョブ追加
    [void] AddJob([string]$name, [scriptblock]$script, [hashtable]$parameters) {
        $job = [UnattendGenerationJob]::new($name, $script, $parameters)
        
        $job.PowerShell = [System.Management.Automation.PowerShell]::Create()
        $job.PowerShell.RunspacePool = $this.RunspacePool
        $job.PowerShell.AddScript($job.Script) | Out-Null
        
        foreach ($param in $job.Parameters.GetEnumerator()) {
            $job.PowerShell.AddParameter($param.Key, $param.Value) | Out-Null
        }
        
        $job.AsyncResult = $job.PowerShell.BeginInvoke()
        $this.Jobs.Add($job)
        
        $this.WriteLog([LogLevel]::Info, "並列ジョブ追加: $name (ID: $($job.Id))")
    }
    
    # すべてのジョブ完了待機
    [hashtable] WaitForAllJobs() {
        $results = @{}
        
        $this.WriteLog([LogLevel]::Info, "並列ジョブ完了待機開始 (ジョブ数: $($this.Jobs.Count))")
        
        foreach ($job in $this.Jobs) {
            try {
                $result = $job.PowerShell.EndInvoke($job.AsyncResult)
                $results[$job.Name] = $result
                
                $duration = (Get-Date) - $job.StartTime
                $this.WriteLog([LogLevel]::Info, "ジョブ完了: $($job.Name) (実行時間: $($duration.TotalSeconds)秒)")
            }
            catch {
                $this.WriteLog([LogLevel]::Error, "ジョブエラー [$($job.Name)]: $_")
                $results[$job.Name] = $null
            }
            finally {
                $job.PowerShell.Dispose()
            }
        }
        
        return $results
    }
    
    # UnattendXML生成メイン処理
    [string] GenerateUnattendXML() {
        $this.WriteLog([LogLevel]::Info, "UnattendXML生成開始")
        
        try {
            # XML基本構造作成
            $this.CreateXMLStructure()
            
            # 並列処理でモジュール実行
            $this.ExecuteModulesInParallel()
            
            # 結果統合とXML出力
            $outputPath = $this.FinalizeXMLGeneration()
            
            $this.WriteLog([LogLevel]::Info, "UnattendXML生成完了: $outputPath")
            return $outputPath
        }
        catch {
            $this.WriteLog([LogLevel]::Error, "UnattendXML生成エラー: $_")
            throw
        }
        finally {
            # リソースクリーンアップ
            $this.Cleanup()
        }
    }
    
    # XML基本構造作成
    [void] CreateXMLStructure() {
        $this.WriteLog([LogLevel]::Debug, "XML基本構造作成開始")
        
        # XML宣言とルート要素
        $xmlDeclaration = $this.XmlDocument.CreateXmlDeclaration("1.0", "UTF-8", $null)
        $this.XmlDocument.AppendChild($xmlDeclaration) | Out-Null
        
        # unattend要素作成
        $unattendElement = $this.XmlDocument.CreateElement("unattend")
        $unattendElement.SetAttribute("xmlns", "urn:schemas-microsoft-com:unattend")
        $this.XmlDocument.AppendChild($unattendElement) | Out-Null
        
        $this.WriteLog([LogLevel]::Debug, "XML基本構造作成完了")
    }
    
    # モジュール並列実行
    [void] ExecuteModulesInParallel() {
        $this.WriteLog([LogLevel]::Info, "モジュール並列実行開始")
        
        # ユーザー管理ジョブ
        $userScript = {
            param($config, $xmlDoc)
            Import-Module "$PSScriptRoot\Modules\UserManagement\UserManagement.psm1" -Force
            return New-UnattendUserConfiguration -Config $config -XmlDocument $xmlDoc
        }
        $this.AddJob("UserManagement", $userScript, @{ config = $this.Config; xmlDoc = $this.XmlDocument })
        
        # ネットワーク設定ジョブ
        $networkScript = {
            param($config, $xmlDoc)
            Import-Module "$PSScriptRoot\Modules\NetworkConfig\NetworkConfig.psm1" -Force
            return New-UnattendNetworkConfiguration -Config $config -XmlDocument $xmlDoc
        }
        $this.AddJob("NetworkConfig", $networkScript, @{ config = $this.Config; xmlDoc = $this.XmlDocument })
        
        # Windows機能ジョブ
        $featuresScript = {
            param($config, $xmlDoc)
            Import-Module "$PSScriptRoot\Modules\WindowsFeatures\WindowsFeatures.psm1" -Force
            return New-UnattendWindowsFeatures -Config $config -XmlDocument $xmlDoc
        }
        $this.AddJob("WindowsFeatures", $featuresScript, @{ config = $this.Config; xmlDoc = $this.XmlDocument })
        
        # アプリケーション設定ジョブ
        $appScript = {
            param($config, $xmlDoc)
            Import-Module "$PSScriptRoot\Modules\ApplicationConfig\ApplicationConfig.psm1" -Force
            return New-UnattendApplicationConfiguration -Config $config -XmlDocument $xmlDoc
        }
        $this.AddJob("ApplicationConfig", $appScript, @{ config = $this.Config; xmlDoc = $this.XmlDocument })
        
        # ジョブ完了待機
        $results = $this.WaitForAllJobs()
        $this.WriteLog([LogLevel]::Info, "モジュール並列実行完了")
    }
    
    # XML生成最終化
    [string] FinalizeXMLGeneration() {
        $this.WriteLog([LogLevel]::Info, "XML最終化処理開始")
        
        # 出力ディレクトリ確認
        if (!(Test-Path $Script:OutputPath)) {
            New-Item -Path $Script:OutputPath -ItemType Directory -Force | Out-Null
        }
        
        # ファイル名生成
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $hostname = $this.Config.System.HostName
        $filename = "unattend_${hostname}_${timestamp}.xml"
        $outputPath = Join-Path $Script:OutputPath $filename
        
        # XML保存
        $xmlSettings = New-Object System.Xml.XmlWriterSettings
        $xmlSettings.Indent = $true
        $xmlSettings.IndentChars = "  "
        $xmlSettings.Encoding = [System.Text.Encoding]::UTF8
        
        $writer = [System.Xml.XmlWriter]::Create($outputPath, $xmlSettings)
        try {
            $this.XmlDocument.Save($writer)
        }
        finally {
            $writer.Close()
        }
        
        $this.WriteLog([LogLevel]::Info, "XML最終化処理完了: $outputPath")
        return $outputPath
    }
    
    # リソースクリーンアップ
    [void] Cleanup() {
        $this.WriteLog([LogLevel]::Debug, "リソースクリーンアップ開始")
        
        if ($this.RunspacePool -ne $null) {
            $this.RunspacePool.Close()
            $this.RunspacePool.Dispose()
        }
        
        $this.WriteLog([LogLevel]::Debug, "リソースクリーンアップ完了")
    }
}

# プリセット設定読み込み関数
function Import-UnattendPreset {
    <#
    .SYNOPSIS
        プリセット設定ファイルを読み込む
    
    .PARAMETER PresetName
        読み込むプリセット名
    
    .EXAMPLE
        Import-UnattendPreset -PresetName "Enterprise"
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("Development", "Enterprise", "Minimal", "Custom")]
        [string]$PresetName
    )
    
    $presetPath = Join-Path $Script:ConfigPath "Presets\$PresetName.psd1"
    
    if (!(Test-Path $presetPath)) {
        throw "プリセットファイルが見つかりません: $presetPath"
    }
    
    try {
        $presetData = Import-PowerShellDataFile -Path $presetPath
        
        $config = [UnattendGeneratorConfig]::new()
        
        # システム設定適用
        if ($presetData.ContainsKey("System")) {
            $systemData = $presetData.System
            foreach ($property in $systemData.Keys) {
                if ($config.System.PSObject.Properties.Name -contains $property) {
                    $config.System.$property = $systemData[$property]
                }
            }
        }
        
        # ユーザー設定適用
        if ($presetData.ContainsKey("Users")) {
            foreach ($userData in $presetData.Users) {
                if ($userData.ContainsKey("Password")) {
                    $securePassword = ConvertTo-SecureString $userData.Password -AsPlainText -Force
                    $user = [UnattendUserConfig]::new($userData.Name, $securePassword, $userData.Groups)
                } else {
                    $user = [UnattendUserConfig]::new($userData.Name, $userData.IsEnabled)
                }
                $config.AddUser($user)
            }
        }
        
        # アプリケーション設定適用
        if ($presetData.ContainsKey("Applications")) {
            $appData = $presetData.Applications
            foreach ($property in $appData.Keys) {
                if ($config.Applications.PSObject.Properties.Name -contains $property) {
                    $config.Applications.$property = $appData[$property]
                }
            }
        }
        
        Write-Verbose "プリセット読み込み完了: $PresetName"
        return $config
    }
    catch {
        throw "プリセット読み込みエラー: $_"
    }
}

# UnattendXML生成関数
function New-UnattendXML {
    <#
    .SYNOPSIS
        Windows 11 Sysprep用unattend.xmlファイルを生成する
    
    .PARAMETER Config
        生成設定オブジェクト
    
    .PARAMETER PresetName
        使用するプリセット名
    
    .PARAMETER OutputPath
        出力先パス
    
    .EXAMPLE
        New-UnattendXML -PresetName "Enterprise" -OutputPath "C:\Temp\unattend.xml"
    #>
    [CmdletBinding(DefaultParameterSetName = "Preset")]
    param(
        [Parameter(Mandatory = $true, ParameterSetName = "Config")]
        [UnattendGeneratorConfig]$Config,
        
        [Parameter(Mandatory = $true, ParameterSetName = "Preset")]
        [ValidateSet("Development", "Enterprise", "Minimal")]
        [string]$PresetName,
        
        [Parameter(Mandatory = $false)]
        [string]$OutputPath
    )
    
    try {
        # 設定の準備
        if ($PSCmdlet.ParameterSetName -eq "Preset") {
            $Config = Import-UnattendPreset -PresetName $PresetName
        }
        
        # XML生成器初期化
        $generator = [UnattendXMLGenerator]::new($Config)
        
        # XML生成実行
        $result = $generator.GenerateUnattendXML()
        
        # 指定された出力パスにコピー
        if ($OutputPath) {
            Copy-Item -Path $result -Destination $OutputPath -Force
            Write-Host "UnattendXMLファイルが生成されました: $OutputPath" -ForegroundColor Green
            return $OutputPath
        } else {
            Write-Host "UnattendXMLファイルが生成されました: $result" -ForegroundColor Green
            return $result
        }
    }
    catch {
        Write-Error "UnattendXML生成エラー: $_"
        throw
    }
}

# インタラクティブモード関数
function Start-UnattendXMLWizard {
    <#
    .SYNOPSIS
        対話的なUnattendXML生成ウィザードを開始する
    
    .EXAMPLE
        Start-UnattendXMLWizard
    #>
    [CmdletBinding()]
    param()
    
    Write-Host "=== Windows 11 Sysprep UnattendXML 生成ウィザード ===" -ForegroundColor Cyan
    Write-Host ""
    
    # プリセット選択
    $presets = @("Development", "Enterprise", "Minimal", "Custom")
    $presetIndex = 0
    
    do {
        Write-Host "使用するプリセットを選択してください:"
        for ($i = 0; $i -lt $presets.Count; $i++) {
            $marker = if ($i -eq $presetIndex) { ">" } else { " " }
            Write-Host "$marker $($i + 1). $($presets[$i])"
        }
        
        $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        
        switch ($key.VirtualKeyCode) {
            38 { $presetIndex = [Math]::Max(0, $presetIndex - 1) } # Up
            40 { $presetIndex = [Math]::Min($presets.Count - 1, $presetIndex + 1) } # Down
            13 { break } # Enter
        }
        
        Clear-Host
        Write-Host "=== Windows 11 Sysprep UnattendXML 生成ウィザード ===" -ForegroundColor Cyan
        Write-Host ""
    } while ($key.VirtualKeyCode -ne 13)
    
    $selectedPreset = $presets[$presetIndex]
    Write-Host "選択されたプリセット: $selectedPreset" -ForegroundColor Green
    
    # カスタム設定の場合
    if ($selectedPreset -eq "Custom") {
        $config = New-CustomUnattendConfig
    } else {
        $config = Import-UnattendPreset -PresetName $selectedPreset
    }
    
    # 出力先選択
    $outputPath = Read-Host "出力先パス (空白でデフォルト)"
    
    # XML生成
    if ([string]::IsNullOrWhiteSpace($outputPath)) {
        $result = New-UnattendXML -Config $config
    } else {
        $result = New-UnattendXML -Config $config -OutputPath $outputPath
    }
    
    Write-Host ""
    Write-Host "UnattendXMLファイルの生成が完了しました!" -ForegroundColor Green
    Write-Host "ファイル: $result" -ForegroundColor Yellow
}

# カスタム設定作成関数
function New-CustomUnattendConfig {
    <#
    .SYNOPSIS
        カスタム設定を対話的に作成する
    
    .EXAMPLE
        New-CustomUnattendConfig
    #>
    [CmdletBinding()]
    param()
    
    $config = [UnattendGeneratorConfig]::new()
    
    Write-Host "カスタム設定を作成します..." -ForegroundColor Yellow
    
    # ホスト名設定
    $hostname = Read-Host "ホスト名 (現在: $($config.System.HostName))"
    if (![string]::IsNullOrWhiteSpace($hostname)) {
        $config.System.HostName = $hostname
    }
    
    # ネットワーク設定
    $disableIPv6 = Read-Host "IPv6を無効化しますか? (Y/n)"
    $config.System.DisableIPv6 = ($disableIPv6 -ne "n")
    
    $disableFirewall = Read-Host "Firewallを無効化しますか? (Y/n)"
    $config.System.DisableFirewall = ($disableFirewall -ne "n")
    
    $disableBluetooth = Read-Host "Bluetoothを無効化しますか? (Y/n)"
    $config.System.DisableBluetooth = ($disableBluetooth -ne "n")
    
    # デフォルトユーザー設定
    $setupDefaultUsers = Read-Host "デフォルトユーザー（mirai-user, l-admin）を設定しますか? (Y/n)"
    if ($setupDefaultUsers -ne "n") {
        $config.SetupDefaultUsers()
    }
    
    return $config
}

# モジュールエクスポート
Export-ModuleMember -Function @(
    'New-UnattendXML',
    'Start-UnattendXMLWizard', 
    'Import-UnattendPreset',
    'New-CustomUnattendConfig'
) -Variable @(
    'ModuleRoot',
    'LogPath',
    'OutputPath',
    'ConfigPath'
)