"""
Wi-Fi設定管理モジュール

Windows 11のunattend.xmlファイル用のWi-Fi設定を生成します。
WPA2/WPA3認証、隠れたSSID対応、自動接続設定等を管理します。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from lxml import etree
import base64

logger = logging.getLogger(__name__)


class WiFiAuthType(Enum):
    """Wi-Fi認証タイプの定義"""
    OPEN = "open"
    WEP = "WEP"
    WPA_PSK = "WPAPSK"
    WPA2_PSK = "WPA2PSK"
    WPA3_PSK = "WPA3PSK"
    WPA2_ENTERPRISE = "WPA2"
    WPA3_ENTERPRISE = "WPA3"


class WiFiEncryptionType(Enum):
    """暗号化タイプの定義"""
    NONE = "none"
    WEP = "WEP"
    TKIP = "TKIP"
    AES = "AES"
    GCMP = "GCMP"  # WPA3用


class WiFiConnectionMode(Enum):
    """接続モードの定義"""
    AUTO = "auto"  # 自動接続
    MANUAL = "manual"  # 手動接続


class WiFiSetupMode(Enum):
    """Wi-Fiセットアップモードの定義"""
    INTERACTIVE = "interactive"  # 対話形式で設定
    SKIP = "skip"  # Wi-Fi設定をスキップ
    CONFIGURE = "configure"  # 事前設定を使用


@dataclass
class WiFiProfile:
    """Wi-Fiプロファイルのデータクラス"""
    ssid: str
    auth_type: WiFiAuthType = WiFiAuthType.WPA2_PSK
    encryption_type: WiFiEncryptionType = WiFiEncryptionType.AES
    password: Optional[str] = None
    connect_automatically: bool = True
    connect_even_if_hidden: bool = False
    priority: int = 1
    profile_name: Optional[str] = None
    
    def __post_init__(self):
        """初期化後の処理"""
        # プロファイル名が未設定の場合はSSIDを使用
        if not self.profile_name:
            self.profile_name = self.ssid
        
        # WPA3の場合は暗号化をGCMPに設定
        if self.auth_type == WiFiAuthType.WPA3_PSK:
            self.encryption_type = WiFiEncryptionType.GCMP
    
    def validate(self) -> Tuple[bool, List[str]]:
        """プロファイルの検証"""
        errors = []
        
        # SSID検証
        if not self.ssid or len(self.ssid) > 32:
            errors.append("SSIDは1～32文字で設定してください")
        
        # パスワード検証（認証タイプに応じて）
        if self.auth_type in [WiFiAuthType.WPA_PSK, WiFiAuthType.WPA2_PSK, WiFiAuthType.WPA3_PSK]:
            if not self.password:
                errors.append("WPA/WPA2/WPA3認証にはパスワードが必要です")
            elif len(self.password) < 8 or len(self.password) > 63:
                errors.append("パスワードは8～63文字で設定してください")
        
        # WPA3と暗号化タイプの整合性チェック
        if self.auth_type == WiFiAuthType.WPA3_PSK and self.encryption_type != WiFiEncryptionType.GCMP:
            errors.append("WPA3認証ではGCMP暗号化を使用する必要があります")
        
        return len(errors) == 0, errors
    
    def to_xml_element(self) -> etree.Element:
        """XMLエレメントへの変換"""
        profile = etree.Element("WLANProfile")
        
        # プロファイル名
        name_elem = etree.SubElement(profile, "name")
        name_elem.text = self.profile_name
        
        # SSID設定
        ssid_config = etree.SubElement(profile, "SSIDConfig")
        ssid = etree.SubElement(ssid_config, "SSID")
        
        # 16進数エンコード
        hex_elem = etree.SubElement(ssid, "hex")
        hex_elem.text = self.ssid.encode('utf-8').hex().upper()
        
        # プレーンテキスト名
        name_elem = etree.SubElement(ssid, "name")
        name_elem.text = self.ssid
        
        # 隠れたネットワーク設定
        if self.connect_even_if_hidden:
            non_broadcast = etree.SubElement(ssid_config, "nonBroadcast")
            non_broadcast.text = "true"
        
        # 接続タイプ
        connection_type = etree.SubElement(profile, "connectionType")
        connection_type.text = "ESS"
        
        # 接続モード
        connection_mode = etree.SubElement(profile, "connectionMode")
        connection_mode.text = "auto" if self.connect_automatically else "manual"
        
        # MSM設定
        msm = etree.SubElement(profile, "MSM")
        security = etree.SubElement(msm, "security")
        
        # 認証設定
        auth_encryption = etree.SubElement(security, "authEncryption")
        authentication = etree.SubElement(auth_encryption, "authentication")
        authentication.text = self.auth_type.value
        
        encryption = etree.SubElement(auth_encryption, "encryption")
        encryption.text = self.encryption_type.value
        
        use_onex = etree.SubElement(auth_encryption, "useOneX")
        use_onex.text = "false"
        
        # 共有キー設定（PSKの場合）
        if self.password and self.auth_type in [WiFiAuthType.WPA_PSK, WiFiAuthType.WPA2_PSK, WiFiAuthType.WPA3_PSK]:
            shared_key = etree.SubElement(security, "sharedKey")
            key_type = etree.SubElement(shared_key, "keyType")
            key_type.text = "passPhrase"
            
            protected = etree.SubElement(shared_key, "protected")
            protected.text = "false"
            
            key_material = etree.SubElement(shared_key, "keyMaterial")
            key_material.text = self.password
        
        # 自動スイッチ設定
        auto_switch = etree.SubElement(msm, "autoSwitch")
        auto_switch.text = "false"
        
        return profile


@dataclass
class WiFiConfiguration:
    """Wi-Fi設定全体を管理するクラス"""
    setup_mode: WiFiSetupMode = WiFiSetupMode.CONFIGURE
    profiles: List[WiFiProfile] = field(default_factory=list)
    enable_wifi_sense: bool = False  # Wi-Fiセンスを有効化
    connect_to_suggested_hotspots: bool = False  # 推奨ホットスポットへの接続
    
    def add_profile(self, profile: WiFiProfile) -> None:
        """プロファイルを追加"""
        is_valid, errors = profile.validate()
        if not is_valid:
            raise ValueError(f"Wi-Fiプロファイル検証エラー: {', '.join(errors)}")
        
        self.profiles.append(profile)
        logger.info(f"Wi-Fiプロファイル追加: {profile.ssid}")
    
    def get_profile_by_ssid(self, ssid: str) -> Optional[WiFiProfile]:
        """SSID指定でプロファイルを取得"""
        for profile in self.profiles:
            if profile.ssid == ssid:
                return profile
        return None
    
    def remove_profile(self, ssid: str) -> bool:
        """プロファイルを削除"""
        profile = self.get_profile_by_ssid(ssid)
        if profile:
            self.profiles.remove(profile)
            logger.info(f"Wi-Fiプロファイル削除: {ssid}")
            return True
        return False
    
    def to_commands(self) -> List[Dict[str, Any]]:
        """コマンドリストを生成"""
        commands = []
        
        if self.setup_mode == WiFiSetupMode.SKIP:
            # Wi-Fi設定をスキップする場合
            commands.append({
                "command": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\OOBE" /v BypassNRO /t REG_DWORD /d 1 /f',
                "description": "Skip Wi-Fi setup during OOBE",
                "order": 1
            })
            return commands
        
        # プロファイルごとにコマンドを生成
        for i, profile in enumerate(self.profiles, start=1):
            # XMLプロファイルを一時ファイルに保存してインポートするコマンド
            xml_element = profile.to_xml_element()
            xml_string = etree.tostring(xml_element, pretty_print=True, encoding='unicode')
            
            # Base64エンコード（PowerShellで使用）
            xml_base64 = base64.b64encode(xml_string.encode('utf-8')).decode('ascii')
            
            # PowerShellコマンドを作成
            ps_command = f"""
$xmlContent = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{xml_base64}'))
$xmlContent | Out-File -FilePath "$env:TEMP\\wifi_profile_{profile.ssid}.xml" -Encoding UTF8
netsh wlan add profile filename="$env:TEMP\\wifi_profile_{profile.ssid}.xml" user=all
Remove-Item "$env:TEMP\\wifi_profile_{profile.ssid}.xml"
"""
            
            commands.append({
                "command": f'powershell -ExecutionPolicy Bypass -Command "{ps_command.strip()}"',
                "description": f"Configure Wi-Fi profile: {profile.ssid}",
                "order": i,
                "shell": "powershell"
            })
            
            # 自動接続設定
            if profile.connect_automatically:
                commands.append({
                    "command": f'netsh wlan set profileparameter name="{profile.profile_name}" connectionmode=auto',
                    "description": f"Enable auto-connect for {profile.ssid}",
                    "order": i + 100
                })
        
        return commands


class WiFiConfigManager:
    """Wi-Fi設定管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.configuration = WiFiConfiguration()
        self.logger = logging.getLogger(f"{__name__}.Manager")
        
        # デフォルトプロファイル（20mirai18）を設定
        self._setup_default_profile()
    
    def _setup_default_profile(self):
        """デフォルトプロファイルのセットアップ"""
        default_profile = WiFiProfile(
            ssid="20mirai18",
            auth_type=WiFiAuthType.WPA2_PSK,
            encryption_type=WiFiEncryptionType.AES,
            password="20m!ra!18",
            connect_automatically=True,
            connect_even_if_hidden=False,
            priority=1
        )
        self.configuration.add_profile(default_profile)
        self.logger.info("デフォルトWi-Fiプロファイル（20mirai18）を設定しました")
    
    def set_setup_mode(self, mode: WiFiSetupMode) -> None:
        """セットアップモードを設定"""
        self.configuration.setup_mode = mode
        self.logger.info(f"Wi-Fiセットアップモード設定: {mode.value}")
    
    def update_default_profile(self, auth_type: WiFiAuthType, connect_hidden: bool = False) -> None:
        """デフォルトプロファイルを更新"""
        profile = self.configuration.get_profile_by_ssid("20mirai18")
        if profile:
            profile.auth_type = auth_type
            profile.connect_even_if_hidden = connect_hidden
            
            # WPA3の場合は暗号化タイプも更新
            if auth_type == WiFiAuthType.WPA3_PSK:
                profile.encryption_type = WiFiEncryptionType.GCMP
            else:
                profile.encryption_type = WiFiEncryptionType.AES
            
            self.logger.info(f"デフォルトプロファイル更新: 認証={auth_type.value}, 隠れたSSID={connect_hidden}")
    
    def add_custom_profile(self, ssid: str, password: str, auth_type: WiFiAuthType = WiFiAuthType.WPA2_PSK) -> None:
        """カスタムプロファイルを追加"""
        profile = WiFiProfile(
            ssid=ssid,
            auth_type=auth_type,
            password=password,
            connect_automatically=True
        )
        self.configuration.add_profile(profile)
    
    def generate_xml(self) -> etree.Element:
        """XML要素の生成"""
        wifi_settings = etree.Element("WiFiSettings")
        
        # セットアップモード
        setup_mode_elem = etree.SubElement(wifi_settings, "SetupMode")
        setup_mode_elem.text = self.configuration.setup_mode.value
        
        # プロファイル
        if self.configuration.profiles:
            profiles_elem = etree.SubElement(wifi_settings, "Profiles")
            for profile in self.configuration.profiles:
                profiles_elem.append(profile.to_xml_element())
        
        return wifi_settings
    
    def get_first_logon_commands(self) -> List[Dict[str, Any]]:
        """初回ログオン時のコマンドリストを取得"""
        return self.configuration.to_commands()
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """設定の検証"""
        errors = []
        
        # プロファイルの検証
        for profile in self.configuration.profiles:
            is_valid, profile_errors = profile.validate()
            if not is_valid:
                errors.extend([f"{profile.ssid}: {error}" for error in profile_errors])
        
        # 少なくとも1つのプロファイルが必要（CONFIGUREモードの場合）
        if self.configuration.setup_mode == WiFiSetupMode.CONFIGURE and not self.configuration.profiles:
            errors.append("CONFIGUREモードでは少なくとも1つのWi-Fiプロファイルが必要です")
        
        return len(errors) == 0, errors


class WiFiConfigAgent:
    """Wi-Fi設定管理用SubAgent"""
    
    def __init__(self, manager: WiFiConfigManager):
        """初期化"""
        self.manager = manager
        self.logger = logging.getLogger(f"{__name__}.Agent")
    
    async def configure_wifi_settings(self, wifi_config: Dict[str, Any]) -> bool:
        """非同期でWi-Fi設定を適用"""
        try:
            self.logger.info("Wi-Fi設定開始")
            
            # セットアップモード設定
            if "setup_mode" in wifi_config:
                mode = WiFiSetupMode(wifi_config["setup_mode"])
                self.manager.set_setup_mode(mode)
            
            # デフォルトプロファイルの更新
            if "default_profile" in wifi_config:
                default = wifi_config["default_profile"]
                auth_type = WiFiAuthType(default.get("auth_type", "WPA2PSK"))
                connect_hidden = default.get("connect_hidden", False)
                self.manager.update_default_profile(auth_type, connect_hidden)
            
            # カスタムプロファイルの追加
            if "custom_profiles" in wifi_config:
                for profile_data in wifi_config["custom_profiles"]:
                    self.manager.add_custom_profile(
                        ssid=profile_data["ssid"],
                        password=profile_data["password"],
                        auth_type=WiFiAuthType(profile_data.get("auth_type", "WPA2PSK"))
                    )
            
            self.logger.info("Wi-Fi設定完了")
            return True
            
        except Exception as e:
            self.logger.error(f"Wi-Fi設定エラー: {e}")
            return False
    
    async def validate_configuration(self) -> Tuple[bool, List[str]]:
        """非同期で設定を検証"""
        self.logger.info("Wi-Fi設定の検証開始")
        is_valid, errors = self.manager.validate_configuration()
        
        if is_valid:
            self.logger.info("Wi-Fi設定の検証完了")
        else:
            self.logger.error(f"Wi-Fi設定の検証エラー: {errors}")
        
        return is_valid, errors
    
    async def export_profiles(self) -> List[Dict[str, Any]]:
        """プロファイル情報をエクスポート"""
        profiles = []
        for profile in self.manager.configuration.profiles:
            profiles.append({
                "ssid": profile.ssid,
                "auth_type": profile.auth_type.value,
                "encryption_type": profile.encryption_type.value,
                "connect_automatically": profile.connect_automatically,
                "connect_even_if_hidden": profile.connect_even_if_hidden,
                "priority": profile.priority
            })
        
        return profiles


# サンプル使用例
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # マネージャーとエージェントの初期化
        manager = WiFiConfigManager()
        agent = WiFiConfigAgent(manager)
        
        # Wi-Fi設定
        wifi_config = {
            "setup_mode": "configure",
            "default_profile": {
                "auth_type": "WPA3PSK",
                "connect_hidden": True
            }
        }
        
        # 設定適用
        success = await agent.configure_wifi_settings(wifi_config)
        print(f"Wi-Fi設定適用: {'成功' if success else '失敗'}")
        
        # 検証
        is_valid, errors = await agent.validate_configuration()
        if is_valid:
            print("✅ Wi-Fi設定検証成功")
        else:
            print("❌ Wi-Fi設定検証エラー:")
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