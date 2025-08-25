<#
.SYNOPSIS
    Claude-flow並列処理エンジン for PowerShell
    
.DESCRIPTION
    42体のSubAgentを効率的に並列実行するための処理エンジン
    マルチスレッド/ランスペースによる高速処理を実現
#>

# エクスポート関数
Export-ModuleMember -Function @(
    'Start-ClaudeFlow'
    'New-ParallelJob'
    'Wait-ParallelJob'
    'Get-ParallelResults'
    'Stop-ClaudeFlow'
)

# グローバル変数
$script:RunspacePool = $null
$script:Jobs = @()
$script:MaxThreads = [Environment]::ProcessorCount * 2

function Start-ClaudeFlow {
    <#
    .SYNOPSIS
        Claude-flow並列処理エンジンを初期化
    #>
    [CmdletBinding()]
    param(
        [Parameter()]
        [int]$MaxThreads = $script:MaxThreads,
        
        [Parameter()]
        [switch]$EnableLogging = $true
    )
    
    Write-Verbose "Claude-flow並列処理エンジンを初期化中..."
    
    # ランスペースプールの作成
    $sessionState = [System.Management.Automation.Runspaces.InitialSessionState]::CreateDefault()
    
    # 必要なモジュールをセッション状態に追加
    $modulePaths = @(
        "$PSScriptRoot\..\SubAgentLoader\SubAgentLoader.psm1"
        "$PSScriptRoot\..\Context7\Context7.psm1"
    )
    
    foreach ($modulePath in $modulePaths) {
        if (Test-Path $modulePath) {
            $sessionState.ImportPSModule($modulePath)
        }
    }
    
    $script:RunspacePool = [runspacefactory]::CreateRunspacePool(1, $MaxThreads, $sessionState, $Host)
    $script:RunspacePool.Open()
    
    if ($EnableLogging) {
        Write-Information "Claude-flow: 最大 $MaxThreads スレッドで並列処理を開始" -InformationAction Continue
    }
    
    return @{
        Status = "Initialized"
        MaxThreads = $MaxThreads
        RunspacePool = $script:RunspacePool
    }
}

function New-ParallelJob {
    <#
    .SYNOPSIS
        並列ジョブを作成して実行
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [scriptblock]$ScriptBlock,
        
        [Parameter()]
        [hashtable]$Parameters = @{},
        
        [Parameter()]
        [string]$JobName = "ParallelJob_$(Get-Random)",
        
        [Parameter()]
        [string]$Category = "General"
    )
    
    if (-not $script:RunspacePool) {
        throw "Claude-flowが初期化されていません。Start-ClaudeFlowを実行してください。"
    }
    
    # PowerShellインスタンスの作成
    $powershell = [powershell]::Create()
    $powershell.RunspacePool = $script:RunspacePool
    
    # スクリプトブロックと引数の追加
    [void]$powershell.AddScript($ScriptBlock)
    
    foreach ($param in $Parameters.GetEnumerator()) {
        [void]$powershell.AddParameter($param.Key, $param.Value)
    }
    
    # 非同期実行の開始
    $handle = $powershell.BeginInvoke()
    
    # ジョブ情報の保存
    $job = @{
        Name = $JobName
        Category = $Category
        PowerShell = $powershell
        Handle = $handle
        StartTime = Get-Date
        Status = "Running"
    }
    
    $script:Jobs += $job
    
    Write-Verbose "並列ジョブ '$JobName' (カテゴリ: $Category) を開始"
    
    return $job
}

function Wait-ParallelJob {
    <#
    .SYNOPSIS
        並列ジョブの完了を待機
    #>
    [CmdletBinding()]
    param(
        [Parameter()]
        [array]$Jobs = $script:Jobs,
        
        [Parameter()]
        [int]$TimeoutSeconds = 300,
        
        [Parameter()]
        [switch]$ShowProgress = $true
    )
    
    $startTime = Get-Date
    $timeout = New-TimeSpan -Seconds $TimeoutSeconds
    
    while ($true) {
        $runningJobs = $Jobs | Where-Object { $_.Status -eq "Running" }
        
        if ($runningJobs.Count -eq 0) {
            break
        }
        
        if ($ShowProgress) {
            $completed = ($Jobs | Where-Object { $_.Status -eq "Completed" }).Count
            $total = $Jobs.Count
            $percentComplete = if ($total -gt 0) { ($completed / $total) * 100 } else { 0 }
            
            Write-Progress -Activity "Claude-flow並列処理" `
                          -Status "$completed / $total ジョブ完了" `
                          -PercentComplete $percentComplete
        }
        
        # タイムアウトチェック
        if ((Get-Date) - $startTime -gt $timeout) {
            Write-Warning "並列処理がタイムアウトしました（$TimeoutSeconds 秒）"
            break
        }
        
        # 完了したジョブのチェック
        foreach ($job in $runningJobs) {
            if ($job.Handle.IsCompleted) {
                $job.Status = "Completed"
                $job.EndTime = Get-Date
                $job.Duration = $job.EndTime - $job.StartTime
                Write-Verbose "ジョブ '$($job.Name)' が完了 (所要時間: $($job.Duration))"
            }
        }
        
        Start-Sleep -Milliseconds 100
    }
    
    if ($ShowProgress) {
        Write-Progress -Activity "Claude-flow並列処理" -Completed
    }
}

function Get-ParallelResults {
    <#
    .SYNOPSIS
        並列ジョブの結果を取得
    #>
    [CmdletBinding()]
    param(
        [Parameter()]
        [array]$Jobs = $script:Jobs,
        
        [Parameter()]
        [switch]$IncludeErrors = $true
    )
    
    $results = @{}
    
    foreach ($job in $Jobs) {
        try {
            if ($job.Status -eq "Completed" -or $job.Handle.IsCompleted) {
                $result = $job.PowerShell.EndInvoke($job.Handle)
                $results[$job.Name] = @{
                    Success = $true
                    Result = $result
                    Category = $job.Category
                    Duration = $job.Duration
                }
            }
            elseif ($job.Status -eq "Running") {
                $results[$job.Name] = @{
                    Success = $false
                    Error = "ジョブはまだ実行中です"
                    Category = $job.Category
                }
            }
        }
        catch {
            if ($IncludeErrors) {
                $results[$job.Name] = @{
                    Success = $false
                    Error = $_.Exception.Message
                    Category = $job.Category
                }
            }
        }
        finally {
            # リソースのクリーンアップ
            if ($job.PowerShell) {
                $job.PowerShell.Dispose()
            }
        }
    }
    
    return $results
}

function Stop-ClaudeFlow {
    <#
    .SYNOPSIS
        Claude-flow並列処理エンジンを停止
    #>
    [CmdletBinding()]
    param(
        [Parameter()]
        [switch]$Force = $false
    )
    
    Write-Verbose "Claude-flow並列処理エンジンを停止中..."
    
    # 実行中のジョブを停止
    if ($Force) {
        foreach ($job in $script:Jobs | Where-Object { $_.Status -eq "Running" }) {
            try {
                $job.PowerShell.Stop()
                $job.Status = "Cancelled"
                Write-Verbose "ジョブ '$($job.Name)' を強制停止"
            }
            catch {
                Write-Warning "ジョブ '$($job.Name)' の停止に失敗: $_"
            }
        }
    }
    
    # ランスペースプールのクリーンアップ
    if ($script:RunspacePool) {
        $script:RunspacePool.Close()
        $script:RunspacePool.Dispose()
        $script:RunspacePool = $null
    }
    
    # ジョブリストのクリア
    $script:Jobs = @()
    
    Write-Information "Claude-flow: 並列処理エンジンを停止しました" -InformationAction Continue
}

# 高度な並列処理機能

function Invoke-ParallelForEach {
    <#
    .SYNOPSIS
        コレクションに対して並列ForEach処理を実行
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [array]$InputObject,
        
        [Parameter(Mandatory)]
        [scriptblock]$ScriptBlock,
        
        [Parameter()]
        [int]$ThrottleLimit = $script:MaxThreads,
        
        [Parameter()]
        [hashtable]$SharedVariables = @{}
    )
    
    # Claude-flowの初期化（必要な場合）
    if (-not $script:RunspacePool) {
        Start-ClaudeFlow -MaxThreads $ThrottleLimit
    }
    
    $jobs = @()
    
    foreach ($item in $InputObject) {
        $params = @{
            Item = $item
            Shared = $SharedVariables
        }
        
        $job = New-ParallelJob -ScriptBlock $ScriptBlock -Parameters $params -JobName "ForEach_$($InputObject.IndexOf($item))"
        $jobs += $job
    }
    
    # 完了を待機
    Wait-ParallelJob -Jobs $jobs
    
    # 結果の取得
    $results = Get-ParallelResults -Jobs $jobs
    
    return $results.Values | ForEach-Object { $_.Result }
}

function New-ParallelPipeline {
    <#
    .SYNOPSIS
        並列パイプライン処理を作成
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [array]$Stages,
        
        [Parameter()]
        [hashtable]$InitialData = @{}
    )
    
    $pipelineResults = @{}
    $currentData = $InitialData
    
    foreach ($stage in $Stages) {
        Write-Verbose "パイプラインステージ '$($stage.Name)' を実行中..."
        
        if ($stage.Parallel) {
            # 並列実行
            $jobs = @()
            foreach ($task in $stage.Tasks) {
                $params = @{
                    InputData = $currentData
                    StageConfig = $stage.Config
                }
                
                $job = New-ParallelJob -ScriptBlock $task.ScriptBlock `
                                       -Parameters $params `
                                       -JobName "$($stage.Name)_$($task.Name)" `
                                       -Category $stage.Name
                $jobs += $job
            }
            
            Wait-ParallelJob -Jobs $jobs
            $results = Get-ParallelResults -Jobs $jobs
            
            # 結果の統合
            $stageOutput = @{}
            foreach ($result in $results.GetEnumerator()) {
                if ($result.Value.Success) {
                    $stageOutput += $result.Value.Result
                }
            }
            
            $pipelineResults[$stage.Name] = $stageOutput
            $currentData = $stageOutput
        }
        else {
            # 順次実行
            foreach ($task in $stage.Tasks) {
                $result = & $task.ScriptBlock -InputData $currentData -StageConfig $stage.Config
                $currentData = $result
            }
            $pipelineResults[$stage.Name] = $currentData
        }
    }
    
    return $pipelineResults
}

# ヘルパー関数

function Test-ClaudeFlowStatus {
    <#
    .SYNOPSIS
        Claude-flowの状態を確認
    #>
    [CmdletBinding()]
    param()
    
    $status = @{
        Initialized = $null -ne $script:RunspacePool
        RunspacePoolState = if ($script:RunspacePool) { $script:RunspacePool.RunspacePoolStateInfo.State } else { "NotInitialized" }
        ActiveJobs = ($script:Jobs | Where-Object { $_.Status -eq "Running" }).Count
        CompletedJobs = ($script:Jobs | Where-Object { $_.Status -eq "Completed" }).Count
        TotalJobs = $script:Jobs.Count
        MaxThreads = $script:MaxThreads
    }
    
    return $status
}

function Clear-CompletedJobs {
    <#
    .SYNOPSIS
        完了したジョブをクリア
    #>
    [CmdletBinding()]
    param()
    
    $completed = $script:Jobs | Where-Object { $_.Status -eq "Completed" }
    
    foreach ($job in $completed) {
        if ($job.PowerShell) {
            $job.PowerShell.Dispose()
        }
    }
    
    $script:Jobs = $script:Jobs | Where-Object { $_.Status -ne "Completed" }
    
    Write-Verbose "$($completed.Count) 個の完了ジョブをクリアしました"
}

# エクスポート
Export-ModuleMember -Function @(
    'Start-ClaudeFlow',
    'Stop-ClaudeFlow',
    'New-ParallelJob',
    'Wait-ParallelJob',
    'Get-ParallelResults',
    'Get-ClaudeFlowStatus',
    'Clear-CompletedJobs'
) -Variable @() -Cmdlet @() -Alias @()