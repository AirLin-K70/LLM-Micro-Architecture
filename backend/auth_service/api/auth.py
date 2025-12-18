from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from backend.auth_service.core.db import get_db
from backend.auth_service.core.security import get_password_hash, verify_password
from backend.auth_service.core.jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.shared.models.user import User
from backend.shared.models.wallet import Wallet
from datetime import timedelta
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str

@router.post("/register", response_model=Token)
async def register(user: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    注册新用户：
    1. 检查用户名是否存在
    2. 创建用户账号
    3. 创建初始钱包并赠送余额
    4. 生成 JWT Token
    """
    # Check if user exists
    # 检查用户是否已存在
    result = await db.execute(select(User).where(User.username == user.username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # 创建新用户
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, password_hash=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 为用户创建钱包并初始化余额
    new_wallet = Wallet(user_id=new_user.id, balance=100.0) # Initial balance
    db.add(new_wallet)
    await db.commit()

    # 生成访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": new_user.id, "role": new_user.role},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_id": new_user.id, "username": new_user.username}

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    用户登录：
    1. 验证用户名和密码
    2. 签发 JWT Token
    """
    result = await db.execute(select(User).where(User.username == user.username))
    db_user = result.scalars().first()
    
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username, "user_id": db_user.id, "role": db_user.role},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_id": db_user.id, "username": db_user.username}
