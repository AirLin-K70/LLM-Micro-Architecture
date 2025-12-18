import sys
import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.auth_service.api.auth import router
from backend.shared.telemetry.logging import setup_logging
from backend.shared.telemetry.tracing import setup_tracing, instrument_app
from backend.shared.telemetry.metrics import setup_metrics
from backend.auth_service.core.db import engine
from backend.shared.models.base import Base
from backend.shared.core.discovery import registry, get_local_ip


# 初始化日志和链路追踪
setup_logging()
setup_tracing("auth-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    生命周期管理器：
    - 启动时：初始化数据库表、注册服务到 Nacos
    - 关闭时：从 Nacos 注销服务、关闭数据库连接
    """
    # 初始化数据库表（开发环境便利性）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 注册服务到 Nacos
    ip = get_local_ip()
    port = 8003
    registry.register_service("auth-service", ip, port)

    yield

    # 注销服务
    registry.deregister_service("auth-service", ip, port)

    await engine.dispose()


app = FastAPI(title="Auth Service", lifespan=lifespan)

# 设置监控埋点
instrument_app(app)
setup_metrics(app)

app.include_router(router, prefix="/api/v1/auth")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
