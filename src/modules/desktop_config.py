"""
デスクトップ設定管理モジュール

Windows 11のunattend.xmlファイル用のデスクトップ設定を生成します。
デスクトップアイコン、スタートメニューフォルダー、タスクバー設定等を管理します。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from lxml import etree

logger = logging.getLogger(__name__)


class DesktopIconType(Enum):
    """デスクトップアイコンタイプの定義"""
    THIS_PC = "ThisPC"  # このPC
    USER_FILES = "UserFiles"  # ユーザーファイル
    NETWORK = "Network"  # ネットワーク
    RECYCLE_BIN = "RecycleBin"  # ごみ箱
    CONTROL_PANEL = "ControlPanel"  # コントロールパネル


class StartMenuFolderType(Enum):
    """スタートメニューフォルダータイプの定義"""
    DOCUMENTS = "Documents"  # ドキュメント
    DOWNLOADS = "Downloads"  # ダウンロード
    MUSIC = "Music"  # ミュージック
    PICTURES = "Pictures"  # ピクチャ
    VIDEOS = "Videos"  # ビデオ
    NETWORK = "Network"  # ネットワーク
    PERSONAL_FOLDER = "PersonalFolder"  # 個人用フォルダー
    FILE_EXPLORER = "FileExplorer"  # ファイルエクスプローラー
    SETTINGS = "Settings"  # 設定


@dataclass
class DesktopIconSettings:
    """デスクトップアイコン設定のデータクラス"""
    
    show_this_pc: bool = True
    show_user_files: bool = True
    show_network: bool = False
    show_recycle_bin: bool = True
    show_control_panel: bool = False
    
    def get_enabled_icons(self) -> List[DesktopIconType]:
        """有効なアイコンのリストを取得"""
        enabled = []
        if self.show_this_pc:
            enabled.append(DesktopIconType.THIS_PC)
        if self.show_user_files:
            enabled.append(DesktopIconType.USER_FILES)
        if self.show_network:
            enabled.append(DesktopIconType.NETWORK)
        if self.show_recycle_bin:
            enabled.append(DesktopIconType.RECYCLE_BIN)
        if self.show_control_panel:
            enabled.append(DesktopIconType.CONTROL_PANEL)
        return enabled
    
    def to_dict(self) -> Dict[str, bool]:
        """辞書に変換"""
        return {
            "show_this_pc": self.show_this_pc,
            "show_user_files": self.show_user_files,
            "show_network": self.show_network,
            "show_recycle_bin": self.show_recycle_bin,
            "show_control_panel": self.show_control_panel
        }
    
    def to_registry_commands(self) -> List[str]:
        """レジストリコマンドを生成"""
        commands = []
        base_key = r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel"
        
        # 各アイコンの表示/非表示設定（0=表示、1=非表示）
        icon_guids = {
            DesktopIconType.THIS_PC: "{20D04FE0-3AEA-1069-A2D8-08002B30309D}",
            DesktopIconType.USER_FILES: "{59031a47-3f72-44a7-89c5-5595fe6b30ee}",
            DesktopIconType.NETWORK: "{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}",
            DesktopIconType.RECYCLE_BIN: "{645FF040-5081-101B-9F08-00AA002F954E}",
            DesktopIconType.CONTROL_PANEL: "{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}"
        }
        
        for icon_type, guid in icon_guids.items():
            show = icon_type in self.get_enabled_icons()
            value = 0 if show else 1
            commands.append(
                f'reg add "{base_key}" /v "{guid}" /t REG_DWORD /d {value} /f'
            )
        
        # デスクトップアイコンの設定を有効化
        commands.append(
            f'reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" '
            f'/v "HideIcons" /t REG_DWORD /d 0 /f'
        )
        
        return commands


@dataclass
class StartMenuSettings:
    """スタートメニュー設定のデータクラス"""
    
    show_documents: bool = True
    show_downloads: bool = True
    show_music: bool = False
    show_pictures: bool = True
    show_videos: bool = False
    show_network: bool = False
    show_personal_folder: bool = True
    show_file_explorer: bool = True
    show_settings: bool = True
    
    # 追加のスタートメニュー設定
    show_recently_added_apps: bool = True
    show_most_used_apps: bool = True
    show_suggestions: bool = False
    
    def get_enabled_folders(self) -> List[StartMenuFolderType]:
        """有効なフォルダーのリストを取得"""
        enabled = []
        if self.show_documents:
            enabled.append(StartMenuFolderType.DOCUMENTS)
        if self.show_downloads:
            enabled.append(StartMenuFolderType.DOWNLOADS)
        if self.show_music:
            enabled.append(StartMenuFolderType.MUSIC)
        if self.show_pictures:
            enabled.append(StartMenuFolderType.PICTURES)
        if self.show_videos:
            enabled.append(StartMenuFolderType.VIDEOS)
        if self.show_network:
            enabled.append(StartMenuFolderType.NETWORK)
        if self.show_personal_folder:
            enabled.append(StartMenuFolderType.PERSONAL_FOLDER)
        if self.show_file_explorer:
            enabled.append(StartMenuFolderType.FILE_EXPLORER)
        if self.show_settings:
            enabled.append(StartMenuFolderType.SETTINGS)
        return enabled
    
    def to_dict(self) -> Dict[str, bool]:
        """辞書に変換"""
        return {
            "show_documents": self.show_documents,
            "show_downloads": self.show_downloads,
            "show_music": self.show_music,
            "show_pictures": self.show_pictures,
            "show_videos": self.show_videos,
            "show_network": self.show_network,
            "show_personal_folder": self.show_personal_folder,
            "show_file_explorer": self.show_file_explorer,
            "show_settings": self.show_settings,
            "show_recently_added_apps": self.show_recently_added_apps,
            "show_most_used_apps": self.show_most_used_apps,
            "show_suggestions": self.show_suggestions
        }
    
    def to_registry_commands(self) -> List[str]:
        """レジストリコマンドを生成"""
        commands = []
        base_key = r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
        
        # スタートメニューフォルダーの表示設定
        folder_settings = {
            "Start_ShowDocuments": 1 if self.show_documents else 0,
            "Start_ShowDownloads": 1 if self.show_downloads else 0,
            "Start_ShowMusic": 1 if self.show_music else 0,
            "Start_ShowPictures": 1 if self.show_pictures else 0,
            "Start_ShowVideos": 1 if self.show_videos else 0,
            "Start_ShowNetwork": 1 if self.show_network else 0,
            "Start_ShowUser": 1 if self.show_personal_folder else 0,
            "Start_ShowMyComputer": 1 if self.show_file_explorer else 0,
            "Start_ShowControlPanel": 1 if self.show_settings else 0,
            "Start_ShowRecentDocs": 1 if self.show_recently_added_apps else 0,
            "Start_ShowFrequentlyUsedPrograms": 1 if self.show_most_used_apps else 0
        }
        
        for setting_name, value in folder_settings.items():
            commands.append(
                f'reg add "{base_key}" /v "{setting_name}" /t REG_DWORD /d {value} /f'
            )
        
        # Windows 11特有の設定
        if not self.show_suggestions:
            commands.append(
                f'reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" '
                f'/v "SystemPaneSuggestionsEnabled" /t REG_DWORD /d 0 /f'
            )
            commands.append(
                f'reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" '
                f'/v "SubscribedContent-338388Enabled" /t REG_DWORD /d 0 /f'
            )
        
        return commands


@dataclass
class DesktopConfiguration:
    """デスクトップ設定全体を管理するクラス"""
    
    desktop_icons: DesktopIconSettings = field(default_factory=DesktopIconSettings)
    start_menu: StartMenuSettings = field(default_factory=StartMenuSettings)
    
    # 追加のデスクトップ設定
    show_desktop_button: bool = True  # タスクバーにデスクトップボタンを表示
    auto_hide_taskbar: bool = False  # タスクバーを自動的に隠す
    small_taskbar_buttons: bool = False  # 小さいタスクバーボタンを使用
    combine_taskbar_buttons: str = "always"  # always, when_full, never
    
    def to_commands(self) -> List[Dict[str, Any]]:
        """コマンドリストを生成"""
        commands = []
        order = 1
        
        # デスクトップアイコン設定
        for cmd in self.desktop_icons.to_registry_commands():
            commands.append({
                "command": cmd,
                "description": "Configure desktop icon",
                "order": order
            })
            order += 1
        
        # スタートメニュー設定
        for cmd in self.start_menu.to_registry_commands():
            commands.append({
                "command": cmd,
                "description": "Configure start menu",
                "order": order
            })
            order += 1
        
        # タスクバー設定
        taskbar_key = r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
        
        if not self.show_desktop_button:
            commands.append({
                "command": f'reg add "{taskbar_key}" /v "ShowDesktopButton" /t REG_DWORD /d 0 /f',
                "description": "Hide desktop button",
                "order": order
            })
            order += 1
        
        if self.auto_hide_taskbar:
            commands.append({
                "command": f'reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StuckRects3" '
                         f'/v "Settings" /t REG_BINARY /d "30000000feffffff02000000030000003e0000002800000000000000e00300000f0600005804000060000000010000000" /f',
                "description": "Auto-hide taskbar",
                "order": order
            })
            order += 1
        
        if self.small_taskbar_buttons:
            commands.append({
                "command": f'reg add "{taskbar_key}" /v "TaskbarSmallIcons" /t REG_DWORD /d 1 /f',
                "description": "Use small taskbar icons",
                "order": order
            })
            order += 1
        
        # タスクバーボタンの結合設定
        combine_values = {"always": 0, "when_full": 1, "never": 2}
        if self.combine_taskbar_buttons in combine_values:
            commands.append({
                "command": f'reg add "{taskbar_key}" /v "TaskbarGlomLevel" /t REG_DWORD /d {combine_values[self.combine_taskbar_buttons]} /f',
                "description": f"Taskbar button grouping: {self.combine_taskbar_buttons}",
                "order": order
            })
            order += 1
        
        # エクスプローラーを再起動して設定を反映
        commands.append({
            "command": "taskkill /f /im explorer.exe && start explorer.exe",
            "description": "Restart Explorer to apply settings",
            "order": order
        })
        
        return commands


class DesktopConfigManager:
    """デスクトップ設定管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.configuration = DesktopConfiguration()
        self.logger = logging.getLogger(f"{__name__}.Manager")
    
    def set_desktop_icons(self, **kwargs) -> None:
        """デスクトップアイコン設定を更新"""
        for key, value in kwargs.items():
            if hasattr(self.configuration.desktop_icons, key):
                setattr(self.configuration.desktop_icons, key, value)
                self.logger.info(f"デスクトップアイコン設定更新: {key} = {value}")
    
    def set_start_menu(self, **kwargs) -> None:
        """スタートメニュー設定を更新"""
        for key, value in kwargs.items():
            if hasattr(self.configuration.start_menu, key):
                setattr(self.configuration.start_menu, key, value)
                self.logger.info(f"スタートメニュー設定更新: {key} = {value}")
    
    def set_taskbar_settings(self, **kwargs) -> None:
        """タスクバー設定を更新"""
        for key, value in kwargs.items():
            if hasattr(self.configuration, key):
                setattr(self.configuration, key, value)
                self.logger.info(f"タスクバー設定更新: {key} = {value}")
    
    def apply_preset(self, preset_name: str) -> None:
        """プリセット設定を適用"""
        presets = {
            "minimal": {
                "desktop_icons": {
                    "show_this_pc": True,
                    "show_user_files": False,
                    "show_network": False,
                    "show_recycle_bin": True,
                    "show_control_panel": False
                },
                "start_menu": {
                    "show_documents": False,
                    "show_downloads": False,
                    "show_music": False,
                    "show_pictures": False,
                    "show_videos": False,
                    "show_settings": True,
                    "show_suggestions": False
                }
            },
            "standard": {
                "desktop_icons": {
                    "show_this_pc": True,
                    "show_user_files": True,
                    "show_network": False,
                    "show_recycle_bin": True,
                    "show_control_panel": False
                },
                "start_menu": {
                    "show_documents": True,
                    "show_downloads": True,
                    "show_pictures": True,
                    "show_settings": True,
                    "show_suggestions": False
                }
            },
            "full": {
                "desktop_icons": {
                    "show_this_pc": True,
                    "show_user_files": True,
                    "show_network": True,
                    "show_recycle_bin": True,
                    "show_control_panel": True
                },
                "start_menu": {
                    "show_documents": True,
                    "show_downloads": True,
                    "show_music": True,
                    "show_pictures": True,
                    "show_videos": True,
                    "show_network": True,
                    "show_personal_folder": True,
                    "show_file_explorer": True,
                    "show_settings": True,
                    "show_recently_added_apps": True,
                    "show_most_used_apps": True
                }
            }
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            if "desktop_icons" in preset:
                self.set_desktop_icons(**preset["desktop_icons"])
            if "start_menu" in preset:
                self.set_start_menu(**preset["start_menu"])
            self.logger.info(f"プリセット '{preset_name}' を適用しました")
    
    def generate_xml(self) -> etree.Element:
        """XML要素の生成"""
        desktop_settings = etree.Element("DesktopSettings")
        
        # デスクトップアイコン設定
        icons_elem = etree.SubElement(desktop_settings, "DesktopIcons")
        for icon_type in self.configuration.desktop_icons.get_enabled_icons():
            icon_elem = etree.SubElement(icons_elem, "Icon")
            icon_elem.text = icon_type.value
        
        # スタートメニュー設定
        start_menu_elem = etree.SubElement(desktop_settings, "StartMenuFolders")
        for folder_type in self.configuration.start_menu.get_enabled_folders():
            folder_elem = etree.SubElement(start_menu_elem, "Folder")
            folder_elem.text = folder_type.value
        
        # タスクバー設定
        taskbar_elem = etree.SubElement(desktop_settings, "TaskbarSettings")
        etree.SubElement(taskbar_elem, "ShowDesktopButton").text = str(self.configuration.show_desktop_button).lower()
        etree.SubElement(taskbar_elem, "AutoHide").text = str(self.configuration.auto_hide_taskbar).lower()
        etree.SubElement(taskbar_elem, "SmallButtons").text = str(self.configuration.small_taskbar_buttons).lower()
        etree.SubElement(taskbar_elem, "CombineButtons").text = self.configuration.combine_taskbar_buttons
        
        return desktop_settings
    
    def get_first_logon_commands(self) -> List[Dict[str, Any]]:
        """初回ログオン時のコマンドリストを取得"""
        return self.configuration.to_commands()
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """設定の検証"""
        errors = []
        
        # タスクバーボタン結合設定の検証
        valid_combine_options = ["always", "when_full", "never"]
        if self.configuration.combine_taskbar_buttons not in valid_combine_options:
            errors.append(f"無効なタスクバーボタン結合設定: {self.configuration.combine_taskbar_buttons}")
        
        return len(errors) == 0, errors


class DesktopConfigAgent:
    """デスクトップ設定管理用SubAgent"""
    
    def __init__(self, manager: DesktopConfigManager):
        """初期化"""
        self.manager = manager
        self.logger = logging.getLogger(f"{__name__}.Agent")
    
    async def configure_desktop_settings(self, desktop_config: Dict[str, Any]) -> bool:
        """非同期でデスクトップ設定を適用"""
        try:
            self.logger.info("デスクトップ設定開始")
            
            # デスクトップアイコン設定
            if "desktop_icons" in desktop_config:
                self.manager.set_desktop_icons(**desktop_config["desktop_icons"])
            
            # スタートメニュー設定
            if "start_menu" in desktop_config:
                self.manager.set_start_menu(**desktop_config["start_menu"])
            
            # タスクバー設定
            if "taskbar" in desktop_config:
                self.manager.set_taskbar_settings(**desktop_config["taskbar"])
            
            # プリセット適用
            if "preset" in desktop_config:
                self.manager.apply_preset(desktop_config["preset"])
            
            self.logger.info("デスクトップ設定完了")
            return True
            
        except Exception as e:
            self.logger.error(f"デスクトップ設定エラー: {e}")
            return False
    
    async def validate_configuration(self) -> Tuple[bool, List[str]]:
        """非同期で設定を検証"""
        self.logger.info("デスクトップ設定の検証開始")
        is_valid, errors = self.manager.validate_configuration()
        
        if is_valid:
            self.logger.info("デスクトップ設定の検証完了")
        else:
            self.logger.error(f"デスクトップ設定の検証エラー: {errors}")
        
        return is_valid, errors


# サンプル使用例
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # マネージャーとエージェントの初期化
        manager = DesktopConfigManager()
        agent = DesktopConfigAgent(manager)
        
        # デスクトップ設定
        desktop_config = {
            "desktop_icons": {
                "show_this_pc": True,
                "show_user_files": True,
                "show_network": True,
                "show_recycle_bin": True,
                "show_control_panel": False
            },
            "start_menu": {
                "show_documents": True,
                "show_downloads": True,
                "show_music": False,
                "show_pictures": True,
                "show_videos": False,
                "show_settings": True,
                "show_suggestions": False
            }
        }
        
        # 設定適用
        success = await agent.configure_desktop_settings(desktop_config)
        print(f"デスクトップ設定適用: {'成功' if success else '失敗'}")
        
        # 検証
        is_valid, errors = await agent.validate_configuration()
        if is_valid:
            print("✅ デスクトップ設定検証成功")
        else:
            print("❌ デスクトップ設定検証エラー:")
            for error in errors:
                print(f"  - {error}")
        
        # XML生成
        xml_element = manager.generate_xml()
        xml_string = etree.tostring(xml_element, pretty_print=True, encoding='unicode')
        print("\n生成されたXML:")
        print(xml_string)
        
        # コマンド取得
        commands = manager.get_first_logon_commands()
        print("\n生成されたコマンド:")
        for cmd in commands:
            print(f"  {cmd['order']}: {cmd['description']}")
    
    # 実行
    asyncio.run(main())