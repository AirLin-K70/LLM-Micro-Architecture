from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    """
    验证明文密码是否与哈希密码匹配。
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    对密码进行哈希处理以便存储。
    """
    return pwd_context.hash(password)
