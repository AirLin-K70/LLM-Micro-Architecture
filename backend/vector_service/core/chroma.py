import chromadb
from chromadb.config import Settings
from backend.shared.core.config import settings

class ChromaClient:
    """
    ChromaDB 客户端单例封装。
    """
    _instance = None
    
    @classmethod
    def get_client(cls):
        """
        获取或创建全局 ChromaDB HttpClient 实例。
        """
        if cls._instance is None:
            # Connect to ChromaDB server
            # 连接到 ChromaDB 服务器
            cls._instance = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT
            )
        return cls._instance

    @classmethod
    def get_collection(cls, name: str = "knowledge_base"):
        """
        获取指定名称的集合，如果不存在则创建。
        """
        client = cls.get_client()
        return client.get_or_create_collection(name=name)

def get_chroma_collection(name: str = "knowledge_base"):
    """
    获取默认知识库集合的辅助函数。
    """
    return ChromaClient.get_collection(name)
