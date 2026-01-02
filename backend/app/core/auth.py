import jwt
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from functools import wraps
from .config import settings

logger = logging.getLogger(__name__)

SUPABASE_JWT_SECRET = None

def get_jwt_secret() -> str:
    global SUPABASE_JWT_SECRET
    if SUPABASE_JWT_SECRET is None:
        if settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                decoded = jwt.decode(
                    settings.SUPABASE_SERVICE_ROLE_KEY,
                    options={"verify_signature": False}
                )
                ref = decoded.get("ref", "")
                SUPABASE_JWT_SECRET = f"super-secret-jwt-token-with-at-least-32-characters-long"
            except Exception:
                pass
        SUPABASE_JWT_SECRET = SUPABASE_JWT_SECRET or "your-supabase-jwt-secret"
    return SUPABASE_JWT_SECRET


async def verify_supabase_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        
        if payload.get("iss") and "supabase" in payload.get("iss", ""):
            user_id = payload.get("sub")
            email = payload.get("email")
            role = payload.get("role", "authenticated")
            
            if user_id:
                return {
                    "user_id": user_id,
                    "email": email,
                    "role": role,
                    "exp": payload.get("exp"),
                    "iat": payload.get("iat"),
                }
        
        return None
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    return await verify_supabase_token(auth_header)


async def require_auth(request: Request) -> Dict[str, Any]:
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    return user


def auth_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        if not request:
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
        
        if request:
            user = await get_current_user(request)
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            kwargs["current_user"] = user
        
        return await func(*args, **kwargs)
    return wrapper
