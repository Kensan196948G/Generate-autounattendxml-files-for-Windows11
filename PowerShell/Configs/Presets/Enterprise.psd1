@{
    # Enterprise環境向けプリセット設定
    # 企業でのPCキッティング作業に最適化された設定
    
    # システム設定
    System = @{
        HostName = "WIN11-ENT"
        TimeZone = "Tokyo Standard Time"
        DisableIPv6 = $true
        DisableFirewall = $true
        DisableBluetooth = $true
        MuteAudio = $false  # Enterprise環境では音源を有効にしておく
    }
    
    # ユーザーアカウント設定
    Users = @(
        @{
            Name = "Administrator"
            IsEnabled = $false  # セキュリティのためAdministrator無効化
        },
        @{
            Name = "mirai-user"
            Password = "MiraiUser2025!"
            Groups = @("Administrators", "Users")
            DisplayName = "Mirai User"
            Description = "システム管理用アカウント"
        },
        @{
            Name = "l-admin"
            Password = "LAdmin2025!"
            Groups = @("Administrators", "Users")
            DisplayName = "Local Administrator"
            Description = "ローカル管理者アカウント"
        },
        @{
            Name = "enterprise-user"
            Password = "EntUser2025!"
            Groups = @("Users")
            DisplayName = "Enterprise User"
            Description = "一般企業ユーザーアカウント"
        }
    )
    
    # アプリケーション設定
    Applications = @{
        EnableDotNet35 = $true
        DefaultBrowser = "MSEdgeHTM"  # Microsoft Edge（企業環境標準）
        DefaultMailClient = "Outlook.File.msg.15"  # Outlook
        DefaultPDFReader = "AcroExch.Document"  # Adobe Acrobat Reader DC
        
        # Office設定
        OfficeSettings = @{
            SkipFirstRun = $true
            AcceptEula = $true
            DisableTelemetry = $true
            DisableUpdates = $false  # Enterprise環境では更新を有効
            EnableMacros = $false  # セキュリティ重視
        }
        
        # タスクバー設定（Enterprise向け）
        TaskbarSettings = @{
            ShowSearchBox = 1  # 検索ボックス表示
            ShowCortanaButton = 0  # Cortana無効
            ShowTaskViewButton = 1  # タスクビュー有効
            TaskbarDa = 0  # ニュースと関心事項無効
            TaskbarSi = 0  # 標準サイズのタスクバーボタン
            TaskbarAlignment = 0  # タスクバーを左下に固定
        }
    }
    
    # ネットワーク設定
    Network = @{
        DisableIPv6 = $true
        DisableFirewall = $true  # 企業ファイアウォールを使用する場合
        DisableBluetooth = $true
        DefaultNetworkProfile = "Private"  # 社内ネットワーク用
        
        # グループポリシー設定
        GroupPolicySettings = @{
            EnableInsecureGuestLogons = $true  # ファイル共有用
            EnableNetworkDiscovery = $true
            DisableSMBSigning = $false  # セキュリティ重視でSMB署名有効
        }
    }
    
    # Windows機能設定
    WindowsFeatures = @{
        EnableDotNet35 = $true
        EnableHyperV = $false  # 一般企業環境では無効
        EnableWSL = $false  # 開発用途でなければ無効
        EnableWindowsSandbox = $false
        DisableCortana = $true
        DisableWindowsSearch = $false  # 企業環境では検索機能を残す
        
        # オプション機能
        OptionalFeatures = @{
            TelnetClient = "Disabled"
            TFTP = "Disabled"
            SimpleTCP = "Disabled"
            WorkFoldersClient = "Enabled"  # 企業環境でのファイル同期用
        }
        
        # Windows Capability
        Capabilities = @{
            "OpenSSH.Client" = "Enabled"  # リモート管理用
            "OpenSSH.Server" = "Disabled"  # セキュリティ上無効
            "PowerShell.ISE" = "Enabled"  # 管理者用
        }
    }
    
    # セキュリティ設定
    Security = @{
        DisableUAC = $false  # UAC有効（セキュリティ重視）
        EnableWindowsDefender = $true
        ConfigureWindowsUpdate = @{
            AutoUpdate = $true
            RestartRequired = $false
            DeferFeatureUpdates = 180  # 機能更新は半年延期
            DeferQualityUpdates = 30   # 品質更新は1ヶ月延期
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
    
    # 管理設定
    Management = @{
        EnableRemoteDesktop = $true  # 企業環境でのリモート管理用
        ConfigureEventLogs = @{
            MaxLogSize = 104857600  # 100MB
            RetentionDays = 90
        }
        
        # ドメイン設定（必要に応じて）
        DomainSettings = @{
            JoinDomain = $false
            DomainName = ""
            DomainUser = ""
            DomainPassword = ""
            MachineObjectOU = ""
        }
    }
    
    # カスタム設定
    CustomSettings = @{
        Description = "Enterprise環境向け標準設定"
        Version = "1.0.0"
        LastModified = "2025-01-22"
        CreatedBy = "Windows 11 Sysprep Automation Team"
        
        # 環境固有設定
        Environment = @{
            Type = "Enterprise"
            Purpose = "Corporate PC Provisioning"
            Compliance = @("ISO27001", "SOX", "GDPR")
        }
    }
}