#Requires -Version 5.0

<#
.SYNOPSIS
    Windows 11 Sysprep応答ファイル（unattend.xml）生成メインスクリプト

.DESCRIPTION
    Windows 11のSysprep実行時に使用する応答ファイル（unattend.xml）を自動生成するメインスクリプト。
    PowerShell 5.xのクラス機能とRunspacePoolを活用した高性能な並列処理により、
    企業環境でのPCキッティング作業を効率化します。

.PARAMETER PresetName
    使用するプリセット名（Development, Enterprise, Minimal, Custom）

.PARAMETER ConfigFile
    設定ファイルのパス（JSON/PSD1形式）

.PARAMETER OutputPath
    生成されるunattend.xmlファイルの出力先パス

.PARAMETER Interactive
    対話的なウィザードモードで実行

.PARAMETER ValidateOnly
    既存のXMLファイルの検証のみ実行

.PARAMETER LogLevel
    ログ出力レベル（Debug, Info, Warning, Error, Critical）

.PARAMETER Force
    既存ファイルを強制上書き

.PARAMETER WhatIf
    実際には実行せず、処理内容のみ表示

.EXAMPLE
    .\Generate-UnattendXML.ps1 -PresetName Enterprise -OutputPath "C:\Temp\unattend.xml"
    Enterpriseプリセットを使用してunattend.xmlを生成

.EXAMPLE
    .\Generate-UnattendXML.ps1 -Interactive
    対話的なウィザードモードで実行

.EXAMPLE
    .\Generate-UnattendXML.ps1 -ConfigFile ".\Configs\custom.psd1" -LogLevel Debug
    カスタム設定ファイルを使用してデバッグレベルで実行

.EXAMPLE
    .\Generate-UnattendXML.ps1 -ValidateOnly -OutputPath "C:\Temp\unattend.xml"
    既存のXMLファイルを検証のみ

.VERSION
    1.0.0

.AUTHOR
    Windows 11 Sysprep Automation Team

.COPYRIGHT
    Copyright (c) 2025. All rights reserved.

.LINK
    https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/update-windows-settings-and-scripts-create-your-own-answer-file-sxs
#>

[CmdletBinding(DefaultParameterSetName = "Preset")]
param(
    [Parameter(Mandatory = $true, ParameterSetName = "Preset")]
    [ValidateSet("Development", "Enterprise", "Minimal", "Custom")]
    [string]$PresetName,
    
    [Parameter(Mandatory = $true, ParameterSetName = "ConfigFile")]
    [ValidateScript({
        if (!(Test-Path $_ -PathType Leaf)) {
            throw "設定ファイルが見つかりません: $_"
        }
        if ($_ -notmatch '\.(psd1|json)$') {
            throw "設定ファイルはPSD1またはJSON形式である必要があります: $_"
        }
        return $true
    })]
    [string]$ConfigFile,
    
    [Parameter(Mandatory = $false)]
    [string]$OutputPath,
    
    [Parameter(Mandatory = $true, ParameterSetName = "Interactive")]
    [switch]$Interactive,
    
    [Parameter(Mandatory = $true, ParameterSetName = "ValidateOnly")]
    [switch]$ValidateOnly,
    
    [Parameter(Mandatory = $false)]
    [ValidateSet("Debug", "Info", "Warning", "Error", "Critical")]
    [string]$LogLevel = "Info",
    
    [Parameter(Mandatory = $false)]
    [switch]$Force,
    
    [Parameter(Mandatory = $false)]
    [switch]$WhatIf
)

# スクリプトのルートディレクトリを設定
$Script:ScriptRoot = $PSScriptRoot
$Script:ModulePath = Join-Path $ScriptRoot "Modules"
$Script:ConfigPath = Join-Path $ScriptRoot "Configs"
$Script:OutputPath = Join-Path $ScriptRoot "Outputs"
$Script:LogPath = Join-Path $ScriptRoot "Logs"

# ログ設定
$Script:LogFile = Join-Path $LogPath "Generate-UnattendXML_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# エラーアクション設定
$ErrorActionPreference = "Stop"
$VerbosePreference = if ($LogLevel -eq "Debug") { "Continue" } else { "SilentlyContinue" }

#region Helper Functions

function Write-Log {
    <#
    .SYNOPSIS
        ログメッセージを出力する
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        
        [Parameter(Mandatory = $false)]
        [ValidateSet("Debug", "Info", "Warning", "Error", "Critical")]
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # コンソール出力
    switch ($Level) {
        "Error" { Write-Error $Message }
        "Warning" { Write-Warning $Message }
        "Debug" { Write-Debug $Message }
        "Critical" { Write-Error $Message -ErrorAction Continue; Write-Host $logEntry -ForegroundColor Red }
        default { Write-Host $logEntry -ForegroundColor Green }
    }
    
    # ファイル出力
    try {
        if (!(Test-Path $LogPath)) {
            New-Item -Path $LogPath -ItemType Directory -Force | Out-Null
        }
        Add-Content -Path $Script:LogFile -Value $logEntry -Encoding UTF8
    }
    catch {
        Write-Warning "ログファイルへの書き込みに失敗しました: $_"
    }
}

function Import-RequiredModules {
    <#
    .SYNOPSIS
        必要なモジュールをインポートする
    #>
    
    Write-Log "必要なモジュールをインポート中..." "Info"
    
    $requiredModules = @(
        @{ Path = Join-Path $ModulePath "UserManagement\UserManagement.psm1"; Name = "UserManagement" },
        @{ Path = Join-Path $ModulePath "NetworkConfig\NetworkConfig.psm1"; Name = "NetworkConfig" },
        @{ Path = Join-Path $ModulePath "WindowsFeatures\WindowsFeatures.psm1"; Name = "WindowsFeatures" },
        @{ Path = Join-Path $ModulePath "ApplicationConfig\ApplicationConfig.psm1"; Name = "ApplicationConfig" },
        @{ Path = Join-Path $ModulePath "DesktopConfig\DesktopConfig.psm1"; Name = "DesktopConfig" },
        @{ Path = Join-Path $ModulePath "XMLGenerator\XMLGenerator.psm1"; Name = "XMLGenerator" }
    )
    
    foreach ($module in $requiredModules) {
        try {
            if (!(Test-Path $module.Path)) {
                throw "モジュールファイルが見つかりません: $($module.Path)"
            }
            
            Import-Module $module.Path -Force -DisableNameChecking
            Write-Log "モジュールインポート完了: $($module.Name)" "Debug"
        }
        catch {
            Write-Log "モジュールインポートエラー [$($module.Name)]: $_" "Error"
            throw
        }
    }
    
    Write-Log "すべてのモジュールインポート完了" "Info"
}

function Initialize-Directories {
    <#
    .SYNOPSIS
        必要なディレクトリを初期化する
    #>
    
    $directories = @($OutputPath, $LogPath)
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            try {
                New-Item -Path $dir -ItemType Directory -Force | Out-Null
                Write-Log "ディレクトリ作成: $dir" "Debug"
            }
            catch {
                Write-Log "ディレクトリ作成エラー [$dir]: $_" "Error"
                throw
            }
        }
    }
}

function Get-ConfigurationFromFile {
    <#
    .SYNOPSIS
        設定ファイルから設定を読み込む
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath
    )
    
    try {
        Write-Log "設定ファイル読み込み: $FilePath" "Info"
        
        $extension = [System.IO.Path]::GetExtension($FilePath).ToLower()
        
        switch ($extension) {
            ".psd1" {
                $configData = Import-PowerShellDataFile -Path $FilePath
            }
            ".json" {
                $configData = Get-Content -Path $FilePath -Raw | ConvertFrom-Json -AsHashtable
            }
            default {
                throw "サポートされていないファイル形式: $extension"
            }
        }
        
        Write-Log "設定ファイル読み込み完了" "Info"
        return $configData
    }
    catch {
        Write-Log "設定ファイル読み込みエラー: $_" "Error"
        throw
    }
}

function Show-Banner {
    <#
    .SYNOPSIS
        スクリプトのバナーを表示する
    #>
    
    Write-Host @"
===============================================================================
    Windows 11 Sysprep応答ファイル自動生成システム v1.0.0
    Powered by PowerShell 5.x Advanced Features
===============================================================================
"@ -ForegroundColor Cyan
    
    Write-Host "実行日時: $(Get-Date -Format 'yyyy年MM月dd日 HH:mm:ss')" -ForegroundColor Yellow
    Write-Host "実行ユーザー: $env:USERNAME" -ForegroundColor Yellow
    Write-Host "コンピューター名: $env:COMPUTERNAME" -ForegroundColor Yellow
    Write-Host "PowerShellバージョン: $($PSVersionTable.PSVersion)" -ForegroundColor Yellow
    Write-Host ""
}

function Show-Progress {
    <#
    .SYNOPSIS
        進行状況を表示する
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$Activity,
        
        [Parameter(Mandatory = $true)]
        [string]$Status,
        
        [Parameter(Mandatory = $true)]
        [int]$PercentComplete
    )
    
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $PercentComplete
    Write-Log "$Activity - $Status ($PercentComplete%)" "Debug"
}

function Confirm-OutputPath {
    <#
    .SYNOPSIS
        出力パスの確認と設定
    #>
    param(
        [Parameter(Mandatory = $false)]
        [string]$Path
    )
    
    if ([string]::IsNullOrWhiteSpace($Path)) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $Path = Join-Path $Script:OutputPath "unattend_$timestamp.xml"
    }
    
    # 既存ファイルの確認
    if ((Test-Path $Path) -and !$Force) {
        if ($Interactive) {
            $response = Read-Host "ファイルが既に存在します。上書きしますか？ (y/N)"
            if ($response -ne "y" -and $response -ne "Y") {
                throw "処理が中断されました"
            }
        } else {
            throw "出力ファイルが既に存在します: $Path (上書きする場合は -Force パラメータを使用)"
        }
    }
    
    return $Path
}

#endregion

#region Main Functions

function Invoke-UnattendXMLGeneration {
    <#
    .SYNOPSIS
        UnattendXML生成のメイン処理
    #>
    param(
        [Parameter(Mandatory = $true)]
        [object]$Config,
        
        [Parameter(Mandatory = $true)]
        [string]$OutputFilePath
    )
    
    try {
        Write-Log "UnattendXML生成開始" "Info"
        Show-Progress -Activity "UnattendXML生成" -Status "初期化中..." -PercentComplete 0
        
        # メインモジュールのインポート
        Import-Module (Join-Path $ScriptRoot "Generate-UnattendXML.psm1") -Force -DisableNameChecking
        
        Show-Progress -Activity "UnattendXML生成" -Status "設定検証中..." -PercentComplete 10
        
        # XML生成器の初期化
        $generator = [UnattendXMLGenerator]::new($Config)
        
        if ($WhatIf) {
            Write-Log "WhatIfモード: 実際の生成は行わず、処理内容のみ表示" "Info"
            
            Write-Host "=== 生成予定の設定内容 ===" -ForegroundColor Yellow
            Write-Host "ホスト名: $($Config.System.HostName)" -ForegroundColor White
            Write-Host "ユーザー数: $($Config.Users.Count)" -ForegroundColor White
            Write-Host "IPv6無効化: $($Config.System.DisableIPv6)" -ForegroundColor White
            Write-Host "Firewall無効化: $($Config.System.DisableFirewall)" -ForegroundColor White
            Write-Host "出力先: $OutputFilePath" -ForegroundColor White
            Write-Host "==========================" -ForegroundColor Yellow
            
            return $OutputFilePath
        }
        
        Show-Progress -Activity "UnattendXML生成" -Status "XML生成中..." -PercentComplete 50
        
        # XML生成実行
        $result = New-UnattendXML -Config $Config -OutputPath $OutputFilePath
        
        Show-Progress -Activity "UnattendXML生成" -Status "検証中..." -PercentComplete 80
        
        # 生成されたXMLの検証
        $validation = Test-UnattendXMLDocument -XmlPath $result
        
        if (!$validation.IsValid) {
            Write-Log "生成されたXMLに検証エラーがあります" "Warning"
            foreach ($error in $validation.ValidationErrors) {
                Write-Log "検証エラー: $error" "Warning"
            }
        }
        
        Show-Progress -Activity "UnattendXML生成" -Status "完了" -PercentComplete 100
        Write-Progress -Activity "UnattendXML生成" -Completed
        
        Write-Log "UnattendXML生成完了: $result" "Info"
        return $result
    }
    catch {
        Write-Log "UnattendXML生成エラー: $_" "Error"
        Write-Progress -Activity "UnattendXML生成" -Completed
        throw
    }
}

function Invoke-InteractiveWizard {
    <#
    .SYNOPSIS
        対話的なウィザードを実行
    #>
    
    try {
        Write-Log "対話的ウィザード開始" "Info"
        
        # メインモジュールのインポート
        Import-Module (Join-Path $ScriptRoot "Generate-UnattendXML.psm1") -Force -DisableNameChecking
        
        # ウィザード実行
        Start-UnattendXMLWizard
        
        Write-Log "対話的ウィザード完了" "Info"
    }
    catch {
        Write-Log "対話的ウィザードエラー: $_" "Error"
        throw
    }
}

function Invoke-ValidationOnly {
    <#
    .SYNOPSIS
        XMLファイルの検証のみ実行
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$XmlPath
    )
    
    try {
        Write-Log "XML検証のみモード開始: $XmlPath" "Info"
        
        if (!(Test-Path $XmlPath)) {
            throw "検証対象のXMLファイルが見つかりません: $XmlPath"
        }
        
        # XML検証実行
        $result = Test-UnattendXMLDocument -XmlPath $XmlPath
        
        # 結果表示
        Write-Host ""
        Write-Host "=== 検証結果 ===" -ForegroundColor Cyan
        Write-Host "ファイル: $XmlPath" -ForegroundColor Yellow
        Write-Host "検証結果: $(if ($result.IsValid) { '✓ 成功' } else { '✗ 失敗' })" -ForegroundColor $(if ($result.IsValid) { 'Green' } else { 'Red' })
        
        if ($result.ValidationErrors.Count -gt 0) {
            Write-Host "エラー:" -ForegroundColor Red
            foreach ($error in $result.ValidationErrors) {
                Write-Host "  - $error" -ForegroundColor Red
            }
        }
        
        if ($result.ValidationWarnings.Count -gt 0) {
            Write-Host "警告:" -ForegroundColor Yellow
            foreach ($warning in $result.ValidationWarnings) {
                Write-Host "  - $warning" -ForegroundColor Yellow
            }
        }
        
        Write-Host "================" -ForegroundColor Cyan
        
        Write-Log "XML検証完了" "Info"
        return $result.IsValid
    }
    catch {
        Write-Log "XML検証エラー: $_" "Error"
        throw
    }
}

#endregion

#region Main Execution

try {
    # バナー表示
    Show-Banner
    
    # ディレクトリ初期化
    Initialize-Directories
    
    # ログ開始
    Write-Log "=== スクリプト実行開始 ===" "Info"
    Write-Log "パラメーターセット: $($PSCmdlet.ParameterSetName)" "Info"
    Write-Log "ログレベル: $LogLevel" "Info"
    
    # 必要なモジュールインポート
    Import-RequiredModules
    
    # パラメーターセットに応じた処理実行
    switch ($PSCmdlet.ParameterSetName) {
        "Interactive" {
            Write-Log "対話的ウィザードモードで実行" "Info"
            Invoke-InteractiveWizard
        }
        
        "ValidateOnly" {
            Write-Log "検証のみモードで実行" "Info"
            $validationPath = if ([string]::IsNullOrWhiteSpace($OutputPath)) { 
                Read-Host "検証するXMLファイルのパスを入力してください"
            } else { 
                $OutputPath 
            }
            
            $isValid = Invoke-ValidationOnly -XmlPath $validationPath
            $exitCode = if ($isValid) { 0 } else { 1 }
            exit $exitCode
        }
        
        "Preset" {
            Write-Log "プリセットモードで実行: $PresetName" "Info"
            
            # プリセット設定の読み込み
            $config = Import-UnattendPreset -PresetName $PresetName
            
            # 出力パス確認
            $finalOutputPath = Confirm-OutputPath -Path $OutputPath
            
            # XML生成実行
            $result = Invoke-UnattendXMLGeneration -Config $config -OutputFilePath $finalOutputPath
            
            Write-Host ""
            Write-Host "=== 生成完了 ===" -ForegroundColor Green
            Write-Host "プリセット: $PresetName" -ForegroundColor Yellow
            Write-Host "出力ファイル: $result" -ForegroundColor Yellow
            Write-Host "ログファイル: $Script:LogFile" -ForegroundColor Yellow
            Write-Host "===============" -ForegroundColor Green
        }
        
        "ConfigFile" {
            Write-Log "設定ファイルモードで実行: $ConfigFile" "Info"
            
            # 設定ファイルの読み込み
            $configData = Get-ConfigurationFromFile -FilePath $ConfigFile
            
            # 設定オブジェクトの作成
            $config = [UnattendGeneratorConfig]::new()
            
            # 設定データの適用（簡略化された例）
            if ($configData.ContainsKey("System")) {
                foreach ($prop in $configData.System.Keys) {
                    if ($config.System.PSObject.Properties.Name -contains $prop) {
                        $config.System.$prop = $configData.System[$prop]
                    }
                }
            }
            
            # 出力パス確認
            $finalOutputPath = Confirm-OutputPath -Path $OutputPath
            
            # XML生成実行
            $result = Invoke-UnattendXMLGeneration -Config $config -OutputFilePath $finalOutputPath
            
            Write-Host ""
            Write-Host "=== 生成完了 ===" -ForegroundColor Green
            Write-Host "設定ファイル: $ConfigFile" -ForegroundColor Yellow
            Write-Host "出力ファイル: $result" -ForegroundColor Yellow
            Write-Host "ログファイル: $Script:LogFile" -ForegroundColor Yellow
            Write-Host "===============" -ForegroundColor Green
        }
    }
    
    Write-Log "=== スクリプト実行完了 ===" "Info"
    
    # 成功終了
    exit 0
}
catch {
    Write-Log "=== スクリプト実行エラー ===" "Critical"
    Write-Log "エラー詳細: $_" "Critical"
    Write-Log "スタックトレース: $($_.ScriptStackTrace)" "Debug"
    
    Write-Host ""
    Write-Host "=== エラーが発生しました ===" -ForegroundColor Red
    Write-Host "エラー: $_" -ForegroundColor Red
    Write-Host "ログファイルで詳細を確認してください: $Script:LogFile" -ForegroundColor Yellow
    Write-Host "=========================" -ForegroundColor Red
    
    # エラー終了
    exit 1
}
finally {
    # クリーンアップ処理
    if ($null -ne $ProgressPreference) {
        Write-Progress -Activity "UnattendXML生成" -Completed
    }
    
    Write-Log "スクリプト終了処理完了" "Debug"
}

#endregion