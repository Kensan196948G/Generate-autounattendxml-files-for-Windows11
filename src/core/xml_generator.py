"""
XML生成エンジン

すべてのモジュールから収集した設定を統合し、
Windows 11用の完全なunattend.xmlファイルを生成します。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from datetime import datetime
from lxml import etree
import json
import yaml
import sys
import os

# パスの調整（直接実行時とモジュールインポート時の両方に対応）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# モジュールのインポート
try:
    from ..modules.user_management import UserAccountManager, UserAccountAgent
    from ..modules.network_config import NetworkConfigManager, NetworkConfigAgent
    from ..modules.windows_features import WindowsFeaturesManager, WindowsFeaturesAgent
    from ..modules.application_config import ApplicationManager, ApplicationAgent
    from ..modules.wifi_config import WiFiConfigManager, WiFiConfigAgent
    from ..modules.desktop_config import DesktopConfigManager, DesktopConfigAgent
    from .generation_logger import generation_logger, LogLevel, LogCategory
except ImportError:
    try:
        from modules.user_management import UserAccountManager, UserAccountAgent
        from modules.network_config import NetworkConfigManager, NetworkConfigAgent
        from modules.windows_features import WindowsFeaturesManager, WindowsFeaturesAgent
        from modules.application_config import ApplicationManager, ApplicationAgent
        from modules.wifi_config import WiFiConfigManager, WiFiConfigAgent
        from modules.desktop_config import DesktopConfigManager, DesktopConfigAgent
        from core.generation_logger import generation_logger, LogLevel, LogCategory
    except ImportError:
        from src.modules.user_management import UserAccountManager, UserAccountAgent
        from src.modules.network_config import NetworkConfigManager, NetworkConfigAgent
        from src.modules.windows_features import WindowsFeaturesManager, WindowsFeaturesAgent
        from src.modules.application_config import ApplicationManager, ApplicationAgent
        from src.modules.wifi_config import WiFiConfigManager, WiFiConfigAgent
        from src.modules.desktop_config import DesktopConfigManager, DesktopConfigAgent
        from src.core.generation_logger import generation_logger, LogLevel, LogCategory

logger = logging.getLogger(__name__)


class UnattendXMLGenerator:
    """Unattend.xml生成エンジン"""
    
    # XML名前空間
    NAMESPACES = {
        'unattend': 'urn:schemas-microsoft-com:unattend',
        'wcm': 'http://schemas.microsoft.com/WMIConfig/2002/State',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    # 設定パス定義
    PASS_WINDOWS_PE = "windowsPE"
    PASS_OFFLINE_SERVICING = "offlineServicing"
    PASS_GENERALIZE = "generalize"
    PASS_SPECIALIZE = "specialize"
    PASS_AUDIT_SYSTEM = "auditSystem"
    PASS_AUDIT_USER = "auditUser"
    PASS_OOBE_SYSTEM = "oobeSystem"
    
    def __init__(self):
        """初期化"""
        self.user_manager = UserAccountManager()
        self.network_manager = NetworkConfigManager()
        self.features_manager = WindowsFeaturesManager()
        self.app_manager = ApplicationManager()
        self.wifi_manager = WiFiConfigManager()
        self.desktop_manager = DesktopConfigManager()
        
        self.user_agent = UserAccountAgent(self.user_manager)
        self.network_agent = NetworkConfigAgent(self.network_manager)
        self.features_agent = WindowsFeaturesAgent(self.features_manager)
        self.app_agent = ApplicationAgent(self.app_manager)
        self.wifi_agent = WiFiConfigAgent(self.wifi_manager)
        self.desktop_agent = DesktopConfigAgent(self.desktop_manager)
        
        self.metadata: Dict[str, Any] = {
            "generated_at": None,
            "version": "1.0.0",
            "target_os": "Windows 11",
            "configuration_name": None
        }
    
    def create_root_element(self) -> etree.Element:
        """ルート要素を作成"""
        root = etree.Element(
            "{urn:schemas-microsoft-com:unattend}unattend",
            nsmap={None: self.NAMESPACES['unattend']}
        )
        root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
                 "urn:schemas-microsoft-com:unattend unattend.xsd")
        return root
    
    def create_settings_element(self, pass_name: str) -> etree.Element:
        """設定要素を作成"""
        settings = etree.Element("settings")
        settings.set("pass", pass_name)
        return settings
    
    def add_component(
        self,
        settings: etree.Element,
        name: str,
        processor_architecture: str = "amd64",
        public_key_token: str = "31bf3856ad364e35",
        language: str = "neutral",
        version_scope: str = "nonSxS"
    ) -> etree.Element:
        """コンポーネントを追加"""
        component = etree.SubElement(settings, "component")
        component.set("name", name)
        component.set("processorArchitecture", processor_architecture)
        component.set("publicKeyToken", public_key_token)
        component.set("language", language)
        component.set("versionScope", version_scope)
        return component
    
    def generate_windows_pe_settings(self) -> etree.Element:
        """WindowsPE設定を生成"""
        settings = self.create_settings_element(self.PASS_WINDOWS_PE)
        
        # Microsoft-Windows-International-Core-WinPE
        intl_component = self.add_component(
            settings,
            "Microsoft-Windows-International-Core-WinPE"
        )
        
        # 言語設定
        self._add_text_element(intl_component, "InputLocale", "0411:00000411")
        self._add_text_element(intl_component, "SystemLocale", "ja-JP")
        self._add_text_element(intl_component, "UILanguage", "ja-JP")
        self._add_text_element(intl_component, "UILanguageFallback", "en-US")
        self._add_text_element(intl_component, "UserLocale", "ja-JP")
        
        # セットアップUI言語
        setup_ui_lang = etree.SubElement(intl_component, "SetupUILanguage")
        self._add_text_element(setup_ui_lang, "UILanguage", "ja-JP")
        
        # Microsoft-Windows-Setup
        setup_component = self.add_component(
            settings,
            "Microsoft-Windows-Setup"
        )
        
        # ディスク設定（オプション）
        if hasattr(self, 'disk_configuration'):
            setup_component.append(self.disk_configuration)
        
        return settings
    
    def generate_specialize_settings(self) -> etree.Element:
        """Specialize設定を生成"""
        settings = self.create_settings_element(self.PASS_SPECIALIZE)
        
        # Microsoft-Windows-Shell-Setup
        shell_component = self.add_component(
            settings,
            "Microsoft-Windows-Shell-Setup"
        )
        
        # コンピューター名
        if self.features_manager.system_config.computer_name:
            self._add_text_element(
                shell_component,
                "ComputerName",
                self.features_manager.system_config.computer_name
            )
        
        # タイムゾーン
        self._add_text_element(
            shell_component,
            "TimeZone",
            self.features_manager.system_config.timezone
        )
        
        # Microsoft-Windows-Deployment（実行コマンド）
        deployment_component = self.add_component(
            settings,
            "Microsoft-Windows-Deployment"
        )
        
        # ネットワーク設定コマンドを追加
        run_sync = etree.SubElement(deployment_component, "RunSynchronous")
        network_commands = self.network_manager.config.get_all_commands()
        
        for idx, cmd in enumerate(network_commands[:5], 1):  # 最初の5つのコマンド
            run_sync_cmd = etree.SubElement(run_sync, "RunSynchronousCommand")
            run_sync_cmd.set("{http://schemas.microsoft.com/WMIConfig/2002/State}action", "add")
            
            self._add_text_element(run_sync_cmd, "Order", str(idx))
            self._add_text_element(run_sync_cmd, "Path", cmd["command"])
            self._add_text_element(run_sync_cmd, "Description", cmd["description"])
            self._add_text_element(run_sync_cmd, "WillReboot", "Never")
        
        return settings
    
    def generate_oobe_system_settings(self) -> etree.Element:
        """OOBESystem設定を生成"""
        settings = self.create_settings_element(self.PASS_OOBE_SYSTEM)
        
        # Microsoft-Windows-Shell-Setup
        shell_component = self.add_component(
            settings,
            "Microsoft-Windows-Shell-Setup"
        )
        
        # OOBE設定
        oobe = etree.SubElement(shell_component, "OOBE")
        self._add_text_element(oobe, "HideEULAPage", "true")
        self._add_text_element(oobe, "HideLocalAccountScreen", "true")
        self._add_text_element(oobe, "HideOEMRegistrationScreen", "true")
        self._add_text_element(oobe, "HideOnlineAccountScreens", "true")
        self._add_text_element(oobe, "HideWirelessSetupInOOBE", "true")
        self._add_text_element(oobe, "NetworkLocation", "Work")
        self._add_text_element(oobe, "ProtectYourPC", "3")
        self._add_text_element(oobe, "SkipMachineOOBE", "true")
        self._add_text_element(oobe, "SkipUserOOBE", "true")
        
        # ユーザーアカウント
        if self.user_manager.accounts:
            shell_component.append(self.user_manager.generate_xml())
        
        # 自動ログオン
        autologon_xml = self.user_manager.generate_autologon_xml()
        if autologon_xml is not None:
            shell_component.append(autologon_xml)
        
        # 初回ログオンコマンド
        first_logon_commands = etree.SubElement(shell_component, "FirstLogonCommands")
        
        # すべてのコマンドを統合
        all_commands = []
        all_commands.extend(self.user_manager.get_first_logon_commands())
        all_commands.extend(self.features_manager.generate_commands())
        all_commands.extend(self.app_manager.generate_commands())
        all_commands.extend(self.wifi_manager.get_first_logon_commands())
        all_commands.extend(self.desktop_manager.get_first_logon_commands())
        
        # 残りのネットワークコマンド
        network_commands = self.network_manager.config.get_all_commands()
        for cmd in network_commands[5:]:  # 6つ目以降
            all_commands.append({
                "order": len(all_commands) + 1,
                "command": cmd["command"],
                "description": cmd["description"],
                "requires_user_input": False
            })
        
        # コマンドをXMLに追加
        for cmd in sorted(all_commands, key=lambda x: x.get("order", 999)):
            sync_cmd = etree.SubElement(first_logon_commands, "SynchronousCommand")
            sync_cmd.set("{http://schemas.microsoft.com/WMIConfig/2002/State}action", "add")
            
            self._add_text_element(sync_cmd, "Order", str(cmd.get("order", 1)))
            
            # PowerShellコマンドの処理
            if cmd.get("shell") == "powershell":
                command_line = f'powershell -ExecutionPolicy Bypass -Command "{cmd["command"]}"'
            else:
                command_line = f'cmd /c {cmd.get("command", "")}'
            
            self._add_text_element(sync_cmd, "CommandLine", command_line)
            self._add_text_element(sync_cmd, "Description", cmd.get("description", ""))
            self._add_text_element(sync_cmd, "RequiresUserInput", "false")
        
        # Microsoft-Windows-International-Core
        intl_component = self.add_component(
            settings,
            "Microsoft-Windows-International-Core"
        )
        
        self._add_text_element(intl_component, "InputLocale", "0411:00000411")
        self._add_text_element(intl_component, "SystemLocale", "ja-JP")
        self._add_text_element(intl_component, "UILanguage", "ja-JP")
        self._add_text_element(intl_component, "UILanguageFallback", "en-US")
        self._add_text_element(intl_component, "UserLocale", "ja-JP")
        
        return settings
    
    def _add_text_element(self, parent: etree.Element, name: str, text: str) -> etree.Element:
        """テキスト要素を追加"""
        element = etree.SubElement(parent, name)
        element.text = text
        return element
    
    async def load_configuration(self, config_path: Union[str, Path]) -> None:
        """設定ファイルを読み込み"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # ファイル形式に応じて読み込み
        if config_path.suffix == '.yaml' or config_path.suffix == '.yml':
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        elif config_path.suffix == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            raise ValueError(f"Unsupported configuration format: {config_path.suffix}")
        
        logger.info(f"設定ファイル読み込み: {config_path}")
        
        # 各モジュールに設定を適用
        await self._apply_configuration(config)
    
    async def _apply_configuration(self, config: Dict[str, Any]) -> None:
        """設定を各モジュールに適用"""
        tasks = []
        
        # ユーザー設定
        if 'users' in config:
            for user_config in config['users']:
                tasks.append(self.user_agent.create_user(user_config))
        
        # ネットワーク設定
        if 'network' in config:
            tasks.append(self.network_agent.configure_network_security(config['network']))
        
        # Windows機能設定
        if 'features' in config:
            if config['features'].get('enterprise_settings'):
                tasks.append(self.features_agent.apply_enterprise_settings())
            if config['features'].get('development_environment'):
                tasks.append(self.features_agent.configure_development_environment())
        
        # アプリケーション設定
        if 'applications' in config:
            preset = config['applications'].get('preset', 'enterprise_standard')
            tasks.append(self.app_agent.apply_preset(preset))
        
        # Wi-Fi設定
        if 'wifi' in config:
            tasks.append(self.wifi_agent.configure_wifi_settings(config['wifi']))
        
        # デスクトップ設定
        if 'desktop' in config:
            tasks.append(self.desktop_agent.configure_desktop_settings(config['desktop']))
        
        # メタデータ
        if 'metadata' in config:
            self.metadata.update(config['metadata'])
        
        # 並列実行
        if tasks:
            await asyncio.gather(*tasks)
        
        logger.info("設定の適用完了")
    
    async def generate(self) -> etree.Element:
        """完全なunattend.xmlを生成"""
        logger.info("unattend.xml生成開始")
        
        # 現在の設定を収集
        current_config = {
            'users': [user.to_dict() for user in getattr(self.user_manager, 'users', [])],
            'network': self.network_manager.configuration.to_dict() if hasattr(self.network_manager.configuration, 'to_dict') else {},
            'wifi_config': self.wifi_manager.configuration if hasattr(self.wifi_manager, 'configuration') else {},
            'desktop_config': {
                'desktop_icons': self.desktop_manager.configuration.desktop_icons.to_dict() if hasattr(self.desktop_manager.configuration.desktop_icons, 'to_dict') else {},
                'start_menu': self.desktop_manager.configuration.start_menu.to_dict() if hasattr(self.desktop_manager.configuration.start_menu, 'to_dict') else {}
            }
        }
        
        generation_logger.start_generation(current_config)
        
        try:
            # メタデータ更新
            self.metadata["generated_at"] = datetime.now().isoformat()
            
            # ルート要素作成
            root = self.create_root_element()
            
            # 各設定パスを追加
            generation_logger.add_log(
                LogLevel.INFO,
                LogCategory.XML_GENERATION,
                "XML構造の生成を開始"
            )
            
            root.append(self.generate_windows_pe_settings())
            generation_logger.add_section_log(
                "WindowsPE設定",
                True,
                ["言語設定", "タイムゾーン"]
            )
            
            root.append(self.generate_specialize_settings())
            generation_logger.add_section_log(
                "Specialize設定",
                True,
                ["ネットワーク設定", "システム設定"]
            )
            
            root.append(self.generate_oobe_system_settings())
            generation_logger.add_section_log(
                "OOBE設定",
                True,
                ["ユーザーアカウント", "初回ログオンコマンド"]
            )
            
            logger.info("unattend.xml生成完了")
            return root
            
        except Exception as e:
            generation_logger.add_exception(e, "XML生成処理")
            raise
    
    async def save(self, output_path: Union[str, Path]) -> Tuple[bool, Dict[str, Any]]:
        """XMLファイルを保存してログを返す"""
        output_path = Path(output_path)
        
        try:
            # XMLを生成
            root = await self.generate()
            
            # 検証
            is_valid, validation_errors = await self.validate(root)
            if not is_valid:
                generation_logger.add_validation_log(
                    "XMLスキーマ",
                    False,
                    {'errors': validation_errors}
                )
                generation_logger.end_generation(False)
                return False, {
                    'json_log': generation_logger.export_json(),
                    'text_log': generation_logger.export_text()
                }
            
            generation_logger.add_validation_log(
                "XMLスキーマ",
                True,
                {'message': 'XMLスキーマ検証に成功しました'}
            )
            
            # XMLツリーを作成
            tree = etree.ElementTree(root)
            
            # ファイルに保存
            tree.write(
                str(output_path),
                pretty_print=True,
                xml_declaration=True,
                encoding='utf-8'
            )
            
            logger.info(f"XMLファイル保存: {output_path}")
            generation_logger.add_log(
                LogLevel.SUCCESS,
                LogCategory.XML_GENERATION,
                f"XMLファイルを保存しました: {output_path}"
            )
            
            # メタデータファイルも保存
            metadata_path = output_path.with_suffix('.meta.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"メタデータ保存: {metadata_path}")
            
            # ログファイルを保存
            log_json_path = output_path.with_suffix('.log.json')
            log_text_path = output_path.with_suffix('.log.txt')
            
            with open(log_json_path, 'w', encoding='utf-8') as f:
                f.write(generation_logger.export_json())
                
            with open(log_text_path, 'w', encoding='utf-8') as f:
                f.write(generation_logger.export_text())
                
            generation_logger.end_generation(True, str(output_path))
            
            return True, {
                'xml_path': str(output_path),
                'json_log': generation_logger.export_json(),
                'text_log': generation_logger.export_text(),
                'log_json_path': str(log_json_path),
                'log_text_path': str(log_text_path)
            }
            
        except Exception as e:
            generation_logger.add_exception(e, "XMLファイル保存処理")
            generation_logger.end_generation(False)
            return False, {
                'error': str(e),
                'json_log': generation_logger.export_json(),
                'text_log': generation_logger.export_text()
            }
    
    async def validate(self, xml_element: Optional[etree.Element] = None) -> Tuple[bool, List[str]]:
        """XMLの妥当性を検証"""
        if xml_element is None:
            xml_element = await self.generate()
        
        errors = []
        
        # 基本的な構造チェック
        if xml_element is None:
            errors.append("XMLエレメントがNullです")
            return False, errors
            
        if xml_element.tag != "{urn:schemas-microsoft-com:unattend}unattend":
            errors.append("ルート要素が正しくありません")
        
        # 必須設定パスのチェック
        settings_elements = xml_element.findall("settings") if xml_element is not None else []
        settings_passes = [s.get("pass") for s in settings_elements]
        
        if self.PASS_OOBE_SYSTEM not in settings_passes:
            errors.append("oobeSystem設定が見つかりません")
        
        # ユーザーアカウントのチェック
        if not self.user_manager.accounts:
            errors.append("ユーザーアカウントが設定されていません")
        
        # 各エージェントの検証
        user_valid = await self.user_agent.validate_all_accounts()
        if not user_valid:
            errors.append("ユーザーアカウント設定にエラーがあります")
        
        network_valid, network_errors = await self.network_agent.validate_configuration()
        if not network_valid:
            errors.extend(network_errors)
        
        features_valid, features_errors = await self.features_agent.validate_features()
        if not features_valid:
            errors.extend(features_errors)
        
        app_valid, app_errors = await self.app_agent.validate_configuration()
        if not app_valid:
            errors.extend(app_errors)
        
        wifi_valid, wifi_errors = await self.wifi_agent.validate_configuration()
        if not wifi_valid:
            errors.extend(wifi_errors)
        
        desktop_valid, desktop_errors = await self.desktop_agent.validate_configuration()
        if not desktop_valid:
            errors.extend(desktop_errors)
        
        is_valid = len(errors) == 0
        return is_valid, errors


class UnattendXMLAgent:
    """XML生成用SubAgent"""
    
    def __init__(self, generator: UnattendXMLGenerator):
        """初期化"""
        self.generator = generator
        self.logger = logging.getLogger(f"{__name__}.Agent")
    
    async def generate_from_preset(self, preset: str) -> etree.Element:
        """プリセットからXMLを生成"""
        self.logger.info(f"プリセット '{preset}' からXML生成開始")
        
        # プリセット設定
        presets = {
            "minimal": {
                "users": [
                    {
                        "name": "admin",
                        "groups": ["Administrators"],
                        "password": "P@ssw0rd123!"
                    }
                ]
            },
            "enterprise": {
                "users": [
                    {
                        "name": "mirai-user",
                        "display_name": "Mirai User",
                        "groups": ["Administrators"],
                        "password": "MiraiP@ss2024!"
                    },
                    {
                        "name": "l-admin",
                        "display_name": "Local Admin",
                        "groups": ["Administrators"],
                        "password": "LAdminP@ss2024!"
                    }
                ],
                "network": {
                    "disable_ipv6": True,
                    "disable_firewall": True,
                    "disable_bluetooth": True,
                    "enable_unsafe_guest_logons": True
                },
                "features": {
                    "enterprise_settings": True
                },
                "applications": {
                    "preset": "enterprise_standard"
                },
                "wifi": {
                    "setup_mode": "configure",
                    "default_profile": {
                        "auth_type": "WPA2PSK",
                        "connect_hidden": False
                    }
                },
                "desktop": {
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
                }
            },
            "development": {
                "users": [
                    {
                        "name": "developer",
                        "groups": ["Administrators"],
                        "password": "DevP@ss2024!"
                    }
                ],
                "features": {
                    "development_environment": True
                },
                "applications": {
                    "preset": "developer"
                }
            }
        }
        
        if preset not in presets:
            raise ValueError(f"Unknown preset: {preset}")
        
        # 設定を適用
        await self.generator._apply_configuration(presets[preset])
        
        # XML生成
        xml = await self.generator.generate()
        
        self.logger.info(f"プリセット '{preset}' からのXML生成完了")
        return xml
    
    async def batch_generate(self, configurations: List[Dict[str, Any]]) -> List[etree.Element]:
        """複数の設定から一括でXMLを生成"""
        self.logger.info(f"{len(configurations)}個の設定からXML生成開始")
        
        results = []
        for idx, config in enumerate(configurations, 1):
            self.logger.info(f"設定 {idx}/{len(configurations)} を処理中")
            
            # 新しいジェネレーターインスタンス
            generator = UnattendXMLGenerator()
            await generator._apply_configuration(config)
            xml = await generator.generate()
            results.append(xml)
        
        self.logger.info("バッチXML生成完了")
        return results
    
    async def export_as_string(self, xml_element: Optional[etree.Element] = None) -> str:
        """XMLを文字列として出力"""
        if xml_element is None:
            xml_element = await self.generator.generate()
        
        # XML宣言を含める場合は、一度バイト列として出力してからデコード
        xml_bytes = etree.tostring(
            xml_element,
            pretty_print=True,
            xml_declaration=True,
            encoding='utf-8'
        )
        return xml_bytes.decode('utf-8')


# サンプル使用例
if __name__ == "__main__":
    async def main():
        # ジェネレーターとエージェントの初期化
        generator = UnattendXMLGenerator()
        agent = UnattendXMLAgent(generator)
        
        # エンタープライズプリセットでXML生成
        xml = await agent.generate_from_preset("enterprise")
        
        # 検証
        is_valid, errors = await generator.validate(xml)
        if is_valid:
            print("✅ XML検証成功")
        else:
            print("❌ XML検証エラー:")
            for error in errors:
                print(f"  - {error}")
        
        # XMLを文字列として出力
        xml_string = await agent.export_as_string(xml)
        print("\n生成されたXML（最初の1000文字）:")
        print(xml_string[:1000])
        
        # ファイルに保存
        output_path = Path("outputs/unattend_enterprise.xml")
        output_path.parent.mkdir(exist_ok=True)
        await generator.save(output_path)
        print(f"\n✅ XMLファイル保存: {output_path}")
    
    # 実行
    asyncio.run(main())