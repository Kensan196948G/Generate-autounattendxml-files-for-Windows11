"""
設定ログ生成モジュール
XML生成時の設定内容を日本語で詳細にログ出力
"""

from datetime import datetime
from typing import Dict, Any, List
import json

class ConfigLogGenerator:
    """設定内容を日本語でログ出力するクラス"""
    
    def __init__(self):
        self.log_lines = []
        self.timestamp = datetime.now()
    
    def generate_log(self, config: Dict[str, Any]) -> str:
        """
        設定内容から詳細な日本語ログを生成
        
        Args:
            config: XML生成に使用される最終設定
            
        Returns:
            日本語のログ文字列
        """
        self.log_lines = []
        
        # ヘッダー
        self._add_header()
        
        # 基本設定
        self._add_basic_settings(config)
        
        # Windowsエディションとプロダクトキー
        self._add_windows_edition(config)
        
        # ユーザーアカウント設定
        self._add_user_accounts(config)
        
        # ネットワーク設定
        self._add_network_settings(config)
        
        # Windows機能設定
        self._add_windows_features(config)
        
        # システム設定
        self._add_system_settings(config)
        
        # その他の設定
        self._add_additional_settings(config)
        
        # フッター
        self._add_footer()
        
        return "\n".join(self.log_lines)
    
    def _add_header(self):
        """ログヘッダーを追加"""
        self.log_lines.extend([
            "=" * 80,
            "Windows 11 無人応答ファイル生成システム - 設定ログ",
            "=" * 80,
            f"生成日時: {self.timestamp.strftime('%Y年%m月%d日 %H時%M分%S秒')}",
            "",
            "このログファイルは、生成されたunattend.xmlの設定内容を記録したものです。",
            "=" * 80,
            ""
        ])
    
    def _add_basic_settings(self, config: Dict[str, Any]):
        """基本設定をログに追加"""
        self.log_lines.extend([
            "【基本設定】",
            "-" * 40,
            f"  言語設定: {config.get('language', 'ja-JP')}",
            f"  アーキテクチャ: {config.get('architecture', 'amd64')}",
            f"  タイムゾーン: {config.get('timezone', 'Tokyo Standard Time')}",
            ""
        ])
        
        # 日本語設定の詳細
        if config.get('language') == 'ja-JP':
            self.log_lines.extend([
                "  [言語設定詳細]",
                "    ・表示言語: 日本語",
                "    ・入力方式: 日本語 IME (0411:00000411)",
                "    ・システムロケール: 日本",
                "    ・地域設定: 日本",
                ""
            ])
    
    def _add_windows_edition(self, config: Dict[str, Any]):
        """Windowsエディションとプロダクトキーをログに追加"""
        self.log_lines.extend([
            "【Windowsエディション】",
            "-" * 40,
            f"  エディション: {config.get('windows_edition', 'Windows 11 Pro')}",
        ])
        
        if config.get('product_key'):
            self.log_lines.append(f"  プロダクトキー: {config['product_key']}")
            self.log_lines.append("  ※ 汎用キーを使用（後で本番キーに置換可能）")
        else:
            self.log_lines.append("  プロダクトキー: 未設定（インストール時に入力）")
        
        self.log_lines.append("")
    
    def _add_user_accounts(self, config: Dict[str, Any]):
        """ユーザーアカウント設定をログに追加"""
        self.log_lines.extend([
            "【ユーザーアカウント設定】",
            "-" * 40
        ])
        
        accounts = config.get('local_accounts', [])
        if accounts:
            for i, account in enumerate(accounts, 1):
                self.log_lines.extend([
                    f"  アカウント {i}:",
                    f"    ユーザー名: {account.get('name', '未設定')}",
                    f"    表示名: {account.get('display_name', account.get('name', '未設定'))}",
                    f"    グループ: {account.get('group', 'Users')}",
                    f"    説明: {account.get('description', 'なし')}",
                    f"    パスワード: {'設定済み' if account.get('password') else '未設定'}",
                ])
        else:
            self.log_lines.append("  ローカルアカウントは設定されていません")
        
        # Microsoft アカウントのバイパス設定
        if config.get('bypass_microsoft_account'):
            self.log_lines.extend([
                "",
                "  [Microsoftアカウント設定]",
                "    ・Microsoftアカウントの要求をバイパス: 有効",
                "    ・ローカルアカウントでのセットアップを許可"
            ])
        
        self.log_lines.append("")
    
    def _add_network_settings(self, config: Dict[str, Any]):
        """ネットワーク設定をログに追加"""
        self.log_lines.extend([
            "【ネットワーク設定】",
            "-" * 40
        ])
        
        # Wi-Fi設定
        wifi_settings = config.get('wifi_settings')
        if wifi_settings and wifi_settings.get('ssid'):
            self.log_lines.extend([
                "  [Wi-Fi設定]",
                f"    SSID: {wifi_settings['ssid']}",
                f"    認証方式: {wifi_settings.get('auth_type', 'WPA2PSK')}",
                f"    パスワード: {'設定済み' if wifi_settings.get('password') else '未設定'}",
                f"    自動接続: {'有効' if wifi_settings.get('connect_automatically', True) else '無効'}",
            ])
        else:
            self.log_lines.append("  Wi-Fi設定: なし（セットアップ時に手動設定）")
        
        # ネットワークチェックのバイパス
        if config.get('bypass_network_check') or config.get('bypass_microsoft_account'):
            self.log_lines.extend([
                "",
                "  [ネットワーク要件]",
                "    ・インターネット接続チェックをバイパス: 有効",
                "    ・オフラインでのセットアップを許可"
            ])
        
        self.log_lines.append("")
    
    def _add_windows_features(self, config: Dict[str, Any]):
        """Windows機能設定をログに追加"""
        self.log_lines.extend([
            "【Windows機能】",
            "-" * 40
        ])
        
        features = []
        if config.get('enable_dotnet35'):
            features.append("  ・.NET Framework 3.5: 有効化")
        if config.get('enable_hyperv'):
            features.append("  ・Hyper-V: 有効化")
        if config.get('enable_wsl'):
            features.append("  ・Windows Subsystem for Linux (WSL): 有効化")
        if config.get('enable_sandbox'):
            features.append("  ・Windows サンドボックス: 有効化")
        
        if features:
            self.log_lines.extend(features)
        else:
            self.log_lines.append("  追加のWindows機能は設定されていません")
        
        self.log_lines.append("")
    
    def _add_system_settings(self, config: Dict[str, Any]):
        """システム設定をログに追加"""
        self.log_lines.extend([
            "【システム設定】",
            "-" * 40
        ])
        
        # コンピューター名
        if config.get('computer_name'):
            self.log_lines.append(f"  コンピューター名: {config['computer_name']}")
        else:
            self.log_lines.append("  コンピューター名: 自動生成")
        
        # Windows 11要件のバイパス
        if config.get('bypass_win11_requirements'):
            self.log_lines.extend([
                "",
                "  [Windows 11要件バイパス]",
                "    ・TPM 2.0チェック: スキップ",
                "    ・セキュアブートチェック: スキップ",
                "    ・CPU互換性チェック: スキップ",
                "    ・最小RAM要件チェック: スキップ"
            ])
        
        # プライバシー設定
        if config.get('skip_privacy'):
            self.log_lines.extend([
                "",
                "  [プライバシー設定]",
                "    ・診断データ送信: 最小限",
                "    ・エクスペリエンス向上プログラム: 無効",
                "    ・広告ID: 無効"
            ])
        
        # OOBE設定
        self.log_lines.extend([
            "",
            "  [初期設定画面（OOBE）のスキップ]",
            f"    ・使用許諾契約: スキップ",
            f"    ・OEM登録画面: スキップ",
            f"    ・オンラインアカウント画面: スキップ",
            f"    ・ワイヤレス設定画面: {'表示' if not config.get('skip_network') else 'スキップ'}"
        ])
        
        self.log_lines.append("")
    
    def _add_additional_settings(self, config: Dict[str, Any]):
        """その他の設定をログに追加"""
        self.log_lines.extend([
            "【その他の設定】",
            "-" * 40
        ])
        
        # デスクトップ設定
        if config.get('desktop_icons'):
            self.log_lines.extend([
                "  [デスクトップアイコン]",
                f"    ・このPC: {'表示' if config['desktop_icons'].get('computer') else '非表示'}",
                f"    ・ネットワーク: {'表示' if config['desktop_icons'].get('network') else '非表示'}",
                f"    ・ごみ箱: {'表示' if config['desktop_icons'].get('recycle_bin') else '非表示'}",
                f"    ・ユーザーフォルダー: {'表示' if config['desktop_icons'].get('user_files') else '非表示'}"
            ])
        
        # 削除するアプリ
        if config.get('remove_apps'):
            self.log_lines.extend([
                "",
                "  [削除予定のアプリ]"
            ])
            for app in config['remove_apps'][:10]:  # 最初の10個のみ表示
                self.log_lines.append(f"    ・{app}")
            if len(config['remove_apps']) > 10:
                self.log_lines.append(f"    ...他 {len(config['remove_apps']) - 10} 個のアプリ")
        
        # 初回ログオンコマンド
        if config.get('first_logon_commands'):
            self.log_lines.extend([
                "",
                "  [初回ログオン時実行コマンド]"
            ])
            for i, cmd in enumerate(config['first_logon_commands'][:5], 1):
                self.log_lines.append(f"    {i}. {cmd.get('description', cmd.get('command', ''))}")
        
        self.log_lines.append("")
    
    def _add_footer(self):
        """ログフッターを追加"""
        self.log_lines.extend([
            "=" * 80,
            "【注意事項】",
            "-" * 40,
            "1. このログファイルはunattend.xmlと共に保管してください",
            "2. パスワードは暗号化されており、このログには平文で記載されません",
            "3. 実際のインストール時の動作は、ハードウェアや環境により異なる場合があります",
            "4. 問題が発生した場合は、このログを参照して設定を確認してください",
            "",
            "=" * 80,
            f"ログ生成完了: {datetime.now().strftime('%Y年%m月%d日 %H時%M分%S秒')}",
            "=" * 80
        ])
    
    def save_log(self, filepath: str, config: Dict[str, Any]) -> bool:
        """
        ログをファイルに保存
        
        Args:
            filepath: 保存先のファイルパス
            config: 設定内容
            
        Returns:
            保存成功時True
        """
        try:
            log_content = self.generate_log(config)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(log_content)
            return True
        except Exception as e:
            print(f"ログ保存エラー: {e}")
            return False