import sys
import os
import asyncio
import grpc
from loguru import logger
from concurrent import futures

# Add project root to sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.shared.rpc import vector_pb2_grpc
from backend.vector_service.services.vector_service import VectorService
from backend.shared.telemetry.logging import setup_logging
from backend.shared.telemetry.tracing import setup_tracing
from backend.shared.telemetry.metrics import start_metrics_server
from backend.shared.core.discovery import registry, get_local_ip
from backend.vector_service.core.mq_consumer import RabbitMQConsumer
import signal


def serve():
    """
    Start the gRPC Vector Service.
    启动 gRPC 向量服务。
    """
    setup_logging()
    setup_tracing("vector-service")
    # Start metrics server on a separate port (e.g., 8004) or reuse logic if using an HTTP framework.
    # Since this is pure gRPC, we need a separate HTTP server for Prometheus scraping.
    # Let's use port 8004 for metrics (avoid conflict with 8001/8002/8003).
    # 启动 Prometheus 指标服务器 (端口 8004)
    start_metrics_server(8004)

    port = "50051"

    async def server_start():
        server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
        vector_pb2_grpc.add_VectorServiceServicer_to_server(VectorService(), server)
        server.add_insecure_port("[::]:" + port)

        logger.info(f"Vector Service starting on port {port}...")
        await server.start()

        # Start RabbitMQ Consumer
        # 启动 RabbitMQ 消费者，监听知识库文档上传事件
        consumer = RabbitMQConsumer()
        # We pass the current loop so the consumer thread can schedule tasks on it
        loop = asyncio.get_running_loop()
        consumer.run_in_thread(loop)

        # Register with Nacos
        # 注册服务到 Nacos
        ip = get_local_ip()
        registry.register_service("vector-service", ip, int(port))

        async def shutdown(sig, loop):
            """
            Graceful shutdown handler.
            优雅关闭处理：注销服务并停止 gRPC Server。
            """
            logger.info(f"Received signal {sig.name}...")
            registry.deregister_service("vector-service", ip, int(port))
            await server.stop(5)

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig, lambda s=sig: asyncio.create_task(shutdown(s, loop))
            )

        await server.wait_for_termination()

    asyncio.run(server_start())


if __name__ == "__main__":
    serve()
