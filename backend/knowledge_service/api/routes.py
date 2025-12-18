from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.knowledge_service.core.mq import producer
from loguru import logger
import uuid
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfReader

router = APIRouter()

# 创建线程池以处理阻塞型操作（如 PDF 解析）
executor = ThreadPoolExecutor(max_workers=4)


def parse_pdf(content: bytes) -> str:
    """
    从 PDF 文件内容中提取文本。
    """
    try:
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        return ""


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    上传并处理文档 (PDF/TXT)：
    1. 解析文档内容
    2. 按段落切分文本
    3. 将切片发送到消息队列以进行向量化
    """
    text = ""
    if file.filename.endswith(".pdf"):
        content = await file.read()
        # 在独立线程中运行 CPU 密集型的 PDF 解析任务
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(executor, parse_pdf, content)

        if not text:
            raise HTTPException(
                status_code=400, detail="Failed to extract text from PDF or empty file"
            )

    elif file.filename.endswith(".txt"):
        content = await file.read()
        text = content.decode("utf-8")
    else:
        raise HTTPException(
            status_code=400, detail="Only .txt and .pdf files are supported"
        )

    # 简单的按段落切分策略
    chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]

    doc_id = str(uuid.uuid4())

    for i, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}_{i}"
        message = {
            "id": chunk_id,
            "text": chunk,
            "metadata": {"source": file.filename, "doc_id": doc_id, "chunk_index": i},
        }
        producer.publish(message)

    return {
        "message": "Document processed and queued for embedding",
        "doc_id": doc_id,
        "chunks": len(chunks),
    }
