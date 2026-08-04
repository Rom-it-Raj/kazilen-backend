import secrets
import string

from sqlalchemy.orm import Session

from app.db.models import User


REFERRAL_CODE_LENGTH = 6
REFERRAL_ALPHABET = string.ascii_uppercase + string.digits


def generate_unique_referral_code(db: Session) -> str:
    for _ in range(20):
        code = "".join(secrets.choice(REFERRAL_ALPHABET) for _ in range(REFERRAL_CODE_LENGTH))
        if not db.query(User).filter(User.referral_code == code).first():
            return code

    raise RuntimeError("Unable to generate a unique referral code")


def ensure_customer_referral_codes(db: Session) -> None:
    customers = db.query(User).filter(
        User.role == "customer",
        User.referral_code.is_(None),
    ).all()

    if not customers:
        return

    for customer in customers:
        customer.referral_code = generate_unique_referral_code(db)

    db.commit()
