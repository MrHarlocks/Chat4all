from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from src.domain.models import User
from src.services.user_service import UserService

router = APIRouter()

class LoginRequest(BaseModel):
    user_id: Optional[UUID] = None
    display_name: Optional[str] = None

@router.post("/login", response_model=User, summary="Login/Register", description="Autentica ou registra um usuário pelo ID.")
async def login(
    request: LoginRequest,
    service: UserService = Depends(UserService)
):
    try:
        return await service.get_or_create_user(request.user_id, request.display_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
