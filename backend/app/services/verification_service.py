"""
Vérification email + téléphone à l'inscription.

- Email   : token URL-safe (24 h) stocké en base, lien envoyé par email.
- Phone   : OTP 6 chiffres (10 min) stocké hashé, envoyé par SMS.
            Le provider SMS est laissé pluggable : sans config, l'OTP est
            seulement loggué côté serveur (mode dev / staging).

Les deux collections ont un TTL côté Mongo si l'index ``expires_at`` est créé.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import get_settings
from app.database import mongo_db

logger = logging.getLogger(__name__)

_email_tokens = mongo_db["email_verification_tokens"]
_phone_otps = mongo_db["phone_verification_codes"]
_users = mongo_db["users"]
_organizations = mongo_db["organizations"]


EMAIL_TOKEN_TTL_HOURS = 24
PHONE_OTP_TTL_MINUTES = 10
PHONE_OTP_MAX_ATTEMPTS = 5


# ── helpers ──

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


# ── EMAIL ──

async def create_email_verification_token(user_id: str, email: str) -> str:
    """Génère un token URL-safe, invalide les précédents et le persiste."""
    token = secrets.token_urlsafe(32)
    now = _now()
    await _email_tokens.delete_many({"user_id": user_id})
    await _email_tokens.insert_one({
        "user_id": user_id,
        "email": email.lower().strip(),
        "token": token,
        "created_at": now,
        "expires_at": now + timedelta(hours=EMAIL_TOKEN_TTL_HOURS),
        "consumed_at": None,
    })
    return token


async def consume_email_token(token: str) -> Optional[dict]:
    """Valide le token et marque l'utilisateur ``email_verified=True``."""
    doc = await _email_tokens.find_one({"token": token, "consumed_at": None})
    if not doc:
        return None
    if doc["expires_at"] < _now():
        return None

    from bson import ObjectId
    user_id = doc["user_id"]
    await _users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"email_verified": True, "updated_at": _now()}},
    )
    user = await _users.find_one({"_id": ObjectId(user_id)})
    if user and user.get("organization_id"):
        await _organizations.update_one(
            {"_id": ObjectId(user["organization_id"])},
            {"$set": {"contact_email_verified": True, "updated_at": _now()}},
        )
    await _email_tokens.update_one(
        {"_id": doc["_id"]},
        {"$set": {"consumed_at": _now()}},
    )
    return user


# ── PHONE OTP ──

def _generate_otp() -> str:
    # 6 chiffres, leading zero préservé.
    return f"{secrets.randbelow(1_000_000):06d}"


async def create_phone_otp(user_id: str, phone: str) -> str:
    code = _generate_otp()
    now = _now()
    await _phone_otps.delete_many({"user_id": user_id})
    await _phone_otps.insert_one({
        "user_id": user_id,
        "phone": phone,
        "code_hash": _hash_code(code),
        "attempts": 0,
        "created_at": now,
        "expires_at": now + timedelta(minutes=PHONE_OTP_TTL_MINUTES),
        "consumed_at": None,
    })
    return code


async def verify_phone_otp(user_id: str, code: str) -> bool:
    doc = await _phone_otps.find_one({"user_id": user_id, "consumed_at": None})
    if not doc:
        return False
    if doc["expires_at"] < _now():
        return False
    if doc.get("attempts", 0) >= PHONE_OTP_MAX_ATTEMPTS:
        return False

    if _hash_code(code) != doc["code_hash"]:
        await _phone_otps.update_one(
            {"_id": doc["_id"]},
            {"$inc": {"attempts": 1}},
        )
        return False

    from bson import ObjectId
    await _phone_otps.update_one(
        {"_id": doc["_id"]},
        {"$set": {"consumed_at": _now()}},
    )
    await _users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"phone_verified": True, "updated_at": _now()}},
    )
    user = await _users.find_one({"_id": ObjectId(user_id)})
    if user and user.get("organization_id"):
        await _organizations.update_one(
            {"_id": ObjectId(user["organization_id"])},
            {"$set": {"contact_phone_verified": True, "updated_at": _now()}},
        )
    return True


# ── OTP sending (par email — pluggable vers SMS en prod) ──

async def send_phone_otp(user_id: str, phone: str, code: str) -> bool:
    """
    Envoie l'OTP de vérification téléphone par email (SMTP déjà configuré).

    En production, ce canal peut être remplacé par un vrai provider SMS
    (Twilio / Vonage) via la variable ``sms_provider``.
    Le code est aussi loggué côté serveur en mode dev pour faciliter les tests.
    """
    settings = get_settings()
    provider = (getattr(settings, "sms_provider", None) or "").lower()

    logger.info("otp.send phone=%s user=%s provider=%s", phone, user_id, provider or "email")

    if provider not in ("", "log", "dev", "email"):
        logger.error("sms.provider_unsupported provider=%s phone=%s", provider, phone)
        return False

    # Mode dev : log aussi l'OTP pour les tests sans SMTP.
    if provider in ("log", "dev"):
        logger.warning("otp.dev_mode phone=%s otp=%s ttl=%dmin",
                       phone, code, PHONE_OTP_TTL_MINUTES)

    # Envoi par email — récupère l'adresse depuis le user.
    user = await _users.find_one({"_id": __import__("bson").ObjectId(user_id)})
    if not user or not user.get("email"):
        logger.warning("otp.no_email user_id=%s", user_id)
        return False

    from app.services.email_service import send_phone_otp_email
    return await send_phone_otp_email(user["email"], phone, code)
