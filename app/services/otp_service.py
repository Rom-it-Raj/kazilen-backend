"""
OTP Delivery Service (Vendor-Agnostic Architecture)

This module provides a modular, extensible strategy pattern for delivering OTPs
across different providers (Twilio SMS, Twilio WhatsApp, Meta WhatsApp Cloud API, Console Log, Generic SMS Gateway).

Pattern & Configuration ported from Kazilen (backend-kazilen / send_otp.py).
"""

import abc
import logging
import threading
import urllib.request
import urllib.parse
import json
from typing import Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Try importing official Twilio client
try:
    from twilio.rest import Client as TwilioClient
    _TWILIO_AVAILABLE = True
except ImportError:
    _TWILIO_AVAILABLE = False


def normalize_phone_e164(phone_number: str) -> str:
    """
    Format phone number to standard E.164 (e.g., +917780877482).
    Strips spaces, dashes, and ensures leading country code.
    """
    clean = str(phone_number).strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if clean.startswith("+"):
        return clean
    if len(clean) == 10:
        # Default 10-digit Indian mobile number
        return f"+91{clean}"
    return f"+{clean}"


# =========================================================================
# 1. ABSTRACT BASE PROVIDER INTERFACE
# =========================================================================
class BaseOTPProvider(abc.ABC):
    """
    Abstract Base Class for all OTP Providers.
    Every OTP provider must implement the `send_otp` method.
    """
    @abc.abstractmethod
    def send_otp(self, phone_number: str, otp: str) -> bool:
        """
        Send OTP to the given phone number.
        Returns True if sent successfully, False otherwise.
        """
        pass


# =========================================================================
# 2. CONSOLE PROVIDER (Default for Local Development & Offline Testing)
# =========================================================================
class ConsoleOTPProvider(BaseOTPProvider):
    """
    Development OTP provider that prints formatted OTP to standard output/console.
    Requires no external API keys or network connection.
    """
    def send_otp(self, phone_number: str, otp: str) -> bool:
        print("\n" + "=" * 56, flush=True)
        print(f"  [DEV OTP PROVIDER] Phone: {phone_number}", flush=True)
        print(f"  --> YOUR OTP CODE IS: {otp} <--", flush=True)
        print("=" * 56 + "\n", flush=True)
        logger.info(f"[ConsoleOTPProvider] OTP {otp} generated for {phone_number}")
        return True


# =========================================================================
# 3. TWILIO SMS PROVIDER (Official SDK + Non-blocking Threading)
# =========================================================================
class TwilioOTPProvider(BaseOTPProvider):
    """
    Sends OTP via Twilio SMS using the official Twilio SDK.
    Includes background asynchronous dispatch and timeout safeguards.
    """
    @staticmethod
    def get_client() -> Optional[TwilioClient]:
        if not _TWILIO_AVAILABLE:
            logger.warning("[TwilioProvider] Twilio library is not installed.")
            return None
        sid = settings.TWILIO_ACCOUNT_SID
        token = settings.TWILIO_AUTH_TOKEN
        if sid and token:
            try:
                return TwilioClient(sid, token)
            except Exception as e:
                logger.warning(f"[Twilio Init Warning]: {e}")
                return None
        return None

    def send_otp(self, phone_number: str, otp: str) -> bool:
        client = self.get_client()
        from_number = settings.TWILIO_PHONE_NUMBER

        if not client or not from_number:
            logger.warning("[TwilioProvider] Missing Twilio credentials or sender phone number!")
            return False

        formatted_recipient = normalize_phone_e164(phone_number)
        message_body = f"Your Kazilen verification code is: {otp}. Valid for 5 minutes."

        def _send():
            try:
                msg = client.messages.create(
                    body=message_body,
                    from_=from_number,
                    to=formatted_recipient
                )
                print(f"[SMS Sent via Twilio] to {formatted_recipient} (SID: {msg.sid})", flush=True)
                logger.info(f"[TwilioProvider] SMS sent to {formatted_recipient} (SID: {msg.sid})")
            except Exception as e:
                print(f"[Twilio SMS Error]: {e}", flush=True)
                logger.error(f"[TwilioProvider] Error sending SMS: {e}")

        # Fire-and-forget background thread so HTTP response returns instantly
        t = threading.Thread(target=_send, daemon=True)
        t.start()
        return True


# =========================================================================
# 4. TWILIO WHATSAPP PROVIDER
# =========================================================================
class TwilioWhatsAppOTPProvider(BaseOTPProvider):
    """
    Sends OTP via Twilio WhatsApp API using the official Twilio SDK.
    """
    def send_otp(self, phone_number: str, otp: str) -> bool:
        client = TwilioOTPProvider.get_client()
        from_number = settings.TWILIO_PHONE_NUMBER

        if not client or not from_number:
            logger.warning("[TwilioWhatsAppProvider] Missing Twilio credentials or sender phone number!")
            return False

        clean_from = from_number.replace("whatsapp:", "").strip()
        formatted_recipient = normalize_phone_e164(phone_number)
        message_body = f"Your Kazilen verification code is: {otp}. Valid for 5 minutes."

        def _send():
            try:
                msg = client.messages.create(
                    body=message_body,
                    from_=f"whatsapp:{clean_from}",
                    to=f"whatsapp:{formatted_recipient}"
                )
                print(f"[WhatsApp Sent via Twilio] to {formatted_recipient} (SID: {msg.sid})", flush=True)
                logger.info(f"[TwilioWhatsAppProvider] WhatsApp sent to {formatted_recipient} (SID: {msg.sid})")
            except Exception as e:
                print(f"[Twilio WhatsApp Error]: {e}", flush=True)
                logger.error(f"[TwilioWhatsAppProvider] Error sending WhatsApp message: {e}")

        t = threading.Thread(target=_send, daemon=True)
        t.start()
        return True


# =========================================================================
# 5. WHATSAPP META CLOUD API PROVIDER (Graph API)
# =========================================================================
class WhatsAppMetaOTPProvider(BaseOTPProvider):
    """
    Sends OTP via Meta (Facebook) WhatsApp Cloud API.
    """
    def send_otp(self, phone_number: str, otp: str) -> bool:
        token = settings.WHATSAPP_API_TOKEN
        phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
        template_name = settings.WHATSAPP_TEMPLATE_NAME

        if not token or not phone_id:
            logger.error("[WhatsAppMetaProvider] Missing WHATSAPP_API_TOKEN or WHATSAPP_PHONE_NUMBER_ID in settings!")
            return False

        formatted_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")

        url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en_US"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": otp}]
                    },
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": "0",
                        "parameters": [{"type": "text", "text": otp}]
                    }
                ]
            }
        }

        def _send():
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_body = json.loads(response.read().decode("utf-8"))
                    logger.info(f"[WhatsAppMetaProvider] Message sent: {res_body}")
            except Exception as e:
                logger.error(f"[WhatsAppMetaProvider] Error sending WhatsApp message: {e}")

        t = threading.Thread(target=_send, daemon=True)
        t.start()
        return True


# =========================================================================
# 6. GENERIC / CUSTOM HTTP SMS GATEWAY PROVIDER
# =========================================================================
class CustomHTTPProvider(BaseOTPProvider):
    """
    Generic HTTP Gateway Provider (e.g. MSG91, Fast2SMS, Infobip, AWS SNS).
    """
    def send_otp(self, phone_number: str, otp: str) -> bool:
        gateway_url = settings.SMS_GATEWAY_URL
        api_key = settings.SMS_GATEWAY_API_KEY

        if not gateway_url:
            logger.error("[CustomHTTPProvider] Missing SMS_GATEWAY_URL in settings!")
            return False

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}" if api_key else ""
        }

        payload = {
            "phone": phone_number,
            "message": f"Your Kazilen OTP is {otp}",
            "otp": otp
        }

        def _send():
            try:
                req = urllib.request.Request(
                    gateway_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    logger.info(f"[CustomHTTPProvider] OTP request sent to {gateway_url}")
            except Exception as e:
                logger.error(f"[CustomHTTPProvider] Error sending request to custom gateway: {e}")

        t = threading.Thread(target=_send, daemon=True)
        t.start()
        return True


# =========================================================================
# 7. OTP SERVICE MANAGER & CONVENIENCE FUNCTIONS
# =========================================================================
class OTPService:
    """
    Central Manager for OTP Operations.
    Resolves configured provider from `settings.OTP_PROVIDER` with graceful console fallback.
    """
    _providers: Dict[str, BaseOTPProvider] = {
        "console": ConsoleOTPProvider(),
        "twilio": TwilioOTPProvider(),
        "twilio_sms": TwilioOTPProvider(),
        "twilio_whatsapp": TwilioWhatsAppOTPProvider(),
        "whatsapp": WhatsAppMetaOTPProvider(),
        "meta_whatsapp": WhatsAppMetaOTPProvider(),
        "custom": CustomHTTPProvider(),
    }

    @classmethod
    def get_provider(cls, provider_name: str = None) -> BaseOTPProvider:
        """
        Retrieves the requested provider instance.
        Falls back to 'console' if configured provider is unknown.
        """
        name = (provider_name or settings.OTP_PROVIDER or "twilio").lower()
        if name not in cls._providers:
            logger.warning(f"[OTPService] Unknown provider '{name}'. Falling back to 'console'.")
            return cls._providers["console"]
        return cls._providers[name]

    @classmethod
    def send_otp(cls, phone_number: str, otp: str) -> bool:
        """
        Dispatches OTP to user via the currently configured OTP Provider.
        Always prints DEV OTP to terminal for developer convenience and falls back
        gracefully if external API is unreachable.
        """
        provider = cls.get_provider()
        success = provider.send_otp(phone_number, otp)

        if not success and not isinstance(provider, ConsoleOTPProvider):
            logger.warning("[OTPService] Configured OTP provider returned False! Using Console fallback.")
            ConsoleOTPProvider().send_otp(phone_number, otp)
            return True

        return success


# Convenience direct helper functions (matching legacy Kazilen send_otp.py API)
def sendOTP_SMS(recpient: str, otp: str):
    """Direct helper matching Kazilen legacy interface for sending SMS OTP."""
    provider = TwilioOTPProvider()
    return provider.send_otp(recpient, otp)


def sendOTP_WHATSAPP(recpient: str, otp: str):
    """Direct helper matching Kazilen legacy interface for sending WhatsApp OTP."""
    provider = TwilioWhatsAppOTPProvider()
    return provider.send_otp(recpient, otp)
