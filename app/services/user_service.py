import json
from sqlalchemy.orm import Session
from app.db.models import User
from app.schemas.user import UserUpdateSchema, WorkerServicesUpdateSchema, WorkerAvailabilitySchema

class UserService:
    @staticmethod
    def get_user_profile(user: User) -> dict:
        services_list = []
        if user.offered_services:
            try:
                services_list = json.loads(user.offered_services)
            except Exception:
                services_list = user.offered_services.split(",")

        availability_data = {"days_off": [], "dead_slots": []}
        if user.availability:
            try:
                parsed_avail = json.loads(user.availability)
                if isinstance(parsed_avail, dict):
                    availability_data = {
                        "days_off": parsed_avail.get("days_off", []),
                        "dead_slots": parsed_avail.get("dead_slots", [])
                    }
            except Exception:
                pass

        return {
            "id": user.id,
            "phone_number": user.phone_number,
            "full_name": user.full_name,
            "role": user.role,
            "dob": user.dob,
            "gender": user.gender,
            "offered_services": services_list,
            "availability": availability_data,
            "referral_code": user.referral_code,
            "referral_points": user.referral_points or 0,
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
                "gender": current_user.gender,
                "referral_code": current_user.referral_code,
                "referral_points": current_user.referral_points or 0,
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

    @staticmethod
    def update_worker_availability(data: WorkerAvailabilitySchema, current_user: User, db: Session) -> dict:
        payload = data.model_dump() if hasattr(data, "model_dump") else data.dict()
        current_user.availability = json.dumps(payload)
        db.commit()
        db.refresh(current_user)

        return {
            "status": "success",
            "message": "Worker availability and dead time zones updated in database",
            "availability": payload
        }
