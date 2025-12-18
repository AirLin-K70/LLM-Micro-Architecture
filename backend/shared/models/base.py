from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import MappedAsDataclass

class Base(DeclarativeBase):
    """
    SQLAlchemy Declarative Base.
    All models should inherit from this class.
    SQLAlchemy 声明性基类。
    所有模型都应继承此类。
    """
    pass
