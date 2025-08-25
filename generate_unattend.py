#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル生成システム - メインアプリケーション

このファイルは、Windows 11の無人インストール用XML応答ファイルを生成する
CLIアプリケーションのメインエントリーポイントです。

機能:
- プリセットモード（enterprise, minimal, development）
- インタラクティブ設定モード
- カスタム設定ファイル読み込み
- XML検証とエラーレポート
- 詳細ログ出力
- 日本語対応

使用例:
    # プリセットを使用した生成
    python generate_unattend.py --preset enterprise

    # カスタム設定ファイルを使用
    python generate_unattend.py --config configs/my_config.yaml

    # インタラクティブモード
    python generate_unattend.py --interactive

Author: Windows 11 Sysprep応答ファイル生成システム
Version: 1.0.0
"""

import os
import sys
import logging
import click
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# プロジェクト内モジュールのインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.xml_generator import XMLGenerator
from core.validator import XMLValidator, ConfigValidator
from modules.application_config import ApplicationConfigModule
from modules.network_config import NetworkConfigModule
from modules.user_management import UserManagementModule
from modules.windows_features import WindowsFeaturesModule


class UnattendGenerator:
    """
    無人インストールファイル生成器のメインクラス
    
    各種設定を統合し、最終的なunattend.xmlファイルを生成します。
    """
    
    def __init__(self, verbose: bool = False):
        """
        初期化
        
        Args:
            verbose (bool): 詳細ログ出力を有効にするかどうか
        """
        self.verbose = verbose
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # プロジェクトルートパスの設定
        self.project_root = Path(__file__).parent
        self.configs_dir = self.project_root / "configs"
        self.presets_dir = self.configs_dir / "presets"
        self.outputs_dir = self.project_root / "outputs"
        self.logs_dir = self.project_root / "logs"
        
        # 必要なディレクトリが存在しない場合は作成
        self.outputs_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # バリデーターの初期化
        self.xml_validator = XMLValidator()
        self.config_validator = ConfigValidator()
        
        self.logger.info("UnattendGenerator初期化完了")
    
    def setup_logging(self):
        """ログ設定のセットアップ"""
        log_level = logging.DEBUG if self.verbose else logging.INFO
        
        # ログフォーマットの設定
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # コンソールハンドラーの設定
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # ファイルハンドラーの設定
        log_file = self.project_root / "logs" / "unattend_generator.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # ルートロガーの設定
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
    
    def load_preset(self, preset_name: str) -> Dict[str, Any]:
        """
        プリセット設定を読み込む
        
        Args:
            preset_name (str): プリセット名（enterprise, minimal, development）
            
        Returns:
            Dict[str, Any]: プリセット設定辞書
            
        Raises:
            FileNotFoundError: プリセットファイルが見つからない場合
            yaml.YAMLError: YAML解析エラーの場合
        """
        preset_file = self.presets_dir / f"{preset_name}.yaml"
        
        if not preset_file.exists():
            available_presets = [f.stem for f in self.presets_dir.glob("*.yaml")]
            raise FileNotFoundError(
                f"プリセット '{preset_name}' が見つかりません。\n"
                f"利用可能なプリセット: {', '.join(available_presets)}"
            )
        
        self.logger.info(f"プリセット '{preset_name}' を読み込み中: {preset_file}")
        
        try:
            with open(preset_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 設定の検証
            self.config_validator.validate_config(config)
            
            self.logger.info(f"プリセット '{preset_name}' の読み込み完了")
            return config
            
        except yaml.YAMLError as e:
            self.logger.error(f"プリセットファイルの解析エラー: {e}")
            raise
        except Exception as e:
            self.logger.error(f"プリセット読み込みエラー: {e}")
            raise
    
    def load_config_file(self, config_path: str) -> Dict[str, Any]:
        """
        カスタム設定ファイルを読み込む
        
        Args:
            config_path (str): 設定ファイルのパス
            
        Returns:
            Dict[str, Any]: 設定辞書
            
        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            yaml.YAMLError: YAML解析エラーの場合
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
        
        self.logger.info(f"設定ファイルを読み込み中: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 設定の検証
            self.config_validator.validate_config(config)
            
            self.logger.info("設定ファイルの読み込み完了")
            return config
            
        except yaml.YAMLError as e:
            self.logger.error(f"設定ファイルの解析エラー: {e}")
            raise
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {e}")
            raise
    
    def interactive_setup(self) -> Dict[str, Any]:
        """
        インタラクティブ設定モード
        
        Returns:
            Dict[str, Any]: ユーザー入力に基づく設定辞書
        """
        self.logger.info("インタラクティブ設定モードを開始")
        
        config = {
            'general': {},
            'user_accounts': {},
            'network': {},
            'applications': {},
            'windows_features': {}
        }
        
        click.echo("=== Windows 11 無人インストール設定ウィザード ===")
        click.echo("各項目について設定を行います。\n")
        
        # 基本設定
        click.echo("1. 基本設定")
        config['general']['computer_name'] = click.prompt(
            "コンピューター名", 
            default="WIN11-PC"
        )
        config['general']['time_zone'] = click.prompt(
            "タイムゾーン", 
            default="Tokyo Standard Time"
        )
        config['general']['locale'] = click.prompt(
            "ロケール", 
            default="ja-JP"
        )
        config['general']['keyboard_layout'] = click.prompt(
            "キーボードレイアウト", 
            default="ja-JP"
        )
        
        # ユーザーアカウント設定
        click.echo("\n2. ユーザーアカウント設定")
        create_admin = click.confirm("管理者アカウントを作成しますか？", default=True)
        
        if create_admin:
            admin_name = click.prompt("管理者アカウント名", default="Administrator")
            admin_password = click.prompt("管理者パスワード", hide_input=True)
            
            config['user_accounts']['administrator'] = {
                'username': admin_name,
                'password': admin_password,
                'enabled': True,
                'auto_logon': click.confirm("自動ログオンを有効にしますか？", default=False)
            }
        
        # ネットワーク設定
        click.echo("\n3. ネットワーク設定")
        if click.confirm("静的IPアドレスを設定しますか？", default=False):
            config['network']['static_ip'] = {
                'ip_address': click.prompt("IPアドレス"),
                'subnet_mask': click.prompt("サブネットマスク", default="255.255.255.0"),
                'gateway': click.prompt("デフォルトゲートウェイ"),
                'dns_servers': [
                    click.prompt("プライマリDNS", default="8.8.8.8"),
                    click.prompt("セカンダリDNS", default="8.8.4.4")
                ]
            }
        
        # Windows機能設定
        click.echo("\n4. Windows機能設定")
        features_to_enable = []
        features_to_disable = []
        
        common_features = [
            ("Hyper-V", "Microsoft-Hyper-V-All"),
            ("Windows Subsystem for Linux", "Microsoft-Windows-Subsystem-Linux"),
            ("IIS", "IIS-WebServerRole"),
            ("Telnet Client", "TelnetClient")
        ]
        
        for feature_name, feature_id in common_features:
            if click.confirm(f"{feature_name}を有効にしますか？", default=False):
                features_to_enable.append(feature_id)
        
        if features_to_enable:
            config['windows_features']['enable'] = features_to_enable
        if features_to_disable:
            config['windows_features']['disable'] = features_to_disable
        
        self.logger.info("インタラクティブ設定完了")
        return config
    
    def generate_unattend_xml(self, config: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """
        設定に基づいてunattend.xmlファイルを生成
        
        Args:
            config (Dict[str, Any]): 設定辞書
            output_file (Optional[str]): 出力ファイルパス（指定しない場合は自動生成）
            
        Returns:
            str: 生成されたXMLファイルのパス
        """
        self.logger.info("unattend.xml生成を開始")
        
        try:
            # XMLジェネレーターの初期化
            xml_generator = XMLGenerator()
            
            # 各モジュールの設定を適用
            if 'user_accounts' in config:
                user_module = UserManagementModule()
                xml_generator.add_component(user_module.generate_config(config['user_accounts']))
            
            if 'network' in config:
                network_module = NetworkConfigModule()
                xml_generator.add_component(network_module.generate_config(config['network']))
            
            if 'applications' in config:
                app_module = ApplicationConfigModule()
                xml_generator.add_component(app_module.generate_config(config['applications']))
            
            if 'windows_features' in config:
                features_module = WindowsFeaturesModule()
                xml_generator.add_component(features_module.generate_config(config['windows_features']))
            
            # XMLを生成
            xml_content = xml_generator.generate_xml(config.get('general', {}))
            
            # 出力ファイル名の決定
            if output_file is None:
                output_file = self.outputs_dir / "unattend.xml"
            else:
                output_file = Path(output_file)
            
            # XMLファイルの保存
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            self.logger.info(f"unattend.xml生成完了: {output_file}")
            
            # XML検証
            if self.xml_validator.validate_xml(str(output_file)):
                self.logger.info("XML検証: 成功")
            else:
                self.logger.warning("XML検証: 警告があります")
            
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"XML生成エラー: {e}")
            raise


# CLIインターフェース定義
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='詳細ログ出力を有効にする')
@click.pass_context
def cli(ctx, verbose):
    """Windows 11 Sysprep応答ファイル生成システム"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--preset', '-p', 
              type=click.Choice(['enterprise', 'minimal', 'development']),
              help='使用するプリセット')
@click.option('--config', '-c', type=click.Path(exists=True),
              help='カスタム設定ファイルのパス')
@click.option('--interactive', '-i', is_flag=True,
              help='インタラクティブ設定モード')
@click.option('--output', '-o', type=click.Path(),
              help='出力ファイルパス')
@click.pass_context
def generate(ctx, preset, config, interactive, output):
    """unattend.xmlファイルを生成する"""
    verbose = ctx.obj.get('verbose', False)
    generator = UnattendGenerator(verbose=verbose)
    
    try:
        # 設定の読み込み
        if preset:
            click.echo(f"プリセット '{preset}' を使用して生成します...")
            config_data = generator.load_preset(preset)
        elif config:
            click.echo(f"設定ファイル '{config}' を使用して生成します...")
            config_data = generator.load_config_file(config)
        elif interactive:
            config_data = generator.interactive_setup()
        else:
            click.echo("エラー: プリセット、設定ファイル、またはインタラクティブモードを指定してください。")
            click.echo("使用例:")
            click.echo("  python generate_unattend.py generate --preset enterprise")
            click.echo("  python generate_unattend.py generate --config configs/my_config.yaml")
            click.echo("  python generate_unattend.py generate --interactive")
            sys.exit(1)
        
        # XMLファイル生成
        output_path = generator.generate_unattend_xml(config_data, output)
        
        click.echo(f"✓ unattend.xmlファイルが正常に生成されました: {output_path}")
        
    except Exception as e:
        click.echo(f"✗ エラーが発生しました: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command()
def list_presets():
    """利用可能なプリセット一覧を表示する"""
    generator = UnattendGenerator()
    
    if not generator.presets_dir.exists():
        click.echo("プリセットディレクトリが見つかりません。")
        return
    
    presets = list(generator.presets_dir.glob("*.yaml"))
    
    if not presets:
        click.echo("利用可能なプリセットがありません。")
        return
    
    click.echo("利用可能なプリセット:")
    for preset_file in presets:
        preset_name = preset_file.stem
        click.echo(f"  - {preset_name}")
        
        # プリセットの説明を表示
        try:
            with open(preset_file, 'r', encoding='utf-8') as f:
                preset_data = yaml.safe_load(f)
                description = preset_data.get('metadata', {}).get('description', '')
                if description:
                    click.echo(f"    {description}")
        except Exception:
            pass  # 説明の読み込みに失敗しても継続


@cli.command()
@click.argument('xml_file', type=click.Path(exists=True))
@click.pass_context
def validate(ctx, xml_file):
    """XMLファイルを検証する"""
    verbose = ctx.obj.get('verbose', False)
    generator = UnattendGenerator(verbose=verbose)
    
    try:
        click.echo(f"XMLファイルを検証中: {xml_file}")
        
        if generator.xml_validator.validate_xml(xml_file):
            click.echo("✓ XML検証: 成功")
        else:
            click.echo("✗ XML検証: エラーがあります", err=True)
            
            # エラーレポートの表示
            report = generator.xml_validator.get_validation_report()
            if report:
                click.echo("\n検証レポート:")
                click.echo(report)
            
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"✗ 検証エラー: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()