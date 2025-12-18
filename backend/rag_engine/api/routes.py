from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.shared.core.llm_factory import get_llm_client
from backend.shared.core.config import settings
from backend.rag_engine.core.vector_client import vector_client
from backend.rag_engine.core.cost_client import cost_client
from loguru import logger
import uuid
import json
from redis.asyncio import Redis

router = APIRouter()
redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)

class ChatRequest(BaseModel):
    query: str
    user_id: str


class ChatResponse(BaseModel):
    answer: str
    sources: list


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    RAG 对话接口。
    编排 RAG 流程：费用检查 -> 知识检索 -> LLM 生成。
    使用 Saga 模式（简化版）处理分布式事务。
    """
    logger.info(f"Received chat request from {request.user_id}: {request.query}")

    # 第一步：检查余额并预扣费（乐观锁策略）
    transaction_id = str(uuid.uuid4())
    estimated_tokens = 100  # Simplified token estimation (简化估算)

    try:
        # 调用 Cost Service 进行扣费
        deduct_res = cost_client.deduct(
            request.user_id, estimated_tokens, settings.LLM_MODEL, transaction_id
        )
        if not deduct_res.success:
            logger.warning(
                f"Deduction failed for {request.user_id}: {deduct_res.message}"
            )
            raise HTTPException(
                status_code=402, detail=f"Insufficient funds: {deduct_res.message}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cost service failed: {e}")
        raise HTTPException(status_code=500, detail="Cost service unavailable")

    # 第二步：从向量服务检索上下文
    try:
        search_response = vector_client.search(request.query)
        context_texts = []
        sources = []
        for result in search_response.results:
            context_texts.append(result.content)
            sources.append(result.metadata.get("source", "unknown"))

        context_str = "\n\n".join(context_texts)
        logger.info(f"Retrieved {len(context_texts)} chunks")
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")

        # 补偿事务：如果检索失败，回滚扣费（退款）
        cost_client.refund(
            request.user_id, estimated_tokens, settings.LLM_MODEL, transaction_id
        )
        raise HTTPException(status_code=500, detail="Retrieval failed")

    # 第三步：构建 Prompt 并调用大模型 (Qwen)
    try:
        PROMPT_TEMPLATE = """你是一个专业的企业级智能知识库助手。你的任务是基于提供的【上下文信息】来回答用户的提问。 
 
     ### 核心原则 
     1. **严格基于上下文**：你的所有回答必须完全依据下方的【上下文信息】。严禁利用你原本的训练数据进行编造或发散。 
     2. **诚实兜底**：如果【上下文信息】中没有包含回答用户问题所需的知识，请直接回答：“抱歉，当前的知识库中没有关于该问题的记录，请联系人工客服。” 不要尝试编造答案。 
     3. **格式规范**： 
        - 使用清晰的 Markdown 格式。 
        - 如果信息包含步骤，请使用编号列表 (1. 2. 3.)。 
        - 如果信息包含多个要点，请使用无序列表 (- )。 
     4. **语言风格**：保持专业、客观、简洁，语气亲切。 
 
     ### 上下文信息 (Context) 
     {context} 
     """
        system_content = PROMPT_TEMPLATE.replace("{context}", context_str)
        
        # 从 Redis 获取历史对话记录
        history_key = f"chat_history:{request.user_id}"
        history_json = await redis_client.get(history_key)
        history = json.loads(history_json) if history_json else []
        
        # 构建消息列表
        messages = [{"role": "system", "content": system_content}]
        messages.extend(history)
        
        messages.append({"role": "user", "content": request.query})

        client = get_llm_client()
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.7,
            stream=False,
        )
        answer = response.choices[0].message.content
        
        history.append({"role": "user", "content": request.query})
        history.append({"role": "assistant", "content": answer})
        
        await redis_client.set(history_key, json.dumps(history), ex=3600)

        return ChatResponse(answer=answer, sources=sources)

    except Exception as e:
        logger.error(f"LLM call failed: {e}")

        # Fallback for Arrearage (Overdue Payment) or other API errors during LLM call
        # 针对大模型欠费或其他调用错误的降级处理
        if "Arrearage" in str(e) or "Access denied" in str(e) or "400" in str(e):
             mock_answer = "【系统提示】由于底层大模型服务（阿里云 DashScope）账户欠费或访问被拒绝，无法生成智能回答。\n\n这是一条自动生成的测试响应，用于验证系统链路畅通。请联系管理员检查 API 额度。"
             
             # Still record history for testing flow
             history.append({"role": "user", "content": request.query})
             history.append({"role": "assistant", "content": mock_answer})
             await redis_client.set(history_key, json.dumps(history), ex=3600)
             
             return ChatResponse(answer=mock_answer, sources=sources)

        cost_client.refund(
            request.user_id, estimated_tokens, settings.LLM_MODEL, transaction_id
        )
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")
