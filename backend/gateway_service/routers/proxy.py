import httpx
import random
import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from backend.gateway_service.core.auth_middleware import verify_jwt
from backend.shared.core.discovery import registry

logger = logging.getLogger(__name__)

router = APIRouter()


def get_service_url(service_name: str) -> str:
    """
    从 Nacos 注册中心解析服务地址，如果失败则降级到默认配置。
    """
    # Try Nacos first (优先尝试从 Nacos 获取)
    try:
        instances = registry.get_service(service_name)

        hosts = instances.get("hosts", []) if isinstance(instances, dict) else instances

        # 过滤出健康且已启用的实例
        healthy_instances = [
            ins
            for ins in hosts
            if (ins.get("healthy", True) and ins.get("enabled", True))
        ]

        if healthy_instances:
            # 负载均衡策略：随机选择
            instance = random.choice(healthy_instances)
            return f"http://{instance['ip']}:{instance['port']}"

    except Exception as e:
        logger.error(f"Error resolving {service_name}: {e}")

    # Fallback to localhost defaults (降级到本地默认端口)
    defaults = {
        "auth-service": ("localhost", 8003),
        "knowledge-service": ("localhost", 8001),
        "rag-engine": ("localhost", 8002),
    }

    if service_name in defaults:
        host, port = defaults[service_name]
        return f"http://{host}:{port}"

    raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")


# 认证路由转发
@router.post("/auth/register")
async def proxy_register(request: Request):
    """
    转发注册请求到认证服务。
    """
    url = get_service_url("auth-service")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            body = await request.json()
            response = await client.post(f"{url}/api/v1/auth/register", json=body)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/login")
async def proxy_login(request: Request):
    """
    转发登录请求到认证服务。
    """
    url = get_service_url("auth-service")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            body = await request.json()
            response = await client.post(f"{url}/api/v1/auth/login", json=body)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# 知识库路由转发（需鉴权）
@router.post("/knowledge/upload")
async def proxy_upload(request: Request, user: dict = Depends(verify_jwt)):
    """
    转发文件上传请求到知识库服务。
    """
    url = get_service_url("knowledge-service")

    # 获取原始请求体以支持文件上传转发
    body = await request.body()
    headers = dict(request.headers)
    # 移除 host 头，避免转发时混淆
    headers.pop("host", None)
    headers.pop("content-length", None)  # Let httpx handle this

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # 直接透传原始请求体和 Content-Type 头
            response = await client.post(
                f"{url}/api/v1/upload", content=body, headers=headers
            )
            try:
                return response.json()
            except Exception:
                logger.error(
                    f"Proxy upload failed. Status: {response.status_code}, Body: {response.text}"
                )
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# RAG Routes (Protected)
@router.post("/chat")
async def proxy_chat(request: Request, user: dict = Depends(verify_jwt)):
    url = get_service_url("rag-engine")
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            body = await request.json()

            body["user_id"] = str(user["user_id"])

            response = await client.post(f"{url}/api/v1/chat", json=body)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
