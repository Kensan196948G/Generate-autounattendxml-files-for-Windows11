#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル自動生成システム WebUI版
SubAgentシステム

このモジュールは、30体以上のSubAgentを管理し、
各種設定処理を並列実行するためのエージェントシステムです。
"""

from .base_agent import BaseAgent, AgentResult
from .user_agents import (
    UserCreationAgent, UserPermissionAgent, UserGroupAgent,
    AdministratorAgent, AutoLogonAgent
)
from .network_agents import (
    NetworkConfigAgent, FirewallConfigAgent, IPv6ConfigAgent,
    BluetoothConfigAgent, WiFiConfigAgent, ProxyConfigAgent
)
from .system_agents import (
    TimezoneAgent, LocaleAgent, AudioConfigAgent, TelemetryAgent,
    PowerConfigAgent, DisplayConfigAgent, PrinterConfigAgent
)
from .feature_agents import (
    WindowsFeatureAgent, OptionalFeatureAgent, CapabilityAgent,
    HyperVAgent, WSLAgent, ContainerAgent
)
from .application_agents import (
    OfficeConfigAgent, DefaultProgramAgent, SecuritySoftwareAgent,
    BrowserConfigAgent, EdgeConfigAgent, ChromeConfigAgent
)
from .security_agents import (
    SecurityHardeningAgent, UACAgen, WindowsDefenderAgent,
    BitLockerAgent, AppLockerAgent, FirewallAdvancedAgent
)
from .optimization_agents import (
    OptimizationAgent, PerformanceAgent, MemoryOptAgent,
    DiskOptAgent, ServiceOptAgent, StartupOptAgent
)
from .validation_agents import (
    RegistryValidationAgent, DependencyCheckAgent, ComplianceCheckAgent,
    ConfigValidationAgent, XMLValidationAgent, SchemaValidationAgent
)

# エージェント登録辞書
AGENT_REGISTRY = {
    # ユーザー管理エージェント群（5体）
    "UserCreationAgent": UserCreationAgent,
    "UserPermissionAgent": UserPermissionAgent,
    "UserGroupAgent": UserGroupAgent,
    "AdministratorAgent": AdministratorAgent,
    "AutoLogonAgent": AutoLogonAgent,
    
    # ネットワーク設定エージェント群（6体）
    "NetworkConfigAgent": NetworkConfigAgent,
    "FirewallConfigAgent": FirewallConfigAgent,
    "IPv6ConfigAgent": IPv6ConfigAgent,
    "BluetoothConfigAgent": BluetoothConfigAgent,
    "WiFiConfigAgent": WiFiConfigAgent,
    "ProxyConfigAgent": ProxyConfigAgent,
    
    # システム設定エージェント群（7体）
    "TimezoneAgent": TimezoneAgent,
    "LocaleAgent": LocaleAgent,
    "AudioConfigAgent": AudioConfigAgent,
    "TelemetryAgent": TelemetryAgent,
    "PowerConfigAgent": PowerConfigAgent,
    "DisplayConfigAgent": DisplayConfigAgent,
    "PrinterConfigAgent": PrinterConfigAgent,
    
    # 機能設定エージェント群（6体）
    "WindowsFeatureAgent": WindowsFeatureAgent,
    "OptionalFeatureAgent": OptionalFeatureAgent,
    "CapabilityAgent": CapabilityAgent,
    "HyperVAgent": HyperVAgent,
    "WSLAgent": WSLAgent,
    "ContainerAgent": ContainerAgent,
    
    # アプリケーション設定エージェント群（6体）
    "OfficeConfigAgent": OfficeConfigAgent,
    "DefaultProgramAgent": DefaultProgramAgent,
    "SecuritySoftwareAgent": SecuritySoftwareAgent,
    "BrowserConfigAgent": BrowserConfigAgent,
    "EdgeConfigAgent": EdgeConfigAgent,
    "ChromeConfigAgent": ChromeConfigAgent,
    
    # セキュリティエージェント群（6体）
    "SecurityHardeningAgent": SecurityHardeningAgent,
    "UACAgent": UACAgen,
    "WindowsDefenderAgent": WindowsDefenderAgent,
    "BitLockerAgent": BitLockerAgent,
    "AppLockerAgent": AppLockerAgent,
    "FirewallAdvancedAgent": FirewallAdvancedAgent,
    
    # 最適化エージェント群（6体）
    "OptimizationAgent": OptimizationAgent,
    "PerformanceAgent": PerformanceAgent,
    "MemoryOptAgent": MemoryOptAgent,
    "DiskOptAgent": DiskOptAgent,
    "ServiceOptAgent": ServiceOptAgent,
    "StartupOptAgent": StartupOptAgent,
    
    # 検証エージェント群（6体）
    "RegistryValidationAgent": RegistryValidationAgent,
    "DependencyCheckAgent": DependencyCheckAgent,
    "ComplianceCheckAgent": ComplianceCheckAgent,
    "ConfigValidationAgent": ConfigValidationAgent,
    "XMLValidationAgent": XMLValidationAgent,
    "SchemaValidationAgent": SchemaValidationAgent,
}

def get_agent(agent_name: str) -> type:
    """エージェントクラスを名前から取得"""
    return AGENT_REGISTRY.get(agent_name)

def list_available_agents() -> list:
    """利用可能なエージェント一覧を取得"""
    return list(AGENT_REGISTRY.keys())

def get_agent_count() -> int:
    """登録されているエージェント数を取得"""
    return len(AGENT_REGISTRY)

__all__ = [
    "BaseAgent", "AgentResult", "AGENT_REGISTRY",
    "get_agent", "list_available_agents", "get_agent_count"
]