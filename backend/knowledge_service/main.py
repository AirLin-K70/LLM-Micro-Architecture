import sys
import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.knowledge_service.api.routes import router
from backend.shared.telemetry.logging import setup_logging
from backend.shared.telemetry.tracing import setup_tracing, instrument_app
from backend.shared.telemetry.metrics import setup_metrics
from backend.knowledge_service.core.mq import producer
from backend.shared.core.discovery import registry, get_local_ip


# 初始化日志和链路追踪
setup_logging()
setup_tracing("knowledge-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    生命周期管理器：
    - 启动时：连接 RabbitMQ、注册服务到 Nacos
    - 关闭时：注销服务、关闭 RabbitMQ 连接
    """
    producer.connect()

    # 注册服务到 Nacos
    ip = get_local_ip()
    port = 8001
    registry.register_service("knowledge-service", ip, port)

    yield

    # 注销服务
    registry.deregister_service("knowledge-service", ip, port)

    if producer.connection:
        producer.connection.close()


app = FastAPI(title="Knowledge Service", lifespan=lifespan)

# 设置监控埋点
instrument_app(app)
setup_metrics(app)

app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
