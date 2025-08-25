"""
ネットワーク設定管理モジュール

Windows 11のunattend.xmlファイル用のネットワーク設定を生成します。
IPv6無効化、ファイアウォール設定、Bluetooth設定、DNS設定、
ネットワーク探索設定等を管理します。
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from lxml import etree

logger = logging.getLogger(__name__)


class FirewallProfile(Enum):
    """ファイアウォールプロファイルの定義"""
    DOMAIN = "Domain"
    PRIVATE = "Private" 
    PUBLIC = "Public"
    ALL = "All"


class NetworkDiscoveryMode(Enum):
    """ネットワーク探索モードの定義"""
    ENABLED = "Enabled"
    DISABLED = "Disabled"
    CUSTOM = "Custom"


class FileSharingMode(Enum):
    """ファイル共有モードの定義"""
    ENABLED = "Enabled"
    DISABLED = "Disabled"
    READ_ONLY = "ReadOnly"


class ServiceStartupType(Enum):
    """サービス起動タイプの定義"""
    AUTOMATIC = "Automatic"
    MANUAL = "Manual"
    DISABLED = "Disabled"
    AUTOMATIC_DELAYED = "Automatic (Delayed Start)"


@dataclass
class IPv6Configuration:
    """IPv6設定のデータクラス"""
    disable_ipv6: bool = True
    disable_ipv6_teredo: bool = True
    disable_ipv6_isatap: bool = True
    disable_ipv6_6to4: bool = True
    prefer_ipv4_over_ipv6: bool = True
    
    def to_registry_commands(self) -> List[str]:
        """レジストリ設定コマンドを生成"""
        commands = []
        
        if self.disable_ipv6:
            # IPv6全体の無効化
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" '
                '/v DisabledComponents /t REG_DWORD /d 0xFF /f'
            )
        
        if self.disable_ipv6_teredo:
            # Teredoトンネリング無効化
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" '
                '/v DisableTeredoInterface /t REG_DWORD /d 1 /f'
            )
        
        if self.disable_ipv6_isatap:
            # ISATAPトンネリング無効化
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" '
                '/v DisableIsatapInterface /t REG_DWORD /d 1 /f'
            )
        
        if self.disable_ipv6_6to4:
            # 6to4トンネリング無効化
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" '
                '/v Disable6to4 /t REG_DWORD /d 1 /f'
            )
        
        if self.prefer_ipv4_over_ipv6:
            # IPv4をIPv6より優先
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" '
                '/v DisabledComponents /t REG_DWORD /d 0x20 /f'
            )
        
        return commands
    
    def to_netsh_commands(self) -> List[str]:
        """netshコマンドを生成"""
        commands = []
        
        if self.disable_ipv6_teredo:
            commands.append("netsh interface teredo set state disabled")
        
        if self.disable_ipv6_isatap:
            commands.append("netsh interface isatap set state disabled")
        
        if self.disable_ipv6_6to4:
            commands.append("netsh interface 6to4 set state disabled")
        
        return commands


@dataclass
class FirewallConfiguration:
    """ファイアウォール設定のデータクラス"""
    disable_firewall: bool = True
    profiles: List[FirewallProfile] = field(default_factory=lambda: [FirewallProfile.ALL])
    allow_ping: bool = False
    allow_file_sharing: bool = False
    allow_remote_desktop: bool = False
    
    def to_netsh_commands(self) -> List[str]:
        """netshコマンドを生成"""
        commands = []
        
        if self.disable_firewall:
            if FirewallProfile.ALL in self.profiles:
                commands.extend([
                    "netsh advfirewall set domainprofile state off",
                    "netsh advfirewall set privateprofile state off",
                    "netsh advfirewall set publicprofile state off"
                ])
            else:
                for profile in self.profiles:
                    profile_name = profile.value.lower()
                    commands.append(f"netsh advfirewall set {profile_name}profile state off")
        
        if self.allow_ping:
            commands.append(
                'netsh advfirewall firewall add rule name="Allow ICMPv4-In" '
                'protocol=icmpv4:8,any dir=in action=allow'
            )
        
        if self.allow_file_sharing:
            commands.extend([
                'netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes',
                'netsh advfirewall firewall set rule group="Network Discovery" new enable=Yes'
            ])
        
        if self.allow_remote_desktop:
            commands.append(
                'netsh advfirewall firewall set rule group="Remote Desktop" new enable=Yes'
            )
        
        return commands
    
    def to_registry_commands(self) -> List[str]:
        """レジストリ設定コマンドを生成"""
        commands = []
        
        if self.disable_firewall:
            # Windows Firewallサービス無効化
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\MpsSvc" '
                '/v Start /t REG_DWORD /d 4 /f'
            )
        
        return commands


@dataclass
class BluetoothConfiguration:
    """Bluetooth設定のデータクラス"""
    disable_bluetooth: bool = True
    disable_bluetooth_audio_service: bool = True
    disable_bluetooth_support_service: bool = True
    disable_bluetooth_user_service: bool = True
    
    def to_registry_commands(self) -> List[str]:
        """レジストリ設定コマンドを生成"""
        commands = []
        
        if self.disable_bluetooth:
            # Bluetooth無線管理サービス無効化
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\bthserv" '
                '/v Start /t REG_DWORD /d 4 /f'
            )
        
        if self.disable_bluetooth_audio_service:
            # Bluetoothオーディオゲートウェイサービス無効化
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\BTAGService" '
                '/v Start /t REG_DWORD /d 4 /f'
            )
        
        if self.disable_bluetooth_support_service:
            # Bluetoothサポートサービス無効化
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\BthAvctpSvc" '
                '/v Start /t REG_DWORD /d 4 /f'
            )
        
        if self.disable_bluetooth_user_service:
            # Bluetoothユーザーサポートサービス無効化
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\BluetoothUserService" '
                '/v Start /t REG_DWORD /d 4 /f'
            )
        
        return commands
    
    def to_service_commands(self) -> List[str]:
        """サービス制御コマンドを生成"""
        commands = []
        
        if self.disable_bluetooth:
            commands.extend([
                "sc config bthserv start= disabled",
                "sc stop bthserv"
            ])
        
        if self.disable_bluetooth_audio_service:
            commands.extend([
                "sc config BTAGService start= disabled",
                "sc stop BTAGService"
            ])
        
        if self.disable_bluetooth_support_service:
            commands.extend([
                "sc config BthAvctpSvc start= disabled", 
                "sc stop BthAvctpSvc"
            ])
        
        if self.disable_bluetooth_user_service:
            commands.extend([
                "sc config BluetoothUserService start= disabled",
                "sc stop BluetoothUserService"
            ])
        
        return commands


@dataclass
class GroupPolicyConfiguration:
    """グループポリシー設定のデータクラス"""
    enable_unsafe_guest_logons: bool = True
    disable_windows_defender: bool = False
    disable_windows_update: bool = False
    
    def to_registry_commands(self) -> List[str]:
        """レジストリ設定コマンドを生成"""
        commands = []
        
        if self.enable_unsafe_guest_logons:
            # LanmanWorkstationの安全でないゲストログオンを有効化
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\lanmanserver\\parameters" '
                '/v AllowInsecureGuestAuth /t REG_DWORD /d 1 /f'
            )
        
        if self.disable_windows_defender:
            # Windows Defender無効化
            commands.extend([
                'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" '
                '/v DisableAntiSpyware /t REG_DWORD /d 1 /f',
                'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" '
                '/v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f'
            ])
        
        if self.disable_windows_update:
            # Windows Update無効化
            commands.extend([
                'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" '
                '/v NoAutoUpdate /t REG_DWORD /d 1 /f',
                'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" '
                '/v AUOptions /t REG_DWORD /d 1 /f'
            ])
        
        return commands


@dataclass
class DNSConfiguration:
    """DNS設定のデータクラス"""
    primary_dns: Optional[str] = "8.8.8.8"
    secondary_dns: Optional[str] = "8.8.4.4"
    disable_dns_over_https: bool = False
    flush_dns_cache: bool = True
    
    def to_netsh_commands(self) -> List[str]:
        """netshコマンドを生成"""
        commands = []
        
        if self.primary_dns:
            commands.append(
                f'netsh interface ip set dns "Local Area Connection" static {self.primary_dns}'
            )
            
        if self.secondary_dns:
            commands.append(
                f'netsh interface ip add dns "Local Area Connection" {self.secondary_dns} index=2'
            )
        
        if self.flush_dns_cache:
            commands.append("ipconfig /flushdns")
        
        return commands
    
    def to_registry_commands(self) -> List[str]:
        """レジストリ設定コマンドを生成"""
        commands = []
        
        if self.disable_dns_over_https:
            # DNS over HTTPS無効化
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient" '
                '/v DoHPolicy /t REG_DWORD /d 2 /f'
            )
        
        return commands


@dataclass  
class NetworkDiscoveryConfiguration:
    """ネットワーク探索設定のデータクラス"""
    network_discovery_mode: NetworkDiscoveryMode = NetworkDiscoveryMode.ENABLED
    file_sharing_mode: FileSharingMode = FileSharingMode.ENABLED
    enable_netbios: bool = True
    enable_llmnr: bool = True
    
    def to_netsh_commands(self) -> List[str]:
        """netshコマンドを生成"""
        commands = []
        
        if self.network_discovery_mode == NetworkDiscoveryMode.ENABLED:
            commands.extend([
                'netsh advfirewall firewall set rule group="Network Discovery" new enable=Yes',
                'netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes'
            ])
        elif self.network_discovery_mode == NetworkDiscoveryMode.DISABLED:
            commands.extend([
                'netsh advfirewall firewall set rule group="Network Discovery" new enable=No',
                'netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=No'
            ])
        
        return commands
    
    def to_registry_commands(self) -> List[str]:
        """レジストリ設定コマンドを生成"""
        commands = []
        
        # ネットワーク探索設定
        if self.network_discovery_mode == NetworkDiscoveryMode.ENABLED:
            commands.extend([
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Network\\NewNetworkWindowOff" /f',
                'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\Network Connections" '
                '/v NC_ShowSharedAccessUI /t REG_DWORD /d 1 /f'
            ])
        
        # NetBIOS設定
        if self.enable_netbios:
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\services\\NetBT\\Parameters" '
                '/v NetbiosOptions /t REG_DWORD /d 0 /f'
            )
        else:
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\services\\NetBT\\Parameters" '
                '/v NetbiosOptions /t REG_DWORD /d 2 /f'
            )
        
        # LLMNR設定
        if not self.enable_llmnr:
            commands.append(
                'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient" '
                '/v EnableMulticast /t REG_DWORD /d 0 /f'
            )
        
        return commands
    
    def to_service_commands(self) -> List[str]:
        """サービス制御コマンドを生成"""
        commands = []
        
        if self.network_discovery_mode == NetworkDiscoveryMode.ENABLED:
            commands.extend([
                "sc config FDResPub start= auto",
                "sc start FDResPub",
                "sc config SSDPSRV start= auto", 
                "sc start SSDPSRV",
                "sc config upnphost start= auto",
                "sc start upnphost"
            ])
        elif self.network_discovery_mode == NetworkDiscoveryMode.DISABLED:
            commands.extend([
                "sc config FDResPub start= disabled",
                "sc stop FDResPub",
                "sc config SSDPSRV start= disabled",
                "sc stop SSDPSRV", 
                "sc config upnphost start= disabled",
                "sc stop upnphost"
            ])
        
        return commands


class NetworkConfiguration:
    """統合ネットワーク設定クラス"""
    
    def __init__(self):
        """初期化"""
        self.ipv6_config = IPv6Configuration()
        self.firewall_config = FirewallConfiguration()
        self.bluetooth_config = BluetoothConfiguration()
        self.group_policy_config = GroupPolicyConfiguration()
        self.dns_config = DNSConfiguration()
        self.network_discovery_config = NetworkDiscoveryConfiguration()
        self.custom_commands: List[str] = []
    
    def add_custom_command(self, command: str) -> None:
        """カスタムコマンドを追加"""
        self.custom_commands.append(command)
        logger.info(f"カスタムコマンド追加: {command}")
    
    def get_all_registry_commands(self) -> List[str]:
        """すべてのレジストリコマンドを取得"""
        commands = []
        commands.extend(self.ipv6_config.to_registry_commands())
        commands.extend(self.firewall_config.to_registry_commands())
        commands.extend(self.bluetooth_config.to_registry_commands())
        commands.extend(self.group_policy_config.to_registry_commands())
        commands.extend(self.dns_config.to_registry_commands())
        commands.extend(self.network_discovery_config.to_registry_commands())
        return commands
    
    def get_all_netsh_commands(self) -> List[str]:
        """すべてのnetshコマンドを取得"""
        commands = []
        commands.extend(self.ipv6_config.to_netsh_commands())
        commands.extend(self.firewall_config.to_netsh_commands()) 
        commands.extend(self.dns_config.to_netsh_commands())
        commands.extend(self.network_discovery_config.to_netsh_commands())
        return commands
    
    def get_all_service_commands(self) -> List[str]:
        """すべてのサービス制御コマンドを取得"""
        commands = []
        commands.extend(self.bluetooth_config.to_service_commands())
        commands.extend(self.network_discovery_config.to_service_commands())
        return commands
    
    def get_all_commands(self) -> List[Dict[str, str]]:
        """すべてのコマンドを取得（辞書形式）"""
        commands = []
        
        # レジストリコマンド
        for cmd in self.get_all_registry_commands():
            commands.append({
                "command": cmd,
                "description": "Registry configuration"
            })
        
        # netshコマンド
        for cmd in self.get_all_netsh_commands():
            commands.append({
                "command": cmd,
                "description": "Network configuration"
            })
        
        # サービスコマンド
        for cmd in self.get_all_service_commands():
            commands.append({
                "command": cmd,
                "description": "Service configuration"
            })
        
        # カスタムコマンド
        for cmd in self.custom_commands:
            commands.append({
                "command": cmd,
                "description": "Custom command"
            })
        
        return commands
    
    def get_all_commands_as_strings(self) -> List[str]:
        """すべてのコマンドを文字列のリストとして取得（旧形式）"""
        commands = []
        commands.extend(self.get_all_registry_commands())
        commands.extend(self.get_all_netsh_commands())
        commands.extend(self.get_all_service_commands())
        commands.extend(self.custom_commands)
        return commands


class NetworkConfigManager:
    """ネットワーク設定管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.configuration = NetworkConfiguration()
        self.logger = logging.getLogger(f"{__name__}.Manager")
    
    @property
    def config(self):
        """設定オブジェクトへのエイリアス（後方互換性のため）"""
        return self.configuration
    
    def configure_ipv6(self, **kwargs) -> None:
        """IPv6設定を構成"""
        for key, value in kwargs.items():
            if hasattr(self.configuration.ipv6_config, key):
                setattr(self.configuration.ipv6_config, key, value)
                self.logger.info(f"IPv6設定更新: {key} = {value}")
    
    def configure_firewall(self, **kwargs) -> None:
        """ファイアウォール設定を構成"""
        for key, value in kwargs.items():
            if hasattr(self.configuration.firewall_config, key):
                setattr(self.configuration.firewall_config, key, value)
                self.logger.info(f"ファイアウォール設定更新: {key} = {value}")
    
    def configure_bluetooth(self, **kwargs) -> None:
        """Bluetooth設定を構成"""
        for key, value in kwargs.items():
            if hasattr(self.configuration.bluetooth_config, key):
                setattr(self.configuration.bluetooth_config, key, value)
                self.logger.info(f"Bluetooth設定更新: {key} = {value}")
    
    def configure_group_policy(self, **kwargs) -> None:
        """グループポリシー設定を構成"""
        for key, value in kwargs.items():
            if hasattr(self.configuration.group_policy_config, key):
                setattr(self.configuration.group_policy_config, key, value)
                self.logger.info(f"グループポリシー設定更新: {key} = {value}")
    
    def configure_dns(self, **kwargs) -> None:
        """DNS設定を構成"""
        for key, value in kwargs.items():
            if hasattr(self.configuration.dns_config, key):
                setattr(self.configuration.dns_config, key, value)
                self.logger.info(f"DNS設定更新: {key} = {value}")
    
    def configure_network_discovery(self, **kwargs) -> None:
        """ネットワーク探索設定を構成"""
        for key, value in kwargs.items():
            if hasattr(self.configuration.network_discovery_config, key):
                setattr(self.configuration.network_discovery_config, key, value)
                self.logger.info(f"ネットワーク探索設定更新: {key} = {value}")
    
    def apply_preset(self, preset_name: str) -> None:
        """プリセット設定を適用"""
        presets = {
            "disable_all": {
                "ipv6": {"disable_ipv6": True},
                "firewall": {"disable_firewall": True},
                "bluetooth": {"disable_bluetooth": True},
                "dns": {"primary_dns": "8.8.8.8", "secondary_dns": "8.8.4.4"},
                "network_discovery": {"network_discovery_mode": NetworkDiscoveryMode.DISABLED}
            },
            "minimal_secure": {
                "ipv6": {"disable_ipv6": True, "prefer_ipv4_over_ipv6": True},
                "firewall": {"disable_firewall": False, "allow_ping": False},
                "bluetooth": {"disable_bluetooth": True},
                "dns": {"primary_dns": "1.1.1.1", "secondary_dns": "1.0.0.1"},
                "network_discovery": {"network_discovery_mode": NetworkDiscoveryMode.DISABLED}
            },
            "development": {
                "ipv6": {"disable_ipv6": False},
                "firewall": {"disable_firewall": True},
                "bluetooth": {"disable_bluetooth": False},
                "dns": {"primary_dns": "8.8.8.8", "secondary_dns": "8.8.4.4"},
                "network_discovery": {"network_discovery_mode": NetworkDiscoveryMode.ENABLED}
            }
        }
        
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}")
        
        preset = presets[preset_name]
        
        if "ipv6" in preset:
            self.configure_ipv6(**preset["ipv6"])
        if "firewall" in preset:
            self.configure_firewall(**preset["firewall"])
        if "bluetooth" in preset:
            self.configure_bluetooth(**preset["bluetooth"])
        if "dns" in preset:
            self.configure_dns(**preset["dns"])
        if "network_discovery" in preset:
            self.configure_network_discovery(**preset["network_discovery"])
        
        self.logger.info(f"プリセット適用: {preset_name}")
    
    def validate_configuration(self) -> bool:
        """設定の妥当性を検証"""
        try:
            # DNS設定の検証
            dns_config = self.configuration.dns_config
            if dns_config.primary_dns and not self._is_valid_ip(dns_config.primary_dns):
                self.logger.error(f"無効なプライマリDNS: {dns_config.primary_dns}")
                return False
            
            if dns_config.secondary_dns and not self._is_valid_ip(dns_config.secondary_dns):
                self.logger.error(f"無効なセカンダリDNS: {dns_config.secondary_dns}")
                return False
            
            self.logger.info("設定の妥当性検証完了")
            return True
            
        except Exception as e:
            self.logger.error(f"設定検証エラー: {e}")
            return False
    
    def _is_valid_ip(self, ip_address: str) -> bool:
        """IPアドレスの妥当性を検証"""
        try:
            parts = ip_address.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except (ValueError, TypeError):
            return False
    
    def generate_xml(self) -> etree.Element:
        """XML要素の生成"""
        # ネットワーク設定のXMLルート要素
        network_settings = etree.Element("NetworkSettings")
        
        # コマンド実行設定
        commands_element = etree.SubElement(network_settings, "FirstLogonCommands")
        
        # すべてのコマンドを取得し、XMLに追加
        all_commands = self.configuration.get_all_commands()
        
        for i, command in enumerate(all_commands, start=1):
            command_element = etree.SubElement(commands_element, "SynchronousCommand")
            command_element.set("{http://schemas.microsoft.com/WMIConfig/2002/State}action", "add")
            
            # コマンドライン
            command_line = etree.SubElement(command_element, "CommandLine")
            command_line.text = command
            
            # 説明
            description = etree.SubElement(command_element, "Description")
            description.text = f"Network Configuration Command {i}"
            
            # 順序
            order = etree.SubElement(command_element, "Order")
            order.text = str(i)
            
            # ユーザー入力不要
            requires_user_input = etree.SubElement(command_element, "RequiresUserInput")
            requires_user_input.text = "false"
        
        return network_settings
    
    def get_first_logon_commands(self) -> List[Dict[str, Any]]:
        """初回ログオン時のコマンドリストを取得"""
        # get_all_commandsが既に辞書形式で返すので、そのまま使用
        all_commands = self.configuration.get_all_commands()
        commands = []
        
        for i, cmd_dict in enumerate(all_commands, start=1):
            commands.append({
                "order": i,
                "command": cmd_dict["command"],
                "description": cmd_dict["description"],
                "requires_user_input": False
            })
        
        return commands


class NetworkConfigAgent:
    """ネットワーク設定管理用SubAgent"""
    
    def __init__(self, manager: NetworkConfigManager):
        """初期化"""
        self.manager = manager
        self.logger = logging.getLogger(f"{__name__}.Agent")
    
    async def apply_network_preset(self, preset_name: str) -> bool:
        """非同期でプリセット設定を適用"""
        try:
            self.logger.info(f"プリセット適用開始: {preset_name}")
            self.manager.apply_preset(preset_name)
            
            # 設定の妥当性を検証
            if not self.manager.validate_configuration():
                self.logger.error("設定検証に失敗しました")
                return False
            
            self.logger.info(f"プリセット適用完了: {preset_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"プリセット適用エラー: {e}")
            return False
    
    async def configure_network_security(self, security_config: Dict[str, Any]) -> bool:
        """非同期でネットワークセキュリティ設定を適用"""
        try:
            self.logger.info("ネットワークセキュリティ設定開始")
            
            # IPv6設定
            if "disable_ipv6" in security_config:
                self.manager.configure_ipv6(disable_ipv6=security_config["disable_ipv6"])
            
            # ファイアウォール設定
            if "disable_firewall" in security_config:
                self.manager.configure_firewall(disable_firewall=security_config["disable_firewall"])
            
            # Bluetooth設定
            if "disable_bluetooth" in security_config:
                self.manager.configure_bluetooth(disable_bluetooth=security_config["disable_bluetooth"])
            
            # グループポリシー設定
            if "enable_unsafe_guest_logons" in security_config:
                self.manager.configure_group_policy(
                    enable_unsafe_guest_logons=security_config["enable_unsafe_guest_logons"]
                )
            
            # 設定の妥当性を検証
            if not self.manager.validate_configuration():
                self.logger.error("セキュリティ設定検証に失敗しました")
                return False
            
            self.logger.info("ネットワークセキュリティ設定完了")
            return True
            
        except Exception as e:
            self.logger.error(f"ネットワークセキュリティ設定エラー: {e}")
            return False
    
    async def configure_dns_settings(self, dns_config: Dict[str, Any]) -> bool:
        """非同期でDNS設定を適用"""
        try:
            self.logger.info("DNS設定開始")
            
            # DNS設定を適用
            self.manager.configure_dns(**dns_config)
            
            # 設定の妥当性を検証
            if not self.manager.validate_configuration():
                self.logger.error("DNS設定検証に失敗しました")
                return False
            
            self.logger.info("DNS設定完了")
            return True
            
        except Exception as e:
            self.logger.error(f"DNS設定エラー: {e}")
            return False
    
    async def generate_network_xml(self) -> Optional[etree.Element]:
        """非同期でネットワーク設定XMLを生成"""
        try:
            self.logger.info("ネットワーク設定XML生成開始")
            
            # 設定の妥当性を検証
            if not self.manager.validate_configuration():
                self.logger.error("設定が無効のため、XML生成を中止します")
                return None
            
            xml_element = self.manager.generate_xml()
            self.logger.info("ネットワーク設定XML生成完了")
            return xml_element
            
        except Exception as e:
            self.logger.error(f"XML生成エラー: {e}")
            return None
    
    async def validate_configuration(self) -> tuple[bool, List[str]]:
        """非同期で設定を検証"""
        self.logger.info("ネットワーク設定の検証開始")
        errors = []
        
        # マネージャーの検証メソッドを呼び出し
        is_valid = self.manager.validate_configuration()
        
        if not is_valid:
            errors.append("ネットワーク設定の検証に失敗しました")
        
        # DNS設定の検証
        if self.manager.configuration.dns_config.primary_dns:
            if not self.manager._is_valid_ip(self.manager.configuration.dns_config.primary_dns):
                errors.append(f"無効なプライマリDNSサーバーアドレス: {self.manager.configuration.dns_config.primary_dns}")
        
        if self.manager.configuration.dns_config.secondary_dns:
            if not self.manager._is_valid_ip(self.manager.configuration.dns_config.secondary_dns):
                errors.append(f"無効なセカンダリDNSサーバーアドレス: {self.manager.configuration.dns_config.secondary_dns}")
        
        if is_valid and not errors:
            self.logger.info("ネットワーク設定の検証完了")
        else:
            self.logger.error(f"ネットワーク設定の検証エラー: {errors}")
        
        return is_valid and not errors, errors
    
    async def export_commands(self, format_type: str = "batch") -> Optional[str]:
        """非同期でコマンドをエクスポート"""
        try:
            self.logger.info(f"コマンドエクスポート開始: {format_type}")
            
            commands = self.manager.configuration.get_all_commands_as_strings()
            
            if format_type.lower() == "batch":
                # バッチファイル形式
                content = "@echo off\n"
                content += "echo Network Configuration Script\n"
                content += "echo ==============================\n\n"
                for i, command in enumerate(commands, start=1):
                    content += f"echo Executing command {i}: {command}\n"
                    content += f"{command}\n"
                    content += "if errorlevel 1 echo Error occurred in command above\n\n"
                content += "echo Network configuration completed.\npause\n"
                
            elif format_type.lower() == "powershell":
                # PowerShell形式
                content = "# Network Configuration PowerShell Script\n"
                content += "# ========================================\n\n"
                content += "Write-Host 'Network Configuration Script' -ForegroundColor Green\n\n"
                for i, command in enumerate(commands, start=1):
                    content += f"Write-Host 'Executing command {i}: {command}' -ForegroundColor Yellow\n"
                    content += f"Start-Process -FilePath 'cmd.exe' -ArgumentList '/c {command}' -Wait\n\n"
                content += "Write-Host 'Network configuration completed.' -ForegroundColor Green\n"
                
            else:
                # プレーンテキスト形式
                content = "# Network Configuration Commands\n"
                content += "# ==============================\n\n"
                content += "\n".join(commands)
            
            self.logger.info(f"コマンドエクスポート完了: {format_type}")
            return content
            
        except Exception as e:
            self.logger.error(f"コマンドエクスポートエラー: {e}")
            return None


# サンプル使用例
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # マネージャーの初期化
        manager = NetworkConfigManager()
        agent = NetworkConfigAgent(manager)
        
        # プリセット設定の適用
        await agent.apply_network_preset("disable_all")
        
        # カスタムセキュリティ設定
        security_config = {
            "disable_ipv6": True,
            "disable_firewall": True,
            "disable_bluetooth": True,
            "enable_unsafe_guest_logons": True
        }
        await agent.configure_network_security(security_config)
        
        # DNS設定
        dns_config = {
            "primary_dns": "8.8.8.8",
            "secondary_dns": "8.8.4.4",
            "disable_dns_over_https": True,
            "flush_dns_cache": True
        }
        await agent.configure_dns_settings(dns_config)
        
        # XML生成
        xml_element = await agent.generate_network_xml()
        if xml_element is not None:
            xml_string = etree.tostring(xml_element, pretty_print=True, encoding='unicode')
            print("Generated Network Configuration XML:")
            print(xml_string)
        
        # コマンドエクスポート
        batch_content = await agent.export_commands("batch")
        if batch_content:
            print("\nBatch file content:")
            print(batch_content[:500] + "..." if len(batch_content) > 500 else batch_content)
        
        # 全コマンドの表示
        print(f"\nTotal commands: {len(manager.configuration.get_all_commands())}")
        print("Command preview:")
        for i, command in enumerate(manager.configuration.get_all_commands()[:5], start=1):
            print(f"{i}. {command}")
    
    # 実行
    asyncio.run(main())