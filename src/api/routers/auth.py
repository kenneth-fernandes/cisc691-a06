"""
Authentication API endpoints (optional)
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Simple token-based auth (in production, use proper JWT or OAuth)
security = HTTPBearer(auto_error=False)

# Mock API keys for demo purposes
VALID_API_KEYS = {
    "demo-key-123": {"name": "Demo User", "permissions": ["read", "write"]},
    "readonly-key-456": {"name": "Read Only User", "permissions": ["read"]}
}

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get current user from API key"""
    if not credentials:
        return None  # Allow anonymous access for demo
    
    api_key = credentials.credentials
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return VALID_API_KEYS[api_key]

@router.get("/validate")
async def validate_token(user=Depends(get_current_user)):
    """Validate API token"""
    if not user:
        return {"valid": False, "message": "No token provided"}
    
    return {
        "valid": True,
        "user": user["name"],
        "permissions": user["permissions"]
    }

@router.get("/demo-keys")
async def get_demo_keys():
    """Get demo API keys for testing"""
    return {
        "demo_keys": [
            {
                "key": "demo-key-123",
                "name": "Demo User",
                "permissions": ["read", "write"]
            },
            {
                "key": "readonly-key-456", 
                "name": "Read Only User",
                "permissions": ["read"]
            }
        ],
        "usage": "Include in Authorization header as 'Bearer <key>'"
    }