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
            parsed_services = []
            if w.offered_services:
                try:
                    parsed = json.loads(w.offered_services)
                    if isinstance(parsed, list):
                        parsed_services = parsed
                    else:
                        parsed_services = str(w.offered_services).split(",")
                except Exception:
                    parsed_services = str(w.offered_services).split(",")

            if target_service and parsed_services:
                extracted_ids = []
                for item in parsed_services:
                    if isinstance(item, dict) and "id" in item:
                        extracted_ids.append(str(item["id"]))
                    else:
                        extracted_ids.append(str(item))
                enabled = target_service in extracted_ids

            if enabled:
                filtered.append({
                    "id": w.id,
                    "full_name": w.full_name or "Verified Partner",
                    "phone_number": w.phone_number,
                    "rating": 4.9,
                    "locality": "Dharampeth, Nagpur",
                    "eta": "Arrives in 30 mins",
                    "jobs_completed": "150+",
                    "offered_services": parsed_services
                })

        return {"status": "success", "workers": filtered}
