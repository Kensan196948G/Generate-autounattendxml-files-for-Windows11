"""
統合テスト

すべてのモジュールが連携して正しく動作することを確認
"""

import pytest
import asyncio
from pathlib import Path
import yaml
import json
from lxml import etree
from click.testing import CliRunner

# モジュールのインポート
from generate_unattend import cli
from src.core.xml_generator import UnattendXMLGenerator, UnattendXMLAgent
from src.core.validator import XMLValidator, ConfigValidator, DependencyChecker
from src.modules.user_management import UserAccountManager, UserAccount, UserGroup
from src.modules.network_config import NetworkConfigManager
from src.modules.windows_features import WindowsFeaturesManager
from src.modules.application_config import ApplicationManager


class TestFullIntegration:
    """完全統合テスト"""
    
    @pytest.mark.asyncio
    async def test_enterprise_deployment_scenario(self, tmp_path):
        """企業展開シナリオの完全テスト"""
        # 1. ジェネレーター初期化
        generator = UnattendXMLGenerator()
        agent = UnattendXMLAgent(generator)
        
        # 2. エンタープライズプリセット適用
        xml = await agent.generate_from_preset("enterprise")
        
        # 3. 検証
        is_valid, errors = await generator.validate(xml)
        assert is_valid is True, f"Validation errors: {errors}"
        
        # 4. 各設定の確認
        # ユーザー設定
        assert len(generator.user_manager.accounts) == 2
        assert any(u.name == "mirai-user" for u in generator.user_manager.accounts)
        assert any(u.name == "l-admin" for u in generator.user_manager.accounts)
        
        # ネットワーク設定
        network_config = generator.network_manager.config
        assert network_config.ipv6_config.disable_ipv6 is True
        assert network_config.firewall_config.disable_domain is True
        assert network_config.bluetooth_config.disable_bluetooth is True
        
        # 5. XML保存
        output_file = tmp_path / "enterprise.xml"
        await generator.save(output_file)
        assert output_file.exists()
        
        # 6. XMLの詳細検証
        tree = etree.parse(str(output_file))
        root = tree.getroot()
        
        # 必須要素の確認
        assert root.find(".//ComputerName") is not None
        assert root.find(".//TimeZone") is not None
        assert root.find(".//UserAccounts") is not None
        assert root.find(".//OOBE") is not None
        assert root.find(".//FirstLogonCommands") is not None
        
        # コマンド数の確認
        commands = root.findall(".//SynchronousCommand")
        assert len(commands) > 10  # 十分なコマンドが生成されている
    
    @pytest.mark.asyncio
    async def test_minimal_deployment_scenario(self, tmp_path):
        """最小構成展開シナリオのテスト"""
        generator = UnattendXMLGenerator()
        agent = UnattendXMLAgent(generator)
        
        # 最小プリセット適用
        xml = await agent.generate_from_preset("minimal")
        
        # 検証
        is_valid, errors = await generator.validate(xml)
        assert is_valid is True
        
        # 最小構成の確認
        assert len(generator.user_manager.accounts) == 1
        
        # XML保存とサイズ確認
        output_file = tmp_path / "minimal.xml"
        await generator.save(output_file)
        
        # ファイルサイズが適切であることを確認
        file_size = output_file.stat().st_size
        assert file_size > 1000  # 最小でも1KB以上
        assert file_size < 100000  # 100KB未満
    
    @pytest.mark.asyncio
    async def test_custom_configuration_workflow(self, tmp_path):
        """カスタム設定ワークフローのテスト"""
        # カスタム設定ファイル作成
        custom_config = {
            "users": [
                {
                    "name": "custom-admin",
                    "display_name": "Custom Administrator",
                    "groups": ["Administrators"],
                    "password": "CustomP@ss2024!",
                    "password_never_expires": True
                },
                {
                    "name": "custom-user",
                    "display_name": "Custom User",
                    "groups": ["Users"],
                    "password": "UserP@ss2024!",
                    "change_password_at_logon": True
                }
            ],
            "network": {
                "disable_ipv6": True,
                "disable_firewall": False,
                "disable_bluetooth": True,
                "dns_servers": ["8.8.8.8", "8.8.4.4"]
            },
            "features": {
                "enable_features": [".NET Framework 3.5"],
                "disable_features": ["Windows Media Player"],
                "services": {
                    "Windows Search": "disabled",
                    "Windows Update": "manual"
                }
            },
            "applications": {
                "default_browser": "Edge",
                "default_email": "Outlook",
                "default_pdf": "Adobe Acrobat Reader DC",
                "office_settings": {
                    "disable_first_run": True,
                    "disable_protected_view": True
                }
            },
            "system": {
                "computer_name": "CUSTOM-PC",
                "timezone": "Tokyo Standard Time",
                "power_plan": "high_performance",
                "enable_remote_desktop": True
            }
        }
        
        config_file = tmp_path / "custom_config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(custom_config, f)
        
        # 設定読み込みと処理
        generator = UnattendXMLGenerator()
        await generator.load_configuration(config_file)
        
        # XML生成
        xml = await generator.generate()
        
        # 検証
        validator = XMLValidator()
        is_valid, errors = validator.validate_xml(etree.tostring(xml))
        assert is_valid is True
        
        # カスタム設定が適用されていることを確認
        assert len(generator.user_manager.accounts) == 2
        assert generator.user_manager.accounts[0].name == "custom-admin"
        assert generator.features_manager.system_config.computer_name == "CUSTOM-PC"
    
    @pytest.mark.asyncio
    async def test_parallel_configuration_processing(self):
        """並列設定処理のテスト"""
        generator = UnattendXMLGenerator()
        
        # 複数の設定タスクを並列実行
        tasks = []
        
        # ユーザー作成タスク
        for i in range(5):
            user_config = {
                "name": f"user{i}",
                "groups": ["Users"],
                "password": f"UserP@ss{i:04d}!"
            }
            tasks.append(generator.user_agent.create_user(user_config))
        
        # ネットワーク設定タスク
        network_config = {
            "disable_ipv6": True,
            "disable_firewall": True
        }
        tasks.append(generator.network_agent.configure_network_security(network_config))
        
        # Windows機能設定タスク
        tasks.append(generator.features_agent.apply_enterprise_settings())
        
        # アプリケーション設定タスク
        tasks.append(generator.app_agent.apply_preset("enterprise_standard"))
        
        # 並列実行
        await asyncio.gather(*tasks)
        
        # すべての設定が適用されていることを確認
        assert len(generator.user_manager.accounts) == 5
        assert generator.network_manager.config.ipv6_config.disable_ipv6 is True
        assert len(generator.features_manager.enabled_features) > 0
        assert generator.app_manager.default_apps is not None


class TestCLIIntegration:
    """CLIインターフェースの統合テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.runner = CliRunner()
    
    def test_cli_generate_with_preset(self, tmp_path):
        """CLIでプリセット使用のテスト"""
        output_file = tmp_path / "cli_test.xml"
        
        result = self.runner.invoke(cli, [
            'generate',
            '--preset', 'minimal',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        assert "XML生成完了" in result.output
    
    def test_cli_list_presets(self):
        """プリセット一覧表示のテスト"""
        result = self.runner.invoke(cli, ['list-presets'])
        
        assert result.exit_code == 0
        assert "enterprise" in result.output
        assert "minimal" in result.output
        assert "development" in result.output
    
    def test_cli_validate(self, tmp_path):
        """CLI検証コマンドのテスト"""
        # まずXMLを生成
        xml_file = tmp_path / "validate_test.xml"
        
        generate_result = self.runner.invoke(cli, [
            'generate',
            '--preset', 'minimal',
            '--output', str(xml_file)
        ])
        assert generate_result.exit_code == 0
        
        # 検証実行
        validate_result = self.runner.invoke(cli, [
            'validate',
            str(xml_file)
        ])
        
        assert validate_result.exit_code == 0
        assert "検証成功" in validate_result.output or "Validation successful" in validate_result.output
    
    def test_cli_with_custom_config(self, tmp_path):
        """カスタム設定ファイル使用のテスト"""
        # 設定ファイル作成
        config = {
            "users": [
                {
                    "name": "cli-user",
                    "groups": ["Administrators"],
                    "password": "CLIP@ss2024!"
                }
            ]
        }
        
        config_file = tmp_path / "cli_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        output_file = tmp_path / "cli_custom.xml"
        
        result = self.runner.invoke(cli, [
            'generate',
            '--config', str(config_file),
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()


class TestValidationIntegration:
    """バリデーション統合テスト"""
    
    def test_xml_validator(self):
        """XMLバリデーターのテスト"""
        validator = XMLValidator()
        
        # 有効なXML
        valid_xml = """<?xml version="1.0" encoding="utf-8"?>
        <unattend xmlns="urn:schemas-microsoft-com:unattend">
            <settings pass="oobeSystem">
                <component name="Microsoft-Windows-Shell-Setup">
                    <OOBE>
                        <HideEULAPage>true</HideEULAPage>
                    </OOBE>
                </component>
            </settings>
        </unattend>"""
        
        is_valid, errors = validator.validate_xml(valid_xml)
        assert is_valid is True
        
        # 無効なXML
        invalid_xml = "<invalid>test"
        is_valid, errors = validator.validate_xml(invalid_xml)
        assert is_valid is False
        assert len(errors) > 0
    
    def test_config_validator(self):
        """設定バリデーターのテスト"""
        validator = ConfigValidator()
        
        # 有効な設定
        valid_config = {
            "users": [
                {
                    "name": "test-user",
                    "groups": ["Administrators"],
                    "password": "TestP@ss123!"
                }
            ]
        }
        
        is_valid, errors = validator.validate_config(valid_config)
        assert is_valid is True
        
        # 無効な設定（パスワードなし）
        invalid_config = {
            "users": [
                {
                    "name": "test-user",
                    "groups": ["Administrators"]
                }
            ]
        }
        
        is_valid, errors = validator.validate_config(invalid_config)
        assert is_valid is False
        assert any("password" in error.lower() for error in errors)
    
    def test_dependency_checker(self):
        """依存関係チェッカーのテスト"""
        checker = DependencyChecker()
        
        config = {
            "features": {
                "enable_features": ["IIS-ASPNET45"],
                "disable_features": ["IIS-WebServerRole"]
            }
        }
        
        conflicts = checker.check_dependencies(config)
        assert len(conflicts) > 0  # IIS-ASPNET45はIIS-WebServerRoleに依存


@pytest.mark.asyncio
async def test_performance_large_configuration():
    """大規模設定でのパフォーマンステスト"""
    import time
    
    generator = UnattendXMLGenerator()
    
    # 大量のユーザーを作成
    start_time = time.time()
    
    tasks = []
    for i in range(50):
        user_config = {
            "name": f"user{i:03d}",
            "display_name": f"User {i:03d}",
            "groups": ["Users"] if i % 2 == 0 else ["Administrators"],
            "password": f"UserP@ss{i:04d}!"
        }
        tasks.append(generator.user_agent.create_user(user_config))
    
    await asyncio.gather(*tasks)
    
    # XML生成
    xml = await generator.generate()
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # パフォーマンス基準: 50ユーザーで10秒以内
    assert processing_time < 10.0
    
    # 生成されたXMLのサイズ確認
    xml_string = etree.tostring(xml, encoding='unicode')
    assert len(xml_string) > 10000  # 十分なコンテンツが生成されている
    
    # すべてのユーザーが含まれていることを確認
    assert len(generator.user_manager.accounts) == 50