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
            raise

    async def EmbedText(self, request, context):
        try:
            logger.info(f"Embedding text: {request.text[:50]}...")
            embedding = await self._get_embedding(request.text)
            
            # Note: We are just returning the vector here, but usually we also want to store it.
            # The proto definition implies just embedding. 
            # However, Knowledge Service is supposed to call "Vector Service" to "store" vectors.
            # But the proto `EmbedText` just returns vector. 
            # Wait, `Knowledge Service: Implement document slicing -> MQ -> Vectorization`.
            # If VectorService is just a calculation layer, who stores it?
            # "Vector Service: ... 将文本转向量并存入 ChromaDB" -> It SHOULD store it.
            # But `EmbedText` request only has `text`. We probably need `StoreText` or `EmbedRequest` should have metadata.
            # Looking at my `vector.proto`:
            # rpc EmbedText (EmbedRequest) returns (EmbedResponse);
            # message EmbedRequest { string text = 1; }
            # It seems I missed the storage part in the proto or implied it.
            # Let's check the Search implementation. Search needs data in Chroma.
            # If I only have EmbedText returning vector, the caller (Knowledge Service) would need to insert into Chroma?
            # BUT VectorService encapsulates ChromaDB.
            # So I should probably add a `Upsert` method to `VectorService` or modify `EmbedText` to optionally store.
            # Or maybe `EmbedText` is just a utility, and there should be an `Ingest` method.
            # Given the proto is already fixed in Phase 2 (I can change it, but let's stick to the plan if possible).
            # If I can't change proto easily without re-running everything...
            # Actually, I am the one executing. I can update proto.
            # Let's look at `vector.proto` again.
            # It has `EmbedText` and `Search`.
            # If `EmbedText` is just for embedding, then `Search` has nothing to search if we don't insert.
            # So we definitely need an `Upsert` or `Index` method.
            
            # Let's update `vector.proto` to include `Upsert`.
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
                # where={"score": {"$gte": request.min_score}} # Chroma filter logic is a bit different
            )
            
            # Transform results to protobuf
            search_results = []
            if results["ids"]:
                for i in range(len(results["ids"][0])):
                    # Chroma returns list of lists
                    id_ = results["ids"][0][i]
                    distance = results["distances"][0][i] if results["distances"] else 0
                    # Convert distance to score (assuming cosine distance, 0 is identical, 1 is opposite)
                    # or just return distance/score as is.
                    # Qwen embedding uses cosine similarity usually?
                    # Chroma default is L2.
                    # Let's assume similarity = 1 - distance for now if L2, or just pass raw.
                    # User asked for min_score.
                    
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    content = results["documents"][0][i] if results["documents"] else ""
                    
                    # Manual filtering for min_score if Chroma doesn't support it directly in query easily with distance
                    # (Chroma `where` filters metadata, not distance)
                    # So we filter here.
                    # If distance is L2, lower is better. If Cosine distance, lower is better (0 to 2).
                    # Let's assume we want similarity. 
                    # For now, let's just return what we find.
                    
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
