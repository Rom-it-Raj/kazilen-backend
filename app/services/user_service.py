import json
from sqlalchemy.orm import Session
from app.db.models import User
from app.schemas.user import UserUpdateSchema, WorkerServicesUpdateSchema

class UserService:
    @staticmethod
    def get_user_profile(user: User) -> dict:
        services_list = []
        if user.offered_services:
            try:
                services_list = json.loads(user.offered_services)
            except Exception:
                services_list = user.offered_services.split(",")

        return {
            "id": user.id,
            "phone_number": user.phone_number,
            "full_name": user.full_name,
            "role": user.role,
            "dob": user.dob,
            "gender": user.gender,
            "offered_services": services_list,
            "created_at": str(user.created_at) if user.created_at else None
        }

    @staticmethod
    def update_user_profile(data: UserUpdateSchema, current_user: User, db: Session) -> dict:
        if data.full_name is not None:
            current_user.full_name = data.full_name
        if data.dob is not None:
            current_user.dob = data.dob
        if data.gender is not None:
            current_user.gender = data.gender
            
        db.commit()
        db.refresh(current_user)
        
        return {
            "status": "success",
            "user": {
                "id": current_user.id,
                "phone_number": current_user.phone_number,
                "full_name": current_user.full_name,
                "role": current_user.role,
                "dob": current_user.dob,
                "gender": current_user.gender
            }
        }

    @staticmethod
    def update_worker_services(data: WorkerServicesUpdateSchema, current_user: User, db: Session) -> dict:
        if isinstance(data.offered_services, list):
            current_user.offered_services = json.dumps(data.offered_services)
        else:
            current_user.offered_services = str(data.offered_services)

        db.commit()
        db.refresh(current_user)

        return {
            "status": "success",
            "message": "Offered services updated in database",
            "offered_services": data.offered_services
        }
