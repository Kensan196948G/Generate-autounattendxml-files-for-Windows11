"""
包括的設定ログ生成モジュール
全23項目の設定内容を日本語で詳細にログ出力
"""

from datetime import datetime
from typing import Dict, Any, List
import json

class ComprehensiveLogGenerator:
    """全設定内容を日本語でログ出力するクラス"""
    
    def __init__(self):
        self.log_lines = []
        self.timestamp = datetime.now()
    
    def generate_comprehensive_log(self, config: Dict[str, Any]) -> str:
        """
        全23項目の設定内容から包括的な日本語ログを生成
        """
        self.log_lines = []
        
        # ヘッダー
        self._add_header()
        
        # 全23セクションのログ生成
        self._add_section_1_region_language(config)
        self._add_section_2_architecture(config)
        self._add_section_3_setup_behavior(config)
        self._add_section_4_windows_edition(config)
        self._add_section_5_windows_pe(config)
        self._add_section_6_disk_config(config)
        self._add_section_7_computer_settings(config)
        self._add_section_8_user_accounts(config)
        self._add_section_9_explorer_settings(config)
        self._add_section_10_start_taskbar(config)
        self._add_section_11_system_tweaks(config)
        self._add_section_12_visual_effects(config)
        self._add_section_13_desktop_settings(config)
        self._add_section_14_vm_support(config)
        self._add_section_15_wifi_settings(config)
        self._add_section_16_express_settings(config)
        self._add_section_17_lock_keys(config)
        self._add_section_18_sticky_keys(config)
        self._add_section_19_personalization(config)
        self._add_section_20_remove_apps(config)
        self._add_section_21_custom_scripts(config)
        self._add_section_22_wdac(config)
        self._add_section_23_additional_components(config)
        
        # フッター
        self._add_footer()
        
        return "\n".join(self.log_lines)
    
    def _add_header(self):
        """ログヘッダーを追加"""
        self.log_lines.extend([
            "=" * 80,
            "Windows 11 無人応答ファイル生成システム - 包括的設定ログ",
            "=" * 80,
            f"生成日時: {self.timestamp.strftime('%Y年%m月%d日 %H時%M分%S秒')}",
            "",
            "このログファイルは、生成されたautounattend.xmlの全設定内容を記録したものです。",
            "全23項目の設定が含まれています。",
            "=" * 80,
            ""
        ])
    
    def _add_section_1_region_language(self, config: Dict[str, Any]):
        """1. 地域と言語の設定"""
        self.log_lines.extend([
            "【1. 地域と言語の設定】",
            "-" * 40,
            f"  表示言語: {config.get('language', 'ja-JP')}",
            f"  入力方式: {config.get('input_locale', '0411:00000411')} (日本語 IME)",
            f"  システムロケール: {config.get('system_locale', 'ja-JP')}",
            f"  ユーザーロケール: {config.get('user_locale', 'ja-JP')}",
            f"  UI言語: {config.get('ui_language', 'ja-JP')}",
            f"  UIフォールバック言語: {config.get('ui_language_fallback', 'en-US')}",
            f"  タイムゾーン: {config.get('timezone', 'Tokyo Standard Time')}",
            f"  地理的場所: {config.get('geo_location', '122')} (日本)",
            ""
        ])
    
    def _add_section_2_architecture(self, config: Dict[str, Any]):
        """2. プロセッサー・アーキテクチャ"""
        arch = config.get('architecture', 'amd64')
        arch_desc = config.get('processor_architecture', '64-bit x86/x64')
        
        self.log_lines.extend([
            "【2. プロセッサー・アーキテクチャ】",
            "-" * 40,
            f"  アーキテクチャ: {arch}",
            f"  説明: {arch_desc}",
            f"  対応CPU: {'Intel/AMD 64ビット' if arch == 'amd64' else 'その他'}",
            ""
        ])
    
    def _add_section_3_setup_behavior(self, config: Dict[str, Any]):
        """3. セットアップの挙動"""
        self.log_lines.extend([
            "【3. セットアップの挙動】",
            "-" * 40,
            f"  マシンOOBEスキップ: {'有効' if config.get('skip_machine_oobe', True) else '無効'}",
            f"  ユーザーOOBEスキップ: {'有効' if config.get('skip_user_oobe', False) else '無効'}",
            f"  使用許諾契約の非表示: {'有効' if config.get('hide_eula_page', True) else '無効'}",
            f"  OEM登録画面の非表示: {'有効' if config.get('hide_oem_registration', True) else '無効'}",
            f"  オンラインアカウント画面の非表示: {'有効' if config.get('hide_online_account_screens', True) else '無効'}",
            f"  ワイヤレス設定の非表示: {'有効' if config.get('hide_wireless_setup', False) else '無効'}",
            f"  ネットワークの場所: {config.get('network_location', 'Work')}",
            f"  ドメイン参加のスキップ: {'有効' if config.get('skip_domain_join', True) else '無効'}",
            ""
        ])
    
    def _add_section_4_windows_edition(self, config: Dict[str, Any]):
        """4. エディション/プロダクトキー"""
        self.log_lines.extend([
            "【4. エディション/プロダクトキー】",
            "-" * 40,
            f"  Windowsエディション: {config.get('windows_edition', 'Windows 11 Pro')}",
            f"  プロダクトキー: {config.get('product_key', '未設定') if config.get('product_key') else '未設定（インストール時に入力）'}",
            f"  使用許諾契約の自動承諾: {'有効' if config.get('accept_eula', True) else '無効'}",
            f"  利用可能なパーティションへのインストール: {'有効' if config.get('install_to_available_partition', True) else '無効'}",
            f"  UIの表示設定: {config.get('will_show_ui', 'OnError')}",
            ""
        ])
    
    def _add_section_5_windows_pe(self, config: Dict[str, Any]):
        """5. Windows PE ステージ"""
        pe_config = config.get('windows_pe', {})
        self.log_lines.extend([
            "【5. Windows PE ステージ】",
            "-" * 40,
            f"  コマンドプロンプトの無効化: {'有効' if pe_config.get('disable_command_prompt', False) else '無効'}",
            f"  ファイアウォールの無効化: {'有効' if pe_config.get('disable_firewall', True) else '無効'}",
            f"  ネットワークの有効化: {'有効' if pe_config.get('enable_network', True) else '無効'}",
            f"  リモートアシスタンスの有効化: {'有効' if pe_config.get('enable_remote_assistance', False) else '無効'}",
            f"  ページファイル: {pe_config.get('page_file', 'Auto')}",
            f"  スクラッチ領域: {pe_config.get('scratch_space', 512)}MB",
            ""
        ])
    
    def _add_section_6_disk_config(self, config: Dict[str, Any]):
        """6. ディスク構成"""
        disk = config.get('disk_config', {})
        self.log_lines.extend([
            "【6. ディスク構成】",
            "-" * 40,
            f"  ディスクの初期化: {'有効' if disk.get('wipe_disk', True) else '無効'}",
            f"  対象ディスクID: {disk.get('disk_id', 0)}",
            f"  パーティションスタイル: {disk.get('partition_style', 'GPT')}",
        ])
        
        partitions = disk.get('partitions', [])
        if partitions:
            self.log_lines.append("  パーティション構成:")
            for i, part in enumerate(partitions, 1):
                size = part.get('size')
                size_str = f"{size}MB" if isinstance(size, int) else size
                self.log_lines.append(f"    {i}. {part.get('type')}: {size_str}")
        
        self.log_lines.append("")
    
    def _add_section_7_computer_settings(self, config: Dict[str, Any]):
        """7. コンピューター設定"""
        self.log_lines.extend([
            "【7. コンピューター設定】",
            "-" * 40,
            f"  コンピューター名: {config.get('computer_name', '*')} {'(自動生成)' if config.get('computer_name') == '*' else ''}",
            f"  組織名: {config.get('organization', '未設定')}",
            f"  所有者: {config.get('owner', '未設定')}",
            f"  ドメイン参加: {'有効' if config.get('join_domain', False) else '無効'}",
        ])
        
        if config.get('join_domain'):
            self.log_lines.extend([
                f"  ドメイン名: {config.get('domain', '')}",
                f"  OU: {config.get('domain_ou', '')}",
            ])
        else:
            self.log_lines.append(f"  ワークグループ: {config.get('workgroup', 'WORKGROUP')}")
        
        self.log_lines.append("")
    
    def _add_section_8_user_accounts(self, config: Dict[str, Any]):
        """8. ユーザーアカウント"""
        self.log_lines.extend([
            "【8. ユーザーアカウント】",
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
                    f"    自動ログオン: {'有効' if account.get('auto_logon', False) else '無効'}",
                    f"    パスワード無期限: {'有効' if account.get('password_never_expires', True) else '無効'}",
                ])
        else:
            self.log_lines.append("  ローカルアカウントは設定されていません")
        
        self.log_lines.extend([
            "",
            f"  自動ログオン回数: {config.get('auto_logon_count', 0)}",
            f"  管理者アカウントの無効化: {'有効' if config.get('disable_admin_account', True) else '無効'}",
            f"  ゲストアカウントの有効化: {'有効' if config.get('enable_guest_account', False) else '無効'}",
            ""
        ])
    
    def _add_section_9_explorer_settings(self, config: Dict[str, Any]):
        """9. エクスプローラー調整"""
        explorer = config.get('explorer_settings', {})
        self.log_lines.extend([
            "【9. エクスプローラー調整】",
            "-" * 40,
            f"  隠しファイルの表示: {'有効' if explorer.get('show_hidden_files', False) else '無効'}",
            f"  ファイル拡張子の表示: {'有効' if explorer.get('show_file_extensions', True) else '無効'}",
            f"  保護されたOSファイルの表示: {'有効' if explorer.get('show_protected_os_files', False) else '無効'}",
            f"  サムネイルキャッシュの無効化: {'有効' if explorer.get('disable_thumbnail_cache', False) else '無効'}",
            f"  Thumbs.dbの無効化: {'有効' if explorer.get('disable_thumbs_db', False) else '無効'}",
            f"  起動時の表示: {explorer.get('launch_to', 'このPC')}",
            f"  ナビゲーションペインの展開: {'有効' if explorer.get('nav_pane_expand', True) else '無効'}",
            f"  ナビゲーションペインにすべて表示: {'有効' if explorer.get('nav_pane_show_all', False) else '無効'}",
            ""
        ])
    
    def _add_section_10_start_taskbar(self, config: Dict[str, Any]):
        """10. スタート/タスクバー"""
        start = config.get('start_taskbar', {})
        self.log_lines.extend([
            "【10. スタート/タスクバー】",
            "-" * 40,
            f"  タスクバーの配置: {start.get('taskbar_alignment', '中央')}",
            f"  タスクバー検索: {start.get('taskbar_search', 'アイコン')}",
            f"  ウィジェット: {'表示' if start.get('taskbar_widgets', False) else '非表示'}",
            f"  チャット: {'表示' if start.get('taskbar_chat', False) else '非表示'}",
            f"  タスクビュー: {'表示' if start.get('taskbar_task_view', True) else '非表示'}",
            f"  スタートメニューレイアウト: {start.get('start_menu_layout', 'デフォルト')}",
            f"  最近追加した項目: {'表示' if start.get('show_recently_added', True) else '非表示'}",
            f"  よく使うアプリ: {'表示' if start.get('show_most_used', True) else '非表示'}",
            f"  おすすめ: {'表示' if start.get('show_suggestions', False) else '非表示'}",
            ""
        ])
    
    def _add_section_11_system_tweaks(self, config: Dict[str, Any]):
        """11. システム調整"""
        tweaks = config.get('system_tweaks', {})
        self.log_lines.extend([
            "【11. システム調整】",
            "-" * 40,
            f"  UAC無効化: {'有効' if tweaks.get('disable_uac', False) else '無効'}",
            f"  SmartScreen無効化: {'有効' if tweaks.get('disable_smart_screen', False) else '無効'}",
            f"  Windows Defender無効化: {'有効' if tweaks.get('disable_windows_defender', False) else '無効'}",
            f"  ファイアウォール無効化: {'有効' if tweaks.get('disable_firewall', False) else '無効'}",
            f"  Windows Update無効化: {'有効' if tweaks.get('disable_updates', False) else '無効'}",
            f"  テレメトリ無効化: {'有効' if tweaks.get('disable_telemetry', True) else '無効'}",
            f"  Cortana無効化: {'有効' if tweaks.get('disable_cortana', True) else '無効'}",
            f"  Web検索無効化: {'有効' if tweaks.get('disable_search_web', True) else '無効'}",
            f"  ゲームバー無効化: {'有効' if tweaks.get('disable_game_bar', True) else '無効'}",
            f"  高速スタートアップ: {'有効' if tweaks.get('fast_startup', False) else '無効'}",
            f"  ハイバネーション: {'有効' if tweaks.get('hibernation', False) else '無効'}",
            ""
        ])
    
    def _add_section_12_visual_effects(self, config: Dict[str, Any]):
        """12. 視覚効果"""
        visual = config.get('visual_effects', {})
        self.log_lines.extend([
            "【12. 視覚効果】",
            "-" * 40,
            f"  パフォーマンスモード: {visual.get('performance_mode', 'バランス')}",
            f"  透明効果: {'有効' if visual.get('transparency', True) else '無効'}",
            f"  アニメーション: {'有効' if visual.get('animations', True) else '無効'}",
            f"  影: {'有効' if visual.get('shadows', True) else '無効'}",
            f"  スムーズエッジ: {'有効' if visual.get('smooth_edges', True) else '無効'}",
            f"  フォントスムージング: {visual.get('font_smoothing', 'ClearType')}",
            f"  壁紙品質: {visual.get('wallpaper_quality', 'フィル')}",
            ""
        ])
    
    def _add_section_13_desktop_settings(self, config: Dict[str, Any]):
        """13. デスクトップ設定"""
        icons = config.get('desktop_icons', {})
        desktop = config.get('desktop_settings', {})
        
        self.log_lines.extend([
            "【13. デスクトップ設定】",
            "-" * 40,
            "  [デスクトップアイコン]",
            f"    このPC: {'表示' if icons.get('computer', True) else '非表示'}",
            f"    ユーザーフォルダー: {'表示' if icons.get('user_files', True) else '非表示'}",
            f"    ネットワーク: {'表示' if icons.get('network', False) else '非表示'}",
            f"    ごみ箱: {'表示' if icons.get('recycle_bin', True) else '非表示'}",
            f"    コントロールパネル: {'表示' if icons.get('control_panel', False) else '非表示'}",
            "",
            "  [アイコン設定]",
            f"    アイコンサイズ: {desktop.get('icon_size', '中')}",
            f"    アイコン間隔: {desktop.get('icon_spacing', 'デフォルト')}",
            f"    自動整列: {'有効' if desktop.get('auto_arrange', False) else '無効'}",
            f"    グリッドに合わせる: {'有効' if desktop.get('align_to_grid', True) else '無効'}",
            ""
        ])
    
    def _add_section_14_vm_support(self, config: Dict[str, Any]):
        """14. 仮想マシンサポート"""
        vm = config.get('vm_support', {})
        self.log_lines.extend([
            "【14. 仮想マシンサポート】",
            "-" * 40,
            f"  Hyper-V: {'有効' if vm.get('enable_hyperv', False) else '無効'}",
            f"  WSL: {'有効' if vm.get('enable_wsl', False) else '無効'}",
            f"  WSL 2: {'有効' if vm.get('enable_wsl2', False) else '無効'}",
            f"  Windows Sandbox: {'有効' if vm.get('enable_sandbox', False) else '無効'}",
            f"  コンテナー: {'有効' if vm.get('enable_containers', False) else '無効'}",
            f"  仮想化: {'有効' if vm.get('enable_virtualization', True) else '無効'}",
            f"  ネストされた仮想化: {'有効' if vm.get('nested_virtualization', False) else '無効'}",
            ""
        ])
    
    def _add_section_15_wifi_settings(self, config: Dict[str, Any]):
        """15. Wi-Fi設定"""
        self.log_lines.extend([
            "【15. Wi-Fi設定】",
            "-" * 40
        ])
        
        wifi = config.get('wifi_settings')
        if wifi and wifi.get('ssid'):
            auth_type_display = {
                'WPA2PSK': 'WPA2',
                'WPA3PSK': 'WPA3',
                'WPA2': 'WPA2-Enterprise',
                'WPA3': 'WPA3-Enterprise'
            }.get(wifi.get('auth_type', 'WPA2PSK'), wifi.get('auth_type', 'WPA2PSK'))
            
            self.log_lines.extend([
                "  次の設定を使用してWi-Fiを構成します:",
                f"  ネットワーク名(SSID): {wifi['ssid']}",
                f"  パスワード: {'●' * len(wifi.get('password', '')[:8]) + '...' if wifi.get('password') else '未設定'}",
                f"    (実際のパスワード: 設定済み)",
                f"  認証: {auth_type_display}",
                f"  暗号化: {wifi.get('encryption', 'AES')}",
                f"  自動的に接続する: {'はい' if wifi.get('connect_automatically', True) else 'いいえ'}",
                f"  ブロードキャストしていなくても接続する: {'はい' if wifi.get('connect_even_not_broadcasting', False) else 'いいえ'}",
            ])
        else:
            self.log_lines.append("  Wi-Fi設定をスキップ（セットアップ時に手動設定）")
        
        self.log_lines.append("")
    
    def _add_section_16_express_settings(self, config: Dict[str, Any]):
        """16. Express Settings"""
        express = config.get('express_settings', {})
        mode = express.get('mode', 'default')
        
        self.log_lines.extend([
            "【16. Express Settings】",
            "-" * 40,
            f"  モード: {mode}",
            f"  診断データ送信: {'有効' if express.get('send_diagnostic_data', True) else '無効'}",
            f"  手書き入力の改善: {'有効' if express.get('improve_inking', True) else '無効'}",
            f"  カスタマイズされたエクスペリエンス: {'有効' if express.get('tailored_experiences', True) else '無効'}",
            f"  広告ID: {'有効' if express.get('advertising_id', True) else '無効'}",
            f"  位置情報サービス: {'有効' if express.get('location_services', False) else '無効'}",
            f"  デバイスの検索: {'有効' if express.get('find_my_device', False) else '無効'}",
            ""
        ])
    
    def _add_section_17_lock_keys(self, config: Dict[str, Any]):
        """17. ロックキー設定"""
        lock = config.get('lock_keys', {})
        self.log_lines.extend([
            "【17. ロックキー設定】",
            "-" * 40,
            f"  NumLock: {'有効' if lock.get('num_lock', True) else '無効'}",
            f"  CapsLock: {'有効' if lock.get('caps_lock', False) else '無効'}",
            f"  ScrollLock: {'有効' if lock.get('scroll_lock', False) else '無効'}",
            ""
        ])
    
    def _add_section_18_sticky_keys(self, config: Dict[str, Any]):
        """18. 固定キー"""
        sticky = config.get('sticky_keys', {})
        self.log_lines.extend([
            "【18. 固定キー】",
            "-" * 40,
            f"  固定キー機能: {'有効' if sticky.get('enabled', False) else '無効'}",
            f"  修飾キーのロック: {'有効' if sticky.get('lock_modifier', False) else '無効'}",
            f"  2つのキーで無効化: {'有効' if sticky.get('turn_off_on_two_keys', True) else '無効'}",
            f"  フィードバック: {'有効' if sticky.get('feedback', False) else '無効'}",
            f"  ビープ音: {'有効' if sticky.get('beep', False) else '無効'}",
            ""
        ])
    
    def _add_section_19_personalization(self, config: Dict[str, Any]):
        """19. 個人用設定"""
        personal = config.get('personalization', {})
        self.log_lines.extend([
            "【19. 個人用設定】",
            "-" * 40,
            f"  テーマ: {personal.get('theme', 'ライト')}",
            f"  アクセントカラー: #{personal.get('accent_color', '0078D4')}",
            f"  スタートのカラー: {'有効' if personal.get('start_color', True) else '無効'}",
            f"  タスクバーのカラー: {'有効' if personal.get('taskbar_color', True) else '無効'}",
            f"  タイトルバーのカラー: {'有効' if personal.get('title_bar_color', True) else '無効'}",
            f"  ロック画面の画像: {personal.get('lock_screen_image', 'デフォルト')}",
            f"  ユーザー画像: {personal.get('user_picture', 'デフォルト')}",
            f"  サウンドスキーム: {personal.get('sounds_scheme', 'Windows デフォルト')}",
            f"  マウスカーソルスキーム: {personal.get('mouse_cursor_scheme', 'Windows デフォルト')}",
            ""
        ])
    
    def _add_section_20_remove_apps(self, config: Dict[str, Any]):
        """20. 不要なアプリの削除"""
        apps = config.get('remove_apps', [])
        self.log_lines.extend([
            "【20. 不要なアプリの削除】",
            "-" * 40
        ])
        
        if apps:
            self.log_lines.append(f"  削除予定のアプリ: {len(apps)}個")
            for i, app in enumerate(apps[:15], 1):  # 最初の15個のみ表示
                self.log_lines.append(f"    {i}. {app}")
            if len(apps) > 15:
                self.log_lines.append(f"    ...他 {len(apps) - 15} 個のアプリ")
        else:
            self.log_lines.append("  削除するアプリはありません")
        
        self.log_lines.append("")
    
    def _add_section_21_custom_scripts(self, config: Dict[str, Any]):
        """21. カスタムスクリプト"""
        self.log_lines.extend([
            "【21. カスタムスクリプト】",
            "-" * 40
        ])
        
        first_logon = config.get('first_logon_commands', [])
        if first_logon:
            self.log_lines.append("  [初回ログオン時実行コマンド]")
            for cmd in first_logon[:5]:
                self.log_lines.append(f"    順序{cmd.get('order', 1)}: {cmd.get('description', cmd.get('command', ''))}")
                if cmd.get('requires_restart'):
                    self.log_lines.append("      ※ 再起動が必要")
        
        setup_scripts = config.get('setup_scripts', [])
        if setup_scripts:
            self.log_lines.append("  [セットアップスクリプト]")
            for script in setup_scripts[:5]:
                self.log_lines.append(f"    順序{script.get('order', 1)}: {script.get('description', script.get('path', ''))}")
        
        if not first_logon and not setup_scripts:
            self.log_lines.append("  カスタムスクリプトは設定されていません")
        
        self.log_lines.append("")
    
    def _add_section_22_wdac(self, config: Dict[str, Any]):
        """22. WDAC設定"""
        wdac = config.get('wdac', {})
        self.log_lines.extend([
            "【22. WDAC設定 (Windows Defender Application Control)】",
            "-" * 40,
            f"  WDAC: {'有効' if wdac.get('enabled', False) else '無効'}",
        ])
        
        if wdac.get('enabled'):
            self.log_lines.extend([
                f"  ポリシーモード: {wdac.get('policy_mode', '監査')}",
                f"  Microsoftアプリ許可: {'有効' if wdac.get('allow_microsoft_apps', True) else '無効'}",
                f"  ストアアプリ許可: {'有効' if wdac.get('allow_store_apps', True) else '無効'}",
                f"  評判の良いアプリ許可: {'有効' if wdac.get('allow_reputable_apps', False) else '無効'}",
            ])
        
        self.log_lines.append("")
    
    def _add_section_23_additional_components(self, config: Dict[str, Any]):
        """23. その他のコンポーネント"""
        self.log_lines.extend([
            "【23. その他のコンポーネント】",
            "-" * 40,
            f"  .NET Framework 3.5: {'有効' if config.get('enable_dotnet35', False) else '無効'}",
            f"  .NET Framework 4.8: {'有効' if config.get('enable_dotnet48', True) else '無効'}",
            f"  IIS (インターネットインフォメーションサービス): {'有効' if config.get('enable_iis', False) else '無効'}",
            f"  Telnetクライアント: {'有効' if config.get('enable_telnet_client', False) else '無効'}",
            f"  TFTPクライアント: {'有効' if config.get('enable_tftp_client', False) else '無効'}",
            f"  SMB 1.0: {'有効' if config.get('enable_smb1', False) else '無効'}",
            f"  PowerShell 2.0: {'有効' if config.get('enable_powershell2', False) else '無効'}",
            f"  DirectPlay: {'有効' if config.get('enable_directplay', False) else '無効'}",
            f"  PDF印刷: {'有効' if config.get('enable_print_to_pdf', True) else '無効'}",
            f"  XPSビューアー: {'有効' if config.get('enable_xps_viewer', False) else '無効'}",
            f"  メディア機能: {'有効' if config.get('enable_media_features', True) else '無効'}",
            f"  ワークフォルダー: {'有効' if config.get('enable_work_folders', False) else '無効'}",
            ""
        ])
    
    def _add_footer(self):
        """ログフッターを追加"""
        self.log_lines.extend([
            "=" * 80,
            "【注意事項】",
            "-" * 40,
            "1. このログファイルはautounattend.xmlと共に保管してください",
            "2. パスワードは暗号化されており、このログには平文で記載されません",
            "3. 実際のインストール時の動作は、ハードウェアや環境により異なる場合があります",
            "4. 問題が発生した場合は、このログを参照して設定を確認してください",
            "5. すべての設定項目（全23セクション）が記録されています",
            "",
            "=" * 80,
            f"ログ生成完了: {datetime.now().strftime('%Y年%m月%d日 %H時%M分%S秒')}",
            "=" * 80
        ])
    
    def save_comprehensive_log(self, filepath: str, config: Dict[str, Any]) -> bool:
        """
        包括的ログをファイルに保存
        """
        try:
            log_content = self.generate_comprehensive_log(config)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(log_content)
            return True
        except Exception as e:
            print(f"ログ保存エラー: {e}")
            return False