from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI
from prometheus_client import start_http_server

def setup_metrics(app: FastAPI):
    """
    为 FastAPI 应用初始化 Prometheus 监控指标。
    """
    Instrumentator().instrument(app).expose(app)

def start_metrics_server(port: int):
    """
    为 gRPC 服务或非 FastAPI 服务启动独立的 Prometheus 指标 HTTP 服务器。
    """
    start_http_server(port)
