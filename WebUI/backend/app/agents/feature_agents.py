#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル自動生成システム WebUI版
機能設定エージェント群

Windows機能関連の設定を担当する6つのSubAgentを実装します。
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, XMLGeneratingAgent


class WindowsFeatureAgent(XMLGeneratingAgent):
    """Windows機能設定エージェント"""
    
    def get_description(self) -> str:
        return "Windows機能の有効/無効設定"
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        feature = input_data.get("feature", {})
        
        return {
            "xml_content": {
                "feature_name": feature.get("feature_name"),
                "enabled": feature.get("enabled", True),
                "description": f"Windows機能 {feature.get('feature_name')} を{'有効' if feature.get('enabled') else '無効'}化"
            },
            "xml_section": "servicing",
            "description": f"Windows機能設定: {feature.get('feature_name')}"
        }


class OptionalFeatureAgent(XMLGeneratingAgent):
    """オプション機能設定エージェント"""
    
    def get_description(self) -> str:
        return "Windowsオプション機能設定"
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        features = input_data.get("optional_features", [])
        
        return {
            "xml_content": {
                "optional_features": features,
                "description": f"{len(features)}個のオプション機能を設定"
            },
            "xml_section": "servicing",
            "description": f"オプション機能: {len(features)}個"
        }


class CapabilityAgent(XMLGeneratingAgent):
    """機能ケーパビリティ設定エージェント"""
    
    def get_description(self) -> str:
        return "Windows機能ケーパビリティ設定"
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        capabilities = input_data.get("capabilities", [])
        
        return {
            "xml_content": {
                "capabilities": capabilities,
                "description": f"{len(capabilities)}個のケーパビリティを設定"
            },
            "xml_section": "servicing",
            "description": f"機能ケーパビリティ: {len(capabilities)}個"
        }


class HyperVAgent(XMLGeneratingAgent):
    """Hyper-V設定エージェント"""
    
    def get_description(self) -> str:
        return "Hyper-V仮想化機能設定"
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        enabled = input_data.get("hyper_v_enabled", False)
        
        return {
            "xml_content": {
                "hyper_v_settings": [{
                    "feature_name": "Microsoft-Hyper-V-All",
                    "enabled": enabled,
                    "description": f"Hyper-Vを{'有効' if enabled else '無効'}化"
                }]
            },
            "xml_section": "servicing",
            "description": f"Hyper-V {'有効' if enabled else '無効'}設定"
        }


class WSLAgent(XMLGeneratingAgent):
    """WSL設定エージェント"""
    
    def get_description(self) -> str:
        return "Windows Subsystem for Linux (WSL)設定"
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        enabled = input_data.get("wsl_enabled", False)
        
        return {
            "xml_content": {
                "wsl_settings": [{
                    "feature_name": "Microsoft-Windows-Subsystem-Linux",
                    "enabled": enabled,
                    "description": f"WSLを{'有効' if enabled else '無効'}化"
                }]
            },
            "xml_section": "servicing",
            "description": f"WSL {'有効' if enabled else '無効'}設定"
        }


class ContainerAgent(XMLGeneratingAgent):
    """コンテナ機能設定エージェント"""
    
    def get_description(self) -> str:
        return "Windowsコンテナ機能設定"
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        enabled = input_data.get("containers_enabled", False)
        
        return {
            "xml_content": {
                "container_settings": [{
                    "feature_name": "Containers",
                    "enabled": enabled,
                    "description": f"Windowsコンテナを{'有効' if enabled else '無効'}化"
                }]
            },
            "xml_section": "servicing",
            "description": f"コンテナ機能 {'有効' if enabled else '無効'}設定"
        }
