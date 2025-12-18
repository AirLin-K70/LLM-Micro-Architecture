import grpc
from backend.shared.rpc import vector_pb2, vector_pb2_grpc
from backend.shared.core.discovery import registry
from loguru import logger
import random


class VectorServiceClient:
    """
    向量服务 gRPC 客户端。
    处理向量相似度搜索请求。
    """
    def __init__(self):
        self.service_name = "vector-service"

    def get_channel(self):
        """
        获取带有服务发现功能的 gRPC 通道。
        """
        target = "localhost:50051"  # Default fallback
        try:
            instances = registry.get_service(self.service_name)
            hosts = (
                instances.get("hosts", []) if isinstance(instances, dict) else instances
            )
            healthy = [
                i for i in hosts if i.get("healthy", True) and i.get("enabled", True)
            ]
            if healthy:
                inst = random.choice(healthy)
                target = f"{inst['ip']}:{inst['port']}"
            else:
                logger.warning(
                    f"No healthy {self.service_name} found in Nacos, using default."
                )
        except Exception as e:
            logger.error(f"Failed to discover {self.service_name}: {e}")

        return grpc.insecure_channel(target)

    def search(self, query: str, top_k: int = 3, min_score: float = 0.0):
        """
        通过 gRPC 执行向量搜索。
        """
        with self.get_channel() as channel:
            stub = vector_pb2_grpc.VectorServiceStub(channel)
            request = vector_pb2.SearchRequest(
                query_text=query, top_k=top_k, min_score=min_score
            )
            return stub.Search(request)


vector_client = VectorServiceClient()
