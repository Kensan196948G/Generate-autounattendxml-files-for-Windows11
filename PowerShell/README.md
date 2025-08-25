# PowerShell版 Windows 11 無人応答ファイル生成システム v2.0

## 📋 概要

Windows 11のSysprep実行時に使用する応答ファイル（unattend.xml）を自動生成する高度なPowerShellシステムです。WebUI版と同等の全23項目設定に完全対応し、42体のSubAgentとClaude-flow並列処理エンジンによる革新的な高速処理を実現しています。

## ✨ v2.0 新機能（2024年8月24日リリース）

### 🎯 全23項目完全対応
WebUI版と同じ包括的な設定項目をPowerShellで実現：
- **基本設定（1-11）**: 地域/言語、アーキテクチャ、セットアップ、エディション、PE、ディスク、コンピューター、ユーザー、エクスプローラー、スタート/タスクバー、システム調整
- **拡張設定（12-23）**: 視覚効果、デスクトップ、VM、Wi-Fi、Express Settings、ロックキー、固定キー、個人用設定、アプリ削除、カスタムスクリプト、WDAC、追加コンポーネント

### 🤖 42体のSubAgentシステム
機能別に特化した自律型エージェント：
- **ユーザー管理（8体）**: アカウント作成、権限、グループ、自動ログオン、パスワード、管理者、ゲスト、ドメイン
- **ネットワーク（6体）**: Wi-Fi、Ethernet、ファイアウォール、IPv6、プロキシ、場所
- **システム（10体）**: レジストリ、サービス、タスク、電源、タイムゾーン、ロケール、更新、テレメトリ、プライバシー、UAC
- **アプリケーション（6体）**: アプリ削除、既定アプリ、ストア、Office、ブラウザー、メディア
- **Windows機能（8体）**: .NET、Hyper-V、WSL、Sandbox、IIS、SMB、Telnet、コンテナー
- **UI/UX（4体）**: エクスプローラー、タスクバー、スタートメニュー、デスクトップ

### ⚡ Claude-flow並列処理エンジン
RunspacePoolベースの高度な並列処理：
- 最大8スレッド同時実行
- カテゴリ別並列処理
- 非同期ジョブ管理
- パイプライン処理対応

### 🔧 Context7設定管理エンジン
インテリジェントな設定最適化：
- 7つのコンテキスト（Enterprise、Development、Education、HomeUse、Security、Performance、Minimal）
- 自動コンテキスト検出
- 設定競合の自動解決
- バリデーション機能

## 🚀 クイックスタート

### 基本的な使用方法

```powershell
# 対話モードで実行（推奨）
.\Generate-UnattendXML-V2.ps1 -Interactive

# プリセットを使用（Enterprise/Development/Minimal）
.\Generate-UnattendXML-V2.ps1 -Preset Enterprise

# 設定ファイルから生成
.\Generate-UnattendXML-V2.ps1 -ConfigFile ".\Configs\custom.json"

# 並列処理を有効化（デフォルト）
.\Generate-UnattendXML-V2.ps1 -EnableParallel -GenerateLog
```

## システム要件

- **OS**: Windows 10/11（64ビット）
- **PowerShell**: 5.1以降（PowerShell 7.0以降推奨）
- **権限**: 管理者権限推奨
- **メモリ**: 4GB以上（8GB推奨）
- **.NET Framework**: 4.7.2以降

## ディレクトリ構成

```
PowerShell/
├── Generate-UnattendXML.ps1         # メインスクリプト
├── Generate-UnattendXML.psm1        # メインモジュール
├── README.md                        # このファイル
├── Configs/                         # 設定ファイル
│   └── Presets/                     # プリセット設定
│       ├── Enterprise.psd1          # 企業向け設定
│       ├── Development.psd1         # 開発者向け設定
│       └── Minimal.psd1             # 最小構成設定
├── Modules/                         # 機能モジュール
│   ├── UserManagement/              # ユーザー管理
│   ├── NetworkConfig/               # ネットワーク設定
│   ├── WindowsFeatures/             # Windows機能
│   ├── ApplicationConfig/           # アプリケーション設定
│   └── XMLGenerator/                # XML生成エンジン
├── Outputs/                         # 生成されたXMLファイル
├── Logs/                           # ログファイル
└── Tests/                          # テストスクリプト
```

## 使用方法

### 1. 基本的な使用法

#### Enterpriseプリセットで生成
```powershell
.\Generate-UnattendXML.ps1 -PresetName Enterprise -OutputPath "C:\Temp\unattend.xml"
```

#### 対話的なウィザードモード
```powershell
.\Generate-UnattendXML.ps1 -Interactive
```

#### カスタム設定ファイルを使用
```powershell
.\Generate-UnattendXML.ps1 -ConfigFile ".\Configs\custom.psd1" -LogLevel Debug
```

#### 既存XMLファイルの検証のみ
```powershell
.\Generate-UnattendXML.ps1 -ValidateOnly -OutputPath "C:\Temp\existing-unattend.xml"
```

### 2. パラメータ詳細

| パラメータ | 説明 | 例 |
|-----------|------|---|
| `-PresetName` | プリセット名を指定 | `Enterprise`, `Development`, `Minimal` |
| `-ConfigFile` | カスタム設定ファイル | `.\Configs\custom.psd1` |
| `-OutputPath` | 出力先パス | `C:\Temp\unattend.xml` |
| `-Interactive` | 対話的ウィザードモード | - |
| `-ValidateOnly` | 検証のみ実行 | - |
| `-LogLevel` | ログレベル | `Debug`, `Info`, `Warning`, `Error` |
| `-Force` | 既存ファイル強制上書き | - |
| `-WhatIf` | 実行内容の確認のみ | - |

### 3. プリセット設定

#### Enterprise（企業向け）
- セキュリティ重視の設定
- 管理者権限ユーザー複数作成
- グループポリシー適用
- Office設定最適化
- リモートデスクトップ有効

#### Development（開発者向け）
- 開発効率重視
- Hyper-V、WSL有効化
- Windows Sandbox有効
- 開発者モード有効
- 各種開発ツール設定

#### Minimal（最小構成）
- 軽量・高速起動重視
- 不要サービス無効化
- 視覚効果無効化
- プライバシー保護設定
- リソース使用量最小化

## 高度な使用方法

### 1. カスタム設定ファイル作成

```powershell
@{
    System = @{
        HostName = "CUSTOM-PC"
        TimeZone = "Tokyo Standard Time"
        DisableIPv6 = $true
        DisableFirewall = $true
        DisableBluetooth = $true
    }
    
    Users = @(
        @{
            Name = "custom-user"
            Password = "CustomPass2025!"
            Groups = @("Administrators", "Users")
        }
    )
    
    Applications = @{
        DefaultBrowser = "ChromeHTML"
        DefaultPDFReader = "AcroExch.Document"
    }
}
```

### 2. PowerShellモジュール直接使用

```powershell
# メインモジュールインポート
Import-Module ".\Generate-UnattendXML.psm1"

# プリセット読み込み
$config = Import-UnattendPreset -PresetName "Enterprise"

# XML生成
$result = New-UnattendXML -Config $config -OutputPath "unattend.xml"

# 対話的ウィザード
Start-UnattendXMLWizard
```

### 3. 個別モジュール使用

```powershell
# ユーザー管理モジュール
Import-Module ".\Modules\UserManagement\UserManagement.psm1"
$userConfig = [UserManagementConfig]::new()
$userConfig.SetupDefaultUsers()

# ネットワーク設定モジュール
Import-Module ".\Modules\NetworkConfig\NetworkConfig.psm1"
$networkStatus = Test-NetworkConfiguration

# Windows機能モジュール
Import-Module ".\Modules\WindowsFeatures\WindowsFeatures.psm1"
$featureStatus = Test-WindowsFeatureStatus
```

## ログとトラブルシューティング

### ログファイル
- 場所: `.\Logs\Generate-UnattendXML_YYYYMMDD_HHMMSS.log`
- レベル: Debug, Info, Warning, Error, Critical

### 一般的な問題と解決策

#### 1. 権限不足エラー
```
解決策: PowerShellを「管理者として実行」で起動
```

#### 2. モジュールインポートエラー
```powershell
# 実行ポリシー確認・変更
Get-ExecutionPolicy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3. XMLスキーマ検証エラー
```powershell
# 検証のみ実行
.\Generate-UnattendXML.ps1 -ValidateOnly -OutputPath "unattend.xml"
```

#### 4. パフォーマンス問題
```powershell
# デバッグレベルでログ確認
.\Generate-UnattendXML.ps1 -PresetName Enterprise -LogLevel Debug
```

## 開発・カスタマイズ

### 1. 新しいプリセット作成

```powershell
# 新しいプリセットファイル作成
$presetPath = ".\Configs\Presets\MyCustom.psd1"
$presetData = @{
    System = @{ ... }
    Users = @( ... )
    Applications = @{ ... }
}
$presetData | Export-PowerShellDataFile -Path $presetPath
```

### 2. カスタムモジュール追加

```powershell
# 新しいモジュール作成
New-Item -Path ".\Modules\MyModule\MyModule.psm1" -Force
# モジュール内容実装...

# メインモジュールに統合
# Generate-UnattendXML.psm1 の ExecuteModulesInParallel() に追加
```

### 3. XML検証ルール追加

```powershell
# XMLValidator クラスに新しい検証メソッド追加
[void] ValidateCustomRules() {
    # カスタム検証ロジック
}
```

## セキュリティ考慮事項

### 1. パスワード管理
- プリセット内のパスワードは本番環境では環境変数使用推奨
- SecureStringによる暗号化保存
- XMLファイル内の平文パスワードに注意

### 2. 権限設定
- 生成されたXMLファイルの適切な権限設定
- ログファイルの機密情報マスキング
- 実行時の管理者権限確認

### 3. 監査ログ
- すべての設定変更が記録される
- タイムスタンプ付きログ
- エラー・警告の詳細記録

## パフォーマンス最適化

### 1. 並列処理設定
```powershell
# RunspacePoolサイズ調整
$minRunspaces = 1
$maxRunspaces = [Environment]::ProcessorCount
```

### 2. メモリ使用量削減
```powershell
# 不要なモジュールのアンロード
Remove-Module -Name "ModuleName" -Force
[GC]::Collect()
```

### 3. XML生成最適化
```powershell
# XML最適化有効化
$xmlConfig = [XMLGenerationConfig]::new()
$xmlConfig.OptimizeXML = $true
```

## ライセンス

MIT License

## サポート・コントリビューション

- Issue報告: GitHubリポジトリ
- プルリクエスト: 歓迎します
- ディスカッション: GitHub Discussions

## 更新履歴

### v1.0.0 (2025-01-22)
- 初期リリース
- PowerShell 5.x クラス機能対応
- RunspacePool並列処理実装
- Enterprise/Development/Minimalプリセット追加
- 包括的なXML検証機能
- 対話的ウィザードモード実装

---

**注意**: このシステムは企業環境でのPC展開を想定して設計されています。本番環境での使用前に、必ずテスト環境での動作確認を行ってください。