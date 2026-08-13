from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.api.deps import get_current_user
from app.schemas.user import (
    UserUpdateSchema,
    WorkerServicesUpdateSchema,
    WorkerAvailabilitySchema,
    WorkerLocationSchema
)
from app.services.user_service import UserService

router = APIRouter()

@router.get("/me")
def read_users_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves profile details of currently authenticated user."""
    return UserService.get_user_profile(current_user, db)

@router.put("/me")
def update_user_me(
    data: UserUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates profile information (full_name, dob, gender) for current user."""
    return UserService.update_user_profile(data, current_user, db)

@router.put("/me/services")
def update_worker_services(
    data: WorkerServicesUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates offered service IDs for a worker account."""
    return UserService.update_worker_services(data, current_user, db)

@router.put("/me/availability")
def update_worker_availability(
    data: WorkerAvailabilitySchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates weekly days off and daily dead time zones for a worker account."""
    return UserService.update_worker_availability(data, current_user, db)

@router.put("/me/location")
def update_worker_location(
    data: WorkerLocationSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates operational base/live location for current user or worker."""
    return UserService.update_user_location(data, current_user, db)
