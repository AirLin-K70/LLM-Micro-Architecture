from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from backend.auth_service.core.jwt import SECRET_KEY, ALGORITHM

security = HTTPBearer()


async def verify_jwt(request: Request):
    if "Authorization" not in request.headers:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")

    auth_header = request.headers["Authorization"]
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid Authentication Scheme")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except (ValueError, JWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Dependency wrapper
async def get_current_user(payload: dict = Depends(verify_jwt)):
    return payload
