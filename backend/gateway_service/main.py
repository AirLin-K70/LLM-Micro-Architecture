import sys
import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# 将项目根目录添加到系统路径，确保模块导入正常工作
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.gateway_service.routers.proxy import router
from backend.shared.telemetry.logging import setup_logging
from backend.shared.telemetry.tracing import setup_tracing, instrument_app
from backend.shared.telemetry.metrics import setup_metrics


# 初始化日志和链路追踪
setup_logging()
setup_tracing("gateway-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    用于处理应用启动和关闭时的生命周期事件。
    """
    yield


app = FastAPI(title="Gateway Service", lifespan=lifespan)

# 设置自动链路追踪和 Prometheus 监控指标
instrument_app(app)
setup_metrics(app)

# 注册路由模块
app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
