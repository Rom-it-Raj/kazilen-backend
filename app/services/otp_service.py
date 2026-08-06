"""
OTP Delivery Service (Vendor-Agnostic Architecture)

This module provides a modular, extensible strategy pattern for delivering OTPs
across different providers (Console Log, Meta WhatsApp Cloud API, Twilio, Generic SMS Gateway).

==================================================================================
HOW TO SWITCH PROVIDERS (No code change required!):
==================================================================================
Set `OTP_PROVIDER` in your `.env` file or environment variables:
  - OTP_PROVIDER=console   (Default: Dev terminal logger - no API keys needed)
  - OTP_PROVIDER=whatsapp  (Meta WhatsApp Cloud API)
  - OTP_PROVIDER=twilio    (Twilio SMS API)
  - OTP_PROVIDER=custom    (Custom HTTP SMS Gateway / Webhook)

==================================================================================
HOW TO ADD A BRAND NEW PROVIDER IN 3 SIMPLE STEPS:
==================================================================================
Step 1: Create a new class inheriting from `BaseOTPProvider`:
    class MyCoolProvider(BaseOTPProvider):
        def send_otp(self, phone_number: str, otp: str) -> bool:
            # Add your custom API call here
            return True

Step 2: Add your provider name to `PROVIDER_MAP` inside `OTPService.get_provider()`:
    "my_cool_provider": MyCoolProvider()

Step 3: Set `OTP_PROVIDER=my_cool_provider` in your `.env` file!
==================================================================================
"""

import abc
import logging
import urllib.request
import urllib.parse
import json
from typing import Dict, Type
from app.core.config import settings

logger = logging.getLogger(__name__)

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
# 2. CONSOLE PROVIDER (Default for Local Development & Testing)
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
# 3. WHATSAPP META CLOUD API PROVIDER
# =========================================================================
class WhatsAppMetaOTPProvider(BaseOTPProvider):
    """
    Sends OTP via Meta (Facebook) WhatsApp Cloud API.
    
    Required .env variables:
      - WHATSAPP_API_TOKEN: Meta Graph API User/System Token
      - WHATSAPP_PHONE_NUMBER_ID: Meta Business Phone Number ID
      - WHATSAPP_TEMPLATE_NAME: Approved WhatsApp message template name (default: kazilen_otp)
    
    Setup Guide:
      1. Register your business app at https://developers.facebook.com/
      2. Create an authentication/OTP template in WhatsApp Manager.
      3. Fill WHATSAPP_API_TOKEN & WHATSAPP_PHONE_NUMBER_ID in .env.
    """
    def send_otp(self, phone_number: str, otp: str) -> bool:
        token = settings.WHATSAPP_API_TOKEN
        phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
        template_name = settings.WHATSAPP_TEMPLATE_NAME

        if not token or not phone_id:
            logger.error("[WhatsAppProvider] Missing WHATSAPP_API_TOKEN or WHATSAPP_PHONE_NUMBER_ID in settings!")
            return False

        # Clean phone number (remove + or whitespace)
        formatted_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")

        url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Meta WhatsApp Template Payload Structure
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
                        "parameters": [
                            {"type": "text", "text": otp}
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": "0",
                        "parameters": [
                            {"type": "text", "text": otp}
                        ]
                    }
                ]
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                logger.info(f"[WhatsAppProvider] Message sent successfully: {res_body}")
                return True
        except Exception as e:
            logger.error(f"[WhatsAppProvider] Error sending WhatsApp message: {e}")
            return False


# =========================================================================
# 4. TWILIO SMS PROVIDER
# =========================================================================
class TwilioOTPProvider(BaseOTPProvider):
    """
    Sends OTP via Twilio SMS REST API.
    
    Required .env variables:
      - TWILIO_ACCOUNT_SID: Twilio Account SID
      - TWILIO_AUTH_TOKEN: Twilio Auth Token
      - TWILIO_PHONE_NUMBER: Twilio Sender Phone Number (e.g. +1234567890)
    """
    def send_otp(self, phone_number: str, otp: str) -> bool:
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        from_number = settings.TWILIO_PHONE_NUMBER

        if not account_sid or not auth_token or not from_number:
            logger.error("[TwilioProvider] Missing Twilio SID, Auth Token, or From Phone Number!")
            return False

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        
        message_body = f"Your Kazilen verification code is: {otp}. Valid for 5 minutes."
        data = urllib.parse.urlencode({
            "From": from_number,
            "To": phone_number,
            "Body": message_body
        }).encode("utf-8")

        # Basic Auth header encoding for Twilio
        import base64
        credentials = f"{account_sid}:{auth_token}"
        encoded_credentials = base64.b64encode(credentials.encode("ascii")).decode("ascii")
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                logger.info(f"[TwilioProvider] SMS sent successfully. Message SID: {res_body.get('sid')}")
                return True
        except Exception as e:
            logger.error(f"[TwilioProvider] Error sending Twilio SMS: {e}")
            return False


# =========================================================================
# 5. GENERIC / CUSTOM HTTP SMS GATEWAY PROVIDER (e.g. MSG91, Fast2SMS, AWS SNS)
# =========================================================================
class CustomHTTPProvider(BaseOTPProvider):
    """
    Generic HTTP Gateway Provider.
    Use this if you use Indian SMS providers (MSG91, Fast2SMS), AWS SNS, Infobip, etc.
    
    Required .env variables:
      - SMS_GATEWAY_URL: Target API endpoint URL
      - SMS_GATEWAY_API_KEY: API Key / Token
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

        try:
            req = urllib.request.Request(
                gateway_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                logger.info(f"[CustomHTTPProvider] OTP request sent to {gateway_url}")
                return True
        except Exception as e:
            logger.error(f"[CustomHTTPProvider] Error sending request to custom gateway: {e}")
            return False


# =========================================================================
# 6. OTP SERVICE MANAGER & FACTORY
# =========================================================================
class OTPService:
    """
    Central Manager for OTP Operations.
    Resolves configured provider from `settings.OTP_PROVIDER` with graceful console fallback.
    """
    _providers: Dict[str, BaseOTPProvider] = {
        "console": ConsoleOTPProvider(),
        "whatsapp": WhatsAppMetaOTPProvider(),
        "twilio": TwilioOTPProvider(),
        "custom": CustomHTTPProvider(),
    }

    @classmethod
    def get_provider(cls, provider_name: str = None) -> BaseOTPProvider:
        """
        Retrieves the requested provider instance.
        Falls back to 'console' if configured provider is unknown.
        """
        name = (provider_name or settings.OTP_PROVIDER or "console").lower()
        if name not in cls._providers:
            logger.warning(f"[OTPService] Unknown provider '{name}'. Falling back to 'console'.")
            return cls._providers["console"]
        return cls._providers[name]

    @classmethod
    def send_otp(cls, phone_number: str, otp: str) -> bool:
        """
        Dispatches OTP to user via the currently configured OTP Provider.
        If external provider fails (e.g. invalid API key or network down),
        it safely falls back to ConsoleOTPProvider so local testing isn't blocked.
        """
        provider = cls.get_provider()
        success = provider.send_otp(phone_number, otp)

        # Fallback safeguard for development/testing if API fails
        if not success and not isinstance(provider, ConsoleOTPProvider):
            logger.warning("[OTPService] Configured OTP provider failed! Using Console fallback.")
            ConsoleOTPProvider().send_otp(phone_number, otp)
            return True

        return success
