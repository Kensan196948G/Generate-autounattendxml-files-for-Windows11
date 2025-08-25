#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル自動生成システム WebUI版
設定管理モジュール

このモジュールは、アプリケーション全体の設定を管理し、
環境変数やコンフィグファイルからの設定読み込みを提供します。
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from functools import lru_cache

from pydantic import BaseSettings, Field, validator
from pydantic.types import SecretStr


logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """データベース設定
    
    ログとプリセット保存用のデータベース接続設定
    """
    url: str = Field(
        default="sqlite:///./webui_database.db",
        description="データベース接続URL"
    )
    echo: bool = Field(
        default=False,
        description="SQLAlchemyのクエリログ出力"
    )
    pool_size: int = Field(
        default=10,
        description="コネクションプールサイズ"
    )
    max_overflow: int = Field(
        default=20,
        description="最大オーバーフロー接続数"
    )
    
    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """Redis設定
    
    Celeryのブローカーとして使用するRedisの設定
    """
    host: str = Field(default="localhost", description="Redisホスト")
    port: int = Field(default=6379, description="Redisポート")
    password: Optional[SecretStr] = Field(default=None, description="Redisパスワード")
    db: int = Field(default=0, description="Redis データベース番号")
    
    @property
    def url(self) -> str:
        """Redis接続URLを生成"""
        password_part = f":{self.password.get_secret_value()}@" if self.password else ""
        return f"redis://{password_part}{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_prefix = "REDIS_"


class SubAgentSettings(BaseSettings):
    """SubAgent機能設定
    
    30体以上のSubAgentの動作設定
    """
    max_concurrent_agents: int = Field(
        default=50,
        description="同時実行可能な最大エージェント数"
    )
    agent_timeout: int = Field(
        default=300,
        description="エージェントタイムアウト（秒）"
    )
    retry_attempts: int = Field(
        default=3,
        description="エージェント実行失敗時のリトライ回数"
    )
    batch_size: int = Field(
        default=10,
        description="バッチ処理時のエージェント数"
    )
    
    # エージェント別の優先度設定
    user_agent_priority: int = Field(default=10, description="ユーザー管理エージェントの優先度")
    network_agent_priority: int = Field(default=8, description="ネットワーク設定エージェントの優先度")
    security_agent_priority: int = Field(default=9, description="セキュリティ設定エージェントの優先度")
    feature_agent_priority: int = Field(default=7, description="機能設定エージェントの優先度")
    application_agent_priority: int = Field(default=6, description="アプリケーション設定エージェントの優先度")
    
    class Config:
        env_prefix = "SUBAGENT_"


class ClaudeFlowSettings(BaseSettings):
    """Claude-flow並列処理設定
    
    並列処理エンジンの設定
    """
    max_workers: int = Field(
        default=20,
        description="最大ワーカー数"
    )
    queue_size: int = Field(
        default=1000,
        description="タスクキューサイズ"
    )
    task_timeout: int = Field(
        default=600,
        description="タスクタイムアウト（秒）"
    )
    result_ttl: int = Field(
        default=3600,
        description="結果の有効期限（秒）"
    )
    progress_update_interval: float = Field(
        default=1.0,
        description="進捗更新間隔（秒）"
    )
    
    class Config:
        env_prefix = "CLAUDE_FLOW_"


class XMLSettings(BaseSettings):
    """XML生成・バリデーション設定
    
    Sysprep応答ファイルの生成とバリデーションに関する設定
    """
    schema_directory: Path = Field(
        default=Path(__file__).parent.parent / "schemas",
        description="XSDスキーマファイルディレクトリ"
    )
    template_directory: Path = Field(
        default=Path(__file__).parent.parent / "templates",
        description="XMLテンプレートディレクトリ"
    )
    output_directory: Path = Field(
        default=Path(__file__).parent.parent.parent / "outputs",
        description="生成XMLファイル出力ディレクトリ"
    )
    encoding: str = Field(
        default="utf-8",
        description="XMLファイルエンコーディング"
    )
    indent_size: int = Field(
        default=2,
        description="XMLインデントサイズ"
    )
    validate_on_generation: bool = Field(
        default=True,
        description="生成時のXMLバリデーション実行フラグ"
    )
    
    @validator('schema_directory', 'template_directory', 'output_directory')
    def ensure_directory_exists(cls, v):
        """ディレクトリが存在しない場合は作成"""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    class Config:
        env_prefix = "XML_"


class SecuritySettings(BaseSettings):
    """セキュリティ設定
    
    認証・認可に関する設定
    """
    secret_key: SecretStr = Field(
        default=SecretStr("your-secret-key-here"),
        description="JWT署名用秘密鍵"
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT署名アルゴリズム"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="アクセストークン有効期限（分）"
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="許可されたホスト一覧"
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="CORSで許可するオリジン一覧"
    )
    
    class Config:
        env_prefix = "SECURITY_"


class LoggingSettings(BaseSettings):
    """ログ設定
    
    アプリケーションログの設定
    """
    level: str = Field(
        default="INFO",
        description="ログレベル"
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="ログフォーマット"
    )
    file_path: Optional[Path] = Field(
        default=Path(__file__).parent.parent.parent / "logs" / "webui.log",
        description="ログファイルパス"
    )
    max_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="ログファイル最大サイズ（バイト）"
    )
    backup_count: int = Field(
        default=5,
        description="ログファイルバックアップ保持数"
    )
    json_logging: bool = Field(
        default=True,
        description="JSON形式でのログ出力"
    )
    
    @validator('file_path')
    def ensure_log_directory(cls, v):
        """ログディレクトリの存在確認・作成"""
        if v and isinstance(v, (str, Path)):
            if isinstance(v, str):
                v = Path(v)
            v.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    class Config:
        env_prefix = "LOGGING_"


class Settings(BaseSettings):
    """メイン設定クラス
    
    すべての設定を統合管理するクラス
    """
    
    # アプリケーション基本設定
    app_name: str = Field(
        default="Windows 11 Sysprep WebUI",
        description="アプリケーション名"
    )
    app_version: str = Field(
        default="1.0.0",
        description="アプリケーションバージョン"
    )
    debug: bool = Field(
        default=False,
        description="デバッグモード"
    )
    
    # サーバー設定
    host: str = Field(
        default="127.0.0.1",
        description="サーバーホスト"
    )
    port: int = Field(
        default=8000,
        description="サーバーポート"
    )
    
    # 各種サブ設定
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    subagent: SubAgentSettings = Field(default_factory=SubAgentSettings)
    claude_flow: ClaudeFlowSettings = Field(default_factory=ClaudeFlowSettings)
    xml: XMLSettings = Field(default_factory=XMLSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    # 環境固有設定
    environment: str = Field(
        default="development",
        description="実行環境（development/production/testing）"
    )
    
    # プリセット設定
    preset_directory: Path = Field(
        default=Path(__file__).parent.parent.parent.parent / "configs" / "presets",
        description="プリセット設定ディレクトリ"
    )
    
    @validator('preset_directory')
    def ensure_preset_directory(cls, v):
        """プリセットディレクトリの存在確認"""
        if isinstance(v, str):
            v = Path(v)
        if not v.exists():
            logger.warning(f"プリセットディレクトリが存在しません: {v}")
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        """環境設定のバリデーション"""
        allowed_environments = ["development", "production", "testing"]
        if v not in allowed_environments:
            raise ValueError(f"無効な環境設定: {v}. 許可される値: {allowed_environments}")
        return v
    
    def get_database_url(self) -> str:
        """データベースURL取得"""
        return self.database.url
    
    def get_redis_url(self) -> str:
        """Redis URL取得"""
        return self.redis.url
    
    def get_available_presets(self) -> List[str]:
        """利用可能なプリセット一覧取得"""
        presets = []
        if self.preset_directory.exists():
            for preset_file in self.preset_directory.glob("*.yaml"):
                presets.append(preset_file.stem)
        return presets
    
    def is_production(self) -> bool:
        """本番環境判定"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """開発環境判定"""
        return self.environment == "development"
    
    def is_testing(self) -> bool:
        """テスト環境判定"""
        return self.environment == "testing"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # ネストした設定の環境変数サポート
        env_nested_delimiter = "__"


# グローバル設定インスタンスのキャッシュ
@lru_cache()
def get_settings() -> Settings:
    """設定インスタンス取得（シングルトンパターン）
    
    Returns:
        Settings: 設定インスタンス
    """
    return Settings()


def create_directories():
    """必要なディレクトリを作成"""
    settings = get_settings()
    
    directories = [
        settings.xml.output_directory,
        settings.xml.template_directory,
        settings.xml.schema_directory,
    ]
    
    if settings.logging.file_path:
        directories.append(settings.logging.file_path.parent)
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"ディレクトリを作成しました: {directory}")


def validate_settings(settings: Settings) -> Dict[str, Any]:
    """設定の妥当性検証
    
    Args:
        settings: 検証対象の設定
        
    Returns:
        Dict[str, Any]: 検証結果
    """
    issues = []
    warnings = []
    
    # 本番環境でのデバッグモードチェック
    if settings.is_production() and settings.debug:
        issues.append("本番環境でデバッグモードが有効になっています")
    
    # 必須ディレクトリの存在チェック
    required_dirs = [
        ("XML出力", settings.xml.output_directory),
        ("プリセット", settings.preset_directory)
    ]
    
    for name, directory in required_dirs:
        if not directory.exists():
            warnings.append(f"{name}ディレクトリが存在しません: {directory}")
    
    # セキュリティ設定のチェック
    if settings.security.secret_key.get_secret_value() == "your-secret-key-here":
        issues.append("デフォルトの秘密鍵が使用されています")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }


if __name__ == "__main__":
    """設定テスト用メイン関数"""
    settings = get_settings()
    
    print(f"アプリケーション名: {settings.app_name}")
    print(f"バージョン: {settings.app_version}")
    print(f"環境: {settings.environment}")
    print(f"デバッグモード: {settings.debug}")
    print(f"データベースURL: {settings.get_database_url()}")
    print(f"Redis URL: {settings.get_redis_url()}")
    print(f"利用可能プリセット: {settings.get_available_presets()}")
    
    # 設定検証
    validation_result = validate_settings(settings)
    print(f"\n設定検証結果:")
    print(f"有効: {validation_result['valid']}")
    if validation_result['issues']:
        print(f"問題: {validation_result['issues']}")
    if validation_result['warnings']:
        print(f"警告: {validation_result['warnings']}")
    
    # 必要なディレクトリを作成
    create_directories()