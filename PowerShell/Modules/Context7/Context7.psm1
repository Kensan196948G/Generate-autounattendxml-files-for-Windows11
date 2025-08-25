<#
.SYNOPSIS
    Context7設定管理エンジン for PowerShell
    
.DESCRIPTION
    設定の最適化、検証、コンテキスト管理を行う高度な設定エンジン
#>

Export-ModuleMember -Function @(
    'Optimize-Context7Config'
    'Validate-Context7Config'
    'Merge-Context7Configs'
    'Export-Context7Config'
    'Import-Context7Config'
)

# コンテキスト定義
$script:Context7Rules = @{
    Enterprise = @{
        Priority = 1
        Rules = @{
            DisableTelemetry = $true
            DisableConsumerFeatures = $true
            DisableCortana = $true
            JoinDomain = $true
            DisableWindowsStore = $false
            EnableBitLocker = $true
        }
    }
    
    Development = @{
        Priority = 2
        Rules = @{
            EnableHyperV = $true
            EnableWSL = $true
            EnableWSL2 = $true
            EnableSandbox = $true
            EnableDeveloperMode = $true
            InstallDotNet = $true
        }
    }
    
    Education = @{
        Priority = 3
        Rules = @{
            DisableGameBar = $true
            DisableWindowsStore = $true
            EnableParentalControls = $true
            LimitUserPrivileges = $true
        }
    }
    
    HomeUse = @{
        Priority = 4
        Rules = @{
            EnableMediaFeatures = $true
            EnableGameMode = $true
            DisableTelemetry = $false
            EnableCortana = $true
        }
    }
    
    Security = @{
        Priority = 5
        Rules = @{
            EnableWDAC = $true
            EnableBitLocker = $true
            DisableUSB = $true
            RequireSmartCard = $false
            EnableAuditMode = $true
        }
    }
    
    Performance = @{
        Priority = 6
        Rules = @{
            DisableVisualEffects = $true
            DisableSearchIndexing = $true
            DisableSuperfetch = $true
            OptimizeForSSD = $true
        }
    }
    
    Minimal = @{
        Priority = 7
        Rules = @{
            RemoveAllApps = $true
            DisableAllTelemetry = $true
            MinimalServices = $true
        }
    }
}

function Optimize-Context7Config {
    <#
    .SYNOPSIS
        Context7エンジンによる設定の最適化
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object]$Config,
        
        [Parameter()]
        [string[]]$Contexts = @(),
        
        [Parameter()]
        [switch]$AutoDetect = $true
    )
    
    Write-Verbose "Context7: 設定の最適化を開始"
    
    # コンテキストの自動検出
    if ($AutoDetect -and $Contexts.Count -eq 0) {
        $Contexts = Detect-OptimalContext -Config $Config
    }
    
    # 最適化ルールの適用
    foreach ($contextName in $Contexts) {
        if ($script:Context7Rules.ContainsKey($contextName)) {
            $context = $script:Context7Rules[$contextName]
            Write-Verbose "Context7: コンテキスト '$contextName' を適用中"
            
            $Config = Apply-ContextRules -Config $Config -Rules $context.Rules
        }
    }
    
    # 設定の整合性チェック
    $Config = Resolve-ConfigConflicts -Config $Config
    
    # パフォーマンス最適化
    $Config = Optimize-Performance -Config $Config
    
    Write-Verbose "Context7: 設定の最適化完了"
    
    return $Config
}

function Detect-OptimalContext {
    <#
    .SYNOPSIS
        設定から最適なコンテキストを自動検出
    #>
    param(
        [object]$Config
    )
    
    $detectedContexts = @()
    
    # ドメイン参加設定がある場合はEnterprise
    if ($Config.ComputerSettings.JoinDomain) {
        $detectedContexts += "Enterprise"
    }
    
    # 仮想化機能が有効な場合はDevelopment
    if ($Config.VMSupport.EnableHyperV -or $Config.VMSupport.EnableWSL) {
        $detectedContexts += "Development"
    }
    
    # パフォーマンスモードが設定されている場合
    if ($Config.VisualEffects.PerformanceMode -eq "BestPerformance") {
        $detectedContexts += "Performance"
    }
    
    # セキュリティ設定が厳格な場合
    if ($Config.WDAC.Enabled -or $Config.SystemTweaks.DisableUSB) {
        $detectedContexts += "Security"
    }
    
    # デフォルトコンテキスト
    if ($detectedContexts.Count -eq 0) {
        $detectedContexts = @("HomeUse")
    }
    
    Write-Verbose "Context7: 検出されたコンテキスト: $($detectedContexts -join ', ')"
    
    return $detectedContexts
}

function Apply-ContextRules {
    <#
    .SYNOPSIS
        コンテキストルールを設定に適用
    #>
    param(
        [object]$Config,
        [hashtable]$Rules
    )
    
    foreach ($rule in $Rules.GetEnumerator()) {
        switch ($rule.Key) {
            "DisableTelemetry" {
                if ($rule.Value) {
                    $Config.SystemTweaks.DisableTelemetry = $true
                    $Config.ExpressSettings.SendDiagnosticData = $false
                }
            }
            
            "EnableHyperV" {
                if ($rule.Value) {
                    $Config.VMSupport.EnableHyperV = $true
                    $Config.VMSupport.EnableVirtualization = $true
                }
            }
            
            "EnableWSL" {
                if ($rule.Value) {
                    $Config.VMSupport.EnableWSL = $true
                    $Config.VMSupport.EnableWSL2 = $true
                }
            }
            
            "DisableVisualEffects" {
                if ($rule.Value) {
                    $Config.VisualEffects.PerformanceMode = "BestPerformance"
                    $Config.VisualEffects.Transparency = $false
                    $Config.VisualEffects.Animations = $false
                }
            }
            
            "EnableWDAC" {
                if ($rule.Value) {
                    $Config.WDAC.Enabled = $true
                    $Config.WDAC.PolicyMode = "Enforced"
                }
            }
            
            "RemoveAllApps" {
                if ($rule.Value) {
                    # より多くのアプリを削除リストに追加
                    $Config.RemoveApps.Apps += @(
                        "Microsoft.Xbox*"
                        "Microsoft.SkypeApp"
                        "Microsoft.MixedReality*"
                        "Microsoft.Microsoft3DViewer"
                    )
                }
            }
        }
    }
    
    return $Config
}

function Resolve-ConfigConflicts {
    <#
    .SYNOPSIS
        設定の競合を解決
    #>
    param(
        [object]$Config
    )
    
    # Hyper-VとWSL2の依存関係
    if ($Config.VMSupport.EnableWSL2 -and -not $Config.VMSupport.EnableVirtualization) {
        Write-Warning "Context7: WSL2にはVirtualizationが必要です。自動的に有効化します。"
        $Config.VMSupport.EnableVirtualization = $true
    }
    
    # ドメイン参加とワークグループの競合
    if ($Config.ComputerSettings.JoinDomain) {
        $Config.ComputerSettings.Workgroup = ""
    }
    
    # パフォーマンスモードと視覚効果の調整
    if ($Config.VisualEffects.PerformanceMode -eq "BestPerformance") {
        $Config.VisualEffects.Transparency = $false
        $Config.VisualEffects.Animations = $false
        $Config.VisualEffects.Shadows = $false
    }
    
    # セキュリティ設定の整合性
    if ($Config.WDAC.Enabled -and $Config.WDAC.PolicyMode -eq "Enforced") {
        # 厳格モードではストアアプリを制限
        $Config.WDAC.AllowStoreApps = $false
    }
    
    return $Config
}

function Optimize-Performance {
    <#
    .SYNOPSIS
        パフォーマンス最適化
    #>
    param(
        [object]$Config
    )
    
    # 不要なサービスの無効化リスト
    $unnecessaryServices = @(
        "XboxGipSvc"
        "XblAuthManager"
        "XblGameSave"
        "XboxNetApiSvc"
    )
    
    # カスタムスクリプトに追加
    if ($Config.SystemTweaks.DisableGameBar) {
        foreach ($service in $unnecessaryServices) {
            $Config.CustomScripts.FirstLogon += @{
                Order = 100
                Command = "sc config `"$service`" start=disabled"
                Description = "Disable $service"
                RequiresRestart = $false
            }
        }
    }
    
    return $Config
}

function Validate-Context7Config {
    <#
    .SYNOPSIS
        設定の検証
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object]$Config
    )
    
    $validationResults = @{
        IsValid = $true
        Errors = @()
        Warnings = @()
        Info = @()
    }
    
    # 必須項目のチェック
    if (-not $Config.WindowsEdition.ProductKey) {
        $validationResults.Warnings += "プロダクトキーが設定されていません"
    }
    
    if ($Config.UserAccounts.Accounts.Count -eq 0) {
        $validationResults.Errors += "少なくとも1つのユーザーアカウントが必要です"
        $validationResults.IsValid = $false
    }
    
    # パスワードポリシーのチェック
    foreach ($account in $Config.UserAccounts.Accounts) {
        if ($account.Password.Length -lt 8) {
            $validationResults.Warnings += "ユーザー '$($account.Name)' のパスワードが短すぎます"
        }
    }
    
    # ディスク構成の検証
    if ($Config.DiskConfig.PartitionStyle -eq "GPT" -and $Config.Architecture -eq "x86") {
        $validationResults.Warnings += "32ビットシステムでGPTを使用することは推奨されません"
    }
    
    # Wi-Fi設定の検証
    if ($Config.WiFiSettings.SetupMode -eq "configure" -and -not $Config.WiFiSettings.SSID) {
        $validationResults.Errors += "Wi-Fi設定が有効ですがSSIDが指定されていません"
        $validationResults.IsValid = $false
    }
    
    return $validationResults
}

function Merge-Context7Configs {
    <#
    .SYNOPSIS
        複数の設定をマージ
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object]$BaseConfig,
        
        [Parameter(Mandatory)]
        [object]$OverrideConfig,
        
        [Parameter()]
        [switch]$DeepMerge = $true
    )
    
    if ($DeepMerge) {
        return Merge-DeepConfig -Base $BaseConfig -Override $OverrideConfig
    }
    else {
        # 浅いマージ（プロパティレベル）
        foreach ($property in $OverrideConfig.PSObject.Properties) {
            $BaseConfig.$($property.Name) = $property.Value
        }
        return $BaseConfig
    }
}

function Merge-DeepConfig {
    <#
    .SYNOPSIS
        設定の深いマージ
    #>
    param(
        [object]$Base,
        [object]$Override
    )
    
    foreach ($property in $Override.PSObject.Properties) {
        $propertyName = $property.Name
        $overrideValue = $property.Value
        
        if ($null -eq $overrideValue) {
            continue
        }
        
        if ($Base.PSObject.Properties[$propertyName]) {
            $baseValue = $Base.$propertyName
            
            if ($overrideValue -is [hashtable] -and $baseValue -is [hashtable]) {
                # ハッシュテーブルの再帰的マージ
                foreach ($key in $overrideValue.Keys) {
                    $baseValue[$key] = $overrideValue[$key]
                }
            }
            elseif ($overrideValue -is [array]) {
                # 配列の場合は置き換え
                $Base.$propertyName = $overrideValue
            }
            else {
                # その他の値は上書き
                $Base.$propertyName = $overrideValue
            }
        }
        else {
            # 新しいプロパティを追加
            $Base | Add-Member -MemberType NoteProperty -Name $propertyName -Value $overrideValue -Force
        }
    }
    
    return $Base
}

function Export-Context7Config {
    <#
    .SYNOPSIS
        設定をファイルにエクスポート
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object]$Config,
        
        [Parameter(Mandatory)]
        [string]$Path,
        
        [Parameter()]
        [ValidateSet("JSON", "PSD1", "XML")]
        [string]$Format = "JSON"
    )
    
    switch ($Format) {
        "JSON" {
            $Config | ConvertTo-Json -Depth 10 | Out-File -FilePath $Path -Encoding UTF8
        }
        
        "PSD1" {
            $psd1Content = ConvertTo-PSD1String -Object $Config
            $psd1Content | Out-File -FilePath $Path -Encoding UTF8
        }
        
        "XML" {
            $xmlContent = ConvertTo-Xml -InputObject $Config -Depth 10 -As String
            $xmlContent | Out-File -FilePath $Path -Encoding UTF8
        }
    }
    
    Write-Verbose "Context7: 設定を $Format 形式で $Path にエクスポート"
}

function Import-Context7Config {
    <#
    .SYNOPSIS
        ファイルから設定をインポート
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )
    
    if (-not (Test-Path $Path)) {
        throw "設定ファイルが見つかりません: $Path"
    }
    
    $extension = [System.IO.Path]::GetExtension($Path).ToLower()
    
    switch ($extension) {
        ".json" {
            $content = Get-Content $Path -Raw
            return $content | ConvertFrom-Json
        }
        
        ".psd1" {
            return Import-PowerShellDataFile $Path
        }
        
        ".xml" {
            [xml]$xml = Get-Content $Path
            return Convert-XmlToObject -Xml $xml
        }
        
        default {
            throw "サポートされていないファイル形式: $extension"
        }
    }
}

# ヘルパー関数

function ConvertTo-PSD1String {
    param([object]$Object)
    
    # オブジェクトをPSD1形式の文字列に変換
    # 簡略化された実装
    return "@{`n" + ($Object | Out-String) + "`n}"
}

function Convert-XmlToObject {
    param([xml]$Xml)
    
    # XMLをオブジェクトに変換
    # 簡略化された実装
    return $Xml.DocumentElement
}

# エクスポート
Export-ModuleMember -Function @(
    'Get-Context7Detection',
    'Optimize-Context7Config',
    'Validate-Context7Config',
    'Resolve-Context7Conflict',
    'Get-Context7Priority',
    'ConvertTo-PSD1String',
    'Convert-XmlToObject'
) -Variable @() -Cmdlet @() -Alias @()