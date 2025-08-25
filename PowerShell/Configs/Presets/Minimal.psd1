@{
    # Minimal環境向けプリセット設定
    # 最小構成でのPCキッティング（軽量・高速起動重視）
    
    # システム設定
    System = @{
        HostName = "WIN11-MIN"
        TimeZone = "Tokyo Standard Time"
        DisableIPv6 = $true  # 軽量化のため無効
        DisableFirewall = $false  # 最小限のセキュリティは保持
        DisableBluetooth = $true  # リソース節約
        MuteAudio = $true  # 静音環境用
    }
    
    # ユーザーアカウント設定（最小構成）
    Users = @(
        @{
            Name = "Administrator"
            IsEnabled = $false
        },
        @{
            Name = "mirai-user"
            Password = "MiraiMin2025!"
            Groups = @("Administrators", "Users")
            DisplayName = "Mirai User"
            Description = "最小構成管理アカウント"
        },
        @{
            Name = "l-admin"
            Password = "LAdminMin2025!"
            Groups = @("Administrators", "Users")
            DisplayName = "Local Administrator"  
            Description = "ローカル管理者アカウント"
        }
    )
    
    # アプリケーション設定（最小構成）
    Applications = @{
        EnableDotNet35 = $false  # 軽量化のため無効
        DefaultBrowser = "MSEdgeHTM"  # 標準ブラウザのみ
        DefaultMailClient = "Mail"  # Windows標準メールアプリ
        DefaultPDFReader = "MSEdgeHTM"  # Edge内蔵PDF表示
        
        # Office設定（最小限）
        OfficeSettings = @{
            SkipFirstRun = $true
            AcceptEula = $true
            DisableTelemetry = $true  # プライバシー重視
            DisableUpdates = $true  # 軽量化のため更新無効
            EnableMacros = $false  # セキュリティ重視
        }
        
        # タスクバー設定（最小構成）
        TaskbarSettings = @{
            ShowSearchBox = 0  # 検索ボックス非表示
            ShowCortanaButton = 0  # Cortana無効
            ShowTaskViewButton = 0  # タスクビュー無効
            TaskbarDa = 0  # ニュース無効
            TaskbarSi = 1  # 小さいボタン
            TaskbarAlignment = 0  # 左寄せ
        }
    }
    
    # ネットワーク設定（最小構成）
    Network = @{
        DisableIPv6 = $true
        DisableFirewall = $false  # 基本的なセキュリティ保持
        DisableBluetooth = $true
        DefaultNetworkProfile = "Public"  # より安全な設定
        
        # グループポリシー設定（最小限）
        GroupPolicySettings = @{
            EnableInsecureGuestLogons = $false  # セキュリティ重視
            EnableNetworkDiscovery = $false  # プライバシー重視
            DisableSMBSigning = $false  # セキュリティ保持
        }
    }
    
    # Windows機能設定（最小構成）
    WindowsFeatures = @{
        EnableDotNet35 = $false  # 軽量化
        EnableHyperV = $false  # リソース節約
        EnableWSL = $false  # 不要
        EnableWindowsSandbox = $false  # リソース節約
        DisableCortana = $true  # リソース節約
        DisableWindowsSearch = $true  # 軽量化（ファイル検索は手動）
        
        # オプション機能（最小限）
        OptionalFeatures = @{
            TelnetClient = "Disabled"
            TFTP = "Disabled"
            SimpleTCP = "Disabled"
            WorkFoldersClient = "Disabled"
        }
        
        # Windows Capability（最小限）
        Capabilities = @{
            "OpenSSH.Client" = "Disabled"  # 不要
            "OpenSSH.Server" = "Disabled"  # 不要
            "PowerShell.ISE" = "Disabled"  # PowerShellコンソールのみ
        }
    }
    
    # セキュリティ設定（最小限＋安全性）
    Security = @{
        DisableUAC = $false  # セキュリティ保持
        EnableWindowsDefender = $true  # 必須セキュリティ
        ConfigureWindowsUpdate = @{
            AutoUpdate = $true  # セキュリティ更新は重要
            RestartRequired = $false
            DeferFeatureUpdates = 365  # 機能更新は1年延期
            DeferQualityUpdates = 7    # セキュリティ更新は1週間のみ延期
        }
        
        # プライバシー設定（最小構成向け）
        PrivacySettings = @{
            DisableTelemetry = $true
            DisableAdvertisingID = $true
            DisableLocationServices = $true
            DisableCameraAccess = $true
            DisableMicrophoneAccess = $true
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
    
    # 管理設定（最小構成）
    Management = @{
        EnableRemoteDesktop = $false  # セキュリティのため無効
        ConfigureEventLogs = @{
            MaxLogSize = 20971520  # 20MB（最小限）
            RetentionDays = 7  # 短期保存
        }
        
        # パフォーマンス設定（軽量化重視）
        PerformanceSettings = @{
            VisualEffects = "Performance"  # 最高パフォーマンス
            VirtualMemory = "SystemManaged"
            EnableIndexing = $false  # 検索インデックス無効（軽量化）
            DisableAnimations = $true
            DisableTransparency = $true
        }
        
        # ドメイン設定
        DomainSettings = @{
            JoinDomain = $false
            DomainName = ""
            DomainUser = ""
            DomainPassword = ""
            MachineObjectOU = ""
        }
    }
    
    # 軽量化設定
    OptimizationSettings = @{
        # 不要なサービス無効化
        DisableServices = @(
            "Fax",                    # FAXサービス
            "WerSvc",                 # エラー報告サービス
            "DiagTrack",              # 診断追跡サービス
            "dmwappushservice",       # プッシュ通知システムサービス
            "MapsBroker",             # ダウンロードマネージャー
            "NetTcpPortSharing",      # Net.Tcp Port Sharing Service
            "RemoteAccess",           # リモートアクセス自動接続マネージャー
            "RemoteRegistry",         # リモートレジストリ
            "SharedAccess",           # インターネット接続共有
            "TrkWks",                 # 分散リンクトラッキングクライアント
            "WbioSrvc",               # Windows生体認証サービス
            "XblAuthManager",         # Xbox Live認証マネージャー
            "XblGameSave",            # Xbox Liveゲーム保存
            "XboxNetApiSvc",          # Xbox Liveネットワークサービス
            "XboxGipSvc"              # Xbox Accessory Management Service
        )
    }
    
    # スタートアップ無効化
    DisableStartupApps = @(
            "Microsoft Teams",
            "Skype",
            "OneDrive",
            "Spotify",
            "Adobe Updater",
            "Java Update Scheduler"
        )
        
    # 視覚効果無効化
    DisableVisualEffects = @{
            AnimateMinMax = $false
            CursorShadow = $false
            DragFullWindows = $false
            DropShadow = $false
            FontSmoothing = $false
            ListBoxSmoothScrolling = $false
            MenuAnimation = $false
            SelectionFade = $false
            ToolTipAnimation = $false
            UIEffects = $false
    }
    
    # カスタム設定
    CustomSettings = @{
        Description = "最小構成・軽量化設定"
        Version = "1.0.0"
        LastModified = "2025-01-22"
        CreatedBy = "Windows 11 Sysprep Automation Team"
        
        # 環境固有設定
        Environment = @{
            Type = "Minimal"
            Purpose = "Lightweight PC Provisioning"
            Characteristics = @(
                "Low Resource Usage",
                "Fast Boot Time",
                "Minimal Features",
                "Basic Security",
                "Privacy Focused"
            )
        }
        
        # 軽量化の目標
        OptimizationGoals = @{
            BootTimeReduction = "30%以上高速化"
            MemoryUsageReduction = "20%以上削減"
            StorageUsageReduction = "15%以上削減"
            ServiceCount = "必要最小限に削減"
            StartupTime = "3秒以内"
        }
    }
}