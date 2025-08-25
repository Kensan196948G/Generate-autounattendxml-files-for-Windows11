@{
    # Development環境向けプリセット設定
    # 開発者向けPCキッティングに最適化された設定
    
    # システム設定
    System = @{
        HostName = "WIN11-DEV"
        TimeZone = "Tokyo Standard Time"
        DisableIPv6 = $false  # 開発環境ではIPv6も使用する場合がある
        DisableFirewall = $true  # 開発作業の利便性を重視
        DisableBluetooth = $false  # デバイステスト用に有効
        MuteAudio = $false
    }
    
    # ユーザーアカウント設定
    Users = @(
        @{
            Name = "Administrator"
            IsEnabled = $false
        },
        @{
            Name = "mirai-user"
            Password = "MiraiDev2025!"
            Groups = @("Administrators", "Users")
            DisplayName = "Mirai Developer"
            Description = "メイン開発者アカウント"
        },
        @{
            Name = "l-admin"
            Password = "LAdminDev2025!"
            Groups = @("Administrators", "Users")
            DisplayName = "Local Administrator"
            Description = "ローカル管理者アカウント"
        },
        @{
            Name = "dev-user"
            Password = "DevUser2025!"
            Groups = @("Users", "Remote Desktop Users")
            DisplayName = "Developer User"
            Description = "開発者ユーザーアカウント"
        }
    )
    
    # アプリケーション設定
    Applications = @{
        EnableDotNet35 = $true  # レガシーアプリケーション開発用
        DefaultBrowser = "ChromeHTML"  # 開発者はChromeを好む傾向
        DefaultMailClient = "Outlook.File.msg.15"
        DefaultPDFReader = "MSEdgeHTM"  # 軽量なPDF表示
        
        # Office設定
        OfficeSettings = @{
            SkipFirstRun = $true
            AcceptEula = $true
            DisableTelemetry = $false  # 開発環境では問題レポート有効
            DisableUpdates = $false
            EnableMacros = $true  # 開発・テスト用途でマクロ有効
        }
        
        # タスクバー設定（Development向け）
        TaskbarSettings = @{
            ShowSearchBox = 1  # 検索ボックス表示
            ShowCortanaButton = 0  # Cortana無効
            ShowTaskViewButton = 1  # マルチタスク用
            TaskbarDa = 0  # ニュース無効（集中のため）
            TaskbarSi = 1  # 小さいボタン（より多くのアプリ表示）
            TaskbarAlignment = 0  # 左寄せ
        }
    }
    
    # ネットワーク設定
    Network = @{
        DisableIPv6 = $false  # 最新技術のテスト用
        DisableFirewall = $true  # 開発作業の利便性
        DisableBluetooth = $false  # IoTデバイス開発用
        DefaultNetworkProfile = "Private"
        
        # グループポリシー設定
        GroupPolicySettings = @{
            EnableInsecureGuestLogons = $true
            EnableNetworkDiscovery = $true
            DisableSMBSigning = $true  # 開発環境での性能重視
        }
    }
    
    # Windows機能設定（開発者向け）
    WindowsFeatures = @{
        EnableDotNet35 = $true
        EnableHyperV = $true  # 仮想環境でのテスト用
        EnableWSL = $true  # Linux開発環境
        EnableWindowsSandbox = $true  # セキュリティテスト用
        DisableCortana = $false  # 開発中の検索で有用
        DisableWindowsSearch = $false
        
        # オプション機能（開発者向け）
        OptionalFeatures = @{
            TelnetClient = "Enabled"  # ネットワークテスト用
            TFTP = "Enabled"  # ファームウェア開発用
            SimpleTCP = "Enabled"  # プロトコルテスト用
            WorkFoldersClient = "Disabled"  # 不要
        }
        
        # Windows Capability（開発者向け）
        Capabilities = @{
            "OpenSSH.Client" = "Enabled"  # リモート開発用
            "OpenSSH.Server" = "Enabled"  # リモートアクセス用
            "PowerShell.ISE" = "Enabled"  # スクリプト開発用
        }
    }
    
    # 開発者向けセキュリティ設定
    Security = @{
        DisableUAC = $false  # セキュリティは保持
        EnableWindowsDefender = $true
        ConfigureWindowsUpdate = @{
            AutoUpdate = $false  # 開発作業中断を避ける
            RestartRequired = $false
            DeferFeatureUpdates = 365  # 機能更新は1年延期
            DeferQualityUpdates = 90   # 品質更新は3ヶ月延期
        }
        
        # 開発者モード設定
        DeveloperMode = @{
            EnableDeveloperMode = $true
            EnableSideloading = $true
            EnableDevicePortal = $true
        }
    }
    
    # 地域設定
    Regional = @{
        InputLocale = "ja-JP"
        SystemLocale = "ja-JP"
        UILanguage = "ja-JP"
        UserLocale = "ja-JP"
        TimeZone = "Tokyo Standard Time"
        GeoID = 122  # Japan
    }
    
    # 開発環境管理設定
    Management = @{
        EnableRemoteDesktop = $true
        ConfigureEventLogs = @{
            MaxLogSize = 52428800  # 50MB（ログサイズは中程度）
            RetentionDays = 30
        }
        
        # パフォーマンス設定（開発用）
        PerformanceSettings = @{
            VisualEffects = "Performance"  # パフォーマンス重視
            VirtualMemory = "SystemManaged"
            EnableIndexing = $true  # コード検索のため
        }
        
        # ドメイン設定
        DomainSettings = @{
            JoinDomain = $false  # 開発環境は独立
            DomainName = ""
            DomainUser = ""
            DomainPassword = ""
            MachineObjectOU = ""
        }
    }
    
    # 開発ツール設定
    DevelopmentTools = @{
        # Git設定
        GitConfig = @{
            EnableGitCredentialManager = $true
            DefaultBranch = "main"
            AutoCRLF = $true  # Windows環境用
        }
        
        # Visual Studio Code設定
        VSCodeSettings = @{
            InstallExtensions = @(
                "ms-vscode.powershell",
                "ms-python.python",
                "ms-vscode.csharp",
                "ms-vscode.vscode-json"
            )
            EnableTelemetry = $false
            AutoUpdate = $true
        }
        
        # PowerShell設定
        PowerShellSettings = @{
            ExecutionPolicy = "RemoteSigned"
            EnablePSReadLine = $true
            InstallModules = @(
                "Pester",
                "PSScriptAnalyzer",
                "ImportExcel",
                "Az"
            )
        }
    }
    
    # カスタム設定
    CustomSettings = @{
        Description = "Development環境向け設定"
        Version = "1.0.0"
        LastModified = "2025-01-22"
        CreatedBy = "Windows 11 Sysprep Automation Team"
        
        # 環境固有設定
        Environment = @{
            Type = "Development"
            Purpose = "Developer PC Provisioning"
            Features = @(
                "Hyper-V", 
                "WSL", 
                "Windows Sandbox", 
                "Developer Mode",
                "SSH Server"
            )
        }
        
        # 開発環境向け最適化
        Optimizations = @{
            DisableStartupPrograms = $true
            ConfigurePageFile = $true
            EnableHighPerformanceMode = $true
            DisableUnnecessaryServices = $true
        }
    }
}