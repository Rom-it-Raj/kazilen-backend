import secrets
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.db.database import engine
from app.db.models import User, Booking, BookingReview, Address
from app.core.config import settings


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request):
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        is_user_valid = secrets.compare_digest(username, settings.ADMIN_USER)
        is_pass_valid = secrets.compare_digest(password, settings.ADMIN_PASSWORD)

        if is_pass_valid and is_user_valid:
            request.session.update({"authenticated": True})
            return True
        return False

    async def logout(self, request: Request):
        request.session.clear
        return True

    async def authenticate(self, request: Request):
        if not request.session.get("authenticated"):
            return False
        return True


authenticationBackend = AdminAuth(secret_key=settings.ADMIN_SECRET_KEY)


class userAdmin(ModelView, model=User):
    column_list = "__all__"


class bookingAdmin(ModelView, model=Booking):
    column_list = "__all__"


class bookingReviewAdmin(ModelView, model=BookingReview):
    column_list = "__all__"


class addressAdmin(ModelView, model=Address):
    column_list = "__all__"


def setup_admin(app):
    admin = Admin(
        app=app,
        engine=engine,
        audit_backend=authenticationBackend,
        title="Kazilen Admin Panel",
    )
    admin.add_view(userAdmin)
    admin.add_view(bookingAdmin)
    admin.add_view(bookingReviewAdmin)
    admin.add_view(addressAdmin)
