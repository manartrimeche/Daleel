"""
Authentication service: password hashing, JWT tokens, user/org/invitation CRUD.
"""

from __future__ import annotations

import logging
import re
import secrets
import uuid
from calendar import monthrange
from datetime import datetime, timedelta, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
import jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.database import mongo_db

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_users = mongo_db["users"]
_organizations = mongo_db["organizations"]
_invitations = mongo_db["invitations"]


def normalize_email(email: str) -> str:
    return email.lower().strip()


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    return re.sub(r"[\s\-().]", "", phone.strip())


def normalize_organization_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).casefold()


def _object_id(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def normalize_subscription_type(subscription_type: Optional[str]) -> str:
    value = (subscription_type or "monthly").strip().lower()
    return value if value in {"monthly", "annual"} else "monthly"

def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)

def calculate_subscription_end_date(
    started_at: datetime,
    subscription_type: Optional[str],
) -> datetime:
    months = 12 if normalize_subscription_type(subscription_type) == "annual" else 1
    return _add_months(started_at, months)


def _as_utc(value: datetime | str | None) -> datetime | None:
    if not value:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def is_subscription_expired(org: dict, now: datetime | None = None) -> bool:
    subscription_ends_at = _as_utc(org.get("subscription_ends_at"))
    if not subscription_ends_at:
        return False
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return subscription_ends_at < now


# ── Password helpers ──

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ──

def create_access_token(user_id: str, role: str, org_id: Optional[str] = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "org_id": org_id,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": expires,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": expires,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm], options={"require": ["exp", "sub"]})


# ── Organization CRUD ──

async def create_organization(
    name: str,
    sector: str,
    size: Optional[str] = None,
    employees: Optional[int] = None,
    activities: Optional[str] = None,
    country: Optional[str] = None,
    jurisdiction: str = "tunisia",
    needs: Optional[list[str]] = None,
    requested_by_email: Optional[str] = None,
    requested_by_phone: Optional[str] = None,
    logo_url: Optional[str] = None,
    subscription_type: str = "monthly",
    status: str = "active",
) -> dict:
    name = name.strip()
    name_key = normalize_organization_name(name)
    normalized_requested_email = normalize_email(requested_by_email) if requested_by_email else None
    normalized_requested_phone = normalize_phone(requested_by_phone)

    if await get_organization_by_name(name):
        raise ValueError("Le nom de l'entreprise existe déjà.")
    if normalized_requested_phone and (
        await get_organization_by_phone(normalized_requested_phone)
        or await get_user_by_phone(normalized_requested_phone)
    ):
        raise ValueError("Ce numéro de téléphone existe déjà.")
    if normalized_requested_email and (
        await get_organization_by_requested_email(normalized_requested_email)
        or await get_user_by_email(normalized_requested_email)
    ):
        raise ValueError("Cette adresse email existe déjà.")

    now = datetime.now(timezone.utc)
    normalized_subscription_type = normalize_subscription_type(subscription_type)
    doc = {
        "name": name,
        "name_key": name_key,
        "sector": sector,
        "size": size,
        "employees": employees,
        "activities": activities,
        "country": country,
        "jurisdiction": jurisdiction,
        "needs": needs or [],
        "requested_by_email": normalized_requested_email,
        "requested_by_phone": normalized_requested_phone,
        "contact_email_verified": False,
        "contact_phone_verified": False,
        "approved_at": None,
        "approved_by": None,
        "rejection_reason": None,
        "logo_url": logo_url,
        "status": status,
        "subscription_type": normalized_subscription_type,
        "subscription_started_at": now,
        "subscription_ends_at": calculate_subscription_end_date(
            now,
            normalized_subscription_type,
        ),
        "created_at": now,
        "updated_at": now,
    }
    result = await _organizations.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc

async def get_organization(org_id: str) -> Optional[dict]:
    object_id = _object_id(org_id)
    if object_id is None:
        return None
    return await _organizations.find_one({"_id": object_id})

async def get_organization_by_name(name: str) -> Optional[dict]:
    normalized_name = name.strip()
    name_key = normalize_organization_name(normalized_name)
    return await _organizations.find_one({
        "$or": [
            {"name_key": name_key},
            {"name": {"$regex": f"^\\s*{re.escape(normalized_name)}\\s*$", "$options": "i"}},
        ]
    })

async def get_organization_by_phone(phone: str) -> Optional[dict]:
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        return None
    return await _organizations.find_one({"requested_by_phone": normalized_phone})

async def get_organization_by_requested_email(email: str) -> Optional[dict]:
    return await _organizations.find_one({"requested_by_email": normalize_email(email)})

async def list_organizations(skip: int = 0, limit: int = 50) -> tuple[list[dict], int]:
    total = await _organizations.count_documents({})
    cursor = _organizations.find().sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return docs, total

async def update_organization(org_id: str, updates: dict) -> Optional[dict]:
    now = datetime.now(timezone.utc)
    object_id = _object_id(org_id)
    if object_id is None:
        return None
    if "name" in updates:
        normalized_name = updates["name"].strip()
        name_key = normalize_organization_name(normalized_name)
        existing = await _organizations.find_one(
            {
                "$or": [
                    {"name_key": name_key},
                    {"name": {"$regex": f"^\\s*{re.escape(normalized_name)}\\s*$", "$options": "i"}},
                ],
                "_id": {"$ne": object_id},
            },
            {"_id": 1},
        )
        if existing:
            raise ValueError("Le nom de l'entreprise existe déjà.")
        updates["name"] = normalized_name
        updates["name_key"] = name_key
    if "subscription_type" in updates:
        org = await get_organization(org_id)
        if not org:
            return None
        subscription_type = normalize_subscription_type(updates.get("subscription_type"))
        started_at = org.get("subscription_started_at") or org.get("created_at") or now
        updates["subscription_type"] = subscription_type
        updates["subscription_started_at"] = started_at
        updates["subscription_ends_at"] = calculate_subscription_end_date(
            started_at,
            subscription_type,
        )
    updates["updated_at"] = now
    await _organizations.update_one({"_id": object_id}, {"$set": updates})
    return await get_organization(org_id)

async def expire_organization_if_needed(org: dict | None) -> Optional[dict]:
    if not org:
        return org
    if org.get("status") != "active" or not is_subscription_expired(org):
        return org
    await _organizations.update_one(
        {"_id": org["_id"]},
        {"$set": {"status": "inactive", "updated_at": datetime.now(timezone.utc)}},
    )
    org["status"] = "inactive"
    org["updated_at"] = datetime.now(timezone.utc)
    return org

async def renew_organization_subscription(
    org_id: str,
    subscription_type: str,
) -> Optional[dict]:
    org = await get_organization(org_id)
    if not org:
        return None
    now = datetime.now(timezone.utc)
    normalized_subscription_type = normalize_subscription_type(subscription_type)
    updates = {
        "status": "active",
        "subscription_type": normalized_subscription_type,
        "subscription_started_at": now,
        "subscription_ends_at": calculate_subscription_end_date(
            now,
            normalized_subscription_type,
        ),
        "updated_at": now,
    }
    object_id = _object_id(org_id)
    if object_id is None:
        return None
    await _organizations.update_one({"_id": object_id}, {"$set": updates})
    return await get_organization(org_id)

async def get_organization_member_count(org_id: str) -> int:
    return await _users.count_documents({"organization_id": org_id})


async def get_organization_member_counts(org_ids: list[str]) -> dict[str, int]:
    """Batch member counts for multiple organizations in a single aggregation."""
    if not org_ids:
        return {}
    pipeline = [
        {"$match": {"organization_id": {"$in": org_ids}}},
        {"$group": {"_id": "$organization_id", "count": {"$sum": 1}}},
    ]
    result: dict[str, int] = {}
    async for row in _users.aggregate(pipeline):
        if row.get("_id"):
            result[row["_id"]] = row["count"]
    return result


# ── User CRUD ──

async def create_user(
    email: str,
    password_hash: str,
    full_name: str,
    role: str,
    organization_id: Optional[str] = None,
    phone: Optional[str] = None,
    email_verified: bool = False,
    phone_verified: bool = False,
) -> dict:
    normalized_email = normalize_email(email)
    normalized_phone = normalize_phone(phone)
    if await get_user_by_email(normalized_email):
        raise ValueError("Cette adresse email existe déjà.")
    if normalized_phone and await get_user_by_phone(normalized_phone):
        raise ValueError("Ce numéro de téléphone existe déjà.")

    if role == "owner":
        if not organization_id:
            raise ValueError("Organization owner must belong to an organization")
        existing_owner = await _users.find_one(
            {"organization_id": organization_id, "role": "owner"},
            {"_id": 1},
        )
        if existing_owner:
            raise ValueError("Organization already has an owner")

    now = datetime.now(timezone.utc)
    doc = {
        "email": normalized_email,
        "phone": normalized_phone,
        "password_hash": password_hash,
        "full_name": full_name,
        "role": role,
        "organization_id": organization_id,
        "is_active": True,
        "email_verified": email_verified,
        "phone_verified": phone_verified,
        "last_login": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await _users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc

async def get_user_by_email(email: str) -> Optional[dict]:
    return await _users.find_one({"email": normalize_email(email)})

async def get_user_by_phone(phone: str) -> Optional[dict]:
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        return None
    return await _users.find_one({"phone": normalized_phone})

async def get_user_by_id(user_id: str) -> Optional[dict]:
    object_id = _object_id(user_id)
    if object_id is None:
        return None
    return await _users.find_one({"_id": object_id})

async def list_users_by_org(org_id: str, skip: int = 0, limit: int = 50) -> tuple[list[dict], int]:
    filt = {"organization_id": org_id}
    total = await _users.count_documents(filt)
    cursor = _users.find(filt).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return docs, total

async def get_organization_owner(org_id: str) -> Optional[dict]:
    return await _users.find_one({
        "organization_id": org_id,
        "role": "owner",
        "is_active": {"$ne": False},
    })

async def update_user(user_id: str, updates: dict) -> Optional[dict]:
    object_id = _object_id(user_id)
    if object_id is None:
        return None
    target = None
    if "role" in updates:
        target = await _users.find_one(
            {"_id": object_id},
            {"_id": 1, "organization_id": 1, "role": 1},
        )
        if not target:
            return None
        if target.get("role") == "owner" and updates["role"] != "owner":
            raise ValueError("Organization owner role cannot be changed")
        if updates["role"] == "owner":
            organization_id = updates.get("organization_id") or target.get("organization_id")
            if not organization_id:
                raise ValueError("Organization owner must belong to an organization")
            existing_owner = await _users.find_one(
                {
                    "organization_id": organization_id,
                    "role": "owner",
                    "_id": {"$ne": object_id},
                },
                {"_id": 1},
            )
            if existing_owner:
                raise ValueError("Organization already has an owner")
    updates["updated_at"] = datetime.now(timezone.utc)
    await _users.update_one({"_id": object_id}, {"$set": updates})
    return await get_user_by_id(user_id)

async def update_last_login(user_id: str) -> None:
    object_id = _object_id(user_id)
    if object_id is None:
        return
    await _users.update_one(
        {"_id": object_id},
        {"$set": {"last_login": datetime.now(timezone.utc)}},
    )

async def deactivate_user(user_id: str) -> None:
    object_id = _object_id(user_id)
    if object_id is None:
        return
    await _users.update_one(
        {"_id": object_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
    )


# ── Invitation CRUD ──

def generate_invitation_token() -> str:
    return secrets.token_urlsafe(32)

async def create_invitation(
    email: str,
    role: str,
    organization_id: str,
    invited_by: str,
    expires_hours: int = 72,
    status: str = "pending",
) -> dict:
    now = datetime.now(timezone.utc)
    token = generate_invitation_token()
    doc = {
        "email": email.lower().strip(),
        "role": role,
        "organization_id": organization_id,
        "invited_by": invited_by,
        "token": token,
        "status": status,
        "created_at": now,
        "expires_at": now + timedelta(hours=expires_hours),
    }
    result = await _invitations.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc

async def get_invitation_by_token(token: str) -> Optional[dict]:
    # Defence in depth: enforce the expiry check at the service layer so
    # any future caller cannot skip it accidentally.
    now = datetime.now(timezone.utc)
    return await _invitations.find_one(
        {"token": token, "status": "pending", "expires_at": {"$gt": now}}
    )

async def get_invitation_by_id(
    invitation_id: str,
    organization_id: str | None = None,
) -> Optional[dict]:
    object_id = _object_id(invitation_id)
    if object_id is None:
        return None
    query = {"_id": object_id}
    if organization_id:
        query["organization_id"] = organization_id
    return await _invitations.find_one(query)

async def list_invitations_by_org(org_id: str) -> tuple[list[dict], int]:
    filt = {"organization_id": org_id}
    total = await _invitations.count_documents(filt)
    cursor = _invitations.find(filt).sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    return docs, total

async def mark_invitation_accepted(invitation_id: str) -> None:
    object_id = _object_id(invitation_id)
    if object_id is None:
        return
    await _invitations.update_one(
        {"_id": object_id},
        {"$set": {"status": "accepted"}},
    )


async def claim_invitation(invitation_id: str) -> bool:
    """
    Atomically transition an invitation to ``accepted`` only if it is still
    ``pending``. Used to serialize concurrent ``/invitations/accept`` calls
    sharing the same token. Returns True if this caller won the claim.
    """
    object_id = _object_id(invitation_id)
    if object_id is None:
        return False
    result = await _invitations.update_one(
        {"_id": object_id, "status": "pending"},
        {"$set": {"status": "accepted"}},
    )
    return result.modified_count == 1

async def update_invitation_status(invitation_id: str, status: str) -> Optional[dict]:
    object_id = _object_id(invitation_id)
    if object_id is None:
        return None
    await _invitations.update_one(
        {"_id": object_id},
        {"$set": {"status": status}},
    )
    return await _invitations.find_one({"_id": object_id})

async def update_invitation_expiry(invitation_id: str, expires_hours: int = 72) -> None:
    object_id = _object_id(invitation_id)
    if object_id is None:
        return
    await _invitations.update_one(
        {"_id": object_id},
        {"$set": {"expires_at": datetime.now(timezone.utc) + timedelta(hours=expires_hours)}},
    )

async def revoke_invitation(
    invitation_id: str,
    organization_id: str | None = None,
) -> bool:
    object_id = _object_id(invitation_id)
    if object_id is None:
        return False
    query = {"_id": object_id}
    if organization_id:
        query["organization_id"] = organization_id
    result = await _invitations.update_one(
        query,
        {"$set": {"status": "revoked"}},
    )
    return result.modified_count > 0


# ── Super admin bootstrap ──

async def ensure_super_admin() -> None:
    settings = get_settings()
    if not settings.super_admin_email or not settings.super_admin_password:
        return
    existing = await get_user_by_email(settings.super_admin_email)
    if existing:
        return
    await create_user(
        email=settings.super_admin_email,
        password_hash=hash_password(settings.super_admin_password),
        full_name="Super Admin",
        role="super_admin",
        organization_id=None,
    )
    logger.info("Super admin account created: %s", settings.super_admin_email)


# ── Helpers ──

def serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "phone": user.get("phone"),
        "full_name": user["full_name"],
        "role": user["role"],
        "organization_id": user.get("organization_id"),
        "is_active": user.get("is_active", True),
        "email_verified": user.get("email_verified", False),
        "phone_verified": user.get("phone_verified", False),
        "last_login": user.get("last_login"),
        "created_at": user["created_at"],
    }

def serialize_organization(org: dict, member_count: int = 0) -> dict:
    subscription_type = normalize_subscription_type(org.get("subscription_type"))
    subscription_started_at = org.get("subscription_started_at") or org.get("created_at")
    subscription_ends_at = org.get("subscription_ends_at")
    if subscription_started_at and not subscription_ends_at:
        subscription_ends_at = calculate_subscription_end_date(
            subscription_started_at,
            subscription_type,
        )

    return {
        "id": str(org["_id"]),
        "name": org["name"],
        "sector": org["sector"],
        "size": org.get("size"),
        "employees": org.get("employees"),
        "activities": org.get("activities"),
        "country": org.get("country"),
        "jurisdiction": org.get("jurisdiction", "tunisia"),
        "needs": org.get("needs", []),
        "logo_url": org.get("logo_url"),
        "status": org.get("status", "active"),
        "rejection_reason": org.get("rejection_reason"),
        "requested_by_email": org.get("requested_by_email"),
        "requested_by_phone": org.get("requested_by_phone"),
        "contact_email_verified": org.get("contact_email_verified", False),
        "contact_phone_verified": org.get("contact_phone_verified", False),
        "approved_at": org.get("approved_at"),
        "approved_by": org.get("approved_by"),
        "subscription_type": subscription_type,
        "subscription_started_at": subscription_started_at,
        "subscription_ends_at": subscription_ends_at,
        "member_count": member_count,
        "created_at": org["created_at"],
        "updated_at": org["updated_at"],
    }

def serialize_invitation(inv: dict, org_name: Optional[str] = None) -> dict:
    return {
        "id": str(inv["_id"]),
        "email": inv["email"],
        "role": inv["role"],
        "organization_id": inv["organization_id"],
        "organization_name": org_name,
        "invited_by": inv["invited_by"],
        "status": inv["status"],
        "created_at": inv["created_at"],
        "expires_at": inv["expires_at"],
    }


# ── Refresh token blacklist ──

_token_blacklist = mongo_db["token_blacklist"]

async def blacklist_token(jti: str, user_id: str, expires_at: datetime) -> None:
    await _token_blacklist.insert_one({
        "jti": jti,
        "user_id": user_id,
        "expires_at": expires_at,
        "blacklisted_at": datetime.now(timezone.utc),
    })

async def is_token_blacklisted(jti: str, user_id: str | None = None, iat: datetime | None = None) -> bool:
    if await _token_blacklist.find_one({"jti": jti}) is not None:
        return True
    if user_id and iat:
        revoke_doc = await _token_blacklist.find_one({
            "user_id": user_id,
            "revoke_all_before": {"$exists": True, "$gte": iat},
        })
        if revoke_doc:
            return True
    return False

async def blacklist_all_user_tokens(user_id: str) -> int:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=get_settings().jwt_refresh_token_expire_days)
    result = await _token_blacklist.insert_one({
        "jti": f"all-{user_id}-{now.timestamp()}",
        "user_id": user_id,
        "expires_at": expires,
        "blacklisted_at": now,
        "revoke_all_before": now,
    })
    return 1 if result.inserted_id else 0


# ── Password reset ──

_password_resets = mongo_db["password_reset_tokens"]

async def create_password_reset_token(email: str) -> Optional[str]:
    user = await get_user_by_email(email)
    if not user:
        return None
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    await _password_resets.delete_many({"email": email.lower().strip()})
    await _password_resets.insert_one({
        "token": token,
        "email": email.lower().strip(),
        "user_id": str(user["_id"]),
        "created_at": now,
        "expires_at": now + timedelta(hours=1),
        "used": False,
    })
    return token

async def validate_reset_token(token: str) -> Optional[dict]:
    doc = await _password_resets.find_one({"token": token, "used": False})
    if not doc:
        return None
    if _as_utc(doc["expires_at"]) < datetime.now(timezone.utc):
        return None
    return doc

async def use_reset_token(token: str, new_password_hash: str) -> bool:
    doc = await validate_reset_token(token)
    if not doc:
        return False
    user_id = doc["user_id"]
    await update_user(user_id, {"password_hash": new_password_hash})
    await _password_resets.update_one(
        {"token": token},
        {"$set": {"used": True, "used_at": datetime.now(timezone.utc)}},
    )
    await blacklist_all_user_tokens(user_id)
    return True
