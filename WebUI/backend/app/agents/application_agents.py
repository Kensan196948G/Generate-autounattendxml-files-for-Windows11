#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル自動生成システム WebUI版
アプリケーション設定エージェント群

アプリケーション関連の設定を担当する6つのSubAgentを実装します。
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, XMLGeneratingAgent


class OfficeConfigAgent(XMLGeneratingAgent):
    """Microsoft Office設定エージェント"""
    
    def get_description(self) -> str:
        return "Microsoft Officeアプリケーションの設定"
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        settings = input_data.get("settings", [])
        
        office_configs = []
        for setting in settings:
            office_configs.append({
                "type": "RegistryConfig",
                "application": setting.get("application_name", "Office"),
                "key": setting.get("setting_key"),
                "value": setting.get("setting_value"),
                "registry_path": setting.get("registry_path")
            })
        
        return {
            "xml_content": {
                "registry_settings": office_configs
            },
            "xml_section": "specialize",
            "description": f"Office設定: {len(settings)}個"
        }


class DefaultProgramAgent(XMLGeneratingAgent):
    """既定のプログラム設定エージェント"""
    
    def get_description(self) -> str:
        return "既定のプログラム関連付け設定"
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        programs = input_data.get("programs", [])
        
        default_programs = []
        for program in programs:
            default_programs.append({
                "type": "DefaultAssociation",
                "extension": program.get("file_association"),
                "program_id": program.get("program_id"),
                "program_name": program.get("program_name")
            })
        
        return {
            "xml_content": {
                "registry_settings": default_programs
            },
            "xml_section": "specialize",
            "description": f"既定プログラム: {len(programs)}個"
        }


class SecuritySoftwareAgent(XMLGeneratingAgent):
    """セキュリティソフト設定エージェント"""
    
    def get_description(self) -> str:
        return "セキュリティソフトウェアの設定"
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        security_config = input_data or {}
        
        return {
            "xml_content": {
                "security_settings": [{
                    "type": "SecuritySoftware",
                    "config": security_config,
                    "description": "セキュリティソフト設定"
                }]
            },
            "xml_section": "specialize",
            "description": "セキュリティソフト設定"
        }


class BrowserConfigAgent(XMLGeneratingAgent):
    """ブラウザ設定エージェント"""
    
    def get_description(self) -> str:
        return "ウェブブラウザの基本設定"
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        default_browser = input_data.get("default_browser", "Edge")
        
        return {
            "xml_content": {
                "browser_settings": [{
                    "type": "DefaultBrowser",
                    "browser": default_browser,
                    "description": f"既定ブラウザを{default_browser}に設定"
                }]
            },
            "xml_section": "specialize",
            "description": f"ブラウザ設定: {default_browser}"
        }


class EdgeConfigAgent(XMLGeneratingAgent):
    """Microsoft Edge設定エージェント"""
    
    def get_description(self) -> str:
        return "Microsoft Edgeブラウザの詳細設定"
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        edge_config = input_data.get("edge_config", {})
        
        return {
            "xml_content": {
                "edge_settings": [{
                    "type": "EdgeConfig",
                    "config": edge_config,
                    "description": "Microsoft Edge詳細設定"
                }]
            },
            "xml_section": "specialize",
            "description": "Microsoft Edge設定"
        }


class ChromeConfigAgent(XMLGeneratingAgent):
    """Google Chrome設定エージェント"""
    
    def get_description(self) -> str:
        return "Google Chromeブラウザの設定"
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        chrome_config = input_data.get("chrome_config", {})
        
        return {
            "xml_content": {
                "chrome_settings": [{
                    "type": "ChromeConfig",
                    "config": chrome_config,
                    "description": "Google Chrome設定"
                }]
            },
            "xml_section": "specialize",
            "description": "Google Chrome設定"
        }
