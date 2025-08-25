"""
XML生成エンジンのテスト
"""

import pytest
import asyncio
from pathlib import Path
from lxml import etree
import yaml
import json
from src.core.xml_generator import (
    UnattendXMLGenerator,
    UnattendXMLAgent
)


class TestUnattendXMLGenerator:
    """UnattendXMLGeneratorクラスのテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.generator = UnattendXMLGenerator()
    
    def test_create_root_element(self):
        """ルート要素作成のテスト"""
        root = self.generator.create_root_element()
        
        assert root.tag == "{urn:schemas-microsoft-com:unattend}unattend"
        assert root.get("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation") is not None
    
    def test_create_settings_element(self):
        """設定要素作成のテスト"""
        settings = self.generator.create_settings_element("specialize")
        
        assert settings.tag == "settings"
        assert settings.get("pass") == "specialize"
    
    def test_add_component(self):
        """コンポーネント追加のテスト"""
        settings = self.generator.create_settings_element("specialize")
        component = self.generator.add_component(
            settings,
            "Microsoft-Windows-Shell-Setup"
        )
        
        assert component.tag == "component"
        assert component.get("name") == "Microsoft-Windows-Shell-Setup"
        assert component.get("processorArchitecture") == "amd64"
    
    def test_generate_windows_pe_settings(self):
        """WindowsPE設定生成のテスト"""
        settings = self.generator.generate_windows_pe_settings()
        
        assert settings.tag == "settings"
        assert settings.get("pass") == "windowsPE"
        
        # 言語設定の確認
        intl_component = settings.find(".//component[@name='Microsoft-Windows-International-Core-WinPE']")
        assert intl_component is not None
        assert intl_component.find("UILanguage").text == "ja-JP"
        assert intl_component.find("SystemLocale").text == "ja-JP"
    
    def test_generate_specialize_settings(self):
        """Specialize設定生成のテスト"""
        # システム設定を追加
        self.generator.features_manager.system_config.computer_name = "TEST-PC"
        self.generator.features_manager.system_config.timezone = "Tokyo Standard Time"
        
        settings = self.generator.generate_specialize_settings()
        
        assert settings.tag == "settings"
        assert settings.get("pass") == "specialize"
        
        # コンピューター名の確認
        shell_component = settings.find(".//component[@name='Microsoft-Windows-Shell-Setup']")
        assert shell_component is not None
        assert shell_component.find("ComputerName").text == "TEST-PC"
        assert shell_component.find("TimeZone").text == "Tokyo Standard Time"
    
    def test_generate_oobe_system_settings(self):
        """OOBESystem設定生成のテスト"""
        settings = self.generator.generate_oobe_system_settings()
        
        assert settings.tag == "settings"
        assert settings.get("pass") == "oobeSystem"
        
        # OOBE設定の確認
        oobe = settings.find(".//OOBE")
        assert oobe is not None
        assert oobe.find("HideEULAPage").text == "true"
        assert oobe.find("SkipMachineOOBE").text == "true"
        assert oobe.find("SkipUserOOBE").text == "true"
    
    @pytest.mark.asyncio
    async def test_generate_complete_xml(self):
        """完全なXML生成のテスト"""
        xml = await self.generator.generate()
        
        assert xml.tag == "{urn:schemas-microsoft-com:unattend}unattend"
        
        # 必須設定パスの確認
        settings_passes = [s.get("pass") for s in xml.findall("settings")]
        assert "windowsPE" in settings_passes
        assert "specialize" in settings_passes
        assert "oobeSystem" in settings_passes
    
    @pytest.mark.asyncio
    async def test_load_configuration(self, tmp_path):
        """設定ファイル読み込みのテスト"""
        # テスト用設定ファイル作成
        config = {
            "users": [
                {
                    "name": "test-user",
                    "groups": ["Administrators"],
                    "password": "TestP@ss123!"
                }
            ],
            "network": {
                "disable_ipv6": True,
                "disable_firewall": False
            },
            "metadata": {
                "configuration_name": "test-config"
            }
        }
        
        config_file = tmp_path / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # 設定読み込み
        await self.generator.load_configuration(config_file)
        
        # 設定が適用されていることを確認
        assert len(self.generator.user_manager.accounts) == 1
        assert self.generator.user_manager.accounts[0].name == "test-user"
        assert self.generator.metadata["configuration_name"] == "test-config"
    
    @pytest.mark.asyncio
    async def test_save_xml(self, tmp_path):
        """XML保存のテスト"""
        output_file = tmp_path / "test_unattend.xml"
        
        # XML保存
        await self.generator.save(output_file)
        
        # ファイルが作成されていることを確認
        assert output_file.exists()
        
        # メタデータファイルも作成されていることを確認
        metadata_file = output_file.with_suffix('.meta.json')
        assert metadata_file.exists()
        
        # XMLが読み込み可能であることを確認
        tree = etree.parse(str(output_file))
        root = tree.getroot()
        assert root.tag == "{urn:schemas-microsoft-com:unattend}unattend"
    
    @pytest.mark.asyncio
    async def test_validate(self):
        """バリデーションのテスト"""
        # ユーザーを追加
        from src.modules.user_management import UserAccount, UserGroup
        user = UserAccount(
            name="test-user",
            display_name="Test User",
            groups=[UserGroup.ADMINISTRATORS],
            password="TestP@ss123!"
        )
        self.generator.user_manager.add_account(user)
        
        # バリデーション実行
        is_valid, errors = await self.generator.validate()
        
        assert is_valid is True
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_with_errors(self):
        """エラーありバリデーションのテスト"""
        # ユーザーなしでバリデーション
        is_valid, errors = await self.generator.validate()
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("ユーザーアカウント" in error for error in errors)


@pytest.mark.asyncio
class TestUnattendXMLAgent:
    """UnattendXMLAgentクラスのテスト"""
    
    async def test_generate_from_preset_enterprise(self):
        """エンタープライズプリセットからの生成テスト"""
        generator = UnattendXMLGenerator()
        agent = UnattendXMLAgent(generator)
        
        xml = await agent.generate_from_preset("enterprise")
        
        assert xml.tag == "{urn:schemas-microsoft-com:unattend}unattend"
        
        # エンタープライズ設定が適用されていることを確認
        assert len(generator.user_manager.accounts) == 2
        assert generator.user_manager.accounts[0].name == "mirai-user"
        assert generator.user_manager.accounts[1].name == "l-admin"
    
    async def test_generate_from_preset_minimal(self):
        """最小プリセットからの生成テスト"""
        generator = UnattendXMLGenerator()
        agent = UnattendXMLAgent(generator)
        
        xml = await agent.generate_from_preset("minimal")
        
        assert xml.tag == "{urn:schemas-microsoft-com:unattend}unattend"
        
        # 最小設定が適用されていることを確認
        assert len(generator.user_manager.accounts) == 1
        assert generator.user_manager.accounts[0].name == "admin"
    
    async def test_generate_from_preset_invalid(self):
        """無効なプリセットのテスト"""
        generator = UnattendXMLGenerator()
        agent = UnattendXMLAgent(generator)
        
        with pytest.raises(ValueError, match="Unknown preset"):
            await agent.generate_from_preset("invalid_preset")
    
    async def test_batch_generate(self):
        """バッチ生成のテスト"""
        generator = UnattendXMLGenerator()
        agent = UnattendXMLAgent(generator)
        
        configurations = [
            {
                "users": [
                    {
                        "name": "user1",
                        "groups": ["Users"],
                        "password": "User1P@ss123!"
                    }
                ]
            },
            {
                "users": [
                    {
                        "name": "user2",
                        "groups": ["Administrators"],
                        "password": "User2P@ss123!"
                    }
                ]
            }
        ]
        
        results = await agent.batch_generate(configurations)
        
        assert len(results) == 2
        assert all(xml.tag == "{urn:schemas-microsoft-com:unattend}unattend" for xml in results)
    
    async def test_export_as_string(self):
        """文字列エクスポートのテスト"""
        generator = UnattendXMLGenerator()
        agent = UnattendXMLAgent(generator)
        
        xml_string = await agent.export_as_string()
        
        assert isinstance(xml_string, str)
        assert '<?xml version' in xml_string
        assert 'unattend' in xml_string


@pytest.fixture
def sample_config():
    """サンプル設定のフィクスチャ"""
    return {
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
        "metadata": {
            "configuration_name": "Enterprise Configuration",
            "version": "1.0.0"
        }
    }


@pytest.mark.asyncio
async def test_end_to_end_scenario(sample_config, tmp_path):
    """エンドツーエンドシナリオテスト"""
    generator = UnattendXMLGenerator()
    agent = UnattendXMLAgent(generator)
    
    # 設定を適用
    await generator._apply_configuration(sample_config)
    
    # XML生成
    xml = await generator.generate()
    
    # バリデーション
    is_valid, errors = await generator.validate(xml)
    assert is_valid is True
    
    # ファイル保存
    output_file = tmp_path / "enterprise_unattend.xml"
    await generator.save(output_file)
    
    # ファイル検証
    assert output_file.exists()
    
    # XMLの内容検証
    tree = etree.parse(str(output_file))
    root = tree.getroot()
    
    # ユーザー設定の確認
    users = root.findall(".//LocalAccount")
    assert len(users) >= 2
    
    # 設定パスの確認
    settings = root.findall("settings")
    passes = [s.get("pass") for s in settings]
    assert "windowsPE" in passes
    assert "specialize" in passes
    assert "oobeSystem" in passes