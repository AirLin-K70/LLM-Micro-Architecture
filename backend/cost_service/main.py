import asyncio
import grpc
from concurrent import futures
import signal
import sys
from loguru import logger

from backend.shared.rpc import cost_pb2_grpc
from backend.cost_service.services.cost_service import CostService
from backend.shared.core.discovery import registry, get_local_ip
from backend.shared.telemetry.logging import setup_logging
from backend.shared.telemetry.metrics import start_metrics_server
from backend.cost_service.services.cost_service import (
    engine,
)  # Import engine from where it is defined
from backend.shared.models.base import Base
from backend.shared.models.user import User  # Import User for FK resolution
from backend.shared.models.wallet import Wallet  # Import Wallet to register in metadata

setup_logging()


async def serve():
    # 启动成本服务的指标服务器 (端口 8005)
    start_metrics_server(8005)

    # 初始化数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    cost_pb2_grpc.add_CostServiceServicer_to_server(CostService(), server)

    # 监听随机端口或固定端口。对于微服务，每个服务固定端口更便于开发。
    # 假设成本服务使用 50053（向量服务通常是 50051 或类似）。
    port = 50053
    server.add_insecure_port(f"[::]:{port}")

    await server.start()

    # 注册到 Nacos
    ip = get_local_ip()
    registry.register_service("cost-service", ip, port)
    logger.info(f"Cost Service started on port {port}")

    async def shutdown(sig, loop):
        logger.info(f"Received signal {sig.name}...")
        registry.deregister_service("cost-service", ip, port)
        await server.stop(5)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(shutdown(s, loop))
        )

    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    asyncio.run(serve())
