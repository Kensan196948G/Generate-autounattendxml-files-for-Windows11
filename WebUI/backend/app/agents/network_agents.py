#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル自動生成システム WebUI版
ネットワーク設定エージェント群

ネットワーク関連の設定を担当する6つのSubAgentを実装します。
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, XMLGeneratingAgent


class NetworkConfigAgent(XMLGeneratingAgent):
    """ネットワーク基本設定エージェント"""
    
    def get_description(self) -> str:
        return "Windows 11の基本ネットワーク設定（ホスト名、IP設定など）"
    
    def get_supported_tasks(self) -> List[str]:
        return ["network_basic", "hostname", "ip_config"]
    
    def get_required_inputs(self) -> List[str]:
        return ["network"]
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        network = input_data["network"]
        
        network_settings = []
        
        # ホスト名設定
        if "hostname" in network:
            network_settings.append({
                "type": "ComputerName",
                "hostname": network["hostname"],
                "description": f"コンピューター名を'{network['hostname']}'に設定"
            })
        
        # ネットワークインターフェース設定
        if "interfaces" in network:
            for interface in network["interfaces"]:
                if not interface.get("dhcp_enabled", True):
                    # 固定IP設定
                    network_settings.append({
                        "type": "StaticIP",
                        "interface": interface.get("interface_name", "Ethernet"),
                        "ip_address": interface["ip_address"],
                        "subnet_mask": interface["subnet_mask"],
                        "default_gateway": interface.get("default_gateway"),
                        "dns_servers": interface.get("dns_servers", []),
                        "description": "固定IP設定"
                    })
        
        return {
            "xml_content": {"network_settings": network_settings},
            "xml_section": "specialize",
            "description": f"{len(network_settings)}個のネットワーク設定を生成"
        }


class FirewallConfigAgent(XMLGeneratingAgent):
    """Windows Firewall設定エージェント"""
    
    def get_description(self) -> str:
        return "Windows Firewallの有効/無効設定"
    
    def get_supported_tasks(self) -> List[str]:
        return ["firewall_config", "windows_firewall"]
    
    def get_required_inputs(self) -> List[str]:
        return ["enabled"]
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        enabled = input_data.get("enabled", False)
        
        firewall_settings = [{
            "type": "WindowsFirewall",
            "enabled": enabled,
            "profiles": {
                "domain": enabled,
                "private": enabled,
                "public": enabled
            },
            "description": f"Windows Firewallを{'有効' if enabled else '無効'}に設定"
        }]
        
        if not enabled:
            firewall_settings.append({
                "type": "SecurityWarning",
                "message": "Windows Firewallが無効に設定されています",
                "recommendation": "セキュリティ上の理由から有効化を推奨します"
            })
        
        return {
            "xml_content": {"firewall_settings": firewall_settings},
            "xml_section": "specialize",
            "description": f"Windows Firewall {'有効' if enabled else '無効'}設定"
        }


class IPv6ConfigAgent(XMLGeneratingAgent):
    """IPv6設定エージェント"""
    
    def get_description(self) -> str:
        return "IPv6プロトコルの有効/無効設定"
    
    def get_supported_tasks(self) -> List[str]:
        return ["ipv6_config", "network_protocols"]
    
    def get_required_inputs(self) -> List[str]:
        return ["enabled"]
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        enabled = input_data.get("enabled", False)
        
        ipv6_settings = [{
            "type": "IPv6Protocol",
            "enabled": enabled,
            "registry_path": r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters",
            "registry_value": "DisabledComponents",
            "registry_data": 0 if enabled else 255,
            "description": f"IPv6プロトコルを{'有効' if enabled else '無効'}に設定"
        }]
        
        return {
            "xml_content": {"ipv6_settings": ipv6_settings},
            "xml_section": "specialize",
            "description": f"IPv6 {'有効' if enabled else '無効'}設定"
        }


class BluetoothConfigAgent(XMLGeneratingAgent):
    """Bluetooth設定エージェント"""
    
    def get_description(self) -> str:
        return "Bluetooth機能の有効/無効設定"
    
    def get_supported_tasks(self) -> List[str]:
        return ["bluetooth_config", "wireless_config"]
    
    def get_required_inputs(self) -> List[str]:
        return ["enabled"]
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        enabled = input_data.get("enabled", False)
        
        bluetooth_settings = [{
            "type": "BluetoothService",
            "enabled": enabled,
            "service_name": "bthserv",
            "startup_type": "Automatic" if enabled else "Disabled",
            "description": f"Bluetoothサービスを{'有効' if enabled else '無効'}に設定"
        }]
        
        if not enabled:
            bluetooth_settings.append({
                "type": "BluetoothRadio",
                "radio_enabled": False,
                "discoverable": False,
                "description": "Bluetooth無線機能を無効化"
            })
        
        return {
            "xml_content": {"bluetooth_settings": bluetooth_settings},
            "xml_section": "specialize",
            "description": f"Bluetooth {'有効' if enabled else '無効'}設定"
        }


class WiFiConfigAgent(XMLGeneratingAgent):
    """Wi-Fi設定エージェント"""
    
    def get_description(self) -> str:
        return "Wi-Fi接続とワイヤレス設定"
    
    def get_supported_tasks(self) -> List[str]:
        return ["wifi_config", "wireless_networks", "wlan_profiles"]
    
    def get_required_inputs(self) -> List[str]:
        return []
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        wifi_networks = input_data.get("wifi_networks", [])
        wifi_enabled = input_data.get("wifi_enabled", True)
        
        wifi_settings = []
        
        # Wi-Fi機能の有効/無効
        wifi_settings.append({
            "type": "WiFiService",
            "enabled": wifi_enabled,
            "service_name": "WLAN AutoConfig",
            "startup_type": "Automatic" if wifi_enabled else "Disabled",
            "description": f"Wi-Fi機能を{'有効' if wifi_enabled else '無効'}に設定"
        })
        
        # Wi-Fiネットワークプロファイル
        for network in wifi_networks:
            wifi_settings.append({
                "type": "WiFiProfile",
                "ssid": network["ssid"],
                "security_type": network.get("security_type", "WPA2-PSK"),
                "password": network.get("password"),
                "auto_connect": network.get("auto_connect", True),
                "description": f"Wi-Fiネットワーク '{network['ssid']}' の設定"
            })
        
        return {
            "xml_content": {"wifi_settings": wifi_settings},
            "xml_section": "specialize",
            "description": f"Wi-Fi設定（{len(wifi_networks)}個のネットワーク）"
        }


class ProxyConfigAgent(XMLGeneratingAgent):
    """プロキシ設定エージェント"""
    
    def get_description(self) -> str:
        return "インターネット接続プロキシ設定"
    
    def get_supported_tasks(self) -> List[str]:
        return ["proxy_config", "internet_settings", "corporate_proxy"]
    
    def get_required_inputs(self) -> List[str]:
        return []
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        proxy_enabled = input_data.get("proxy_enabled", False)
        
        proxy_settings = []
        
        if proxy_enabled:
            proxy_server = input_data.get("proxy_server")
            proxy_port = input_data.get("proxy_port", 8080)
            proxy_exceptions = input_data.get("proxy_exceptions", [])
            
            if proxy_server:
                proxy_settings.append({
                    "type": "ProxyServer",
                    "enabled": True,
                    "server": proxy_server,
                    "port": proxy_port,
                    "exceptions": proxy_exceptions,
                    "bypass_local": input_data.get("bypass_local", True),
                    "description": f"プロキシサーバー {proxy_server}:{proxy_port} を設定"
                })
                
                # 認証設定
                if input_data.get("proxy_username"):
                    proxy_settings.append({
                        "type": "ProxyAuth",
                        "username": input_data["proxy_username"],
                        "password": input_data.get("proxy_password"),
                        "description": "プロキシ認証設定"
                    })
        else:
            proxy_settings.append({
                "type": "ProxyServer",
                "enabled": False,
                "description": "プロキシサーバーを無効に設定"
            })
        
        return {
            "xml_content": {"proxy_settings": proxy_settings},
            "xml_section": "specialize",
            "description": f"プロキシ設定 ({'有効' if proxy_enabled else '無効'})"
        }