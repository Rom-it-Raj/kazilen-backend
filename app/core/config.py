import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Kazilen Backend"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-local-dev")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./kazilen.db")

    # =========================================================================
    # OTP DELIVERY PROVIDER CONFIGURATION
    # Options: "console" (Dev), "whatsapp" (Meta), "twilio" (SMS), "custom" (HTTP API)
    # =========================================================================
    OTP_PROVIDER: str = os.getenv("OTP_PROVIDER", "console")

    # Meta WhatsApp Cloud API Settings
    # Get these from https://developers.facebook.com/
    WHATSAPP_API_TOKEN: str = os.getenv("WHATSAPP_API_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_TEMPLATE_NAME: str = os.getenv("WHATSAPP_TEMPLATE_NAME", "kazilen_otp")

    # Twilio SMS API Settings
    # Get these from https://console.twilio.com/
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    # Custom HTTP / SMS Gateway Settings (e.g., MSG91, Fast2SMS, Infobip, AWS SNS)
    SMS_GATEWAY_URL: str = os.getenv("SMS_GATEWAY_URL", "")
    SMS_GATEWAY_API_KEY: str = os.getenv("SMS_GATEWAY_API_KEY", "")

    class Config:
        env_file = ".env"

settings = Settings()

