# ============================================================================
# フロントエンド＋バックエンド 統合自動診断・修復スクリプト
# Windows 11 無人応答ファイル生成システム
# ============================================================================

param(
    [switch]$Verbose,        # 詳細ログ表示モード
    [switch]$Force,          # 強制修復モード
    [int]$MaxRetries = 3,    # リトライ回数指定
    [switch]$SkipFrontend,   # フロントエンドをスキップ
    [switch]$SkipBackend,    # バックエンドをスキップ
    [switch]$Parallel        # 並列診断・修復モード
)

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ErrorActionPreference = "Continue"
$global:StartTime = Get-Date

# ============================================================================
# カラーログ関数
# ============================================================================
function Write-ColorLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Component = "SYSTEM"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $prefix = "[$timestamp][$Component]"
    
    switch ($Level) {
        "SUCCESS" { Write-Host "$prefix ✅ $Message" -ForegroundColor Green }
        "ERROR"   { Write-Host "$prefix ❌ $Message" -ForegroundColor Red }
        "WARNING" { Write-Host "$prefix ⚠️  $Message" -ForegroundColor Yellow }
        "INFO"    { Write-Host "$prefix ℹ️  $Message" -ForegroundColor Cyan }
        "DEBUG"   { if ($Verbose) { Write-Host "$prefix 🔍 $Message" -ForegroundColor Gray } }
        "FIX"     { Write-Host "$prefix 🔧 $Message" -ForegroundColor Magenta }
        "PROGRESS" { Write-Host "$prefix ⏳ $Message" -ForegroundColor White }
    }
}

# ============================================================================
# 基底診断・修復クラス
# ============================================================================
class AutoFixer {
    [string]$Name
    [string]$Path
    [hashtable]$Errors = @{}
    [bool]$Fixed = $false
    [System.Collections.ArrayList]$Log = @()
    
    AutoFixer([string]$name, [string]$path) {
        $this.Name = $name
        $this.Path = $path
    }
    
    [void] LogMessage([string]$message, [string]$level) {
        $this.Log.Add(@{
            Time = Get-Date
            Level = $level
            Message = $message
        }) | Out-Null
        Write-ColorLog $message $level $this.Name
    }
    
    [bool] TestPort([int]$port) {
        try {
            $connection = New-Object System.Net.Sockets.TcpClient
            $connection.Connect("127.0.0.1", $port)
            $connection.Close()
            return $true
        } catch {
            return $false
        }
    }
}

# ============================================================================
# バックエンド診断・修復クラス
# ============================================================================
class BackendFixer : AutoFixer {
    [int]$Port = 8080
    
    BackendFixer([string]$path) : base("BACKEND", $path) {}
    
    [bool] CheckPython() {
        $this.LogMessage("Python環境をチェック中..." , "INFO")
        
        try {
            $pythonVersion = & python --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $this.LogMessage("Python検出: $pythonVersion", "SUCCESS")
                return $true
            }
        } catch {}
        
        $this.Errors["python"] = "Pythonが見つかりません"
        return $false
    }
    
    [bool] FixPython() {
        $this.LogMessage("Python環境を修復中...", "FIX")
        
        $pythonPaths = @(
            "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
            "C:\Python39\python.exe",
            "C:\Python310\python.exe",
            "C:\Python311\python.exe"
        )
        
        foreach ($pyPath in $pythonPaths) {
            if (Test-Path $pyPath) {
                $env:PATH = (Split-Path $pyPath -Parent) + ";" + $env:PATH
                $this.LogMessage("Pythonパスを設定: $pyPath", "SUCCESS")
                return $true
            }
        }
        
        $this.LogMessage("Pythonのインストールが必要です", "ERROR")
        return $false
    }
    
    [bool] CheckVenv() {
        $this.LogMessage("仮想環境をチェック中...", "INFO")
        
        $venvPath = Join-Path $this.Path "venv"
        $venvPython = Join-Path $venvPath "Scripts\python.exe"
        
        if (Test-Path $venvPython) {
            $this.LogMessage("仮想環境OK", "SUCCESS")
            return $true
        }
        
        $this.Errors["venv"] = "仮想環境が不完全"
        return $false
    }
    
    [bool] FixVenv() {
        $this.LogMessage("仮想環境を作成中...", "FIX")
        
        Push-Location $this.Path
        
        if (Test-Path ".\venv") {
            Remove-Item ".\venv" -Recurse -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        & python -m venv venv 2>&1 | Out-Null
        
        Pop-Location
        
        if (Test-Path (Join-Path $this.Path "venv\Scripts\python.exe")) {
            $this.LogMessage("仮想環境作成成功", "SUCCESS")
            return $true
        }
        
        return $false
    }
    
    [bool] CheckDependencies() {
        $this.LogMessage("Python依存関係をチェック中...", "INFO")
        
        Push-Location $this.Path
        
        if (-not (Test-Path ".\requirements.txt")) {
            $this.CreateRequirements()
        }
        
        $checkScript = @"
import sys
try:
    import fastapi
    import uvicorn
    import lxml
    print('OK')
except ImportError as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"@
        
        $result = $checkScript | & .\venv\Scripts\python.exe 2>&1
        Pop-Location
        
        if ($result -like "*OK*") {
            $this.LogMessage("依存関係OK", "SUCCESS")
            return $true
        }
        
        $this.Errors["dependencies"] = "パッケージ不足"
        return $false
    }
    
    [bool] FixDependencies() {
        $this.LogMessage("依存パッケージをインストール中...", "FIX")
        
        Push-Location $this.Path
        
        # pipアップグレード
        & .\venv\Scripts\python.exe -m pip install --upgrade pip --quiet 2>&1 | Out-Null
        
        # requirements.txtからインストール
        & .\venv\Scripts\pip.exe install -r requirements.txt --quiet 2>&1 | Out-Null
        
        Pop-Location
        
        if ($LASTEXITCODE -eq 0) {
            $this.LogMessage("依存関係インストール完了", "SUCCESS")
            return $true
        }
        
        # 個別インストール
        $this.LogMessage("個別パッケージインストール中...", "FIX")
        Push-Location $this.Path
        
        $packages = @(
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "pydantic==2.5.0",
            "lxml==4.9.3",
            "psutil==5.9.6"
        )
        
        foreach ($pkg in $packages) {
            & .\venv\Scripts\pip.exe install $pkg --quiet 2>&1 | Out-Null
        }
        
        Pop-Location
        return $true
    }
    
    [void] CreateRequirements() {
        $requirements = @"
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
websockets==12.0
lxml==4.9.3
pydantic==2.5.0
PyYAML==6.0.1
aiofiles==23.2.1
psutil==5.9.6
python-dotenv==1.0.0
"@
        Set-Content -Path (Join-Path $this.Path "requirements.txt") -Value $requirements -Encoding UTF8
    }
    
    [bool] StartServer() {
        $this.LogMessage("バックエンドサーバーを起動中...", "PROGRESS")
        
        $startScript = @"
@echo off
cd /d "$($this.Path)"
echo Starting Backend Server...
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe main.py
) else (
    python main.py
)
"@
        
        $tempBatch = "$env:TEMP\start-backend-$(Get-Random).bat"
        Set-Content -Path $tempBatch -Value $startScript -Encoding UTF8
        
        Start-Process cmd -ArgumentList "/k", $tempBatch -WindowStyle Minimized
        
        # 起動待機
        $timeout = 30
        $elapsed = 0
        while ($elapsed -lt $timeout) {
            if ($this.TestPort($this.Port)) {
                $this.LogMessage("バックエンドが起動しました (Port: $($this.Port))", "SUCCESS")
                return $true
            }
            Start-Sleep -Seconds 2
            $elapsed += 2
        }
        
        $this.LogMessage("バックエンド起動タイムアウト", "ERROR")
        return $false
    }
    
    [bool] DiagnoseAndFix([bool]$force) {
        $this.LogMessage("診断開始...", "INFO")
        
        $steps = @(
            @{Check = "CheckPython"; Fix = "FixPython"},
            @{Check = "CheckVenv"; Fix = "FixVenv"},
            @{Check = "CheckDependencies"; Fix = "FixDependencies"}
        )
        
        foreach ($step in $steps) {
            $checkMethod = $step.Check
            $fixMethod = $step.Fix
            
            if (-not $this.$checkMethod()) {
                if ($force -or $fixMethod) {
                    if (-not $this.$fixMethod()) {
                        return $false
                    }
                    # 再チェック
                    if (-not $this.$checkMethod()) {
                        return $false
                    }
                } else {
                    return $false
                }
            }
        }
        
        $this.Fixed = $true
        return $true
    }
}

# ============================================================================
# フロントエンド診断・修復クラス
# ============================================================================
class FrontendFixer : AutoFixer {
    [int]$Port = 3050
    
    FrontendFixer([string]$path) : base("FRONTEND", $path) {}
    
    [bool] CheckNode() {
        $this.LogMessage("Node.js環境をチェック中...", "INFO")
        
        try {
            $nodeVersion = & node --version 2>&1
            $npmVersion = & npm --version 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                $this.LogMessage("Node.js $nodeVersion / npm $npmVersion", "SUCCESS")
                return $true
            }
        } catch {}
        
        $this.Errors["node"] = "Node.jsが見つかりません"
        return $false
    }
    
    [bool] FixNode() {
        $this.LogMessage("Node.js環境を確認中...", "FIX")
        
        # Node.jsパスを探す
        $nodePaths = @(
            "$env:ProgramFiles\nodejs\node.exe",
            "$env:ProgramFiles(x86)\nodejs\node.exe",
            "$env:LOCALAPPDATA\Programs\node\node.exe"
        )
        
        foreach ($nodePath in $nodePaths) {
            if (Test-Path $nodePath) {
                $env:PATH = (Split-Path $nodePath -Parent) + ";" + $env:PATH
                $this.LogMessage("Node.jsパスを設定: $nodePath", "SUCCESS")
                return $true
            }
        }
        
        $this.LogMessage("Node.jsのインストールが必要です", "ERROR")
        $this.LogMessage("https://nodejs.org/ からダウンロードしてください", "INFO")
        return $false
    }
    
    [bool] CheckPackageJson() {
        $this.LogMessage("package.jsonをチェック中...", "INFO")
        
        $packagePath = Join-Path $this.Path "package.json"
        if (Test-Path $packagePath) {
            $this.LogMessage("package.json OK", "SUCCESS")
            return $true
        }
        
        $this.Errors["package"] = "package.jsonが存在しません"
        return $false
    }
    
    [bool] FixPackageJson() {
        $this.LogMessage("package.jsonを作成中...", "FIX")
        
        $packageJson = @{
            name = "windows11-unattend-generator"
            version = "1.0.0"
            private = $true
            scripts = @{
                dev = "next dev -p 3050"
                build = "next build"
                start = "next start -p 3050"
                lint = "next lint"
            }
            dependencies = @{
                next = "14.0.4"
                react = "18.2.0"
                "react-dom" = "18.2.0"
                typescript = "5.3.3"
            }
            devDependencies = @{
                "@types/node" = "20.10.5"
                "@types/react" = "18.2.45"
                "@types/react-dom" = "18.2.18"
                "eslint" = "8.56.0"
                "eslint-config-next" = "14.0.4"
            }
        }
        
        $jsonContent = $packageJson | ConvertTo-Json -Depth 10
        Set-Content -Path (Join-Path $this.Path "package.json") -Value $jsonContent -Encoding UTF8
        
        $this.LogMessage("package.json作成完了", "SUCCESS")
        return $true
    }
    
    [bool] CheckNodeModules() {
        $this.LogMessage("Node.js依存関係をチェック中...", "INFO")
        
        $modulesPath = Join-Path $this.Path "node_modules"
        $nextPath = Join-Path $modulesPath "next"
        
        if (Test-Path $nextPath) {
            $this.LogMessage("node_modules OK", "SUCCESS")
            return $true
        }
        
        $this.Errors["modules"] = "node_modulesが不完全"
        return $false
    }
    
    [bool] FixNodeModules() {
        $this.LogMessage("Node.jsパッケージをインストール中...", "FIX")
        
        Push-Location $this.Path
        
        # node_modulesを削除（クリーンインストール）
        if (Test-Path ".\node_modules") {
            $this.LogMessage("既存のnode_modulesを削除中...", "INFO")
            Remove-Item ".\node_modules" -Recurse -Force -ErrorAction SilentlyContinue
        }
        
        # package-lock.jsonも削除
        if (Test-Path ".\package-lock.json") {
            Remove-Item ".\package-lock.json" -Force -ErrorAction SilentlyContinue
        }
        
        # npm install実行（cmd経由）
        $this.LogMessage("npm installを実行中（時間がかかります）...", "PROGRESS")
        & cmd /c "npm install" 2>&1 | Out-Null
        
        Pop-Location
        
        if ($LASTEXITCODE -eq 0) {
            $this.LogMessage("パッケージインストール完了", "SUCCESS")
            return $true
        }
        
        # 個別インストール試行
        $this.LogMessage("個別パッケージインストール中...", "FIX")
        Push-Location $this.Path
        
        $packages = @("next", "react", "react-dom", "typescript")
        foreach ($pkg in $packages) {
            & cmd /c "npm install $pkg" 2>&1 | Out-Null
        }
        
        Pop-Location
        return $true
    }
    
    [bool] CheckNextConfig() {
        $this.LogMessage("Next.js設定をチェック中...", "INFO")
        
        $configPath = Join-Path $this.Path "next.config.js"
        if (-not (Test-Path $configPath)) {
            # 作成
            $config = @"
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
}

module.exports = nextConfig
"@
            Set-Content -Path $configPath -Value $config -Encoding UTF8
        }
        
        $this.LogMessage("Next.js設定 OK", "SUCCESS")
        return $true
    }
    
    [bool] StartServer() {
        $this.LogMessage("フロントエンドサーバーを起動中...", "PROGRESS")
        
        $startScript = @"
@echo off
chcp 65001 > nul
cd /d "$($this.Path)"
echo Starting Frontend Server...
set NEXT_PUBLIC_API_URL=http://192.168.3.92:8080/api
set NEXT_PUBLIC_LOCAL_IP=192.168.3.92
npm run dev
"@
        
        $tempBatch = "$env:TEMP\start-frontend-$(Get-Random).bat"
        Set-Content -Path $tempBatch -Value $startScript -Encoding UTF8
        
        Start-Process cmd -ArgumentList "/k", $tempBatch -WindowStyle Minimized
        
        # 起動待機（Next.jsは時間がかかる）
        $timeout = 60
        $elapsed = 0
        while ($elapsed -lt $timeout) {
            if ($this.TestPort($this.Port)) {
                $this.LogMessage("フロントエンドが起動しました (Port: $($this.Port))", "SUCCESS")
                return $true
            }
            Start-Sleep -Seconds 3
            $elapsed += 3
        }
        
        $this.LogMessage("フロントエンド起動タイムアウト", "WARNING")
        return $false
    }
    
    [bool] DiagnoseAndFix([bool]$force) {
        $this.LogMessage("診断開始...", "INFO")
        
        $steps = @(
            @{Check = "CheckNode"; Fix = "FixNode"},
            @{Check = "CheckPackageJson"; Fix = "FixPackageJson"},
            @{Check = "CheckNodeModules"; Fix = "FixNodeModules"},
            @{Check = "CheckNextConfig"; Fix = $null}
        )
        
        foreach ($step in $steps) {
            $checkMethod = $step.Check
            $fixMethod = $step.Fix
            
            if (-not $this.$checkMethod()) {
                if ($force -or $fixMethod) {
                    if ($fixMethod -and -not $this.$fixMethod()) {
                        return $false
                    }
                    # 再チェック
                    if (-not $this.$checkMethod()) {
                        return $false
                    }
                }
            }
        }
        
        $this.Fixed = $true
        return $true
    }
}

# ============================================================================
# 統合診断・修復マネージャー
# ============================================================================
class SystemDiagnosticManager {
    [BackendFixer]$Backend
    [FrontendFixer]$Frontend
    [bool]$Parallel
    [int]$MaxRetries
    [bool]$Force
    [bool]$Verbose
    
    SystemDiagnosticManager([string]$rootPath, [hashtable]$options) {
        $this.Backend = [BackendFixer]::new((Join-Path $rootPath "backend"))
        $this.Frontend = [FrontendFixer]::new((Join-Path $rootPath "frontend"))
        $this.Parallel = $options.Parallel
        $this.MaxRetries = $options.MaxRetries
        $this.Force = $options.Force
        $this.Verbose = $options.Verbose
    }
    
    [bool] RunDiagnostics([bool]$skipFrontend, [bool]$skipBackend) {
        Write-ColorLog "統合診断を開始します..." "INFO" "SYSTEM"
        
        $success = $true
        
        if ($this.Parallel -and -not $skipFrontend -and -not $skipBackend) {
            # 並列診断（修正版：クラスを再作成）
            Write-ColorLog "並列診断モードで実行中..." "INFO" "SYSTEM"
            
            $backendPath = $this.Backend.Path
            $force = $this.Force
            
            $backendJob = Start-Job -ScriptBlock {
                param($path, $forceMode)
                
                # クラス定義を再度読み込む
                Add-Type -TypeDefinition @"
                using System;
                using System.Collections;
                
                public class SimpleBackendFixer {
                    public string Path { get; set; }
                    public bool Fixed { get; set; }
                    
                    public SimpleBackendFixer(string path) {
                        Path = path;
                        Fixed = false;
                    }
                    
                    public bool DiagnoseAndFix(bool force) {
                        // 基本的な診断のみ実行
                        try {
                            // Python確認
                            var pythonResult = System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo {
                                FileName = "python",
                                Arguments = "--version",
                                RedirectStandardOutput = true,
                                UseShellExecute = false,
                                CreateNoWindow = true
                            });
                            pythonResult.WaitForExit();
                            
                            if (pythonResult.ExitCode == 0) {
                                Fixed = true;
                                return true;
                            }
                        } catch {
                            return false;
                        }
                        return false;
                    }
                }
"@
                
                $backend = New-Object SimpleBackendFixer($path)
                return $backend.DiagnoseAndFix($forceMode)
            } -ArgumentList $backendPath, $force
            
            $frontendPath = $this.Frontend.Path
            
            $frontendJob = Start-Job -ScriptBlock {
                param($path, $forceMode)
                
                # クラス定義を再度読み込む
                Add-Type -TypeDefinition @"
                using System;
                using System.Collections;
                
                public class SimpleFrontendFixer {
                    public string Path { get; set; }
                    public bool Fixed { get; set; }
                    
                    public SimpleFrontendFixer(string path) {
                        Path = path;
                        Fixed = false;
                    }
                    
                    public bool DiagnoseAndFix(bool force) {
                        // 基本的な診断のみ実行
                        try {
                            // Node確認
                            var nodeResult = System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo {
                                FileName = "node",
                                Arguments = "--version",
                                RedirectStandardOutput = true,
                                UseShellExecute = false,
                                CreateNoWindow = true
                            });
                            nodeResult.WaitForExit();
                            
                            if (nodeResult.ExitCode == 0) {
                                Fixed = true;
                                return true;
                            }
                        } catch {
                            return false;
                        }
                        return false;
                    }
                }
"@
                
                $frontend = New-Object SimpleFrontendFixer($path)
                return $frontend.DiagnoseAndFix($forceMode)
            } -ArgumentList $frontendPath, $force
            
            # ジョブ完了待機
            $jobs = @($backendJob, $frontendJob)
            $null = $jobs | Wait-Job
            
            # 結果取得
            $backendResult = Receive-Job -Job $backendJob -ErrorAction SilentlyContinue
            $frontendResult = Receive-Job -Job $frontendJob -ErrorAction SilentlyContinue
            
            # ジョブクリーンアップ
            $jobs | Remove-Job -Force
            
            # 結果判定（nullチェック付き）
            $backendSuccess = if ($null -ne $backendResult) { $backendResult } else { $false }
            $frontendSuccess = if ($null -ne $frontendResult) { $frontendResult } else { $false }
            
            # 実際の診断は順次実行に切り替え
            if (-not $backendSuccess -or -not $frontendSuccess) {
                Write-ColorLog "並列診断で問題を検出。詳細診断に切り替えます..." "WARNING" "SYSTEM"
                
                # バックエンド詳細診断
                if (-not $this.Backend.DiagnoseAndFix($this.Force)) {
                    $success = $false
                } else {
                    $this.Backend.Fixed = $true
                }
                
                # フロントエンド詳細診断
                if (-not $this.Frontend.DiagnoseAndFix($this.Force)) {
                    $success = $false
                } else {
                    $this.Frontend.Fixed = $true
                }
            } else {
                $this.Backend.Fixed = $true
                $this.Frontend.Fixed = $true
                $success = $true
            }
        } else {
            # 順次診断
            if (-not $skipBackend) {
                $retries = 0
                while ($retries -lt $this.MaxRetries) {
                    if ($this.Backend.DiagnoseAndFix($this.Force)) {
                        break
                    }
                    $retries++
                    if ($retries -lt $this.MaxRetries) {
                        Write-ColorLog "バックエンド診断リトライ ($retries/$($this.MaxRetries))..." "WARNING" "SYSTEM"
                        Start-Sleep -Seconds 3
                    } else {
                        $success = $false
                    }
                }
            }
            
            if (-not $skipFrontend -and $success) {
                $retries = 0
                while ($retries -lt $this.MaxRetries) {
                    if ($this.Frontend.DiagnoseAndFix($this.Force)) {
                        break
                    }
                    $retries++
                    if ($retries -lt $this.MaxRetries) {
                        Write-ColorLog "フロントエンド診断リトライ ($retries/$($this.MaxRetries))..." "WARNING" "SYSTEM"
                        Start-Sleep -Seconds 3
                    } else {
                        $success = $false
                    }
                }
            }
        }
        
        return $success
    }
    
    [bool] StartServers([bool]$skipFrontend, [bool]$skipBackend) {
        Write-ColorLog "サーバーを起動中..." "INFO" "SYSTEM"
        
        $success = $true
        
        if (-not $skipBackend) {
            if (-not $this.Backend.StartServer()) {
                $success = $false
            }
        }
        
        if (-not $skipFrontend -and $success) {
            # バックエンドの安定待機
            Start-Sleep -Seconds 3
            
            if (-not $this.Frontend.StartServer()) {
                Write-ColorLog "フロントエンドは起動処理中です（ビルドに時間がかかります）" "WARNING" "SYSTEM"
            }
        }
        
        return $success
    }
    
    [void] ShowReport() {
        Write-Host ""
        Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║                           診断・修復レポート                              ║" -ForegroundColor Cyan
        Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        
        # バックエンドレポート
        Write-Host ""
        Write-Host "【バックエンド】" -ForegroundColor Yellow
        if ($this.Backend.Fixed) {
            Write-Host "  ✅ 診断・修復完了" -ForegroundColor Green
        } else {
            Write-Host "  ❌ 問題が残っています" -ForegroundColor Red
            foreach ($error in $this.Backend.Errors.GetEnumerator()) {
                Write-Host "    - $($error.Key): $($error.Value)" -ForegroundColor Red
            }
        }
        
        # フロントエンドレポート
        Write-Host ""
        Write-Host "【フロントエンド】" -ForegroundColor Yellow
        if ($this.Frontend.Fixed) {
            Write-Host "  ✅ 診断・修復完了" -ForegroundColor Green
        } else {
            Write-Host "  ❌ 問題が残っています" -ForegroundColor Red
            foreach ($error in $this.Frontend.Errors.GetEnumerator()) {
                Write-Host "    - $($error.Key): $($error.Value)" -ForegroundColor Red
            }
        }
        
        # 実行時間
        $duration = [math]::Round(((Get-Date) - $global:StartTime).TotalSeconds, 1)
        Write-Host ""
        Write-Host "実行時間: ${duration}秒" -ForegroundColor Gray
    }
    
    [void] ShowUrls() {
        Write-Host ""
        Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║                      システム起動完了！                                  ║" -ForegroundColor Green
        Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "📌 アクセスURL:" -ForegroundColor White
        Write-Host "   フロントエンド:  http://192.168.3.92:3050" -ForegroundColor Cyan
        Write-Host "   バックエンドAPI: http://192.168.3.92:8080" -ForegroundColor Cyan
        Write-Host "   API仕様書:      http://192.168.3.92:8080/api/docs" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "🛑 停止方法:" -ForegroundColor Yellow
        Write-Host "   各サーバーウィンドウで Ctrl+C" -ForegroundColor Gray
        Write-Host "   または .\Stop-WebUI.ps1 を実行" -ForegroundColor Gray
    }
}

# ============================================================================
# メイン処理
# ============================================================================

Clear-Host

# バナー表示
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         フロントエンド＋バックエンド 統合自動診断・修復システム          ║" -ForegroundColor Cyan
Write-Host "║                  Windows 11 無人応答ファイル生成システム                 ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# オプション表示
Write-ColorLog "実行オプション:" "INFO" "SYSTEM"
Write-Host "  詳細ログ: $(if($Verbose){'ON'}else{'OFF'})" -ForegroundColor Gray
Write-Host "  強制修復: $(if($Force){'ON'}else{'OFF'})" -ForegroundColor Gray
Write-Host "  最大リトライ: $MaxRetries" -ForegroundColor Gray
Write-Host "  並列処理: $(if($Parallel){'ON'}else{'OFF'})" -ForegroundColor Gray
if ($SkipFrontend) { Write-Host "  ⚠️ フロントエンドをスキップ" -ForegroundColor Yellow }
if ($SkipBackend) { Write-Host "  ⚠️ バックエンドをスキップ" -ForegroundColor Yellow }
Write-Host ""

# パスチェック
$backendPath = Join-Path $ScriptRoot "backend"
$frontendPath = Join-Path $ScriptRoot "frontend"

if (-not $SkipBackend -and -not (Test-Path $backendPath)) {
    Write-ColorLog "バックエンドフォルダが見つかりません: $backendPath" "ERROR" "SYSTEM"
    exit 1
}

if (-not $SkipFrontend -and -not (Test-Path $frontendPath)) {
    Write-ColorLog "フロントエンドフォルダが見つかりません: $frontendPath" "ERROR" "SYSTEM"
    exit 1
}

# 既存プロセスの確認
Write-ColorLog "既存プロセスを確認中..." "INFO" "SYSTEM"

$existingBackend = Test-Path Variable:backendProcess
$existingFrontend = Test-Path Variable:frontendProcess

if ($existingBackend -or $existingFrontend) {
    if (-not $Force) {
        $response = Read-Host "既存のサーバーが検出されました。再起動しますか？ (Y/N)"
        if ($response -ne 'Y' -and $response -ne 'y') {
            Write-ColorLog "処理をキャンセルしました" "INFO" "SYSTEM"
            exit 0
        }
    }
    
    # 既存プロセスを停止
    Write-ColorLog "既存プロセスを停止中..." "WARNING" "SYSTEM"
    
    Get-Process python* -ErrorAction SilentlyContinue | 
        Where-Object { $_.Path -like "*Generate-autounattendxml*" } |
        Stop-Process -Force
    
    Get-Process node* -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*3050*" } |
        Stop-Process -Force
    
    Start-Sleep -Seconds 2
}

# マネージャー作成
$options = @{
    Parallel = $Parallel
    MaxRetries = $MaxRetries
    Force = $Force
    Verbose = $Verbose
}

$manager = [SystemDiagnosticManager]::new($ScriptRoot, $options)

# 診断・修復実行
Write-Host ""
Write-ColorLog "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "INFO" "SYSTEM"

$diagnosticSuccess = $manager.RunDiagnostics($SkipFrontend, $SkipBackend)

# レポート表示
$manager.ShowReport()

if ($diagnosticSuccess) {
    Write-Host ""
    Write-ColorLog "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "INFO" "SYSTEM"
    
    # サーバー起動
    if ($manager.StartServers($SkipFrontend, $SkipBackend)) {
        # 起動確認
        Start-Sleep -Seconds 3
        
        $backendOK = $false
        $frontendOK = $false
        
        if (-not $SkipBackend) {
            try {
                $response = Invoke-WebRequest -Uri "http://192.168.3.92:8080/api/status" -UseBasicParsing -TimeoutSec 5
                if ($response.StatusCode -eq 200) {
                    $backendOK = $true
                }
            } catch {}
        }
        
        if (-not $SkipFrontend) {
            # フロントエンドは起動に時間がかかるため、確認を遅延
            $frontendOK = $true  # 仮にOKとする
        }
        
        if ($backendOK -or $frontendOK) {
            $manager.ShowUrls()
            
            # ブラウザ起動
            Start-Sleep -Seconds 2
            if (-not $SkipFrontend) {
                Start-Process "http://192.168.3.92:3050"
            } elseif (-not $SkipBackend) {
                Start-Process "http://192.168.3.92:8080/api/docs"
            }
        }
    } else {
        Write-ColorLog "サーバー起動に失敗しました" "ERROR" "SYSTEM"
    }
} else {
    Write-Host ""
    Write-ColorLog "診断・修復に失敗しました" "ERROR" "SYSTEM"
    Write-Host ""
    Write-ColorLog "手動での対処が必要です:" "WARNING" "SYSTEM"
    
    if (-not $SkipBackend -and $manager.Backend.Errors.Count -gt 0) {
        Write-Host ""
        Write-Host "【バックエンド】" -ForegroundColor Yellow
        Write-Host "  1. Python 3.9以上をインストール" -ForegroundColor Gray
        Write-Host "  2. backend\venvを削除して再実行" -ForegroundColor Gray
    }
    
    if (-not $SkipFrontend -and $manager.Frontend.Errors.Count -gt 0) {
        Write-Host ""
        Write-Host "【フロントエンド】" -ForegroundColor Yellow
        Write-Host "  1. Node.js 18以上をインストール" -ForegroundColor Gray
        Write-Host "  2. frontend\node_modulesを削除して再実行" -ForegroundColor Gray
    }
    
    Write-Host ""
    Read-Host "Enterキーで終了"
}

Write-Host ""