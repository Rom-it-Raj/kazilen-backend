from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.worker_service import WorkerService

router = APIRouter()

@router.get("/available")
@router.get("")
def get_available_workers(
    service_id: Optional[str] = None,
    sub_category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves list of available workers filtered optionally by service or sub-category ID."""
    return WorkerService.get_available_workers(service_id=service_id, sub_category=sub_category, db=db)
