import json
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import User

class WorkerService:
    @staticmethod
    def get_available_workers(
        service_id: Optional[str] = None,
        sub_category: Optional[str] = None,
        db: Session = None
    ) -> dict:
        target_service = service_id or sub_category
        workers = db.query(User).filter(User.role == "worker").all()
        filtered = []

        for w in workers:
            enabled = True
            if target_service and w.offered_services:
                try:
                    services_list = json.loads(w.offered_services)
                    if isinstance(services_list, list):
                        enabled = target_service in services_list
                    else:
                        enabled = target_service in str(services_list).split(",")
                except Exception:
                    enabled = target_service in str(w.offered_services).split(",")

            if enabled:
                filtered.append({
                    "id": w.id,
                    "full_name": w.full_name or "Verified Partner",
                    "phone_number": w.phone_number,
                    "rating": 4.9,
                    "locality": "Dharampeth, Nagpur",
                    "eta": "Arrives in 30 mins",
                    "jobs_completed": "150+"
                })

        return {"status": "success", "workers": filtered}
