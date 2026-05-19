"""
Authentication & user management routes.

POST /auth/register          — Create account + organization (owner)
POST /auth/login             — Login, get JWT tokens
POST /auth/refresh           — Refresh access token
GET  /auth/me                — Current user profile
PUT  /auth/me/password       — Change password

GET  /auth/organizations                 — List orgs (super_admin)
GET  /auth/organizations/{id}            — Org details
PUT  /auth/organizations/{id}            — Update org (owner/super_admin)

GET  /auth/organizations/{id}/users      — List org members (admin+)
PUT  /auth/users/{id}                    — Update user role/status (admin+)
DELETE /auth/users/{id}                  — Deactivate user (admin+)

POST /auth/invitations                   — Invite user (admin+)
GET  /auth/invitations                   — List org invitations (admin+)
POST /auth/invitations/accept            — Accept invitation + create account
DELETE /auth/invitations/{id}            — Revoke invitation (admin+)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import get_current_user, require_role
from app.config import get_settings
from app.database import mongo_db
from app.services import auth_service
from app.services.email_service import send_invitation_email
from app.services.notification_service import create_notification
from app.schemas_auth import (
    AcceptInvitationRequest,
    ChangePasswordRequest,
    InvitationCreate,
    InvitationListOut,
    InvitationOut,
    LoginRequest,
    OrganizationListOut,
    OrganizationOut,
    OrganizationUpdate,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserListOut,
    UserOut,
    UserUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


# ── Register ──

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest):
    existing = await auth_service.get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    org = await auth_service.create_organization(
        name=body.organization_name,
        sector=body.sector,
        size=body.size,
        employees=body.employees,
        jurisdiction=body.jurisdiction,
        subscription_type=body.subscription_type,
        status="pending_approval",
    )
    org_id = str(org["_id"])

    user = await auth_service.create_user(
        email=body.email,
        password_hash=auth_service.hash_password(body.password),
        full_name=body.full_name,
        role="owner",
        organization_id=org_id,
    )
    user_id = str(user["_id"])

    await auth_service.update_last_login(user_id)
    await create_notification(
        mongo_db,
        alert_type="approval_organization",
        title="Nouvelle inscription entreprise",
        message=(
            f"L'entreprise « {org['name']} » demande l'activation de son compte. "
            "Une approbation super admin est requise."
        ),
        details={
            "target_type": "organization",
            "organization_id": org_id,
            "organization_name": org["name"],
            "requested_by": user_id,
            "requested_by_email": user["email"],
            "approval_status": "pending_approval",
        },
    )

    settings = get_settings()
    access_token = auth_service.create_access_token(user_id, "owner", org_id)
    refresh_token = auth_service.create_refresh_token(user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserOut(
            **auth_service.serialize_user(user),
            organization_name=org["name"],
            organization_status=org.get("status"),
        ),
    )


# ── Login ──

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = await auth_service.get_user_by_email(body.email)
    if not user or not auth_service.verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account deactivated")

    user_id = str(user["_id"])
    org_id = user.get("organization_id")
    await auth_service.update_last_login(user_id)

    org_name = None
    org_status = None
    if org_id:
        org = await auth_service.get_organization(org_id)
        if org:
            org_name = org["name"]
            org_status = org.get("status", "active")
            if org_status == "pending_approval":
                raise HTTPException(
                    status_code=403,
                    detail="Votre inscription entreprise est en attente d'approbation par le super admin.",
                )
            if org_status == "rejected":
                raise HTTPException(
                    status_code=403,
                    detail="Votre inscription entreprise a été refusée par le super admin.",
                )
            if org_status != "active":
                raise HTTPException(
                    status_code=403,
                    detail="Votre entreprise n'est pas active.",
                )

    # Notify super_admin of login activity
    await create_notification(
        mongo_db,
        alert_type="account_login",
        title="Connexion utilisateur",
        message=(
            f"{user.get('full_name') or user.get('email')} "
            f"({user.get('role', 'member')}) s'est connecté"
            f"{' — ' + org_name if org_name else ''}."
        ),
        details={
            "target_type": "account_activity",
            "activity": "login",
            "user_id": user_id,
            "email": user.get("email"),
            "role": user.get("role"),
            "organization_name": org_name,
        },
    )

    settings = get_settings()
    access_token = auth_service.create_access_token(user_id, user["role"], org_id)
    refresh_token = auth_service.create_refresh_token(user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserOut(
            **auth_service.serialize_user(user),
            organization_name=org_name,
            organization_status=org_status,
        ),
    )


# ── Refresh ──

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest):
    try:
        payload = auth_service.decode_token(body.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user = await auth_service.get_user_by_id(payload["sub"])
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    user_id = str(user["_id"])
    org_id = user.get("organization_id")

    org_name = None
    org_status = None
    if org_id:
        org = await auth_service.get_organization(org_id)
        if org:
            org_name = org["name"]
            org_status = org.get("status", "active")

    settings = get_settings()
    access_token = auth_service.create_access_token(user_id, user["role"], org_id)
    new_refresh = auth_service.create_refresh_token(user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserOut(
            **auth_service.serialize_user(user),
            organization_name=org_name,
            organization_status=org_status,
        ),
    )


# ── Current user ──

@router.get("/me", response_model=UserOut)
async def get_me(user: dict = Depends(get_current_user)):
    org_name = None
    org_status = None
    if user.get("organization_id"):
        org = await auth_service.get_organization(user["organization_id"])
        if org:
            org_name = org["name"]
            org_status = org.get("status", "active")
    return UserOut(
        **auth_service.serialize_user(user),
        organization_name=org_name,
        organization_status=org_status,
    )


@router.put("/me/password")
async def change_password(body: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    if not auth_service.verify_password(body.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hash = auth_service.hash_password(body.new_password)
    await auth_service.update_user(str(user["_id"]), {"password_hash": new_hash})
    return {"message": "Password updated"}


# ── Organizations (super_admin) ──

@router.get("/organizations", response_model=OrganizationListOut)
async def list_organizations(
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(require_role("super_admin")),
):
    orgs, total = await auth_service.list_organizations(skip, limit)
    items = []
    for org in orgs:
        count = await auth_service.get_organization_member_count(str(org["_id"]))
        items.append(OrganizationOut(**auth_service.serialize_organization(org, count)))
    return OrganizationListOut(organizations=items, total=total)


@router.get("/organizations/{org_id}", response_model=OrganizationOut)
async def get_organization(org_id: str, user: dict = Depends(get_current_user)):
    if user["role"] != "super_admin" and user.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    org = await auth_service.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    count = await auth_service.get_organization_member_count(org_id)
    return OrganizationOut(**auth_service.serialize_organization(org, count))


@router.put("/organizations/{org_id}", response_model=OrganizationOut)
async def update_organization(
    org_id: str,
    body: OrganizationUpdate,
    user: dict = Depends(get_current_user),
):
    if user["role"] == "super_admin":
        pass
    elif user.get("organization_id") == org_id and user["role"] == "owner":
        pass
    else:
        raise HTTPException(status_code=403, detail="Only owner or super_admin can update organization")

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    org = await auth_service.update_organization(org_id, updates)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    count = await auth_service.get_organization_member_count(org_id)
    return OrganizationOut(**auth_service.serialize_organization(org, count))


# ── User management (org admin+) ──

@router.get("/organizations/{org_id}/users", response_model=UserListOut)
async def list_org_users(
    org_id: str,
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    if user["role"] != "super_admin" and user.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if user["role"] not in ("super_admin", "owner", "admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    users, total = await auth_service.list_users_by_org(org_id, skip, limit)
    org = await auth_service.get_organization(org_id)
    org_name = org["name"] if org else None

    items = [
        UserOut(**auth_service.serialize_user(u), organization_name=org_name)
        for u in users
    ]
    return UserListOut(users=items, total=total)


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    body: UserUpdate,
    current_user: dict = Depends(get_current_user),
):
    target = await auth_service.get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user["role"] == "super_admin":
        pass
    elif current_user.get("organization_id") == target.get("organization_id"):
        if current_user["role"] not in ("owner", "admin"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        if target["role"] == "owner" and str(current_user["_id"]) != user_id:
            raise HTTPException(status_code=403, detail="Cannot modify owner")
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updated = await auth_service.update_user(user_id, updates)

    # Notify super_admin of account modification
    changes_desc = []
    if "role" in updates:
        changes_desc.append(f"rôle → {updates['role']}")
    if "is_active" in updates:
        changes_desc.append("activé" if updates["is_active"] else "désactivé")
    await create_notification(
        mongo_db,
        alert_type="account_updated",
        title="Modification de compte",
        message=(
            f"Le compte de {target.get('full_name') or target.get('email')} "
            f"a été modifié par {current_user.get('full_name') or current_user.get('email')} : "
            f"{', '.join(changes_desc) or 'mise à jour'}."
        ),
        details={
            "target_type": "account_activity",
            "activity": "update",
            "user_id": user_id,
            "email": target.get("email"),
            "changes": updates,
            "modified_by": str(current_user["_id"]),
        },
    )

    org_name = None
    if updated.get("organization_id"):
        org = await auth_service.get_organization(updated["organization_id"])
        if org:
            org_name = org["name"]
    return UserOut(**auth_service.serialize_user(updated), organization_name=org_name)


@router.delete("/users/{user_id}")
async def deactivate_user(user_id: str, current_user: dict = Depends(get_current_user)):
    target = await auth_service.get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target["role"] == "owner":
        raise HTTPException(status_code=400, detail="Cannot deactivate organization owner")
    if current_user["role"] == "super_admin":
        pass
    elif current_user.get("organization_id") == target.get("organization_id"):
        if current_user["role"] not in ("owner", "admin"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    await auth_service.deactivate_user(user_id)

    # Notify super_admin of account deactivation
    await create_notification(
        mongo_db,
        alert_type="account_deactivated",
        title="Compte désactivé",
        message=(
            f"Le compte de {target.get('full_name') or target.get('email')} "
            f"a été désactivé par {current_user.get('full_name') or current_user.get('email')}."
        ),
        details={
            "target_type": "account_activity",
            "activity": "deactivation",
            "user_id": user_id,
            "email": target.get("email"),
            "deactivated_by": str(current_user["_id"]),
        },
    )

    return {"message": "User deactivated"}


# ── Invitations ──

@router.post("/invitations", response_model=InvitationOut, status_code=201)
async def create_invitation(
    body: InvitationCreate,
    user: dict = Depends(get_current_user),
):
    if user["role"] not in ("super_admin", "owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owner/admin can invite users")
    org_id = user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization associated")

    existing_user = await auth_service.get_user_by_email(body.email)
    if existing_user:
        if existing_user.get("organization_id") == org_id:
            detail = "Cette adresse email est deja membre de votre organisation."
        else:
            detail = (
                "Cette adresse email est deja associee a un compte Daleel. "
                "Utilisez une autre adresse email."
            )
        raise HTTPException(status_code=409, detail=detail)

    org = await auth_service.get_organization(org_id)
    org_name = org["name"] if org else "Organisation"
    inv = await auth_service.create_invitation(
        email=body.email,
        role="member",
        organization_id=org_id,
        invited_by=str(user["_id"]),
        status="pending_approval",
    )

    await create_notification(
        mongo_db,
        alert_type="approval_invitation",
        title="Invitation membre à approuver",
        message=(
            f"L'entreprise « {org_name} » souhaite inviter {body.email}. "
            "Une approbation super admin est requise avant l'envoi."
        ),
        details={
            "target_type": "invitation",
            "invitation_id": str(inv["_id"]),
            "organization_id": org_id,
            "organization_name": org_name,
            "email": body.email,
            "requested_by": str(user["_id"]),
            "approval_status": "pending_approval",
        },
    )

    return InvitationOut(**auth_service.serialize_invitation(inv, org_name))


@router.get("/invitations", response_model=InvitationListOut)
async def list_invitations(user: dict = Depends(get_current_user)):
    if user["role"] not in ("super_admin", "owner", "admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    org_id = user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization associated")

    org = await auth_service.get_organization(org_id)
    org_name = org["name"] if org else None
    invitations, total = await auth_service.list_invitations_by_org(org_id)
    items = [InvitationOut(**auth_service.serialize_invitation(i, org_name)) for i in invitations]
    return InvitationListOut(invitations=items, total=total)


@router.post("/invitations/accept", response_model=TokenResponse, status_code=201)
async def accept_invitation(body: AcceptInvitationRequest):
    inv = await auth_service.get_invitation_by_token(body.token)
    if not inv:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")
    if _as_utc(inv["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Invitation expired")

    existing = await auth_service.get_user_by_email(inv["email"])
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Cette adresse email est deja associee a un compte Daleel.",
        )

    org_id = inv["organization_id"]
    user = await auth_service.create_user(
        email=inv["email"],
        password_hash=auth_service.hash_password(body.password),
        full_name=body.full_name,
        role=inv["role"],
        organization_id=org_id,
    )
    await auth_service.mark_invitation_accepted(str(inv["_id"]))

    user_id = str(user["_id"])
    await auth_service.update_last_login(user_id)

    org = await auth_service.get_organization(org_id)
    org_name = org["name"] if org else None

    settings = get_settings()
    access_token = auth_service.create_access_token(user_id, inv["role"], org_id)
    refresh_token = auth_service.create_refresh_token(user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserOut(**auth_service.serialize_user(user), organization_name=org_name),
    )


@router.delete("/invitations/{invitation_id}")
async def revoke_invitation(invitation_id: str, user: dict = Depends(get_current_user)):
    if user["role"] not in ("super_admin", "owner", "admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    await auth_service.revoke_invitation(invitation_id)

    await create_notification(
        mongo_db,
        alert_type="invitation_revoked",
        title="Invitation révoquée",
        message=(
            f"Une invitation a été révoquée par "
            f"{user.get('full_name') or user.get('email')}."
        ),
        details={
            "target_type": "account_activity",
            "activity": "invitation_revoked",
            "invitation_id": invitation_id,
            "revoked_by": str(user["_id"]),
        },
    )

    return {"message": "Invitation revoked"}
