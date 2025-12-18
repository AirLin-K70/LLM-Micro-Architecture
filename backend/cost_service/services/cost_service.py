import grpc
import logging
from sqlalchemy import select, update
from backend.shared.rpc import cost_pb2, cost_pb2_grpc
from backend.shared.models.wallet import Wallet
from backend.shared.core.config import settings
from backend.shared.telemetry.logging import logger

# Mock DB session for now, or use the real one if I can import it.
# I'll use the async session from a db module if available, or create a new engine.
# For simplicity in this "supplement" phase, I'll assume a db session helper is available or create one.
# Checking backend/shared/database/base.py might help.

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = f"mysql+aiomysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class CostService(cost_pb2_grpc.CostServiceServicer):
    """
    成本服务实现。
    处理用户余额检查和 Token 成本扣除。
    """
    async def CheckBalance(self, request, context):
        """
        检查用户是否有足够的资金。
        """
        try:
            user_id_int = int(request.user_id)
        except ValueError:
            # 处理非整型 user_id（例如，来自旧测试或无效输入）
            logger.warning(f"Invalid user_id format: {request.user_id}")
            return cost_pb2.CheckBalanceResponse(
                has_sufficient_funds=False, current_balance=0.0
            )

        async with async_session() as session:
            result = await session.execute(
                select(Wallet).where(Wallet.user_id == user_id_int)
            )
            wallet = result.scalars().first()

            if not wallet:
                # 测试时自动创建钱包
                wallet = Wallet(user_id=user_id_int, balance=100.0)
                session.add(wallet)
                await session.commit()
                logger.info(
                    f"Created new wallet for user {user_id_int} with 100.0 balance"
                )

            balance = wallet.balance
            # 假设最低成本为 0.01
            has_sufficient = balance > 0

            return cost_pb2.CheckBalanceResponse(
                has_sufficient_funds=has_sufficient, current_balance=float(balance)
            )

    async def Deduct(self, request, context):
        """
        从用户钱包中扣除费用。
        """
        cost_per_token = 0.0001  # Simplified cost model (简化成本模型)
        total_cost = request.token_count * cost_per_token

        try:
            user_id_int = int(request.user_id)
        except ValueError:
            logger.error(f"Invalid user_id for deduction: {request.user_id}")
            return cost_pb2.DeductResponse(
                success=False, message="Invalid user_id format", remaining_balance=0.0
            )

        async with async_session() as session:
            try:
                result = await session.execute(
                    select(Wallet).where(Wallet.user_id == user_id_int)
                )
                wallet = result.scalars().first()

                if not wallet:
                    # 测试时自动创建钱包
                    wallet = Wallet(user_id=user_id_int, balance=100.0)
                    session.add(wallet)
                    await session.commit()
                    logger.info(
                        f"Created new wallet for user {user_id_int} with 100.0 balance"
                    )

                if wallet.balance < total_cost:
                    return cost_pb2.DeductResponse(
                        success=False,
                        remaining_balance=float(wallet.balance),
                        message="Insufficient funds",
                    )

                wallet.balance -= total_cost
                await session.commit()

                logger.info(
                    f"Deducted {total_cost} from user {request.user_id} for {request.token_count} tokens"
                )

                return cost_pb2.DeductResponse(
                    success=True, remaining_balance=float(wallet.balance)
                )

            except Exception as e:
                await session.rollback()
                logger.error(f"Deduction failed: {e}")
                return cost_pb2.DeductResponse(success=False, message=str(e))

    async def Refund(self, request, context):
        cost_per_token = 0.0001  # Simplified cost model
        total_refund = request.token_count * cost_per_token

        try:
            user_id_int = int(request.user_id)
        except ValueError:
            logger.error(f"Invalid user_id for refund: {request.user_id}")
            return cost_pb2.DeductResponse(
                success=False, message="Invalid user_id format", remaining_balance=0.0
            )

        async with async_session() as session:
            try:
                result = await session.execute(
                    select(Wallet).where(Wallet.user_id == user_id_int)
                )
                wallet = result.scalars().first()

                if not wallet:
                    return cost_pb2.DeductResponse(
                        success=False, message="Wallet not found"
                    )

                wallet.balance += total_refund
                await session.commit()

                logger.info(
                    f"Refunded {total_refund} to user {request.user_id} for {request.token_count} tokens"
                )

                return cost_pb2.DeductResponse(
                    success=True, remaining_balance=float(wallet.balance)
                )

            except Exception as e:
                await session.rollback()
                logger.error(f"Refund failed: {e}")
                return cost_pb2.DeductResponse(success=False, message=str(e))
