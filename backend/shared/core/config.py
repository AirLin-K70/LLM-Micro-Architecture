import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    全局配置类，用于管理整个微服务架构的配置项。
    使用 Pydantic 的 BaseSettings 自动从环境变量或 .env 文件加载配置。
    """
    # LLM Configuration (大语言模型配置)
    OPENAI_BASE_URL: str # 模型服务的基础 URL
    OPENAI_API_KEY: str # 模型服务的 API Key
    LLM_MODEL: str = "qwen-plus" # 默认使用的 LLM 模型名称
    EMBEDDING_MODEL: str = "text-embedding-v2" # 默认使用的 Embedding 模型名称

    # Database Configuration (MySQL 数据库配置)
    MYSQL_ROOT_PASSWORD: Optional[str] = None
    MYSQL_DATABASE: Optional[str] = None
    MYSQL_USER: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306

    # Redis Configuration (Redis 缓存配置)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # Nacos Configuration (服务注册与发现配置)
    NACOS_SERVER_ADDR: str = "localhost:8848" # Nacos 服务地址
    NACOS_NAMESPACE: str = "" # Nacos 命名空间ID，默认 public 为空字符串
    NACOS_USERNAME: Optional[str] = None
    NACOS_PASSWORD: Optional[str] = None

    # RabbitMQ Configuration (消息队列配置)
    RABBITMQ_DEFAULT_USER: str = "guest"
    RABBITMQ_DEFAULT_PASS: str = "guest"
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672

    # ChromaDB Configuration (向量数据库配置)
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # Telemetry (可观测性配置 - Jaeger/Prometheus)
    JAEGER_HOST: str = "localhost"
    JAEGER_PORT: int = 6831

    # Pydantic 配置
    model_config = SettingsConfigDict(
        # 指定 .env 文件路径 (从当前文件向上查找 deploy/.env)
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "deploy", ".env"),
        env_file_encoding="utf-8",
        extra="ignore" # 忽略多余的环境变量
    )

@lru_cache
def get_settings() -> Settings:
    """
    获取全局配置实例，使用 lru_cache 缓存结果，避免重复读取环境变量。
    """
    return Settings()

# Global settings instance (全局配置单例)
settings = get_settings()
