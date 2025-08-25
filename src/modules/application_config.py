"""
Windows 11 アプリケーション設定管理モジュール

Windows 11のunattend.xmlファイル用のアプリケーション設定を生成します。
デフォルトアプリケーション、Office設定、タスクバー設定、スタートメニュー設定、
セキュリティソフト確認、Windows Update設定等を管理します。
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from lxml import etree

logger = logging.getLogger(__name__)


class DefaultApplicationType(Enum):
    """デフォルトアプリケーションタイプ"""
    BROWSER = "Browser"
    EMAIL = "Email"
    PDF_READER = "PDFReader"
    VIDEO_PLAYER = "VideoPlayer"
    AUDIO_PLAYER = "AudioPlayer"
    IMAGE_VIEWER = "ImageViewer"
    TEXT_EDITOR = "TextEditor"


class OfficeProtectionView(Enum):
    """Office保護ビューの設定"""
    DISABLED = "Disabled"
    ENABLED = "Enabled"
    FILES_FROM_INTERNET = "FilesFromInternet"
    UNSAFE_LOCATIONS = "UnsafeLocations"
    OUTLOOK_ATTACHMENTS = "OutlookAttachments"


class TaskbarPosition(Enum):
    """タスクバーの位置"""
    BOTTOM = 0
    LEFT = 1
    TOP = 2
    RIGHT = 3


class StartMenuLayout(Enum):
    """スタートメニューレイアウト"""
    FULL_SCREEN = "FullScreen"
    WINDOWED = "Windowed"
    CLASSIC = "Classic"


@dataclass
class DefaultApplication:
    """デフォルトアプリケーションの設定"""
    app_type: DefaultApplicationType
    application_name: str
    executable_path: str
    file_associations: List[str] = field(default_factory=list)
    protocol_associations: List[str] = field(default_factory=list)
    registry_path: Optional[str] = None
    prog_id: Optional[str] = None
    
    def to_registry_commands(self) -> List[str]:
        """レジストリ設定コマンドを生成"""
        commands = []
        
        # ファイル関連付け設定
        for ext in self.file_associations:
            if self.prog_id:
                commands.append(
                    f'reg add "HKLM\\SOFTWARE\\Classes\\{ext}" /ve /t REG_SZ /d "{self.prog_id}" /f'
                )
                commands.append(
                    f'reg add "HKLM\\SOFTWARE\\Classes\\{self.prog_id}\\shell\\open\\command" '
                    f'/ve /t REG_SZ /d "\\"{self.executable_path}\\" \\"%1\\"" /f'
                )
        
        # プロトコル関連付け設定
        for protocol in self.protocol_associations:
            if self.prog_id:
                commands.append(
                    f'reg add "HKLM\\SOFTWARE\\Classes\\{protocol}" /ve /t REG_SZ /d "{self.prog_id}" /f'
                )
                commands.append(
                    f'reg add "HKLM\\SOFTWARE\\Classes\\{protocol}\\shell\\open\\command" '
                    f'/ve /t REG_SZ /d "\\"{self.executable_path}\\" \\"%1\\"" /f'
                )
        
        return commands


@dataclass 
class TaskbarConfiguration:
    """タスクバー設定"""
    position: TaskbarPosition = TaskbarPosition.BOTTOM
    auto_hide: bool = False
    show_badges: bool = True
    show_cortana_button: bool = False
    show_task_view_button: bool = True
    show_widgets_button: bool = False
    combine_buttons: bool = True
    small_icons: bool = False
    pinned_applications: List[str] = field(default_factory=list)
    unpinned_applications: List[str] = field(default_factory=list)
    
    def to_registry_commands(self) -> List[str]:
        """レジストリ設定コマンドを生成"""
        commands = []
        
        # タスクバー位置設定
        commands.append(
            f'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StuckRects3" '
            f'/v Settings /t REG_BINARY /d "30000000feffffff{self.position.value:02x}000000" /f'
        )
        
        # 自動非表示設定
        if self.auto_hide:
            commands.append(
                'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StuckRects3" '
                '/v Settings /t REG_BINARY /d "30000000feffffff01000000" /f'
            )
        
        # Cortanaボタン非表示
        if not self.show_cortana_button:
            commands.append(
                'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" '
                '/v ShowCortanaButton /t REG_DWORD /d 0 /f'
            )
        
        # タスクビューボタン設定
        commands.append(
            'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" '
            f'/v ShowTaskViewButton /t REG_DWORD /d {1 if self.show_task_view_button else 0} /f'
        )
        
        # ウィジェットボタン非表示
        if not self.show_widgets_button:
            commands.append(
                'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" '
                '/v TaskbarDa /t REG_DWORD /d 0 /f'
            )
        
        # スモールアイコン設定
        if self.small_icons:
            commands.append(
                'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" '
                '/v TaskbarSmallIcons /t REG_DWORD /d 1 /f'
            )
        
        return commands
    
    def to_powershell_commands(self) -> List[str]:
        """PowerShellコマンドを生成"""
        commands = []
        
        # アプリケーションのピン留め解除
        for app in self.unpinned_applications:
            commands.append(
                f'(New-Object -Com Shell.Application).NameSpace("shell::{{4234d49b-0245-4df3-b780-3893943456e1}}").Items() | '
                f'Where-Object {{$_.Name -eq "{app}"}} | '
                f'ForEach-Object {{$_.Verbs() | Where-Object {{$_.Name -eq "タスク バーからピン留めを外す(&U)"}} | '
                f'ForEach-Object {{$_.DoIt()}}}}'
            )
        
        # アプリケーションのピン留め
        for app in self.pinned_applications:
            commands.append(
                f'$app = Get-StartApps | Where-Object {{$_.Name -like "*{app}*"}}; '
                f'if ($app) {{ $app | ForEach-Object {{ '
                f'(New-Object -Com Shell.Application).NameSpace($_.AppID).Self.InvokeVerb("taskbarpin") }} }}'
            )
        
        return commands


@dataclass
class StartMenuConfiguration:
    """スタートメニュー設定"""
    layout: StartMenuLayout = StartMenuLayout.WINDOWED
    show_recently_added_apps: bool = False
    show_most_used_apps: bool = False
    show_suggestions: bool = False
    show_recently_opened_items: bool = False
    custom_layout_path: Optional[str] = None
    pinned_apps: List[str] = field(default_factory=list)
    
    def to_registry_commands(self) -> List[str]:
        """レジストリ設定コマンドを生成"""
        commands = []
        
        # スタートメニューレイアウト設定
        if self.layout == StartMenuLayout.FULL_SCREEN:
            commands.append(
                'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" '
                '/v Start_TrackProgs /t REG_DWORD /d 0 /f'
            )
        
        # 最近追加されたアプリの表示
        commands.append(
            'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" '
            f'/v Start_TrackProgs /t REG_DWORD /d {1 if self.show_recently_added_apps else 0} /f'
        )
        
        # よく使うアプリの表示
        commands.append(
            'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" '
            f'/v Start_TrackDocs /t REG_DWORD /d {1 if self.show_most_used_apps else 0} /f'
        )
        
        # 提案の表示
        if not self.show_suggestions:
            commands.append(
                'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" '
                '/v SubscribedContent-338388Enabled /t REG_DWORD /d 0 /f'
            )
        
        # 最近開いた項目の表示
        commands.append(
            'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" '
            f'/v Start_TrackDocs /t REG_DWORD /d {1 if self.show_recently_opened_items else 0} /f'
        )
        
        return commands
    
    def get_import_layout_command(self) -> Optional[str]:
        """レイアウトインポートコマンドを取得"""
        if self.custom_layout_path and Path(self.custom_layout_path).exists():
            return f'Import-StartLayout -LayoutPath "{self.custom_layout_path}" -MountPath C:\\'
        return None


@dataclass
class OfficeConfiguration:
    """Office設定"""
    disable_first_run_dialog: bool = True
    update_mode: str = "automatic"  # automatic, manual, disabled
    protection_view_internet: OfficeProtectionView = OfficeProtectionView.DISABLED
    protection_view_unsafe_locations: OfficeProtectionView = OfficeProtectionView.DISABLED
    protection_view_outlook_attachments: OfficeProtectionView = OfficeProtectionView.DISABLED
    disable_macro_warnings: bool = False
    enable_vba_object_model: bool = False
    office_version: str = "2016"  # 2016, 2019, 365
    
    def to_registry_commands(self) -> List[str]:
        """レジストリ設定コマンドを生成"""
        commands = []
        
        # Office バージョンに基づくレジストリパス
        version_paths = {
            "2016": "16.0",
            "2019": "16.0", 
            "365": "16.0"
        }
        version_path = version_paths.get(self.office_version, "16.0")
        
        office_apps = ["Word", "Excel", "PowerPoint", "Outlook", "Access"]
        
        for app in office_apps:
            app_path = f"HKCU\\SOFTWARE\\Microsoft\\Office\\{version_path}\\{app}\\Security"
            
            # 保護ビュー設定
            if self.protection_view_internet == OfficeProtectionView.DISABLED:
                commands.append(
                    f'reg add "{app_path}\\ProtectedView" '
                    f'/v DisableInternetFilesInPV /t REG_DWORD /d 1 /f'
                )
            
            if self.protection_view_unsafe_locations == OfficeProtectionView.DISABLED:
                commands.append(
                    f'reg add "{app_path}\\ProtectedView" '
                    f'/v DisableUnsafeLocationsInPV /t REG_DWORD /d 1 /f'
                )
            
            if self.protection_view_outlook_attachments == OfficeProtectionView.DISABLED:
                commands.append(
                    f'reg add "{app_path}\\ProtectedView" '
                    f'/v DisableAttachmentsInPV /t REG_DWORD /d 1 /f'
                )
            
            # マクロ設定
            if self.disable_macro_warnings:
                commands.append(
                    f'reg add "{app_path}" /v Level /t REG_DWORD /d 1 /f'
                )
            
            if self.enable_vba_object_model:
                commands.append(
                    f'reg add "{app_path}" /v AccessVBOM /t REG_DWORD /d 1 /f'
                )
        
        # 初回実行ダイアログ無効化
        if self.disable_first_run_dialog:
            commands.extend([
                f'reg add "HKCU\\SOFTWARE\\Microsoft\\Office\\{version_path}\\Common\\General" '
                f'/v ShownFirstRunOptin /t REG_DWORD /d 1 /f',
                f'reg add "HKCU\\SOFTWARE\\Microsoft\\Office\\{version_path}\\Common\\General" '
                f'/v ShownOptinDialog /t REG_DWORD /d 1 /f'
            ])
        
        # 更新モード設定
        update_values = {
            "automatic": 0,
            "manual": 2,
            "disabled": 1
        }
        update_value = update_values.get(self.update_mode, 0)
        commands.append(
            f'reg add "HKLM\\SOFTWARE\\Microsoft\\Office\\{version_path}\\Common\\OfficeUpdate" '
            f'/v EnableAutomaticUpdates /t REG_DWORD /d {update_value} /f'
        )
        
        return commands


@dataclass
class SecuritySoftware:
    """セキュリティソフトウェア設定"""
    name: str
    executable_path: Optional[str] = None
    service_name: Optional[str] = None
    registry_keys: List[str] = field(default_factory=list)
    check_installation: bool = True
    
    def get_check_commands(self) -> List[str]:
        """インストール確認コマンドを生成"""
        commands = []
        
        if self.check_installation:
            # サービス確認
            if self.service_name:
                commands.append(
                    f'sc query "{self.service_name}" > nul 2>&1 || echo "{self.name} service not found"'
                )
            
            # 実行ファイル確認
            if self.executable_path:
                commands.append(
                    f'if not exist "{self.executable_path}" echo "{self.name} executable not found"'
                )
            
            # レジストリキー確認
            for reg_key in self.registry_keys:
                commands.append(
                    f'reg query "{reg_key}" > nul 2>&1 || echo "{self.name} registry key not found: {reg_key}"'
                )
        
        return commands


@dataclass
class DesktopIconConfiguration:
    """デスクトップアイコン設定"""
    show_this_pc: bool = True
    show_network: bool = True
    show_recycle_bin: bool = True
    show_control_panel: bool = False
    show_user_files: bool = False
    
    def to_registry_commands(self) -> List[str]:
        """レジストリ設定コマンドを生成"""
        commands = []
        
        # デスクトップアイコン設定のベースパス
        base_path = "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\HideDesktopIcons\\NewStartPanel"
        
        # このPC
        commands.append(
            f'reg add "{base_path}" /v "{{20D04FE0-3AEA-1069-A2D8-08002B30309D}}" '
            f'/t REG_DWORD /d {0 if self.show_this_pc else 1} /f'
        )
        
        # ネットワーク
        commands.append(
            f'reg add "{base_path}" /v "{{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}}" '
            f'/t REG_DWORD /d {0 if self.show_network else 1} /f'
        )
        
        # ごみ箱
        commands.append(
            f'reg add "{base_path}" /v "{{645FF040-5081-101B-9F08-00AA002F954E}}" '
            f'/t REG_DWORD /d {0 if self.show_recycle_bin else 1} /f'
        )
        
        # コントロールパネル
        commands.append(
            f'reg add "{base_path}" /v "{{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}}" '
            f'/t REG_DWORD /d {0 if self.show_control_panel else 1} /f'
        )
        
        # ユーザーファイル
        commands.append(
            f'reg add "{base_path}" /v "{{59031a47-3f72-44a7-89c5-5595fe6b30ee}}" '
            f'/t REG_DWORD /d {0 if self.show_user_files else 1} /f'
        )
        
        return commands


@dataclass
class WindowsUpdateConfiguration:
    """Windows Update設定"""
    auto_update_option: int = 2  # 1=無効, 2=通知のみ, 3=自動ダウンロード/手動インストール, 4=自動
    scheduled_day: int = 0  # 0=毎日, 1=日曜日, 2=月曜日, ...
    scheduled_time: int = 3  # 0-23時
    disable_auto_restart: bool = True
    defer_feature_updates: bool = False
    defer_quality_updates: bool = False
    
    def to_registry_commands(self) -> List[str]:
        """レジストリ設定コマンドを生成"""
        commands = []
        
        base_path = "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU"
        
        # 自動更新オプション
        commands.append(
            f'reg add "{base_path}" /v AUOptions /t REG_DWORD /d {self.auto_update_option} /f'
        )
        
        # スケジュール設定
        if self.auto_update_option == 4:  # 自動インストールの場合
            commands.extend([
                f'reg add "{base_path}" /v ScheduledInstallDay /t REG_DWORD /d {self.scheduled_day} /f',
                f'reg add "{base_path}" /v ScheduledInstallTime /t REG_DWORD /d {self.scheduled_time} /f'
            ])
        
        # 自動再起動無効化
        if self.disable_auto_restart:
            commands.extend([
                f'reg add "{base_path}" /v NoAutoRebootWithLoggedOnUsers /t REG_DWORD /d 1 /f',
                f'reg add "{base_path}" /v AUPowerManagement /t REG_DWORD /d 0 /f'
            ])
        
        # 機能更新の延期
        if self.defer_feature_updates:
            commands.append(
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate" '
                '/v DeferFeatureUpdates /t REG_DWORD /d 1 /f'
            )
        
        # 品質更新の延期
        if self.defer_quality_updates:
            commands.append(
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate" '
                '/v DeferQualityUpdates /t REG_DWORD /d 1 /f'
            )
        
        return commands


class ApplicationManager:
    """アプリケーション設定統合管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.default_applications: List[DefaultApplication] = []
        self.taskbar_config = TaskbarConfiguration()
        self.start_menu_config = StartMenuConfiguration()
        self.office_config = OfficeConfiguration()
        self.desktop_config = DesktopIconConfiguration()
        self.windows_update_config = WindowsUpdateConfiguration()
        self.security_software: List[SecuritySoftware] = []
        self.custom_commands: List[Dict[str, Any]] = []
        
    def add_default_application(self, app: DefaultApplication) -> None:
        """デフォルトアプリケーションを追加"""
        self.default_applications.append(app)
        logger.info(f"デフォルトアプリケーション追加: {app.application_name}")
    
    def configure_taskbar(self, config: TaskbarConfiguration) -> None:
        """タスクバー設定を適用"""
        self.taskbar_config = config
        logger.info("タスクバー設定を更新")
    
    def configure_start_menu(self, config: StartMenuConfiguration) -> None:
        """スタートメニュー設定を適用"""
        self.start_menu_config = config
        logger.info("スタートメニュー設定を更新")
    
    def configure_office(self, config: OfficeConfiguration) -> None:
        """Office設定を適用"""
        self.office_config = config
        logger.info("Office設定を更新")
    
    def configure_desktop_icons(self, config: DesktopIconConfiguration) -> None:
        """デスクトップアイコン設定を適用"""
        self.desktop_config = config
        logger.info("デスクトップアイコン設定を更新")
    
    def configure_windows_update(self, config: WindowsUpdateConfiguration) -> None:
        """Windows Update設定を適用"""
        self.windows_update_config = config
        logger.info("Windows Update設定を更新")
    
    def add_security_software(self, software: SecuritySoftware) -> None:
        """セキュリティソフトウェアを追加"""
        self.security_software.append(software)
        logger.info(f"セキュリティソフトウェア追加: {software.name}")
    
    def add_custom_command(self, command: str, description: str, order: Optional[int] = None) -> None:
        """カスタムコマンドを追加"""
        self.custom_commands.append({
            "command": command,
            "description": description,
            "order": order or len(self.custom_commands) + 1000
        })
        logger.info(f"カスタムコマンド追加: {description}")
    
    def apply_preset_configuration(self, preset_name: str) -> None:
        """プリセット設定を適用"""
        presets = {
            "enterprise_standard": self._apply_enterprise_standard,
            "minimal": self._apply_minimal_configuration,
            "developer": self._apply_developer_configuration
        }
        
        if preset_name in presets:
            presets[preset_name]()
            logger.info(f"プリセット設定適用: {preset_name}")
        else:
            raise ValueError(f"未知のプリセット: {preset_name}")
    
    def _apply_enterprise_standard(self) -> None:
        """企業標準設定を適用"""
        # デフォルトアプリケーション設定
        self.add_default_application(DefaultApplication(
            app_type=DefaultApplicationType.BROWSER,
            application_name="Microsoft Edge",
            executable_path="C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            file_associations=[".html", ".htm", ".url"],
            protocol_associations=["http", "https"],
            prog_id="MSEdgeHTM"
        ))
        
        self.add_default_application(DefaultApplication(
            app_type=DefaultApplicationType.EMAIL,
            application_name="Microsoft Outlook",
            executable_path="C:\\Program Files\\Microsoft Office\\root\\Office16\\OUTLOOK.EXE",
            file_associations=[".msg", ".eml"],
            protocol_associations=["mailto"],
            prog_id="Outlook.File.msg.16"
        ))
        
        self.add_default_application(DefaultApplication(
            app_type=DefaultApplicationType.PDF_READER,
            application_name="Adobe Acrobat Reader DC",
            executable_path="C:\\Program Files (x86)\\Adobe\\Acrobat Reader DC\\Reader\\AcroRd32.exe",
            file_associations=[".pdf"],
            prog_id="AcroExch.Document.DC"
        ))
        
        # タスクバー設定
        self.configure_taskbar(TaskbarConfiguration(
            show_cortana_button=False,
            show_widgets_button=False,
            unpinned_applications=["Mail", "Microsoft Store"],
            pinned_applications=["Microsoft Outlook"]
        ))
        
        # スタートメニュー設定
        self.configure_start_menu(StartMenuConfiguration(
            show_recently_added_apps=False,
            show_suggestions=False
        ))
        
        # Office設定
        self.configure_office(OfficeConfiguration(
            disable_first_run_dialog=True,
            update_mode="automatic",
            protection_view_internet=OfficeProtectionView.DISABLED,
            protection_view_unsafe_locations=OfficeProtectionView.DISABLED,
            protection_view_outlook_attachments=OfficeProtectionView.DISABLED
        ))
        
        # デスクトップアイコン設定
        self.configure_desktop_icons(DesktopIconConfiguration(
            show_this_pc=True,
            show_network=True,
            show_recycle_bin=True
        ))
        
        # セキュリティソフトウェア
        self.add_security_software(SecuritySoftware(
            name="Carbon Black",
            service_name="CarbonBlack",
            registry_keys=["HKLM\\SOFTWARE\\CarbonBlack"]
        ))
        
        self.add_security_software(SecuritySoftware(
            name="FortiClient",
            executable_path="C:\\Program Files\\Fortinet\\FortiClient\\FortiClient.exe",
            service_name="FortiClient",
            registry_keys=["HKLM\\SOFTWARE\\Fortinet\\FortiClient"]
        ))
    
    def _apply_minimal_configuration(self) -> None:
        """最小設定を適用"""
        # 基本的なデフォルトアプリケーションのみ
        self.add_default_application(DefaultApplication(
            app_type=DefaultApplicationType.BROWSER,
            application_name="Microsoft Edge",
            executable_path="C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            file_associations=[".html", ".htm"],
            protocol_associations=["http", "https"],
            prog_id="MSEdgeHTM"
        ))
    
    def _apply_developer_configuration(self) -> None:
        """開発者設定を適用"""
        self._apply_enterprise_standard()
        
        # 開発者向け追加設定
        self.configure_taskbar(TaskbarConfiguration(
            show_cortana_button=False,
            show_widgets_button=False,
            pinned_applications=["Visual Studio Code", "Windows Terminal"]
        ))
    
    def generate_commands(self) -> List[Dict[str, Any]]:
        """すべてのコマンドを生成"""
        commands = []
        order = 1
        
        # デフォルトアプリケーション設定
        for app in self.default_applications:
            for cmd in app.to_registry_commands():
                commands.append({
                    "order": order,
                    "command": cmd,
                    "description": f"Set default application: {app.application_name}",
                    "requires_user_input": False
                })
                order += 1
        
        # タスクバー設定
        for cmd in self.taskbar_config.to_registry_commands():
            commands.append({
                "order": order,
                "command": cmd,
                "description": "Configure taskbar",
                "requires_user_input": False
            })
            order += 1
        
        # タスクバー PowerShell コマンド
        for cmd in self.taskbar_config.to_powershell_commands():
            commands.append({
                "order": order,
                "command": f'powershell -Command "{cmd}"',
                "description": "Configure taskbar pinning",
                "requires_user_input": False
            })
            order += 1
        
        # スタートメニュー設定
        for cmd in self.start_menu_config.to_registry_commands():
            commands.append({
                "order": order,
                "command": cmd,
                "description": "Configure start menu",
                "requires_user_input": False
            })
            order += 1
        
        # Office設定
        for cmd in self.office_config.to_registry_commands():
            commands.append({
                "order": order,
                "command": cmd,
                "description": "Configure Office",
                "requires_user_input": False
            })
            order += 1
        
        # デスクトップアイコン設定
        for cmd in self.desktop_config.to_registry_commands():
            commands.append({
                "order": order,
                "command": cmd,
                "description": "Configure desktop icons",
                "requires_user_input": False
            })
            order += 1
        
        # Windows Update設定
        for cmd in self.windows_update_config.to_registry_commands():
            commands.append({
                "order": order,
                "command": cmd,
                "description": "Configure Windows Update",
                "requires_user_input": False
            })
            order += 1
        
        # セキュリティソフトウェア確認
        for software in self.security_software:
            for cmd in software.get_check_commands():
                commands.append({
                    "order": order,
                    "command": cmd,
                    "description": f"Check {software.name} installation",
                    "requires_user_input": False
                })
                order += 1
        
        # カスタムコマンド
        for custom_cmd in self.custom_commands:
            commands.append({
                "order": custom_cmd.get("order", order),
                "command": custom_cmd["command"],
                "description": custom_cmd["description"],
                "requires_user_input": False
            })
            order += 1
        
        return sorted(commands, key=lambda x: x["order"])
    
    def validate_configuration(self) -> bool:
        """設定の妥当性を検証"""
        try:
            # デフォルトアプリケーションの検証
            for app in self.default_applications:
                if not app.application_name or not app.executable_path:
                    logger.error(f"無効なアプリケーション設定: {app.application_name}")
                    return False
            
            # Office設定の検証
            if self.office_config.office_version not in ["2016", "2019", "365"]:
                logger.error(f"無効なOfficeバージョン: {self.office_config.office_version}")
                return False
            
            # Windows Update設定の検証
            if not 1 <= self.windows_update_config.auto_update_option <= 4:
                logger.error(f"無効なWindows Update設定: {self.windows_update_config.auto_update_option}")
                return False
            
            logger.info("アプリケーション設定の検証完了")
            return True
            
        except Exception as e:
            logger.error(f"設定検証エラー: {e}")
            return False
    
    def generate_xml(self) -> etree.Element:
        """XML要素を生成"""
        commands = self.generate_commands()
        
        first_logon_commands = etree.Element("FirstLogonCommands")
        
        for cmd in commands:
            sync_cmd = etree.SubElement(first_logon_commands, "SynchronousCommand")
            sync_cmd.set("{http://schemas.microsoft.com/WMIConfig/2002/State}action", "add")
            
            order_elem = etree.SubElement(sync_cmd, "Order")
            order_elem.text = str(cmd["order"])
            
            cmd_elem = etree.SubElement(sync_cmd, "CommandLine")
            cmd_elem.text = cmd["command"]
            
            desc_elem = etree.SubElement(sync_cmd, "Description")
            desc_elem.text = cmd["description"]
            
            input_elem = etree.SubElement(sync_cmd, "RequiresUserInput")
            input_elem.text = "false"
        
        return first_logon_commands
    
    def export_default_apps_xml(self, file_path: str) -> None:
        """デフォルトアプリケーション設定XMLをエクスポート"""
        root = etree.Element("DefaultAssociations")
        
        for app in self.default_applications:
            for ext in app.file_associations:
                association = etree.SubElement(root, "Association")
                association.set("Identifier", ext)
                association.set("ProgId", app.prog_id or "")
                association.set("ApplicationName", app.application_name)
            
            for protocol in app.protocol_associations:
                association = etree.SubElement(root, "Association")
                association.set("Identifier", protocol)
                association.set("ProgId", app.prog_id or "")
                association.set("ApplicationName", app.application_name)
        
        tree = etree.ElementTree(root)
        tree.write(file_path, pretty_print=True, xml_declaration=True, encoding="utf-8")
        logger.info(f"デフォルトアプリケーション設定XMLをエクスポート: {file_path}")


class ApplicationAgent:
    """アプリケーション設定管理用SubAgent"""
    
    def __init__(self, manager: ApplicationManager):
        """初期化"""
        self.manager = manager
        self.logger = logging.getLogger(f"{__name__}.Agent")
    
    async def apply_preset(self, preset_name: str) -> bool:
        """非同期でプリセット設定を適用（エイリアスメソッド）"""
        return await self.apply_application_preset(preset_name)
    
    async def apply_application_preset(self, preset_name: str) -> bool:
        """非同期でプリセット設定を適用"""
        try:
            self.logger.info(f"アプリケーションプリセット適用開始: {preset_name}")
            self.manager.apply_preset_configuration(preset_name)
            
            # 設定の妥当性を検証
            if not self.manager.validate_configuration():
                self.logger.error("アプリケーション設定検証に失敗しました")
                return False
            
            self.logger.info(f"アプリケーションプリセット適用完了: {preset_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"アプリケーションプリセット適用エラー: {e}")
            return False
    
    async def validate_configuration(self) -> tuple[bool, List[str]]:
        """非同期で設定を検証"""
        self.logger.info("アプリケーション設定の検証開始")
        errors = []
        
        # マネージャーの検証メソッドを呼び出し
        is_valid = self.manager.validate_configuration()
        
        if not is_valid:
            errors.append("アプリケーション設定の検証に失敗しました")
        
        if is_valid:
            self.logger.info("アプリケーション設定の検証完了")
        else:
            self.logger.error(f"アプリケーション設定の検証エラー: {errors}")
        
        return is_valid, errors
    
    async def configure_default_applications(self, apps_config: List[Dict[str, Any]]) -> bool:
        """非同期でデフォルトアプリケーション設定を適用"""
        try:
            self.logger.info("デフォルトアプリケーション設定開始")
            
            for app_config in apps_config:
                app_type = DefaultApplicationType(app_config["type"])
                app = DefaultApplication(
                    app_type=app_type,
                    application_name=app_config["name"],
                    executable_path=app_config["executable_path"],
                    file_associations=app_config.get("file_associations", []),
                    protocol_associations=app_config.get("protocol_associations", []),
                    prog_id=app_config.get("prog_id")
                )
                self.manager.add_default_application(app)
            
            self.logger.info("デフォルトアプリケーション設定完了")
            return True
            
        except Exception as e:
            self.logger.error(f"デフォルトアプリケーション設定エラー: {e}")
            return False
    
    async def configure_office_settings(self, office_config: Dict[str, Any]) -> bool:
        """非同期でOffice設定を適用"""
        try:
            self.logger.info("Office設定開始")
            
            config = OfficeConfiguration(
                disable_first_run_dialog=office_config.get("disable_first_run_dialog", True),
                update_mode=office_config.get("update_mode", "automatic"),
                protection_view_internet=OfficeProtectionView(
                    office_config.get("protection_view_internet", "Disabled")
                ),
                protection_view_unsafe_locations=OfficeProtectionView(
                    office_config.get("protection_view_unsafe_locations", "Disabled")
                ),
                protection_view_outlook_attachments=OfficeProtectionView(
                    office_config.get("protection_view_outlook_attachments", "Disabled")
                ),
                office_version=office_config.get("office_version", "2016")
            )
            
            self.manager.configure_office(config)
            
            self.logger.info("Office設定完了")
            return True
            
        except Exception as e:
            self.logger.error(f"Office設定エラー: {e}")
            return False
    
    async def check_security_software(self) -> Dict[str, bool]:
        """非同期でセキュリティソフトウェアの状態を確認"""
        try:
            self.logger.info("セキュリティソフトウェア確認開始")
            
            results = {}
            for software in self.manager.security_software:
                # 実際の確認ロジックは省略（デモ用）
                results[software.name] = True  # 仮の結果
                self.logger.info(f"{software.name}の確認完了")
            
            self.logger.info("セキュリティソフトウェア確認完了")
            return results
            
        except Exception as e:
            self.logger.error(f"セキュリティソフトウェア確認エラー: {e}")
            return {}
    
    async def generate_application_xml(self) -> Optional[etree.Element]:
        """非同期でアプリケーション設定XMLを生成"""
        try:
            self.logger.info("アプリケーション設定XML生成開始")
            
            # 設定の妥当性を検証
            if not self.manager.validate_configuration():
                self.logger.error("設定が無効のため、XML生成を中止します")
                return None
            
            xml_element = self.manager.generate_xml()
            self.logger.info("アプリケーション設定XML生成完了")
            return xml_element
            
        except Exception as e:
            self.logger.error(f"XML生成エラー: {e}")
            return None
    
    async def export_configuration(self, export_path: str) -> bool:
        """非同期で設定をエクスポート"""
        try:
            self.logger.info(f"設定エクスポート開始: {export_path}")
            
            export_data = {
                "default_applications": [
                    {
                        "type": app.app_type.value,
                        "name": app.application_name,
                        "executable_path": app.executable_path,
                        "file_associations": app.file_associations,
                        "protocol_associations": app.protocol_associations,
                        "prog_id": app.prog_id
                    }
                    for app in self.manager.default_applications
                ],
                "taskbar_config": {
                    "position": self.manager.taskbar_config.position.value,
                    "auto_hide": self.manager.taskbar_config.auto_hide,
                    "show_cortana_button": self.manager.taskbar_config.show_cortana_button,
                    "pinned_applications": self.manager.taskbar_config.pinned_applications,
                    "unpinned_applications": self.manager.taskbar_config.unpinned_applications
                },
                "office_config": {
                    "disable_first_run_dialog": self.manager.office_config.disable_first_run_dialog,
                    "update_mode": self.manager.office_config.update_mode,
                    "protection_view_internet": self.manager.office_config.protection_view_internet.value,
                    "office_version": self.manager.office_config.office_version
                },
                "security_software": [
                    {
                        "name": sw.name,
                        "executable_path": sw.executable_path,
                        "service_name": sw.service_name,
                        "registry_keys": sw.registry_keys
                    }
                    for sw in self.manager.security_software
                ]
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"設定エクスポート完了: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"設定エクスポートエラー: {e}")
            return False


# サンプル使用例
if __name__ == "__main__":
    async def main():
        # マネージャーとエージェントの初期化
        manager = ApplicationManager()
        agent = ApplicationAgent(manager)
        
        # 企業標準設定を適用
        await agent.apply_application_preset("enterprise_standard")
        
        # カスタムコマンドを追加
        manager.add_custom_command(
            command="C:\\kitting\\SetUp20211012.bat",
            description="Run Setup Script"
        )
        manager.add_custom_command(
            command="C:\\kitting\\DomainUserAdd.bat", 
            description="Add Domain User"
        )
        
        # セキュリティソフトウェア確認
        security_status = await agent.check_security_software()
        print("セキュリティソフトウェア状態:")
        for name, status in security_status.items():
            print(f"  {name}: {'OK' if status else 'NG'}")
        
        # XML生成
        xml_element = await agent.generate_application_xml()
        if xml_element is not None:
            xml_string = etree.tostring(xml_element, pretty_print=True, encoding='unicode')
            print("Generated Application Configuration XML:")
            print(xml_string[:1000] + "..." if len(xml_string) > 1000 else xml_string)
        
        # 設定情報の表示
        commands = manager.generate_commands()
        print(f"\n生成されたコマンド数: {len(commands)}")
        print("コマンドプレビュー:")
        for i, cmd in enumerate(commands[:5], start=1):
            print(f"{i}. {cmd['description']}: {cmd['command'][:80]}...")
    
    # 実行
    asyncio.run(main())