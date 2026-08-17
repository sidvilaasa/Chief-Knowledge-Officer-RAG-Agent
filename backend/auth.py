"""
Simple user identity: reads X-User-ID header.
Can be swapped for JWT middleware without changing any other file.
"""
from fastapi import Depends, Header, HTTPException, status


async def get_current_user(x_user_id: str = Header(..., alias="X-User-ID")) -> str:
    """FastAPI dependency – returns the user_id string or raises 401."""
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-ID header is required.",
        )
    return x_user_id.strip()
