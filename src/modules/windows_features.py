"""
Windows機能設定モジュール

Windows 11の機能の有効化/無効化、システム設定、サービス管理を行います。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from lxml import etree
from pathlib import Path

logger = logging.getLogger(__name__)


class WindowsFeature(Enum):
    """Windows機能の定義"""
    # .NET Framework
    NETFX3 = "NetFx3"  # .NET Framework 3.5 (2.0, 3.0含む)
    NETFX4_ADVANCED = "NetFx4-AdvSrvs"  # .NET Framework 4.x Advanced Services
    
    # IIS関連
    IIS_WEBSERVER = "IIS-WebServerRole"
    IIS_ASPNET45 = "IIS-ASPNET45"
    IIS_NETEXTENSIBILITY45 = "IIS-NetExtensibility45"
    
    # Hyper-V
    HYPERV = "Microsoft-Hyper-V-All"
    HYPERV_MANAGEMENT = "Microsoft-Hyper-V-Management-PowerShell"
    
    # Windows Subsystem
    WSL = "Microsoft-Windows-Subsystem-Linux"
    WSL2 = "VirtualMachinePlatform"
    
    # PowerShell
    POWERSHELL_ISE = "MicrosoftWindowsPowerShellISE"
    POWERSHELL_V2 = "MicrosoftWindowsPowerShellV2"
    
    # メディア機能
    MEDIA_FEATURES = "MediaPlayback"
    WINDOWS_MEDIA_PLAYER = "WindowsMediaPlayer"
    
    # その他
    TELNET_CLIENT = "TelnetClient"
    TFTP_CLIENT = "TFTP"
    SMB1 = "SMB1Protocol"
    DIRECT_PLAY = "DirectPlay"
    WORK_FOLDERS = "WorkFolders-Client"


class ServiceStartType(Enum):
    """サービス開始タイプ"""
    BOOT = 0
    SYSTEM = 1
    AUTOMATIC = 2
    MANUAL = 3
    DISABLED = 4


@dataclass
class WindowsService:
    """Windowsサービスの設定"""
    name: str
    display_name: str
    start_type: ServiceStartType
    description: str = ""
    
    def to_command(self) -> str:
        """サービス設定コマンドを生成"""
        return f'sc config "{self.name}" start= {self._get_start_string()}'
    
    def _get_start_string(self) -> str:
        """開始タイプを文字列に変換"""
        mapping = {
            ServiceStartType.BOOT: "boot",
            ServiceStartType.SYSTEM: "system",
            ServiceStartType.AUTOMATIC: "auto",
            ServiceStartType.MANUAL: "demand",
            ServiceStartType.DISABLED: "disabled"
        }
        return mapping.get(self.start_type, "demand")


@dataclass
class SystemConfiguration:
    """システム設定"""
    computer_name: Optional[str] = None
    timezone: str = "Tokyo Standard Time"
    ui_language: str = "ja-JP"
    system_locale: str = "ja-JP"
    user_locale: str = "ja-JP"
    input_locale: str = "0411:00000411"
    enable_remote_desktop: bool = False
    disable_uac_prompts: bool = False
    disable_cortana: bool = True
    disable_web_search: bool = True
    disable_telemetry: bool = True
    disable_customer_experience: bool = True
    power_plan: str = "balanced"  # balanced, high_performance, power_saver
    disable_hibernation: bool = True
    disable_fast_startup: bool = False
    disable_system_restore: bool = False
    
    def get_registry_commands(self) -> List[Dict[str, Any]]:
        """レジストリ設定コマンドを取得"""
        commands = []
        
        # Cortana無効化
        if self.disable_cortana:
            commands.append({
                "path": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f',
                "description": "Disable Cortana"
            })
        
        # Web検索無効化
        if self.disable_web_search:
            commands.append({
                "path": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v ConnectedSearchUseWeb /t REG_DWORD /d 0 /f',
                "description": "Disable Web Search"
            })
        
        # テレメトリ無効化
        if self.disable_telemetry:
            commands.extend([
                {
                    "path": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
                    "description": "Disable Telemetry"
                },
                {
                    "path": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
                    "description": "Disable Telemetry (CurrentVersion)"
                }
            ])
        
        # カスタマーエクスペリエンス無効化
        if self.disable_customer_experience:
            commands.append({
                "path": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\SQMClient\\Windows" /v CEIPEnable /t REG_DWORD /d 0 /f',
                "description": "Disable Customer Experience Improvement Program"
            })
        
        # UAC設定
        if self.disable_uac_prompts:
            commands.append({
                "path": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v ConsentPromptBehaviorAdmin /t REG_DWORD /d 0 /f',
                "description": "Disable UAC Prompts for Administrators"
            })
        
        # リモートデスクトップ有効化
        if self.enable_remote_desktop:
            commands.extend([
                {
                    "path": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f',
                    "description": "Enable Remote Desktop"
                },
                {
                    "path": 'netsh advfirewall firewall set rule group="remote desktop" new enable=yes',
                    "description": "Allow Remote Desktop through firewall"
                }
            ])
        
        return commands


class WindowsFeaturesManager:
    """Windows機能管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.enabled_features: List[WindowsFeature] = []
        self.disabled_features: List[WindowsFeature] = []
        self.services: List[WindowsService] = []
        self.system_config = SystemConfiguration()
        self.custom_commands: List[Dict[str, Any]] = []
    
    def enable_feature(self, feature: WindowsFeature, source: Optional[str] = None) -> None:
        """機能を有効化"""
        if feature not in self.enabled_features:
            self.enabled_features.append(feature)
            logger.info(f"機能有効化設定: {feature.value}")
            
            # 依存関係の処理
            dependencies = self._get_feature_dependencies(feature)
            for dep in dependencies:
                if dep not in self.enabled_features:
                    self.enabled_features.append(dep)
                    logger.info(f"依存機能有効化: {dep.value}")
    
    def disable_feature(self, feature: WindowsFeature) -> None:
        """機能を無効化"""
        if feature not in self.disabled_features:
            self.disabled_features.append(feature)
            logger.info(f"機能無効化設定: {feature.value}")
    
    def _get_feature_dependencies(self, feature: WindowsFeature) -> List[WindowsFeature]:
        """機能の依存関係を取得"""
        dependencies = {
            WindowsFeature.IIS_ASPNET45: [WindowsFeature.IIS_WEBSERVER, WindowsFeature.NETFX4_ADVANCED],
            WindowsFeature.WSL2: [WindowsFeature.WSL],
            WindowsFeature.HYPERV_MANAGEMENT: [WindowsFeature.HYPERV]
        }
        return dependencies.get(feature, [])
    
    def configure_service(self, service: WindowsService) -> None:
        """サービスを設定"""
        self.services.append(service)
        logger.info(f"サービス設定: {service.name} -> {service.start_type.name}")
    
    def set_system_configuration(self, config: SystemConfiguration) -> None:
        """システム設定を適用"""
        self.system_config = config
        logger.info("システム設定を更新")
    
    def add_custom_command(self, command: str, description: str, order: Optional[int] = None) -> None:
        """カスタムコマンドを追加"""
        self.custom_commands.append({
            "command": command,
            "description": description,
            "order": order or len(self.custom_commands) + 100
        })
    
    def generate_commands(self) -> List[Dict[str, Any]]:
        """すべてのコマンドを生成"""
        commands = []
        order = 1
        
        # Windows機能の有効化
        for feature in self.enabled_features:
            commands.append({
                "order": order,
                "command": f"dism /online /enable-feature /featurename:{feature.value} /all /norestart",
                "description": f"Enable {feature.value}",
                "requires_user_input": False
            })
            order += 1
        
        # Windows機能の無効化
        for feature in self.disabled_features:
            commands.append({
                "order": order,
                "command": f"dism /online /disable-feature /featurename:{feature.value} /norestart",
                "description": f"Disable {feature.value}",
                "requires_user_input": False
            })
            order += 1
        
        # サービス設定
        for service in self.services:
            commands.append({
                "order": order,
                "command": service.to_command(),
                "description": f"Configure service: {service.display_name}",
                "requires_user_input": False
            })
            order += 1
        
        # システム設定（レジストリ）
        for reg_cmd in self.system_config.get_registry_commands():
            commands.append({
                "order": order,
                "command": reg_cmd["path"],
                "description": reg_cmd["description"],
                "requires_user_input": False
            })
            order += 1
        
        # 電源プラン設定
        if self.system_config.power_plan:
            power_guid = self._get_power_plan_guid(self.system_config.power_plan)
            if power_guid:
                commands.append({
                    "order": order,
                    "command": f"powercfg /setactive {power_guid}",
                    "description": f"Set power plan: {self.system_config.power_plan}",
                    "requires_user_input": False
                })
                order += 1
        
        # ハイバネーション設定
        if self.system_config.disable_hibernation:
            commands.append({
                "order": order,
                "command": "powercfg /hibernate off",
                "description": "Disable hibernation",
                "requires_user_input": False
            })
            order += 1
        
        # 高速スタートアップ設定
        if self.system_config.disable_fast_startup:
            commands.append({
                "order": order,
                "command": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" /v HiberbootEnabled /t REG_DWORD /d 0 /f',
                "description": "Disable fast startup",
                "requires_user_input": False
            })
            order += 1
        
        # システムの復元設定
        if self.system_config.disable_system_restore:
            commands.append({
                "order": order,
                "command": 'Disable-ComputerRestore -Drive "C:\\"',
                "description": "Disable System Restore",
                "requires_user_input": False,
                "shell": "powershell"
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
    
    def _get_power_plan_guid(self, plan_name: str) -> Optional[str]:
        """電源プランのGUIDを取得"""
        plans = {
            "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
            "high_performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
            "power_saver": "a1841308-3541-4fab-bc81-f71556f20b4a"
        }
        return plans.get(plan_name)
    
    def generate_xml(self) -> etree.Element:
        """XML要素を生成"""
        commands = self.generate_commands()
        
        first_logon_commands = etree.Element("FirstLogonCommands")
        
        for cmd in commands:
            sync_cmd = etree.SubElement(first_logon_commands, "SynchronousCommand")
            sync_cmd.set("{http://schemas.microsoft.com/WMIConfig/2002/State}action", "add")
            
            order_elem = etree.SubElement(sync_cmd, "Order")
            order_elem.text = str(cmd["order"])
            
            # PowerShellコマンドの処理
            if cmd.get("shell") == "powershell":
                command_line = f'powershell -ExecutionPolicy Bypass -Command "{cmd["command"]}"'
            else:
                command_line = f'cmd /c {cmd["command"]}'
            
            cmd_elem = etree.SubElement(sync_cmd, "CommandLine")
            cmd_elem.text = command_line
            
            desc_elem = etree.SubElement(sync_cmd, "Description")
            desc_elem.text = cmd["description"]
            
            input_elem = etree.SubElement(sync_cmd, "RequiresUserInput")
            input_elem.text = "false"
        
        return first_logon_commands


class WindowsFeaturesAgent:
    """Windows機能管理用SubAgent"""
    
    def __init__(self, manager: WindowsFeaturesManager):
        """初期化"""
        self.manager = manager
        self.logger = logging.getLogger(f"{__name__}.Agent")
    
    async def apply_enterprise_settings(self) -> None:
        """企業向け標準設定を適用"""
        self.logger.info("企業向け標準設定の適用開始")
        
        # .NET Framework 3.5有効化
        self.manager.enable_feature(WindowsFeature.NETFX3)
        
        # 不要な機能の無効化
        features_to_disable = [
            WindowsFeature.SMB1,  # セキュリティリスク
            WindowsFeature.POWERSHELL_V2,  # 古いバージョン
            WindowsFeature.WINDOWS_MEDIA_PLAYER  # 企業環境では不要
        ]
        
        for feature in features_to_disable:
            self.manager.disable_feature(feature)
        
        # システム設定
        system_config = SystemConfiguration(
            timezone="Tokyo Standard Time",
            disable_cortana=True,
            disable_web_search=True,
            disable_telemetry=True,
            disable_customer_experience=True,
            power_plan="high_performance",
            disable_hibernation=True,
            enable_remote_desktop=False
        )
        self.manager.set_system_configuration(system_config)
        
        # サービス設定
        services_to_configure = [
            WindowsService(
                name="WSearch",
                display_name="Windows Search",
                start_type=ServiceStartType.DISABLED,
                description="Disable Windows Search for performance"
            ),
            WindowsService(
                name="SysMain",
                display_name="SysMain (Superfetch)",
                start_type=ServiceStartType.DISABLED,
                description="Disable Superfetch for SSD optimization"
            ),
            WindowsService(
                name="DiagTrack",
                display_name="Connected User Experiences and Telemetry",
                start_type=ServiceStartType.DISABLED,
                description="Disable telemetry service"
            )
        ]
        
        for service in services_to_configure:
            self.manager.configure_service(service)
        
        self.logger.info("企業向け標準設定の適用完了")
    
    async def configure_development_environment(self) -> None:
        """開発環境向け設定"""
        self.logger.info("開発環境設定の適用開始")
        
        # 開発ツール有効化
        dev_features = [
            WindowsFeature.WSL,
            WindowsFeature.WSL2,
            WindowsFeature.HYPERV,
            WindowsFeature.POWERSHELL_ISE,
            WindowsFeature.NETFX3,
            WindowsFeature.NETFX4_ADVANCED
        ]
        
        for feature in dev_features:
            self.manager.enable_feature(feature)
        
        # システム設定（開発者向け）
        system_config = SystemConfiguration(
            enable_remote_desktop=True,
            disable_uac_prompts=True,
            power_plan="high_performance",
            disable_hibernation=True,
            disable_fast_startup=True
        )
        self.manager.set_system_configuration(system_config)
        
        self.logger.info("開発環境設定の適用完了")
    
    async def validate_features(self) -> Tuple[bool, List[str]]:
        """機能設定の妥当性を検証"""
        self.logger.info("機能設定の検証開始")
        
        errors = []
        
        # 競合チェック
        if WindowsFeature.SMB1 in self.manager.enabled_features:
            errors.append("SMB1は セキュリティリスクがあります")
        
        # 依存関係チェック
        if WindowsFeature.WSL2 in self.manager.enabled_features:
            if WindowsFeature.WSL not in self.manager.enabled_features:
                errors.append("WSL2にはWSLが必要です")
        
        # Hyper-V競合チェック
        if WindowsFeature.HYPERV in self.manager.enabled_features:
            if WindowsFeature.WSL2 in self.manager.enabled_features:
                self.logger.warning("Hyper-VとWSL2は競合する可能性があります")
        
        is_valid = len(errors) == 0
        self.logger.info(f"機能設定の検証完了: {'有効' if is_valid else '無効'}")
        
        return is_valid, errors
    
    async def generate_feature_report(self) -> Dict[str, Any]:
        """機能設定レポートを生成"""
        self.logger.info("機能設定レポートの生成開始")
        
        report = {
            "enabled_features": [f.value for f in self.manager.enabled_features],
            "disabled_features": [f.value for f in self.manager.disabled_features],
            "services": [
                {
                    "name": s.name,
                    "display_name": s.display_name,
                    "start_type": s.start_type.name
                }
                for s in self.manager.services
            ],
            "system_configuration": {
                "timezone": self.manager.system_config.timezone,
                "ui_language": self.manager.system_config.ui_language,
                "power_plan": self.manager.system_config.power_plan,
                "remote_desktop": self.manager.system_config.enable_remote_desktop,
                "cortana_disabled": self.manager.system_config.disable_cortana,
                "telemetry_disabled": self.manager.system_config.disable_telemetry
            },
            "total_commands": len(self.manager.generate_commands())
        }
        
        self.logger.info("機能設定レポートの生成完了")
        return report


# サンプル使用例
if __name__ == "__main__":
    async def main():
        # マネージャーとエージェントの初期化
        manager = WindowsFeaturesManager()
        agent = WindowsFeaturesAgent(manager)
        
        # 企業向け設定を適用
        await agent.apply_enterprise_settings()
        
        # .NET Framework 3.5を有効化
        manager.enable_feature(WindowsFeature.NETFX3)
        
        # カスタムコマンドを追加
        manager.add_custom_command(
            command="C:\\kitting\\SetUp20211012.bat",
            description="Run Setup Script"
        )
        manager.add_custom_command(
            command="C:\\kitting\\DomainUserAdd.bat",
            description="Add Domain User"
        )
        
        # 検証
        is_valid, errors = await agent.validate_features()
        if not is_valid:
            print("検証エラー:", errors)
        
        # レポート生成
        report = await agent.generate_feature_report()
        print("機能設定レポート:")
        print(f"  有効化機能数: {len(report['enabled_features'])}")
        print(f"  無効化機能数: {len(report['disabled_features'])}")
        print(f"  設定サービス数: {len(report['services'])}")
        print(f"  生成コマンド数: {report['total_commands']}")
        
        # XML生成
        xml_element = manager.generate_xml()
        xml_string = etree.tostring(xml_element, pretty_print=True, encoding='unicode')
        print("\n生成されたXML:")
        print(xml_string)
    
    # 実行
    asyncio.run(main())