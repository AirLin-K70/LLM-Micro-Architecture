import sys
import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.rag_engine.api.routes import router
from backend.shared.telemetry.logging import setup_logging
from backend.shared.telemetry.tracing import setup_tracing, instrument_app
from backend.shared.telemetry.metrics import setup_metrics
from backend.shared.core.discovery import registry, get_local_ip


# Initialize observability
# 初始化可观测性组件
setup_logging()
setup_tracing("rag-engine")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    生命周期管理器：
    - 启动时：获取本机 IP 并注册到 Nacos
    - 关闭时：从 Nacos 注销服务
    """
    ip = get_local_ip()
    port = 8002
    registry.register_service("rag-engine", ip, port)

    yield

    registry.deregister_service("rag-engine", ip, port)


app = FastAPI(title="RAG Engine", lifespan=lifespan)

# 设置监控埋点
instrument_app(app)
setup_metrics(app)

app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
