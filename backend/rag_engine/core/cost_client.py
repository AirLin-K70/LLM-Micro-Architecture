import grpc
from backend.shared.rpc import cost_pb2, cost_pb2_grpc
from backend.shared.core.discovery import registry
from loguru import logger
import random

class CostServiceClient:
    """
    成本服务 gRPC 客户端。
    处理服务发现和远程过程调用。
    """
    def __init__(self):
        self.service_name = "cost-service"

    def get_channel(self):
        """
        获取带有服务发现功能的 gRPC 通道。
        """
        target = "localhost:50053" # Default fallback
        try:
            instances = registry.get_service(self.service_name)
            hosts = instances.get('hosts', []) if isinstance(instances, dict) else instances
            healthy = [i for i in hosts if i.get('healthy', True) and i.get('enabled', True)]
            if healthy:
                inst = random.choice(healthy)
                target = f"{inst['ip']}:{inst['port']}"
            else:
                 logger.warning(f"No healthy {self.service_name} found in Nacos, using default.")
        except Exception as e:
            logger.error(f"Failed to discover {self.service_name}: {e}")
        
        return grpc.insecure_channel(target)

    def check_balance(self, user_id: str):
        """
        通过 gRPC 检查用户余额。
        """
        with self.get_channel() as channel:
            stub = cost_pb2_grpc.CostServiceStub(channel)
            request = cost_pb2.CheckBalanceRequest(user_id=user_id)
            return stub.CheckBalance(request)

    def deduct(self, user_id: str, token_count: int, model_name: str, transaction_id: str):
        """
        通过 gRPC 扣除费用。
        """
        with self.get_channel() as channel:
            stub = cost_pb2_grpc.CostServiceStub(channel)
            request = cost_pb2.DeductRequest(
                user_id=user_id,
                token_count=token_count,
                model_name=model_name,
                transaction_id=transaction_id
            )
            return stub.Deduct(request)

    def refund(self, user_id: str, token_count: int, model_name: str, transaction_id: str):
        """
        通过 gRPC 退还费用（回滚）。
        """
        with self.get_channel() as channel:
            stub = cost_pb2_grpc.CostServiceStub(channel)
            request = cost_pb2.DeductRequest(
                user_id=user_id,
                token_count=token_count,
                model_name=model_name,
                transaction_id=transaction_id
            )
            return stub.Refund(request)

cost_client = CostServiceClient()