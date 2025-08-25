#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル自動生成システム WebUI版
データモデル・スキーマ定義

このモジュールは、API通信およびデータ交換に使用する
Pydanticモデルを定義します。すべてのデータ構造と
バリデーションルールを統一管理します。
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, model_validator


class StatusEnum(str, Enum):
    """処理状態を表すEnum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PresetTypeEnum(str, Enum):
    """プリセットタイプEnum"""
    ENTERPRISE = "enterprise"
    DEVELOPMENT = "development"
    MINIMAL = "minimal"
    CUSTOM = "custom"


class PriorityEnum(int, Enum):
    """優先度レベルEnum"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


# ===== ユーザー管理関連モデル =====

class UserAccountModel(BaseModel):
    """ユーザーアカウント設定モデル"""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="ユーザー名（Windows制限に準拠）",
        pattern=r"^[a-zA-Z0-9._-]+$"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=127,
        description="パスワード（強度要件あり）"
    )
    display_name: Optional[str] = Field(
        None,
        max_length=256,
        description="表示名"
    )
    groups: List[str] = Field(
        default_factory=lambda: ["Users"],
        description="所属グループ一覧"
    )
    description: Optional[str] = Field(
        None,
        max_length=512,
        description="ユーザー説明"
    )
    auto_logon: bool = Field(
        default=False,
        description="自動ログオン設定"
    )
    password_expires: bool = Field(
        default=True,
        description="パスワード期限設定"
    )
    
    @validator("password")
    def validate_password_strength(cls, v):
        """パスワード強度チェック"""
        if len(v) < 8:
            raise ValueError("パスワードは8文字以上である必要があります")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        strength_count = sum([has_upper, has_lower, has_digit, has_special])
        
        if strength_count < 3:
            raise ValueError("パスワードは大文字、小文字、数字、記号のうち3種類以上を含む必要があります")
        
        return v
    
    @validator("groups")
    def validate_groups(cls, v):
        """グループ名バリデーション"""
        allowed_groups = [
            "Users", "Administrators", "Power Users", "Backup Operators",
            "Network Configuration Operators", "Performance Log Users",
            "Remote Desktop Users", "Guests"
        ]
        
        for group in v:
            if group not in allowed_groups:
                raise ValueError(f"無効なグループ名: {group}")
        
        return v


class DomainJoinModel(BaseModel):
    """ドメイン参加設定モデル"""
    
    enabled: bool = Field(default=False, description="ドメイン参加有効フラグ")
    domain_name: Optional[str] = Field(
        None,
        max_length=255,
        description="ドメイン名",
        pattern=r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    username: Optional[str] = Field(
        None,
        max_length=104,
        description="ドメインユーザー名"
    )
    password: Optional[str] = Field(
        None,
        description="ドメインパスワード"
    )
    organizational_unit: Optional[str] = Field(
        None,
        max_length=512,
        description="組織単位（OU）"
    )
    
    @model_validator(mode='after')
    def validate_domain_settings(self):
        """ドメイン設定の整合性チェック"""
        if self.enabled:
            required_fields = [
                ("domain_name", self.domain_name),
                ("username", self.username), 
                ("password", self.password)
            ]
            for field_name, field_value in required_fields:
                if not field_value:
                    raise ValueError(f"ドメイン参加が有効の場合、{field_name}は必須です")
        
        return self


# ===== ネットワーク設定関連モデル =====

class NetworkInterfaceModel(BaseModel):
    """ネットワークインターフェース設定モデル"""
    
    interface_name: str = Field(..., description="インターフェース名")
    dhcp_enabled: bool = Field(default=True, description="DHCP有効フラグ")
    ip_address: Optional[str] = Field(
        None,
        description="固定IPアドレス",
        pattern=r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    subnet_mask: Optional[str] = Field(
        None,
        description="サブネットマスク",
        pattern=r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    default_gateway: Optional[str] = Field(
        None,
        description="デフォルトゲートウェイ",
        pattern=r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    dns_servers: List[str] = Field(
        default_factory=list,
        description="DNSサーバー一覧"
    )
    
    @validator("dns_servers")
    def validate_dns_servers(cls, v):
        """DNSサーバーのIPアドレス形式チェック"""
        ip_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        
        for dns in v:
            import re
            if not re.match(ip_pattern, dns):
                raise ValueError(f"無効なDNSサーバーアドレス: {dns}")
        
        return v
    
    @model_validator(mode='after')
    def validate_static_ip_config(self):
        """固定IP設定の整合性チェック"""
        if not self.dhcp_enabled:
            if not self.ip_address:
                raise ValueError("DHCP無効時にはip_addressが必要です")
            if not self.subnet_mask:
                raise ValueError("DHCP無効時にはsubnet_maskが必要です")
        
        return self


class NetworkConfigModel(BaseModel):
    """ネットワーク設定統合モデル"""
    
    hostname: str = Field(
        ...,
        min_length=1,
        max_length=15,
        description="ホスト名（NetBIOS制限準拠）",
        pattern=r"^[a-zA-Z0-9-]+$"
    )
    workgroup_or_domain: str = Field(
        default="WORKGROUP",
        max_length=15,
        description="ワークグループ名またはドメイン名"
    )
    ipv6_enabled: bool = Field(default=False, description="IPv6有効フラグ")
    firewall_enabled: bool = Field(default=False, description="Windows Firewall有効フラグ")
    bluetooth_enabled: bool = Field(default=False, description="Bluetooth有効フラグ")
    interfaces: List[NetworkInterfaceModel] = Field(
        default_factory=list,
        description="ネットワークインターフェース設定"
    )
    
    @validator("hostname")
    def validate_hostname(cls, v):
        """ホスト名の妥当性チェック"""
        # Windows NetBIOS制限
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("ホスト名の先頭・末尾にハイフンは使用できません")
        
        # 予約語チェック
        reserved_names = [
            "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
            "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4",
            "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
        ]
        
        if v.upper() in reserved_names:
            raise ValueError(f"予約語のため使用できないホスト名: {v}")
        
        return v


# ===== Windows機能設定関連モデル =====

class WindowsFeatureModel(BaseModel):
    """Windows機能設定モデル"""
    
    feature_name: str = Field(..., description="機能名")
    enabled: bool = Field(default=True, description="機能有効フラグ")
    description: Optional[str] = Field(None, description="機能説明")
    
    class Config:
        schema_extra = {
            "example": {
                "feature_name": "NetFx3",
                "enabled": True,
                "description": ".NET Framework 3.5"
            }
        }


class SystemConfigModel(BaseModel):
    """システム設定モデル"""
    
    timezone: str = Field(
        default="Tokyo Standard Time",
        description="タイムゾーン設定"
    )
    keyboard_layout: str = Field(
        default="0411:00000411",
        description="キーボードレイアウト（日本語）"
    )
    locale: str = Field(
        default="ja-JP",
        description="ロケール設定"
    )
    windows_features: List[WindowsFeatureModel] = Field(
        default_factory=list,
        description="Windows機能一覧"
    )
    audio_muted: bool = Field(default=True, description="音源ミュート設定")
    telemetry_level: str = Field(
        default="Security",
        description="テレメトリレベル（Security/Basic/Enhanced/Full）"
    )
    
    @validator("telemetry_level")
    def validate_telemetry_level(cls, v):
        """テレメトリレベルのバリデーション"""
        allowed_levels = ["Security", "Basic", "Enhanced", "Full"]
        if v not in allowed_levels:
            raise ValueError(f"無効なテレメトリレベル: {v}")
        return v


# ===== アプリケーション設定関連モデル =====

class ApplicationSettingModel(BaseModel):
    """アプリケーション設定モデル"""
    
    application_name: str = Field(..., description="アプリケーション名")
    setting_key: str = Field(..., description="設定キー")
    setting_value: Union[str, int, bool, Dict[str, Any]] = Field(
        ...,
        description="設定値"
    )
    registry_path: Optional[str] = Field(
        None,
        description="レジストリパス"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "application_name": "Microsoft Office",
                "setting_key": "AcceptAllEulas",
                "setting_value": True,
                "registry_path": "HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\16.0\\Registration"
            }
        }


class DefaultProgramModel(BaseModel):
    """既定のプログラム設定モデル"""
    
    file_association: str = Field(..., description="ファイル関連付け")
    program_id: str = Field(..., description="プログラムID")
    program_name: str = Field(..., description="プログラム名")
    
    class Config:
        schema_extra = {
            "example": {
                "file_association": ".pdf",
                "program_id": "AcroExch.Document.DC",
                "program_name": "Adobe Acrobat Reader DC"
            }
        }


class ApplicationConfigModel(BaseModel):
    """アプリケーション設定統合モデル"""
    
    office_settings: List[ApplicationSettingModel] = Field(
        default_factory=list,
        description="Office設定一覧"
    )
    default_programs: List[DefaultProgramModel] = Field(
        default_factory=list,
        description="既定のプログラム設定"
    )
    security_software_config: Optional[Dict[str, Any]] = Field(
        None,
        description="セキュリティソフトウェア設定"
    )


# ===== プリセット・設定統合モデル =====

class ConfigurationPresetModel(BaseModel):
    """設定プリセットモデル"""
    
    name: str = Field(..., description="プリセット名")
    preset_type: PresetTypeEnum = Field(..., description="プリセットタイプ")
    description: Optional[str] = Field(None, description="プリセット説明")
    
    # 各種設定
    users: List[UserAccountModel] = Field(
        default_factory=list,
        description="ユーザーアカウント設定"
    )
    domain_join: Optional[DomainJoinModel] = Field(
        None,
        description="ドメイン参加設定"
    )
    network: NetworkConfigModel = Field(
        ...,
        description="ネットワーク設定"
    )
    wifi: Optional["WiFiConfigModel"] = Field(
        None,
        description="Wi-Fi設定"
    )
    system: SystemConfigModel = Field(
        ...,
        description="システム設定"
    )
    applications: ApplicationConfigModel = Field(
        default_factory=ApplicationConfigModel,
        description="アプリケーション設定"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="作成日時"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="更新日時"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "企業標準設定",
                "preset_type": "enterprise",
                "description": "企業環境向けの標準的な設定プリセット"
            }
        }


# ===== XML生成・処理関連モデル =====

class XMLGenerationRequestModel(BaseModel):
    """XML生成リクエストモデル"""
    
    session_id: UUID = Field(
        default_factory=uuid4,
        description="セッションID"
    )
    preset_name: Optional[str] = Field(
        None,
        description="使用するプリセット名"
    )
    custom_config: Optional[ConfigurationPresetModel] = Field(
        None,
        description="カスタム設定（プリセット未使用時）"
    )
    validation_enabled: bool = Field(
        default=True,
        description="XML検証有効フラグ"
    )
    output_filename: Optional[str] = Field(
        None,
        description="出力ファイル名"
    )
    
    @model_validator(mode='after')
    def validate_config_source(self):
        """設定ソースの妥当性チェック"""
        if not self.preset_name and not self.custom_config:
            raise ValueError("preset_nameまたはcustom_configのいずれかを指定してください")
        
        if self.preset_name and self.custom_config:
            raise ValueError("preset_nameとcustom_configは同時に指定できません")
        
        return self


class SubAgentTaskModel(BaseModel):
    """SubAgentタスクモデル"""
    
    task_id: UUID = Field(default_factory=uuid4, description="タスクID")
    agent_name: str = Field(..., description="エージェント名")
    task_type: str = Field(..., description="タスクタイプ")
    priority: PriorityEnum = Field(default=PriorityEnum.NORMAL, description="優先度")
    status: StatusEnum = Field(default=StatusEnum.PENDING, description="処理状態")
    
    input_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="入力データ"
    )
    output_data: Optional[Dict[str, Any]] = Field(
        None,
        description="出力データ"
    )
    error_message: Optional[str] = Field(
        None,
        description="エラーメッセージ"
    )
    
    start_time: Optional[datetime] = Field(None, description="開始日時")
    end_time: Optional[datetime] = Field(None, description="終了日時")
    
    @property
    def duration(self) -> Optional[float]:
        """処理時間を秒で取得"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class XMLGenerationProgressModel(BaseModel):
    """XML生成進捗モデル"""
    
    session_id: UUID = Field(..., description="セッションID")
    overall_status: StatusEnum = Field(..., description="全体処理状態")
    progress_percentage: int = Field(
        default=0,
        ge=0,
        le=100,
        description="進捗率（%）"
    )
    current_stage: str = Field(..., description="現在の処理段階")
    
    total_agents: int = Field(default=0, description="総エージェント数")
    completed_agents: int = Field(default=0, description="完了エージェント数")
    
    agent_tasks: List[SubAgentTaskModel] = Field(
        default_factory=list,
        description="エージェントタスク一覧"
    )
    
    messages: List[str] = Field(
        default_factory=list,
        description="進捗メッセージ"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="作成日時"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="更新日時"
    )


class XMLGenerationResultModel(BaseModel):
    """XML生成結果モデル"""
    
    session_id: UUID = Field(..., description="セッションID")
    status: StatusEnum = Field(..., description="生成結果")
    
    xml_content: Optional[str] = Field(None, description="生成されたXMLコンテンツ")
    output_file_path: Optional[str] = Field(None, description="出力ファイルパス")
    validation_result: Optional[Dict[str, Any]] = Field(
        None,
        description="XMLバリデーション結果"
    )
    
    processing_time: Optional[float] = Field(None, description="処理時間（秒）")
    agent_results: List[SubAgentTaskModel] = Field(
        default_factory=list,
        description="各エージェントの結果"
    )
    
    error_details: Optional[Dict[str, Any]] = Field(
        None,
        description="エラー詳細"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="生成日時"
    )
    
    logs: Optional[Dict[str, Any]] = Field(
        None,
        description="生成ログ情報"
    )


# ===== API共通レスポンスモデル =====

class APIResponseModel(BaseModel):
    """API共通レスポンスモデル"""
    
    success: bool = Field(..., description="処理成功フラグ")
    message: str = Field(..., description="メッセージ")
    data: Optional[Any] = Field(None, description="レスポンスデータ")
    errors: Optional[List[str]] = Field(None, description="エラー一覧")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="レスポンス生成日時"
    )


class HealthCheckModel(BaseModel):
    """ヘルスチェックモデル"""
    
    status: str = Field(..., description="サービス状態")
    timestamp: float = Field(..., description="チェック実行時刻")
    services: Dict[str, Any] = Field(
        default_factory=dict,
        description="各サービスの状態"
    )


# ===== WebSocket通信モデル =====

class WebSocketMessageModel(BaseModel):
    """WebSocketメッセージモデル"""
    
    type: str = Field(..., description="メッセージタイプ")
    session_id: Optional[UUID] = Field(None, description="セッションID")
    data: Optional[Dict[str, Any]] = Field(None, description="メッセージデータ")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="メッセージ送信日時"
    )


# ===== Wi-Fi設定関連モデル =====

class WiFiAuthTypeEnum(str, Enum):
    """Wi-Fi認証タイプEnum"""
    OPEN = "open"
    WEP = "WEP"
    WPA_PSK = "WPAPSK"
    WPA2_PSK = "WPA2PSK"
    WPA3_PSK = "WPA3PSK"


class WiFiSetupModeEnum(str, Enum):
    """Wi-Fiセットアップモード"""
    INTERACTIVE = "interactive"  # 対話形式で設定
    SKIP = "skip"  # Wi-Fi設定をスキップ
    CONFIGURE = "configure"  # 事前設定を使用


class WiFiProfileModel(BaseModel):
    """Wi-Fiプロファイルモデル"""
    
    ssid: str = Field(
        default="20mirai18",
        min_length=1,
        max_length=32,
        description="ネットワーク名(SSID)"
    )
    auth_type: WiFiAuthTypeEnum = Field(
        default=WiFiAuthTypeEnum.WPA2_PSK,
        description="認証タイプ"
    )
    password: Optional[str] = Field(
        default="20m!ra!18",
        min_length=8,
        max_length=63,
        description="パスワード"
    )
    connect_automatically: bool = Field(
        default=True,
        description="自動接続を有効にする"
    )
    connect_even_if_hidden: bool = Field(
        default=False,
        description="ブロードキャストしていなくても接続する"
    )
    priority: int = Field(
        default=1,
        ge=1,
        le=100,
        description="接続優先度"
    )
    
    @validator("password")
    def validate_password(cls, v, values):
        """パスワードの検証"""
        auth_type = values.get("auth_type")
        if auth_type and auth_type != WiFiAuthTypeEnum.OPEN:
            if not v:
                raise ValueError("認証タイプがOPEN以外の場合、パスワードが必要です")
            if len(v) < 8 or len(v) > 63:
                raise ValueError("パスワードは8～63文字で設定してください")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "ssid": "20mirai18",
                "auth_type": "WPA3PSK",
                "password": "20m!ra!18",
                "connect_automatically": True,
                "connect_even_if_hidden": True,
                "priority": 1
            }
        }


class WiFiConfigModel(BaseModel):
    """Wi-Fi設定モデル"""
    
    setup_mode: WiFiSetupModeEnum = Field(
        default=WiFiSetupModeEnum.CONFIGURE,
        description="Wi-Fiセットアップモード"
    )
    profiles: List[WiFiProfileModel] = Field(
        default_factory=lambda: [WiFiProfileModel()],
        description="Wi-Fiプロファイルリスト"
    )
    enable_wifi_sense: bool = Field(
        default=False,
        description="Wi-Fiセンスを有効化"
    )
    connect_to_suggested_hotspots: bool = Field(
        default=False,
        description="推奨ホットスポットへの接続"
    )
    
    @model_validator(mode='after')
    def validate_config(self):
        """設定の整合性チェック"""
        if self.setup_mode == WiFiSetupModeEnum.CONFIGURE and not self.profiles:
            raise ValueError("CONFIGUREモードでは少なくとも1つのプロファイルが必要です")
        
        return self
    
    class Config:
        schema_extra = {
            "example": {
                "setup_mode": "configure",
                "profiles": [
                    {
                        "ssid": "20mirai18",
                        "auth_type": "WPA3PSK",
                        "password": "20m!ra!18",
                        "connect_automatically": True,
                        "connect_even_if_hidden": True
                    }
                ],
                "enable_wifi_sense": False,
                "connect_to_suggested_hotspots": False
            }
        }


# 前方参照の解決
ConfigurationPresetModel.update_forward_refs()

# エクスポート用のモデル一覧
__all__ = [
    # Enums
    "StatusEnum", "PresetTypeEnum", "PriorityEnum",
    
    # User Management
    "UserAccountModel", "DomainJoinModel",
    
    # Network Configuration  
    "NetworkInterfaceModel", "NetworkConfigModel",
    
    # Wi-Fi Configuration
    "WiFiAuthTypeEnum", "WiFiSetupModeEnum", "WiFiProfileModel", "WiFiConfigModel",
    
    # System & Features
    "WindowsFeatureModel", "SystemConfigModel",
    
    # Applications
    "ApplicationSettingModel", "DefaultProgramModel", "ApplicationConfigModel",
    
    # Presets & Configuration
    "ConfigurationPresetModel",
    
    # XML Generation
    "XMLGenerationRequestModel", "SubAgentTaskModel", 
    "XMLGenerationProgressModel", "XMLGenerationResultModel",
    
    # API Response
    "APIResponseModel", "HealthCheckModel",
    
    # WebSocket
    "WebSocketMessageModel"
]