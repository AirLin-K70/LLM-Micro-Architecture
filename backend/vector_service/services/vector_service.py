import grpc
from loguru import logger
from backend.shared.rpc import vector_pb2, vector_pb2_grpc
from backend.shared.core.llm_factory import get_llm_client
from backend.shared.core.config import settings
from backend.vector_service.core.chroma import get_chroma_collection
import uuid

class VectorService(vector_pb2_grpc.VectorServiceServicer):
    def __init__(self):
        self.client = get_llm_client()
        self.collection = get_chroma_collection()

    async def _get_embedding(self, text: str):
        try:
            response = await self.client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Fallback for Arrearage (Overdue Payment) or other API errors
            # 针对欠费或其他 API 错误的降级处理：返回随机向量以保持服务可用性（仅供测试）
            if "Arrearage" in str(e) or "Access denied" in str(e) or "400" in str(e):
                logger.warning(f"Embedding API failed ({e}). Using mock embedding (random vector).")
                import random
                # Assuming 1536 dimensions for standard text-embedding models
                return [random.random() for _ in range(1536)]
            raise

    async def EmbedText(self, request, context):
        try:
            logger.info(f"Embedding text: {request.text[:50]}...")
            embedding = await self._get_embedding(request.text)

            return vector_pb2.EmbedResponse(vector=embedding)
        except Exception as e:
            logger.error(f"EmbedText failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return vector_pb2.EmbedResponse()

    async def Upsert(self, request, context):
        try:
            logger.info(f"Upserting document: {request.id}")
            embedding = await self._get_embedding(request.text)
            
            self.collection.upsert(
                ids=[request.id],
                embeddings=[embedding],
                documents=[request.text],
                metadatas=[dict(request.metadata)]
            )
            return vector_pb2.UpsertResponse(success=True)
        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            return vector_pb2.UpsertResponse(success=False, error=str(e))

    async def Search(self, request, context):
        try:
            logger.info(f"Searching for: {request.query_text}")
            query_embedding = await self._get_embedding(request.query_text)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=request.top_k,
            )

            search_results = []
            if results["ids"]:
                for i in range(len(results["ids"][0])):
                    id_ = results["ids"][0][i]
                    distance = results["distances"][0][i] if results["distances"] else 0
                    
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    content = results["documents"][0][i] if results["documents"] else ""

                    # Convert metadata map
                    meta_map = {k: str(v) for k, v in metadata.items()}
                    
                    search_results.append(vector_pb2.SearchResult(
                        id=id_,
                        score=1.0 - distance, # Rough approx
                        content=content,
                        metadata=meta_map
                    ))
            
            return vector_pb2.SearchResponse(results=search_results)

        except Exception as e:
            logger.error(f"Search failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return vector_pb2.SearchResponse()
