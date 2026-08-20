import json
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models import User, BookingReview, Address

class WorkerService:
    @staticmethod
    def get_available_workers(
        service_id: Optional[str] = None,
        sub_category: Optional[str] = None,
        db: Session = None
    ) -> dict:
        target_service = service_id or sub_category
        workers = (
            db.query(User)
            .filter(
                User.role == "worker",
                User.is_online != 0
            )
            .all()
            if db else []
        )
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
                # Calculate real rating and review count from BookingReview table
                reviews = db.query(BookingReview).filter(BookingReview.reviewee_id == w.id).all() if db else []
                if reviews:
                    total_score = sum(r.rating for r in reviews if r.rating is not None)
                    avg_rating = round(total_score / len(reviews), 1)
                    reviews_count = len(reviews)
                else:
                    avg_rating = None
                    reviews_count = 0

                # Resolve worker operational locality
                worker_addr = (
                    db.query(Address)
                    .filter(Address.user_id == w.id)
                    .order_by(desc(Address.is_default), desc(Address.id))
                    .first()
                    if db else None
                )
                if worker_addr and worker_addr.area:
                    locality_val = f"{worker_addr.area}, {worker_addr.city or 'Nagpur'}"
                elif worker_addr and worker_addr.full_address:
                    locality_val = worker_addr.full_address
                else:
                    locality_val = "Dharampeth, Nagpur"

                filtered.append({
                    "id": w.id,
                    "full_name": w.full_name or "Verified Partner",
                    "phone_number": w.phone_number,
                    "rating": avg_rating,
                    "reviews_count": reviews_count,
                    "locality": locality_val,
                    "eta": "Arrives in 30 mins",
                    "jobs_completed": f"{reviews_count}+" if reviews_count > 0 else "0",
                    "offered_services": parsed_services
                })

        return {"status": "success", "workers": filtered}

    @staticmethod
    def get_worker_dashboard(current_user: User, db: Session) -> dict:
        from app.db.models import Booking
        completed_bookings = db.query(Booking).filter(
            Booking.worker_id == current_user.id,
            Booking.status == "completed"
        ).all()

        total_earnings = 0
        for b in completed_bookings:
            try:
                total_earnings += float(b.amount) if b.amount else 0
            except (ValueError, TypeError):
                pass

        completed_count = len(completed_bookings)

        # Calculate ratings and recent reviews for dashboard
        reviews = (
            db.query(BookingReview, User)
            .join(User, User.id == BookingReview.reviewer_id)
            .filter(BookingReview.reviewee_id == current_user.id)
            .order_by(BookingReview.created_at.desc())
            .all()
        )

        if reviews:
            total_score = sum(r.rating for r, _ in reviews if r.rating is not None)
            avg_rating = round(total_score / len(reviews), 1)
            reviews_count = len(reviews)
        else:
            avg_rating = None
            reviews_count = 0

        recent_reviews = []
        for r, reviewer in reviews[:3]:
            recent_reviews.append({
                "id": r.id,
                "booking_id": r.booking_id,
                "reviewer_name": reviewer.full_name or "Verified Customer",
                "rating": r.rating,
                "description": r.description,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        # Count active services
        active_services_count = 0
        if current_user.offered_services:
            try:
                parsed = json.loads(current_user.offered_services)
                if isinstance(parsed, list):
                    active_services_count = len(parsed)
            except Exception:
                pass

        return {
            "status": "success",
            "progress": {
                "today": {
                    "earnings": total_earnings,
                    "hours": f"{completed_count * 2}:00 hrs",
                    "orders": completed_count
                },
                "week": {
                    "earnings": total_earnings,
                    "hours": f"{completed_count * 2}:00 hrs",
                    "orders": completed_count
                }
            },
            "rating": avg_rating,
            "reviews_count": reviews_count,
            "recent_reviews": recent_reviews,
            "active_services_count": active_services_count,
            "plan": {
                "completed": completed_count,
                "totalLabel": "10",
                "price": "399",
                "timeLeft": "28 Days left"
            },
            "recharge": {
                "price": "399",
                "validityDays": 30,
                "orderType": "Instant Local Dispatch"
            }
        }

