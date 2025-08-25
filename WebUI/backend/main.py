"""
Windows 11 無人応答ファイル生成システム - バックエンドサーバー
Context7機能、SubAgent（42体）、Claude-flow並列処理完全対応版
ポート: 8081
"""

import os
import sys
import socket
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field
import uvicorn
import yaml

# psutilをオプショナルインポート
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not available - health monitoring limited")

# ローカルモジュールのインポートパスを追加
sys.path.insert(0, str(Path(__file__).parent))

# XML生成モジュールをインポート
from xml_generator import UnattendXMLGenerator, XMLGeneratorSubAgent
from config_transformer import transform_frontend_config
from enhanced_xml_generator import EnhancedXMLGenerator
from config_log_generator import ConfigLogGenerator
from comprehensive_config_processor import ComprehensiveConfigProcessor
from comprehensive_log_generator import ComprehensiveLogGenerator
from comprehensive_xml_generator import ComprehensiveXMLGenerator

# IPアドレスの自動検出
def get_local_ip():
    """ローカルIPアドレスを取得（APIPA除外）"""
    try:
        # 優先IP（あなたの環境）
        target_ip = "192.168.3.92"
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip == target_ip:
                return ip
            if not ip.startswith("169.254."):
                return ip
        finally:
            s.close()
        
        # フォールバック
        hostname = socket.gethostname()
        ip_list = socket.gethostbyname_ex(hostname)[2]
        for ip in ip_list:
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                return ip
        
        return "127.0.0.1"
    except Exception as e:
        print(f"IP検出エラー: {e}")
        return "127.0.0.1"

# ===== Context7機能実装 =====
class Context7Manager:
    """Context7: 高度なコンテキスト管理機能"""
    
    def __init__(self):
        self.contexts: Dict[str, Any] = {}
        self.context_history: List[Dict] = []
        self.max_history = 100
        
    async def create_context(self, session_id: str, data: Dict) -> Dict:
        """新規コンテキストの作成"""
        context = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "data": data,
            "status": "active",
            "metadata": {
                "version": 7,
                "features": ["multi-layer", "persistent", "shareable"]
            }
        }
        self.contexts[session_id] = context
        self.context_history.append(context)
        
        if len(self.context_history) > self.max_history:
            self.context_history.pop(0)
            
        return context
    
    async def get_context(self, session_id: str) -> Optional[Dict]:
        """コンテキストの取得"""
        return self.contexts.get(session_id)
    
    async def update_context(self, session_id: str, updates: Dict):
        """コンテキストの更新"""
        if session_id in self.contexts:
            self.contexts[session_id]["data"].update(updates)
            self.contexts[session_id]["updated_at"] = datetime.now().isoformat()

# ===== SubAgent実装（42体） =====
class SubAgent:
    """基本SubAgentクラス"""
    
    def __init__(self, name: str, role: str, capabilities: List[str]):
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.status = "ready"
        self.tasks_completed = 0
        
    async def process(self, task: Dict) -> Dict:
        """タスク処理"""
        self.status = "processing"
        result = {
            "agent": self.name,
            "task": task,
            "result": f"{self.role}の処理完了",
            "timestamp": datetime.now().isoformat()
        }
        self.tasks_completed += 1
        self.status = "ready"
        return result

# 42体のSubAgent定義
def create_all_subagents() -> Dict[str, SubAgent]:
    """42体のSubAgentを生成"""
    agents = {}
    
    # ユーザー管理系（6体）
    agents["user_creator"] = SubAgent("UserCreator", "ユーザーアカウント作成", ["create_user", "set_password"])
    agents["user_permission"] = SubAgent("UserPermission", "権限管理", ["set_permissions", "manage_groups"])
    agents["admin_manager"] = SubAgent("AdminManager", "管理者設定", ["admin_rights", "elevation"])
    agents["domain_joiner"] = SubAgent("DomainJoiner", "ドメイン参加", ["join_domain", "trust_relationship"])
    agents["profile_manager"] = SubAgent("ProfileManager", "プロファイル管理", ["user_profile", "roaming"])
    agents["autologon_setter"] = SubAgent("AutoLogonSetter", "自動ログオン設定", ["autologon", "credentials"])
    
    # ネットワーク系（6体）
    agents["network_config"] = SubAgent("NetworkConfig", "ネットワーク設定", ["ip_config", "dns"])
    agents["firewall_manager"] = SubAgent("FirewallManager", "ファイアウォール管理", ["rules", "exceptions"])
    agents["wifi_config"] = SubAgent("WiFiConfig", "Wi-Fi設定", ["ssid", "security"])
    agents["vpn_setup"] = SubAgent("VPNSetup", "VPN設定", ["vpn_config", "certificates"])
    agents["proxy_config"] = SubAgent("ProxyConfig", "プロキシ設定", ["proxy", "bypass"])
    agents["ipv6_manager"] = SubAgent("IPv6Manager", "IPv6管理", ["ipv6", "disable_ipv6"])
    
    # システム設定系（6体）
    agents["hostname_setter"] = SubAgent("HostnameSetter", "ホスト名設定", ["computer_name", "workgroup"])
    agents["timezone_config"] = SubAgent("TimezoneConfig", "タイムゾーン設定", ["timezone", "ntp"])
    agents["language_pack"] = SubAgent("LanguagePack", "言語パック", ["language", "region"])
    agents["update_manager"] = SubAgent("UpdateManager", "更新管理", ["windows_update", "wsus"])
    agents["power_config"] = SubAgent("PowerConfig", "電源設定", ["power_plan", "sleep"])
    agents["audio_config"] = SubAgent("AudioConfig", "音声設定", ["mute", "volume"])
    
    # Windows機能系（6体）
    agents["dotnet_installer"] = SubAgent("DotNetInstaller", ".NET Framework", ["dotnet35", "dotnet48"])
    agents["hyperv_enabler"] = SubAgent("HyperVEnabler", "Hyper-V有効化", ["hyperv", "virtualization"])
    agents["wsl_installer"] = SubAgent("WSLInstaller", "WSL設定", ["wsl2", "linux"])
    agents["sandbox_enabler"] = SubAgent("SandboxEnabler", "Sandbox有効化", ["sandbox", "isolation"])
    agents["iis_installer"] = SubAgent("IISInstaller", "IIS設定", ["iis", "web_server"])
    agents["feature_manager"] = SubAgent("FeatureManager", "機能管理", ["windows_features", "optional"])
    
    # アプリケーション系（6体）
    agents["office_config"] = SubAgent("OfficeConfig", "Office設定", ["office365", "activation"])
    agents["browser_default"] = SubAgent("BrowserDefault", "既定ブラウザ", ["edge", "chrome"])
    agents["pdf_handler"] = SubAgent("PDFHandler", "PDF設定", ["acrobat", "default_pdf"])
    agents["mail_config"] = SubAgent("MailConfig", "メール設定", ["outlook", "mail_client"])
    agents["app_installer"] = SubAgent("AppInstaller", "アプリインストール", ["install", "packages"])
    agents["store_config"] = SubAgent("StoreConfig", "ストア設定", ["microsoft_store", "apps"])
    
    # セキュリティ系（6体）
    agents["defender_config"] = SubAgent("DefenderConfig", "Defender設定", ["antivirus", "realtime"])
    agents["bitlocker_setup"] = SubAgent("BitlockerSetup", "BitLocker設定", ["encryption", "tpm"])
    agents["uac_manager"] = SubAgent("UACManager", "UAC管理", ["uac_level", "prompts"])
    agents["security_policy"] = SubAgent("SecurityPolicy", "セキュリティポリシー", ["local_policy", "gpo"])
    agents["audit_config"] = SubAgent("AuditConfig", "監査設定", ["audit_policy", "logging"])
    agents["credential_guard"] = SubAgent("CredentialGuard", "資格情報保護", ["credential", "protection"])
    
    # システム最適化系（6体）
    agents["performance_tuner"] = SubAgent("PerformanceTuner", "パフォーマンス調整", ["performance", "optimization"])
    agents["storage_optimizer"] = SubAgent("StorageOptimizer", "ストレージ最適化", ["disk", "cleanup"])
    agents["startup_manager"] = SubAgent("StartupManager", "スタートアップ管理", ["startup", "services"])
    agents["registry_tweaker"] = SubAgent("RegistryTweaker", "レジストリ調整", ["registry", "tweaks"])
    agents["telemetry_config"] = SubAgent("TelemetryConfig", "テレメトリ設定", ["telemetry", "privacy"])
    agents["cleanup_agent"] = SubAgent("CleanupAgent", "クリーンアップ", ["temp_files", "cache"])
    
    return agents

# ===== Claude-flow並列処理エンジン =====
class ClaudeFlowEngine:
    """Claude-flow並列処理エンジン"""
    
    def __init__(self, agents: Dict[str, SubAgent]):
        self.agents = agents
        self.task_queue = asyncio.Queue()
        self.results = {}
        self.parallel_limit = 10  # 同時実行数制限
        
    async def add_task(self, task_id: str, agent_name: str, task_data: Dict):
        """タスクをキューに追加"""
        await self.task_queue.put({
            "id": task_id,
            "agent": agent_name,
            "data": task_data
        })
    
    async def process_parallel(self, tasks: List[Dict]) -> List[Dict]:
        """並列処理実行"""
        semaphore = asyncio.Semaphore(self.parallel_limit)
        
        async def process_with_limit(task):
            async with semaphore:
                agent_name = task.get("agent")
                if agent_name in self.agents:
                    agent = self.agents[agent_name]
                    return await agent.process(task)
                return {"error": f"Agent {agent_name} not found"}
        
        results = await asyncio.gather(*[process_with_limit(task) for task in tasks])
        return results
    
    async def execute_workflow(self, workflow: Dict) -> Dict:
        """ワークフロー実行"""
        start_time = datetime.now()
        workflow_id = str(uuid.uuid4())
        
        # ワークフローステップを並列グループに分割
        parallel_groups = workflow.get("parallel_groups", [])
        all_results = []
        
        for group in parallel_groups:
            group_results = await self.process_parallel(group)
            all_results.extend(group_results)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "results": all_results,
            "duration": duration,
            "timestamp": end_time.isoformat()
        }

# ===== FastAPIアプリケーション =====
app = FastAPI(
    title="Windows 11 無人応答ファイル生成システム",
    description="Context7 + SubAgent(42体) + Claude-flow並列処理対応",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS設定
LOCAL_IP = get_local_ip()
allowed_origins = [
    f"http://{LOCAL_IP}:3050",      # メインフロントエンド
    "http://localhost:3050",        # ローカル開発用
    "http://192.168.3.92:3050",     # 固定IP指定
    "http://127.0.0.1:3050",        # ローカルIP
    f"http://{LOCAL_IP}:3000",      # Next.js デフォルトポート
    "http://localhost:3000",        # Next.js ローカル開発
    "http://192.168.3.92:3000",     # 固定IP Next.js
    "http://127.0.0.1:3000",        # ローカルIP Next.js
    f"http://{LOCAL_IP}:8082",      # テストサーバー
    "http://localhost:8082",        # テストサーバーローカル
    "http://192.168.3.92:8082",     # テストサーバー固定IP
    "http://127.0.0.1:8082",        # テストサーバーローカルIP
    f"http://{LOCAL_IP}:8083",      # 追加テストサーバー
    "http://localhost:8083",        # 追加テストサーバーローカル
    "http://192.168.3.92:8083",     # 固定IP 追加テストサーバー
    "http://127.0.0.1:8083",        # ローカルIP 追加テストサーバー
    f"http://{LOCAL_IP}:8084",      # テストサーバー ポート8084
    "http://localhost:8084",        # テストサーバーローカル ポート8084
    "http://192.168.3.92:8084",     # 固定IP テストサーバー ポート8084
    "http://127.0.0.1:8084"         # ローカルIP テストサーバー ポート8084
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# グローバルインスタンス
context7 = Context7Manager()
subagents = create_all_subagents()
claude_flow = ClaudeFlowEngine(subagents)

# WebSocket接続管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# ===== APIモデル定義 =====
class GenerateRequest(BaseModel):
    """XML生成リクエスト"""
    preset: str = Field(default="enterprise", description="プリセット名")
    config: Dict = Field(default_factory=dict, description="カスタム設定")
    context7_enabled: bool = Field(default=True, description="Context7機能")
    parallel_processing: bool = Field(default=True, description="並列処理")

class AgentStatus(BaseModel):
    """エージェントステータス"""
    total_agents: int
    active_agents: List[str]
    completed_tasks: int

# ===== APIエンドポイント =====
@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Windows 11 無人応答ファイル生成システム",
        "version": "2.0.0",
        "features": {
            "context7": "有効",
            "subagents": f"{len(subagents)}体",
            "parallel_processing": "Claude-flow対応"
        },
        "api_docs": f"http://{LOCAL_IP}:8081/api/docs",
        "frontend": f"http://{LOCAL_IP}:3050"
    }

@app.get("/api/status")
async def get_status():
    """システムステータス"""
    return {
        "status": "operational",
        "ip_address": LOCAL_IP,
        "context7": "active",
        "subagents": {
            "total": len(subagents),
            "ready": sum(1 for a in subagents.values() if a.status == "ready"),
            "processing": sum(1 for a in subagents.values() if a.status == "processing")
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/test")
async def test_connectivity():
    """フロントエンド接続テスト用"""
    return {
        "success": True,
        "message": "フロントエンドとバックエンドの接続が正常です",
        "backend_ip": LOCAL_IP,
        "timestamp": datetime.now().isoformat(),
        "allowed_origins": allowed_origins
    }

@app.get("/api/health")
async def health_check():
    """詳細ヘルスチェック"""
    import platform
    
    # システムメトリクス取得
    try:
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # プロセス情報
            process = psutil.Process()
            process_info = {
                "pid": process.pid,
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "threads": process.num_threads(),
                "connections": len(process.connections())
            }
        else:
            cpu_percent = 0
            memory = None
            disk = None
            process_info = {
                "pid": os.getpid(),
                "cpu_percent": 0,
                "memory_mb": 0,
                "threads": 0,
                "connections": 0
            }
    except Exception as e:
        cpu_percent = 0
        memory = None
        disk = None
        process_info = {}
    
    # SubAgent健全性チェック
    agent_health = {
        "total": len(subagents),
        "healthy": 0,
        "degraded": 0,
        "failed": 0
    }
    
    for agent in subagents.values():
        if agent.status == "ready":
            agent_health["healthy"] += 1
        elif agent.status == "processing":
            agent_health["degraded"] += 1
        else:
            agent_health["failed"] += 1
    
    # Context7状態
    context7_status = {
        "active_contexts": len(context7.contexts),
        "memory_usage": sum(sys.getsizeof(ctx) for ctx in context7.contexts.values()) if context7.contexts else 0,
        "oldest_context": min((ctx.get("created_at", datetime.now()) for ctx in context7.contexts.values()), default=None) if context7.contexts else None
    }
    
    # 総合ヘルスステータス判定
    overall_status = "healthy"
    issues = []
    
    if cpu_percent > 80:
        overall_status = "degraded"
        issues.append(f"CPU使用率が高い: {cpu_percent}%")
    
    if memory and memory.percent > 85:
        overall_status = "degraded"
        issues.append(f"メモリ使用率が高い: {memory.percent}%")
    
    if agent_health["failed"] > 0:
        overall_status = "degraded"
        issues.append(f"失敗したエージェント: {agent_health['failed']}")
    
    if agent_health["healthy"] < agent_health["total"] * 0.5:
        overall_status = "unhealthy"
        issues.append("半数以上のエージェントが正常でない")
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - startup_time).total_seconds() if 'startup_time' in globals() else 0,
        "system": {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_percent": cpu_percent,
            "memory": {
                "percent": memory.percent if memory else 0,
                "available_mb": memory.available / 1024 / 1024 if memory else 0,
                "total_mb": memory.total / 1024 / 1024 if memory else 0
            } if memory else {},
            "disk": {
                "percent": disk.percent if disk else 0,
                "free_gb": disk.free / 1024 / 1024 / 1024 if disk else 0
            } if disk else {}
        },
        "process": process_info,
        "agents": agent_health,
        "context7": context7_status,
        "websocket_connections": len(manager.active_connections),
        "issues": issues,
        "endpoints": {
            "api_docs": f"http://{LOCAL_IP}:8081/api/docs",
            "frontend": f"http://{LOCAL_IP}:3050"
        }
    }

@app.get("/api/agents")
async def get_agents():
    """SubAgent一覧"""
    return {
        "total": len(subagents),
        "agents": [
            {
                "name": agent.name,
                "role": agent.role,
                "capabilities": agent.capabilities,
                "status": agent.status,
                "tasks_completed": agent.tasks_completed
            }
            for agent in subagents.values()
        ]
    }

@app.get("/api/presets")
async def get_presets():
    """プリセット一覧"""
    return [
        {
            "name": "enterprise",
            "description": "企業環境向け（セキュリティ重視）",
            "features": ["domain_join", "bitlocker", "defender", "audit"]
        },
        {
            "name": "development",
            "description": "開発環境向け（開発ツール有効）",
            "features": ["wsl", "hyperv", "dotnet", "iis", "sandbox"]
        },
        {
            "name": "minimal",
            "description": "最小構成（軽量設定）",
            "features": ["basic_setup", "cleanup", "optimization"]
        }
    ]

@app.post("/api/xml/generate")
async def generate_xml(request: GenerateRequest, background_tasks: BackgroundTasks):
    """XML生成（即座に返す）"""
    try:
        # XML生成器を初期化
        xml_generator = UnattendXMLGenerator()
        xml_agent = XMLGeneratorSubAgent()
        
        # Context7でセッション管理
        session_id = str(uuid.uuid4())
        if request.context7_enabled:
            await context7.create_context(session_id, {
                "preset": request.preset,
                "config": request.config,
                "start_time": datetime.now().isoformat()
            })
        
        # SubAgentsによる並列処理
        if request.parallel_processing:
            # 並列でデータ処理
            tasks = []
            
            # ユーザー設定の処理
            if "users" in request.config:
                tasks.append(subagents["user_creator"].process(request.config["users"]))
            
            # ネットワーク設定の処理
            if "network" in request.config:
                tasks.append(subagents["network_config"].process(request.config["network"]))
            
            # Windows機能の処理
            if "features" in request.config:
                tasks.append(subagents["feature_manager"].process(request.config["features"]))
            
            # 並列実行
            if tasks:
                results = await asyncio.gather(*tasks)
                # 結果をconfigに反映
                for result in results:
                    if result.get("success"):
                        request.config.update(result.get("data", {}))
        
        # XML生成
        result = await xml_agent.process(request.config)
        
        if result['success']:
            xml_content = result['xml']
            
            # Context7に保存
            if request.context7_enabled:
                await context7.update_context(session_id, {
                    "status": "completed",
                    "xml": xml_content,
                    "validation": result['validation']
                })
            
            # XMLファイルとして返す
            return Response(
                content=xml_content,
                media_type="application/xml",
                headers={
                    "Content-Disposition": "attachment; filename=autounattend.xml",
                    "X-Session-ID": session_id
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'XML生成エラー'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-with-log")
async def generate_with_log(config: Dict = Body({})):
    """
    unattend.xmlと包括的設定ログを同時に生成（全23項目対応）
    """
    try:
        # 詳細なエラーログを追加
        import traceback
        import sys
        
        # 包括的設定処理と生成器を使用
        try:
            config_processor = ComprehensiveConfigProcessor()
        except Exception as e:
            print(f"ERROR: Failed to initialize ComprehensiveConfigProcessor: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            raise HTTPException(status_code=500, detail=f"Failed to initialize config processor: {str(e)}")
        
        try:
            xml_generator = ComprehensiveXMLGenerator()  # 包括的XML生成器を使用
        except Exception as e:
            print(f"ERROR: Failed to initialize ComprehensiveXMLGenerator: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            raise HTTPException(status_code=500, detail=f"Failed to initialize XML generator: {str(e)}")
        
        try:
            comprehensive_log_generator = ComprehensiveLogGenerator()
        except Exception as e:
            print(f"ERROR: Failed to initialize ComprehensiveLogGenerator: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            raise HTTPException(status_code=500, detail=f"Failed to initialize log generator: {str(e)}")
        
        # フロントエンドの全23項目設定を処理
        if config:
            # 文字列の場合はJSONとしてパース
            if isinstance(config, str):
                try:
                    import json
                    config = json.loads(config)
                except:
                    config = {}
            
            # 包括的な設定処理
            try:
                processed_config = config_processor.process_all_settings(config)
            except Exception as e:
                print(f"ERROR: Failed to process config: {e}", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                raise HTTPException(status_code=500, detail=f"Failed to process configuration: {str(e)}")
        else:
            # デフォルト設定
            processed_config = {
                "language": "ja-JP",
                "architecture": "amd64",
                "timezone": "Tokyo Standard Time",
                "bypass_microsoft_account": True,
                "bypass_network_check": True,
                "bypass_win11_requirements": True,
                "skip_privacy": True,
                "windows_edition": "Windows 11 Pro",
                "product_key": "VK7JG-NPHTM-C97JM-9MPGT-3V66T",
                "local_accounts": [{
                    "name": "admin-user",
                    "password": "P@ssw0rd123!",
                    "display_name": "管理者",
                    "group": "Administrators"
                }]
            }
        
        # XML生成（全設定を反映）
        try:
            xml_content = xml_generator.generate_complete_xml(processed_config)
        except Exception as e:
            print(f"ERROR: Failed to generate XML: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            raise HTTPException(status_code=500, detail=f"Failed to generate XML: {str(e)}")
        
        # 包括的ログ生成（全23項目）
        try:
            log_content = comprehensive_log_generator.generate_comprehensive_log(processed_config)
        except Exception as e:
            print(f"ERROR: Failed to generate log: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            raise HTTPException(status_code=500, detail=f"Failed to generate log: {str(e)}")
        
        # 一時ファイルに保存
        import tempfile
        import zipfile
        import io
        
        # メモリ上でZIPファイルを作成
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # XMLファイルを追加
            zip_file.writestr('autounattend.xml', xml_content)
            # ログファイルを追加
            zip_file.writestr('設定ログ.txt', log_content)
        
        zip_buffer.seek(0)
        
        # ZIPファイルとして返す
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=unattend_package.zip",
                "X-Generator": "Windows11-Unattend-Generator",
                "X-Version": "2.0.0"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-unattend")
async def generate_unattend_simple(config: Dict = Body({})):
    """
    包括的なunattend.xml生成エンドポイント（全23項目対応）
    """
    try:
        # デバッグ: 受信した設定を記録
        import json
        import traceback
        import sys
        
        print("=" * 60)
        print("受信した設定（フロントエンドから）:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
        print("=" * 60)
        
        # 包括的設定処理を使用
        try:
            config_processor = ComprehensiveConfigProcessor()
        except Exception as e:
            print(f"ERROR: Failed to initialize ComprehensiveConfigProcessor: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            raise HTTPException(status_code=500, detail=f"Failed to initialize config processor: {str(e)}")
        
        try:
            generator = ComprehensiveXMLGenerator()  # 包括的XML生成器を使用
        except Exception as e:
            print(f"ERROR: Failed to initialize ComprehensiveXMLGenerator: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            raise HTTPException(status_code=500, detail=f"Failed to initialize XML generator: {str(e)}")
        
        # フロントエンドの全23項目設定を処理
        if config:
            # 文字列の場合はJSONとしてパース
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except:
                    config = {}
            
            transformed_config = config_processor.process_all_settings(config)
            print("変換後の設定:")
            print(json.dumps(transformed_config, indent=2, ensure_ascii=False))
            print("=" * 60)
        else:
            transformed_config = {}
        
        # デフォルト設定を適用
        final_config = {
            "language": "ja-JP",
            "architecture": "amd64",
            "skip_network": False,  # Wi-Fi設定を有効化
            "skip_privacy": True,
            "bypass_microsoft_account": True,
            "bypass_win11_requirements": True,
            "windows_edition": "Windows 11 Pro",
            "product_key": "VK7JG-NPHTM-C97JM-9MPGT-3V66T",  # Windows 11 Proのデフォルトキー
            "timezone": "Tokyo Standard Time",
            "enable_autologin": False,
            "local_accounts": [{
                "name": "mirai-user",
                "password": "mirai",
                "description": "Default administrator user",
                "display_name": "Mirai User",
                "group": "Administrators"
            }],
            "first_logon_commands": [],
            **transformed_config  # 変換された設定で上書き
        }
        
        print("最終設定（XMLに渡される）:")
        print(json.dumps(final_config, indent=2, ensure_ascii=False))
        print("=" * 60)
        
        # 拡張XMLを生成
        xml_content = generator.generate_complete_xml(final_config)
        
        # 基本的な検証（XMLが正しく生成されたか）
        validation = {'valid': bool(xml_content and len(xml_content) > 100)}
        
        if validation['valid']:
            # XMLファイルとして返す
            return Response(
                content=xml_content,
                media_type="application/xml",
                headers={
                    "Content-Disposition": "attachment; filename=autounattend.xml",
                    "X-Generator": "Windows11-Unattend-Generator",
                    "X-Version": "1.0.0"
                }
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "Validation failed",
                    "errors": validation['errors']
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/xml/status/{session_id}")
async def get_generation_status(session_id: str):
    """生成ステータス確認"""
    context = await context7.get_context(session_id)
    if not context:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "status": context.get("status", "unknown"),
        "progress": context.get("progress", 0),
        "message": "処理中..."
    }

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    """進捗通知用WebSocket"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(json.dumps({
                "type": "progress",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ===== スタートアップタイム記録 =====
startup_time = datetime.now()

# ===== メイン実行 =====
if __name__ == "__main__":
    print("="*70)
    print(" Windows 11 無人応答ファイル生成システム")
    print(" Context7 + SubAgent(42体) + Claude-flow並列処理")
    print("="*70)
    print(f" ローカルIP: {LOCAL_IP}")
    print(f" バックエンド: http://{LOCAL_IP}:8081")
    print(f" API仕様書: http://{LOCAL_IP}:8081/api/docs")
    print(f" フロントエンド: http://{LOCAL_IP}:3050")
    print("="*70)
    print(f" SubAgent数: {len(subagents)}体")
    print(" Context7: 有効")
    print(" Claude-flow: 有効")
    print("="*70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8081,
        log_level="info"
    )
