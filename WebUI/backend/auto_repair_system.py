"""
自動エラー検知・修復システム
最大20回のリトライループと自動修復機能を実装
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from enum import Enum

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_repair.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """エラータイプの定義"""
    CONNECTION_ERROR = "接続エラー"
    TIMEOUT_ERROR = "タイムアウト"
    VALIDATION_ERROR = "検証エラー"
    PROCESSING_ERROR = "処理エラー"
    RESOURCE_ERROR = "リソースエラー"
    UNKNOWN_ERROR = "不明なエラー"

class RepairStrategy(Enum):
    """修復戦略の定義"""
    RETRY = "リトライ"
    RESTART = "再起動"
    RESET = "リセット"
    RECONNECT = "再接続"
    CLEANUP = "クリーンアップ"
    FALLBACK = "フォールバック"

class AutoRepairSystem:
    """自動エラー検知・修復システム"""
    
    def __init__(self, max_retries: int = 20):
        self.max_retries = max_retries
        self.retry_count = 0
        self.error_history: List[Dict[str, Any]] = []
        self.repair_strategies: Dict[ErrorType, List[RepairStrategy]] = {
            ErrorType.CONNECTION_ERROR: [RepairStrategy.RECONNECT, RepairStrategy.RETRY],
            ErrorType.TIMEOUT_ERROR: [RepairStrategy.RETRY, RepairStrategy.RESTART],
            ErrorType.VALIDATION_ERROR: [RepairStrategy.CLEANUP, RepairStrategy.RESET],
            ErrorType.PROCESSING_ERROR: [RepairStrategy.RETRY, RepairStrategy.FALLBACK],
            ErrorType.RESOURCE_ERROR: [RepairStrategy.CLEANUP, RepairStrategy.RESTART],
            ErrorType.UNKNOWN_ERROR: [RepairStrategy.RETRY, RepairStrategy.RESET],
        }
        self.is_repairing = False
        
    def classify_error(self, error: Exception) -> ErrorType:
        """エラーを分類"""
        error_msg = str(error).lower()
        
        if "connection" in error_msg or "network" in error_msg:
            return ErrorType.CONNECTION_ERROR
        elif "timeout" in error_msg:
            return ErrorType.TIMEOUT_ERROR
        elif "validation" in error_msg or "invalid" in error_msg:
            return ErrorType.VALIDATION_ERROR
        elif "process" in error_msg or "execution" in error_msg:
            return ErrorType.PROCESSING_ERROR
        elif "resource" in error_msg or "memory" in error_msg:
            return ErrorType.RESOURCE_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    async def execute_repair_strategy(
        self, 
        strategy: RepairStrategy, 
        context: Dict[str, Any]
    ) -> bool:
        """修復戦略を実行"""
        logger.info(f"修復戦略を実行: {strategy.value}")
        
        try:
            if strategy == RepairStrategy.RETRY:
                # 単純なリトライ（待機時間付き）
                await asyncio.sleep(2.0)
                return True
                
            elif strategy == RepairStrategy.RESTART:
                # サービスの再起動
                await self.restart_service(context.get('service_name'))
                return True
                
            elif strategy == RepairStrategy.RESET:
                # 状態のリセット
                await self.reset_state(context)
                return True
                
            elif strategy == RepairStrategy.RECONNECT:
                # 再接続
                await self.reconnect(context.get('connection_info'))
                return True
                
            elif strategy == RepairStrategy.CLEANUP:
                # リソースのクリーンアップ
                await self.cleanup_resources(context)
                return True
                
            elif strategy == RepairStrategy.FALLBACK:
                # フォールバック処理
                await self.execute_fallback(context)
                return True
                
        except Exception as e:
            logger.error(f"修復戦略の実行に失敗: {e}")
            return False
        
        return False
    
    async def restart_service(self, service_name: Optional[str]) -> None:
        """サービスを再起動"""
        if not service_name:
            return
            
        logger.info(f"サービス {service_name} を再起動中...")
        # ここに実際の再起動ロジックを実装
        await asyncio.sleep(3.0)
        logger.info(f"サービス {service_name} の再起動完了")
    
    async def reset_state(self, context: Dict[str, Any]) -> None:
        """状態をリセット"""
        logger.info("状態をリセット中...")
        # ここに実際のリセットロジックを実装
        context.clear()
        await asyncio.sleep(1.0)
        logger.info("状態のリセット完了")
    
    async def reconnect(self, connection_info: Optional[Dict[str, Any]]) -> None:
        """再接続"""
        if not connection_info:
            return
            
        logger.info("再接続を試行中...")
        # ここに実際の再接続ロジックを実装
        await asyncio.sleep(2.0)
        logger.info("再接続完了")
    
    async def cleanup_resources(self, context: Dict[str, Any]) -> None:
        """リソースをクリーンアップ"""
        logger.info("リソースをクリーンアップ中...")
        # ここに実際のクリーンアップロジックを実装
        await asyncio.sleep(1.0)
        logger.info("クリーンアップ完了")
    
    async def execute_fallback(self, context: Dict[str, Any]) -> None:
        """フォールバック処理を実行"""
        logger.info("フォールバック処理を実行中...")
        # ここに実際のフォールバックロジックを実装
        context['fallback_mode'] = True
        await asyncio.sleep(1.0)
        logger.info("フォールバック処理完了")
    
    async def execute_with_auto_repair(
        self,
        task_name: str,
        task_func: Callable,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """自動修復付きでタスクを実行"""
        
        if context is None:
            context = {}
            
        self.retry_count = 0
        start_time = time.time()
        
        while self.retry_count < self.max_retries:
            try:
                logger.info(f"タスク '{task_name}' を実行中 (試行 {self.retry_count + 1}/{self.max_retries})")
                
                # タスクを実行
                result = await task_func()
                
                # 成功した場合
                execution_time = time.time() - start_time
                logger.info(f"タスク '{task_name}' が成功しました (実行時間: {execution_time:.2f}秒)")
                
                return {
                    'success': True,
                    'result': result,
                    'retry_count': self.retry_count,
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as error:
                self.retry_count += 1
                
                # エラーを記録
                error_info = {
                    'error': str(error),
                    'type': self.classify_error(error).value,
                    'retry_count': self.retry_count,
                    'timestamp': datetime.now().isoformat()
                }
                self.error_history.append(error_info)
                
                logger.error(f"エラーが発生しました: {error}")
                
                # 最大リトライ回数に達した場合
                if self.retry_count >= self.max_retries:
                    logger.error(f"最大リトライ回数 ({self.max_retries}) に達しました")
                    
                    # 通知を送信
                    await self.send_notification(task_name, error_info)
                    
                    return {
                        'success': False,
                        'error': str(error),
                        'error_type': self.classify_error(error).value,
                        'retry_count': self.retry_count,
                        'execution_time': time.time() - start_time,
                        'timestamp': datetime.now().isoformat(),
                        'error_history': self.error_history
                    }
                
                # 修復を試行
                if not self.is_repairing:
                    self.is_repairing = True
                    error_type = self.classify_error(error)
                    strategies = self.repair_strategies.get(error_type, [RepairStrategy.RETRY])
                    
                    for strategy in strategies:
                        logger.info(f"修復戦略 '{strategy.value}' を試行中...")
                        success = await self.execute_repair_strategy(strategy, context)
                        
                        if success:
                            logger.info(f"修復戦略 '{strategy.value}' が成功しました")
                            break
                    
                    self.is_repairing = False
                
                # 次のリトライまで待機
                wait_time = min(2 ** self.retry_count, 30)  # 指数バックオフ（最大30秒）
                logger.info(f"次のリトライまで {wait_time} 秒待機します...")
                await asyncio.sleep(wait_time)
        
        # ここには到達しないはずだが、念のため
        return {
            'success': False,
            'error': 'Unknown error',
            'retry_count': self.retry_count,
            'timestamp': datetime.now().isoformat()
        }
    
    async def send_notification(self, task_name: str, error_info: Dict[str, Any]) -> None:
        """エラー通知を送信"""
        logger.critical(f"""
        =====================================
        自動修復失敗通知
        =====================================
        タスク名: {task_name}
        エラー: {error_info['error']}
        エラータイプ: {error_info['type']}
        リトライ回数: {error_info['retry_count']}
        タイムスタンプ: {error_info['timestamp']}
        =====================================
        """)
        
        # ここに実際の通知ロジックを実装（メール、Slack、など）
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        if not self.error_history:
            return {
                'total_errors': 0,
                'error_types': {},
                'average_retry_count': 0
            }
        
        error_types = {}
        total_retries = 0
        
        for error in self.error_history:
            error_type = error.get('type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
            total_retries += error.get('retry_count', 0)
        
        return {
            'total_errors': len(self.error_history),
            'error_types': error_types,
            'average_retry_count': total_retries / len(self.error_history) if self.error_history else 0,
            'last_error': self.error_history[-1] if self.error_history else None
        }
    
    def reset(self) -> None:
        """システムをリセット"""
        self.retry_count = 0
        self.error_history.clear()
        self.is_repairing = False
        logger.info("自動修復システムがリセットされました")

# グローバルインスタンス
auto_repair = AutoRepairSystem(max_retries=20)

# デコレーター版の実装
def with_auto_repair(task_name: str):
    """自動修復デコレーター"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async def task():
                return await func(*args, **kwargs)
            
            return await auto_repair.execute_with_auto_repair(
                task_name=task_name,
                task_func=task,
                context={'args': args, 'kwargs': kwargs}
            )
        
        return wrapper
    return decorator

# 使用例
@with_auto_repair("サンプルタスク")
async def sample_task():
    """サンプルタスク"""
    import random
    
    # 50%の確率でエラーを発生させる（テスト用）
    if random.random() < 0.5:
        raise ConnectionError("ネットワーク接続エラー")
    
    return {"status": "success", "data": "処理完了"}

if __name__ == "__main__":
    # テスト実行
    async def main():
        result = await sample_task()
        print(f"結果: {result}")
        
        # 統計情報を表示
        stats = auto_repair.get_statistics()
        print(f"統計: {stats}")
    
    asyncio.run(main())