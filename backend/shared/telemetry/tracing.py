from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.grpc import (
    GrpcInstrumentorClient,
    GrpcInstrumentorServer,
)
from backend.shared.core.config import settings


def setup_tracing(service_name: str):
    """
    初始化 OpenTelemetry 链路追踪。
    配置 Jaeger 导出器以及 HTTPX 和 gRPC 的自动埋点。
    """
    resource = Resource.create(attributes={"service.name": service_name})

    provider = TracerProvider(resource=resource)

    # 配置 OTLP 导出器 (指向 Jaeger)
    endpoint = f"http://{settings.JAEGER_HOST}:4317"

    otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)

    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)

    # 自动埋点：全局 instrument HTTPX 客户端和 gRPC
    HTTPXClientInstrumentor().instrument()
    GrpcInstrumentorClient().instrument()
    GrpcInstrumentorServer().instrument()

    return trace.get_tracer(service_name)


def instrument_app(app):
    """
    为 FastAPI 应用启用自动链路追踪。
    """
    FastAPIInstrumentor.instrument_app(app)
