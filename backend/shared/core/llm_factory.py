from openai import AsyncOpenAI
from backend.shared.core.config import settings


class LLMFactory:
    """
    LLM 客户端工厂类，支持单例模式以复用连接。
    """

    _instance = None

    @classmethod
    def get_client(cls) -> AsyncOpenAI:
        """
        获取或创建全局 AsyncOpenAI 客户端实例。
        """
        if cls._instance is None:
            # 使用兼容 OpenAI 协议的配置初始化客户端（支持通义千问、vLLM 等）
            cls._instance = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
            )
        return cls._instance


def get_llm_client() -> AsyncOpenAI:
    """
    获取 LLM 客户端的辅助函数。
    """
    return LLMFactory.get_client()
