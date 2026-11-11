from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.services.policy_service import PolicyService
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/policies", tags=["Policies & Standard Operating Procedures"])


class PolicyCreate(BaseModel):
    title: str
    category: str = "Store Governance"
    version: str = "1.0"
    content: str
    responsible_role: str = "All Staff"
    is_active: bool = True


@router.get("")
def list_policies(search: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    svc = PolicyService(db)
    return svc.list_policies(search=search, category=category)


@router.post("")
def create_policy(req: PolicyCreate, db: Session = Depends(get_db)):
    svc = PolicyService(db)
    try:
        return svc.create_policy(req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{policy_id}")
def update_policy(policy_id: str, req: PolicyCreate, db: Session = Depends(get_db)):
    svc = PolicyService(db)
    try:
        return svc.update_policy(policy_id, req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{policy_id}")
def delete_policy(policy_id: str, db: Session = Depends(get_db)):
    svc = PolicyService(db)
    try:
        svc.delete_policy(policy_id)
        return {"status": "success", "message": "Policy deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
