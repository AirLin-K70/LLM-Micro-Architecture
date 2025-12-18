from sqlalchemy import String, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
import enum
from backend.shared.models.base import Base

class DocumentStatus(str, enum.Enum):
    """
    Document processing status enum.
    文档处理状态枚举。
    """
    PENDING = "pending"  # Waiting to be processed (等待处理)
    PROCESSING = "processing"  # Currently being processed (正在处理)
    INDEXED = "indexed"  # Successfully indexed in vector DB (已索引)
    FAILED = "failed"  # Processing failed (处理失败)

class Document(Base):
    """
    Document model.
    Stores document content and metadata.
    文档数据模型。
    存储文档内容和元数据。
    """
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING)
    
    # Stores the ID in ChromaDB (optional, or we use doc_id as metadata in chroma)
    # 存储 ChromaDB 中的 ID（可选，或者我们在 chroma 中使用 doc_id 作为元数据）
    vector_id: Mapped[str] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
