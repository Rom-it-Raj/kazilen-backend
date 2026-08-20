from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
import traceback
import asyncio

from app.api.routes import auth, users, workers, bookings, reviews, addresses
from app.db.database import engine, Base, SessionLocal
from app.core.config import settings
from app.services.referral_service import ensure_referral_codes

# Initialize database schema
Base.metadata.create_all(bind=engine)

def auto_migrate():
    """Applies lightweight schema migrations for existing local databases."""
    with engine.begin() as conn:
        # User table columns
        for col_name in ["dob", "gender", "offered_services", "referral_code", "availability"]:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} VARCHAR"))
            except Exception:
                pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN referral_points INTEGER DEFAULT 0"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_online INTEGER DEFAULT 1"))
        except Exception:
            pass
        try:
            conn.execute(text("CREATE UNIQUE INDEX ix_users_referral_code ON users (referral_code)"))
        except Exception:
            pass
        # Booking table columns
        for col_def in [
            "start_otp VARCHAR",
            "end_otp VARCHAR",
            "amount VARCHAR",
            "updated_at DATETIME",
        ]:
            try:
                conn.execute(text(f"ALTER TABLE bookings ADD COLUMN {col_def}"))
            except Exception:
                pass
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS booking_reviews (
                id INTEGER PRIMARY KEY,
                booking_id INTEGER NOT NULL,
                reviewer_id INTEGER NOT NULL,
                reviewee_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                description VARCHAR(2000) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_booking_review_reviewer UNIQUE (booking_id, reviewer_id),
                FOREIGN KEY (booking_id) REFERENCES bookings(id),
                FOREIGN KEY (reviewer_id) REFERENCES users(id),
                FOREIGN KEY (reviewee_id) REFERENCES users(id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS platform_feedback (
                id INTEGER PRIMARY KEY,
                booking_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                description VARCHAR(2000) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_platform_feedback_user UNIQUE (booking_id, user_id),
                FOREIGN KEY (booking_id) REFERENCES bookings(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                tag VARCHAR(50) DEFAULT 'Home',
                flat_no VARCHAR(255),
                street VARCHAR(255),
                area VARCHAR(255) NOT NULL,
                landmark VARCHAR(255),
                city VARCHAR(100) DEFAULT 'Nagpur',
                pincode VARCHAR(20),
                full_address VARCHAR(1000) NOT NULL,
                latitude VARCHAR(50),
                longitude VARCHAR(50),
                is_default INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))

auto_migrate()

with SessionLocal() as db:
    ensure_referral_codes(db)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:4000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:4000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] Uncaught exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "Internal Server Error"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Include Router Modules
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users Profile"])
app.include_router(workers.router, prefix="/api/workers", tags=["Worker Marketplace"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews & Feedback"])
app.include_router(addresses.router, prefix="/api/addresses", tags=["Saved Addresses"])

@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for container orchestrators and load balancers."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }
