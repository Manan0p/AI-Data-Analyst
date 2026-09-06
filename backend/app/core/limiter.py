from fastapi import Request
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def get_user_or_ip_identifier(request: Request) -> str:
    """Identify client by authenticated user ID from JWT bearer token, falling back to remote IP."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except JWTError:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=get_user_or_ip_identifier)
