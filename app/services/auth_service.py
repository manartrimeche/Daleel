"""
Authentication service: password hashing, JWT tokens, user/org/invitation CRUD.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from bson import ObjectId
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.database import mongo_db

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_users = mongo_db["users"]
_organizations = mongo_db["organizations"]
_invitations = mongo_db["invitations"]


# ── Password helpers ──

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ──

def create_access_token(user_id: str, role: str, org_id: Optional[str] = None) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "org_id": org_id,
        "type": "access",
        "exp": expires,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expires,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


# ── Organization CRUD ──

async def create_organization(
    name: str,
    sector: str,
    size: Optional[str] = None,
    employees: Optional[int] = None,
    activities: Optional[str] = None,
    jurisdiction: str = "tunisia",
    logo_url: Optional[str] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    doc = {
        "name": name,
        "sector": sector,
        "size": size,
        "employees": employees,
        "activities": activities,
        "jurisdiction": jurisdiction,
        "logo_url": logo_url,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    result = await _organizations.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc

async def get_organization(org_id: str) -> Optional[dict]:
    return await _organizations.find_one({"_id": ObjectId(org_id)})

async def list_organizations(skip: int = 0, limit: int = 50) -> tuple[list[dict], int]:
    total = await _organizations.count_documents({})
    cursor = _organizations.find().sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return docs, total

async def update_organization(org_id: str, updates: dict) -> Optional[dict]:
    updates["updated_at"] = datetime.now(timezone.utc)
    await _organizations.update_one({"_id": ObjectId(org_id)}, {"$set": updates})
    return await get_organization(org_id)

async def get_organization_member_count(org_id: str) -> int:
    return await _users.count_documents({"organization_id": org_id})


# ── User CRUD ──

async def create_user(
    email: str,
    password_hash: str,
    full_name: str,
    role: str,
    organization_id: Optional[str] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    doc = {
        "email": email.lower().strip(),
        "password_hash": password_hash,
        "full_name": full_name,
        "role": role,
        "organization_id": organization_id,
        "is_active": True,
        "last_login": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await _users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc

async def get_user_by_email(email: str) -> Optional[dict]:
    return await _users.find_one({"email": email.lower().strip()})

async def get_user_by_id(user_id: str) -> Optional[dict]:
    return await _users.find_one({"_id": ObjectId(user_id)})

async def list_users_by_org(org_id: str, skip: int = 0, limit: int = 50) -> tuple[list[dict], int]:
    filt = {"organization_id": org_id}
    total = await _users.count_documents(filt)
    cursor = _users.find(filt).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return docs, total

async def update_user(user_id: str, updates: dict) -> Optional[dict]:
    updates["updated_at"] = datetime.now(timezone.utc)
    await _users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    return await get_user_by_id(user_id)

async def update_last_login(user_id: str) -> None:
    await _users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"last_login": datetime.now(timezone.utc)}},
    )

async def deactivate_user(user_id: str) -> None:
    await _users.update_one(
        {"_id": ObjectId(user_id)},
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
) -> dict:
    now = datetime.now(timezone.utc)
    token = generate_invitation_token()
    doc = {
        "email": email.lower().strip(),
        "role": role,
        "organization_id": organization_id,
        "invited_by": invited_by,
        "token": token,
        "status": "pending",
        "created_at": now,
        "expires_at": now + timedelta(hours=expires_hours),
    }
    result = await _invitations.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc

async def get_invitation_by_token(token: str) -> Optional[dict]:
    return await _invitations.find_one({"token": token, "status": "pending"})

async def list_invitations_by_org(org_id: str) -> tuple[list[dict], int]:
    filt = {"organization_id": org_id}
    total = await _invitations.count_documents(filt)
    cursor = _invitations.find(filt).sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    return docs, total

async def mark_invitation_accepted(invitation_id: str) -> None:
    await _invitations.update_one(
        {"_id": ObjectId(invitation_id)},
        {"$set": {"status": "accepted"}},
    )

async def revoke_invitation(invitation_id: str) -> None:
    await _invitations.update_one(
        {"_id": ObjectId(invitation_id)},
        {"$set": {"status": "revoked"}},
    )


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
        "full_name": user["full_name"],
        "role": user["role"],
        "organization_id": user.get("organization_id"),
        "is_active": user.get("is_active", True),
        "last_login": user.get("last_login"),
        "created_at": user["created_at"],
    }

def serialize_organization(org: dict, member_count: int = 0) -> dict:
    return {
        "id": str(org["_id"]),
        "name": org["name"],
        "sector": org["sector"],
        "size": org.get("size"),
        "employees": org.get("employees"),
        "activities": org.get("activities"),
        "jurisdiction": org.get("jurisdiction", "tunisia"),
        "logo_url": org.get("logo_url"),
        "status": org.get("status", "active"),
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
