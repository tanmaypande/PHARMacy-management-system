from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.services.auth_service import AuthService
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & RBAC"])


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "cashier"


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    auth_svc = AuthService(db)
    user_info = auth_svc.authenticate_user(req.username, req.password)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password, or account inactive."
        )
    return {"status": "success", "user": user_info}


@router.post("/users")
def create_user(req: CreateUserRequest, db: Session = Depends(get_db)):
    auth_svc = AuthService(db)
    try:
        user = auth_svc.create_user(
            username=req.username,
            password=req.password,
            full_name=req.full_name,
            role=req.role
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    auth_svc = AuthService(db)
    auth_svc.seed_default_admin_if_empty()
    return auth_svc.list_users()


@router.put("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: str, db: Session = Depends(get_db)):
    auth_svc = AuthService(db)
    try:
        return auth_svc.toggle_user_active(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
