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
PATCH /auth/organizations/{id}/status    — Manual status update (super_admin)
POST /auth/organizations/{id}/renew      — Renew subscription (super_admin)

GET  /auth/organizations/{id}/users      — List org members (admin+)
PUT  /auth/users/{id}                    — Update user role/status (admin+)
DELETE /auth/users/{id}                  — Deactivate user (admin+)

POST /auth/invitations                   — Invite user (admin+)
GET  /auth/invitations                   — List org invitations (admin+)
POST /auth/invitations/accept            — Accept invitation + create account
DELETE /auth/invitations/{id}            — Revoke invitation (admin+)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Body, Cookie, Depends, HTTPException, Request, Response
from pymongo.errors import DuplicateKeyError

from app.limiter import limiter

from app.api.auth import get_current_user, require_role
from app.config import get_settings
from app.database import mongo_db
from app.services import auth_service
from app.services.notification_service import create_notification as _create_notification
from app.schemas_auth import (
    AcceptInvitationRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    InvitationCreate,
    InvitationListOut,
    InvitationOut,
    LoginRequest,
    OrganizationListOut,
    OrganizationOut,
    OrganizationRejectRequest,
    OrganizationRenewRequest,
    OrganizationStatusUpdate,
    OrganizationUpdate,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    SendPhoneOTPRequest,
    TokenResponse,
    UserListOut,
    UserOut,
    UserUpdate,
    VerifyEmailRequest,
    VerifyPhoneRequest,
)
from app.services import verification_service
from app.services.email_service import send_login_security_email, send_verification_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# ── Refresh token cookie (P2 hardening) ──
# The refresh token lives in an HttpOnly cookie to keep it out of reach of
# any XSS payload that might land in the SPA. The access token stays in
# memory / localStorage (acceptable: 30 min lifetime + revocable via jti).
REFRESH_COOKIE_NAME = "daleel_refresh"


def _set_refresh_cookie(response: Response, request: Request, token: str) -> None:
    settings = get_settings()
    is_https = request.url.scheme == "https"
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.jwt_refresh_token_expire_days * 24 * 3600,
        httponly=True,
        secure=is_https,
        samesite="strict",
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/v1/auth",
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


async def _owner_recipient_details(
    organization_id: str | None,
    *,
    exclude_user_id: str | None = None,
) -> dict[str, str]:
    if not organization_id:
        return {}
    owner = await auth_service.get_organization_owner(organization_id)
    if not owner:
        return {}
    owner_id = str(owner["_id"])
    if exclude_user_id and owner_id == exclude_user_id:
        return {}
    return {
        "recipient_user_id": owner_id,
        "recipient_role": "owner",
    }


def _request_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else "inconnue"


def _request_user_agent(request: Request) -> str:
    return (request.headers.get("user-agent") or "inconnu")[:300]


_OWNER_ACTIVITY_ALERT_TYPES = frozenset({
    "account_login",
    "account_updated",
    "account_deactivated",
    "member_joined",
    "invitation_revoked",
    "organization_approved",
    "organization_rejected",
    "subscription_expiring",
})


async def create_notification(
    db,
    *,
    alert_type: str,
    profile_id=None,
    profile_name=None,
    title: str,
    message: str,
    details: dict | None = None,
):
    details = dict(details or {})
    if alert_type == "account_login":
        owner_recipient = await _owner_recipient_details(
            details.get("organization_id"),
            exclude_user_id=details.get("user_id"),
        )
        if not owner_recipient:
            return {}
        details.update(owner_recipient)
    elif alert_type in _OWNER_ACTIVITY_ALERT_TYPES and details.get("organization_id"):
        owner_recipient = await _owner_recipient_details(
            details.get("organization_id"),
        )
        details.update(owner_recipient)
    return await _create_notification(
        db,
        alert_type=alert_type,
        profile_id=profile_id,
        profile_name=profile_name,
        title=title,
        message=message,
        details=details,
    )


# ── Register ──

@router.post("/register", response_model=RegisterResponse, status_code=201)
@limiter.limit("3/minute")
async def register(request: Request, body: RegisterRequest, background_tasks: BackgroundTasks):
    """
    Inscription d'une nouvelle entreprise.

    Le compte est créé en ``pending_approval`` et ne reçoit AUCUN token.
    Trois étapes restent à franchir avant d'avoir accès :
      1. Vérification email (lien envoyé).
      2. Vérification téléphone (OTP SMS envoyé sur demande).
      3. Approbation par le super admin.
    """
    if (
        await auth_service.get_user_by_email(body.email)
        or await auth_service.get_organization_by_requested_email(body.email)
    ):
        raise HTTPException(
            status_code=409,
            detail="Cette adresse email existe déjà.",
        )

    if (
        await auth_service.get_user_by_phone(body.phone)
        or await auth_service.get_organization_by_phone(body.phone)
    ):
        raise HTTPException(status_code=409, detail="Ce numéro de téléphone existe déjà.")

    if await auth_service.get_organization_by_name(body.organization_name):
        raise HTTPException(status_code=409, detail="Le nom de l'entreprise existe déjà.")

    try:
        org = await auth_service.create_organization(
            name=body.organization_name,
            sector=body.sector,
            size=body.size,
            employees=body.employees,
            activities=body.activities,
            country=body.country,
            jurisdiction=body.jurisdiction,
            needs=body.needs,
            requested_by_email=body.email,
            requested_by_phone=body.phone,
            subscription_type=body.subscription_type,
            status="pending_approval",
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Ces informations existent déjà.")
    org_id = str(org["_id"])

    try:
        user = await auth_service.create_user(
            email=body.email,
            phone=body.phone,
            password_hash=auth_service.hash_password(body.password),
            full_name=body.full_name,
            role="owner",
            organization_id=org_id,
            email_verified=False,
            phone_verified=False,
        )
    except ValueError as exc:
        await mongo_db["organizations"].delete_one({"_id": org["_id"]})
        raise HTTPException(status_code=409, detail=str(exc))
    except DuplicateKeyError:
        await mongo_db["organizations"].delete_one({"_id": org["_id"]})
        raise HTTPException(status_code=409, detail="Ces informations existent déjà.")
    user_id = str(user["_id"])

    # Envoi du lien de vérification email (fire-and-forget).
    email_token = await verification_service.create_email_verification_token(
        user_id, body.email
    )
    background_tasks.add_task(send_verification_email, body.email, email_token)

    # Envoi de l'OTP téléphone.
    otp = await verification_service.create_phone_otp(user_id, body.phone)
    background_tasks.add_task(
        verification_service.send_phone_otp, user_id, body.phone, otp
    )

    # Notification super admin.
    await create_notification(
        mongo_db,
        alert_type="approval_organization",
        title="Nouvelle inscription entreprise",
        message=(
            f"L'entreprise « {org['name']} » demande l'activation de son compte. "
            "Vérifications email/téléphone et approbation super admin requises."
        ),
        details={
            "target_type": "organization",
            "organization_id": org_id,
            "organization_name": org["name"],
            "country": body.country,
            "sector": body.sector,
            "needs": body.needs,
            "requested_by": user_id,
            "requested_by_email": user["email"],
            "requested_by_phone": body.phone,
            "approval_status": "pending_approval",
            "audience": "super_admin",
        },
    )

    return RegisterResponse(
        user_id=user_id,
        organization_id=org_id,
        email=body.email,
        phone=body.phone,
        message=(
            "Inscription enregistrée. Vérifiez votre email et votre téléphone, "
            "puis attendez l'approbation du super administrateur."
        ),
    )


# ── Vérification email / téléphone ──

@router.post("/verify-email", status_code=200)
@limiter.limit("10/minute")
async def verify_email(request: Request, body: VerifyEmailRequest):
    user = await verification_service.consume_email_token(body.token)
    if not user:
        raise HTTPException(status_code=400, detail="Lien invalide ou expiré.")
    return {
        "message": "Email vérifié avec succès.",
        "user_id": str(user["_id"]),
        "email_verified": True,
    }


@router.post("/verify-phone/send", status_code=200)
@limiter.limit("3/minute")
async def send_phone_otp(request: Request, body: SendPhoneOTPRequest, background_tasks: BackgroundTasks):
    user = await auth_service.get_user_by_id(body.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    if user.get("phone_verified"):
        return {"message": "Téléphone déjà vérifié.", "already_verified": True}
    phone = user.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="Aucun téléphone associé au compte.")

    code = await verification_service.create_phone_otp(body.user_id, phone)
    background_tasks.add_task(verification_service.send_phone_otp, body.user_id, phone, code)
    return {"message": "Code envoyé.", "ttl_minutes": verification_service.PHONE_OTP_TTL_MINUTES}


@router.post("/verify-phone", status_code=200)
@limiter.limit("10/minute")
async def verify_phone(request: Request, body: VerifyPhoneRequest):
    ok = await verification_service.verify_phone_otp(body.user_id, body.code)
    if not ok:
        raise HTTPException(status_code=400, detail="Code invalide, expiré ou trop de tentatives.")
    return {"message": "Téléphone vérifié avec succès.", "phone_verified": True}


# ── Login ──

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, response: Response, body: LoginRequest, background_tasks: BackgroundTasks):
    user = await auth_service.get_user_by_email(body.email)
    if not user:
        # Run verify_password against a dummy hash to preserve constant-time
        # behaviour even on unknown emails (prevents user enumeration).
        await asyncio.to_thread(
            auth_service.verify_password, body.password,
            "$2b$12$eImiTXuWVxfM37uY4JANjQ" + "x" * 31,
        )
        # P10: trace failed authentication attempts for audit purposes.
        logger.warning(
            "auth.login_failed reason=unknown_email email=%s ip=%s",
            body.email, request.client.host if request.client else "?",
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # bcrypt.verify is CPU-bound — run in a thread pool to avoid blocking
    # the async event loop and delaying every other concurrent request.
    password_ok = await asyncio.to_thread(
        auth_service.verify_password, body.password, user["password_hash"]
    )
    if not password_ok:
        logger.warning(
            "auth.login_failed reason=bad_password user_id=%s ip=%s",
            str(user["_id"]), request.client.host if request.client else "?",
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.get("is_active", True):
        logger.warning("auth.login_blocked reason=deactivated user_id=%s", str(user["_id"]))
        raise HTTPException(status_code=403, detail="Account deactivated")

    user_id = str(user["_id"])
    org_id = user.get("organization_id")
    # Fire-and-forget: updating last_login does not need to block the response.
    background_tasks.add_task(auth_service.update_last_login, user_id)

    org_name = None
    org_status = None
    if org_id:
        org = await auth_service.get_organization(org_id)
        if org:
            org = await auth_service.expire_organization_if_needed(org)
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
            if org_status == "inactive" and auth_service.is_subscription_expired(org):
                raise HTTPException(
                    status_code=403,
                    detail="Votre abonnement a expiré. Veuillez contacter le super admin pour le renouveler.",
                )
            if org_status != "active":
                raise HTTPException(
                    status_code=403,
                    detail="Votre entreprise n'est pas active.",
                )

    # Check subscription expiration for owner
    if user.get("role") == "owner" and org_id and org:
        sub_end = org.get("subscription_ends_at")
        if sub_end:
            now = datetime.now(timezone.utc)
            if isinstance(sub_end, str):
                sub_end = datetime.fromisoformat(sub_end)
            if sub_end.tzinfo is None:
                sub_end = sub_end.replace(tzinfo=timezone.utc)
            days_left = (sub_end - now).days
            if 0 <= days_left <= 3:
                existing = await mongo_db["notifications"].find_one({
                    "alert_type": "subscription_expiring",
                    "details.organization_id": org_id,
                    "read": False,
                })
                if not existing:
                    await create_notification(
                        mongo_db,
                        alert_type="subscription_expiring",
                        title="Abonnement bientôt expiré",
                        message=(
                            f"L'abonnement de « {org_name} » expire dans {days_left} jour(s). "
                            "Veuillez renouveler pour maintenir l'accès."
                        ),
                        details={
                            "target_type": "subscription",
                            "organization_id": org_id,
                            "organization_name": org_name,
                            "days_left": days_left,
                            "expires_at": sub_end.isoformat(),
                        },
                    )

    # Send a personal security email for the login. In-app login activity
    # stays reserved for the organization owner, not the logged-in user.
    login_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    login_ip = _request_ip(request)
    login_user_agent = _request_user_agent(request)
    background_tasks.add_task(
        send_login_security_email,
        user.get("email"),
        full_name=user.get("full_name") or user.get("email") or "",
        login_time=login_time,
        ip_address=login_ip,
        user_agent=login_user_agent,
    )

    background_tasks.add_task(
        create_notification,
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
            "organization_id": org_id,
            "organization_name": org_name,
            "ip_address": login_ip,
            "user_agent": login_user_agent,
            "login_time": login_time,
        },
    )

    settings = get_settings()
    access_token = auth_service.create_access_token(user_id, user["role"], org_id)
    refresh_token = auth_service.create_refresh_token(user_id)
    _set_refresh_cookie(response, request, refresh_token)

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
async def refresh_token(
    request: Request,
    response: Response,
    body: dict | None = Body(default=None),
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    # Prefer the HttpOnly cookie; fall back to body for legacy clients
    # (the cookie-based frontend posts ``{}`` so the body may be empty).
    body_token = body.get("refresh_token") if isinstance(body, dict) else None
    raw_token = refresh_cookie or body_token
    if not raw_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    try:
        payload = auth_service.decode_token(raw_token)
    except Exception:
        logger.warning("auth.refresh_failed reason=decode_error")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    jti = payload.get("jti")
    user_id_from_token = payload["sub"]
    iat_ts = payload.get("iat")
    iat_dt = datetime.fromtimestamp(iat_ts, tz=timezone.utc) if iat_ts else None
    if jti and await auth_service.is_token_blacklisted(jti, user_id_from_token, iat_dt):
        logger.warning("auth.refresh_failed reason=blacklisted user_id=%s", user_id_from_token)
        raise HTTPException(status_code=401, detail="Token has been revoked")

    user = await auth_service.get_user_by_id(user_id_from_token)
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    user_id = str(user["_id"])
    org_id = user.get("organization_id")

    if jti:
        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc)
        await auth_service.blacklist_token(jti, user_id, expires_at)

    org_name = None
    org_status = None
    if org_id:
        org = await auth_service.get_organization(org_id)
        if org:
            org = await auth_service.expire_organization_if_needed(org)
            org_name = org["name"]
            org_status = org.get("status", "active")
            if org_status == "inactive" and auth_service.is_subscription_expired(org):
                raise HTTPException(
                    status_code=403,
                    detail="Votre abonnement a expiré. Veuillez contacter le super admin pour le renouveler.",
                )
            if org_status not in (None, "active") and user.get("role") != "super_admin":
                raise HTTPException(status_code=403, detail="Votre entreprise n'est pas active.")

    settings = get_settings()
    access_token = auth_service.create_access_token(user_id, user["role"], org_id)
    new_refresh = auth_service.create_refresh_token(user_id)
    _set_refresh_cookie(response, request, new_refresh)

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


# ── Logout ──

@router.post("/logout", status_code=200)
async def logout(response: Response, user: dict = Depends(get_current_user)):
    """Blacklist all tokens for the current user, forcing re-login."""
    user_id = str(user["_id"])
    await auth_service.blacklist_all_user_tokens(user_id)
    _clear_refresh_cookie(response)
    return {"detail": "Déconnecté avec succès"}


# ── Current user ──

@router.get("/me", response_model=UserOut)
async def get_me(user: dict = Depends(get_current_user)):
    org_name = None
    org_status = None
    if user.get("organization_id"):
        org = await auth_service.get_organization(user["organization_id"])
        if org:
            org = await auth_service.expire_organization_if_needed(org)
            org_name = org["name"]
            org_status = org.get("status", "active")
    return UserOut(
        **auth_service.serialize_user(user),
        organization_name=org_name,
        organization_status=org_status,
    )


@router.put("/me/password")
@limiter.limit("3/minute")
async def change_password(
    request: Request,
    response: Response,
    body: ChangePasswordRequest,
    user: dict = Depends(get_current_user),
):
    # P4: bcrypt is CPU-bound; offload to a thread to avoid blocking the event loop.
    password_ok = await asyncio.to_thread(
        auth_service.verify_password, body.current_password, user["password_hash"]
    )
    if not password_ok:
        logger.warning("auth.change_password_failed user_id=%s", str(user["_id"]))
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hash = await asyncio.to_thread(auth_service.hash_password, body.new_password)
    await auth_service.update_user(str(user["_id"]), {"password_hash": new_hash})
    await auth_service.blacklist_all_user_tokens(str(user["_id"]))
    _clear_refresh_cookie(response)
    return {"message": "Password updated"}


# ── Password reset ──

@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest):
    token = await auth_service.create_password_reset_token(body.email)
    if token:
        from app.services.email_service import send_password_reset_email
        await send_password_reset_email(body.email, token)
    return {"message": "Si cette adresse existe, un email de réinitialisation a été envoyé."}


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, body: ResetPasswordRequest):
    new_hash = auth_service.hash_password(body.new_password)
    success = await auth_service.use_reset_token(body.token, new_hash)
    if not success:
        logger.warning(
            "auth.reset_password_failed reason=invalid_token ip=%s",
            request.client.host if request.client else "?",
        )
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")
    return {"message": "Mot de passe réinitialisé avec succès"}


# ── Organizations (super_admin) ──

@router.get("/organizations", response_model=OrganizationListOut)
async def list_organizations(
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(require_role("super_admin")),
):
    orgs, total = await auth_service.list_organizations(skip, limit)

    # Batch member counts in a single aggregation instead of N+1 queries
    org_ids = [str(org["_id"]) for org in orgs]
    member_counts = await auth_service.get_organization_member_counts(org_ids) if org_ids else {}

    items = []
    for org in orgs:
        org = await auth_service.expire_organization_if_needed(org)
        count = member_counts.get(str(org["_id"]), 0)
        items.append(OrganizationOut(**auth_service.serialize_organization(org, count)))
    return OrganizationListOut(organizations=items, total=total)


@router.get("/organizations/{org_id}", response_model=OrganizationOut)
async def get_organization(org_id: str, user: dict = Depends(get_current_user)):
    if user["role"] != "super_admin" and user.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    org = await auth_service.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    org = await auth_service.expire_organization_if_needed(org)
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
    try:
        org = await auth_service.update_organization(org_id, updates)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Ces informations existent déjà.")
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    count = await auth_service.get_organization_member_count(org_id)
    return OrganizationOut(**auth_service.serialize_organization(org, count))


@router.patch("/organizations/{org_id}/status", response_model=OrganizationOut)
async def update_organization_status(
    org_id: str,
    body: OrganizationStatusUpdate,
    user: dict = Depends(require_role("super_admin")),
):
    """Met à jour manuellement le statut opérationnel sans toucher au workflow d'inscription."""
    org = await auth_service.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    current_status = org.get("status")
    if current_status in {"pending_approval", "rejected"}:
        raise HTTPException(
            status_code=400,
            detail="Utilisez le workflow d'approbation/refus pour ce statut.",
        )

    updated = await auth_service.update_organization(org_id, {
        "status": body.status,
        "manual_status_updated_at": datetime.now(timezone.utc),
        "manual_status_updated_by": str(user["_id"]),
    })
    if not updated:
        raise HTTPException(status_code=404, detail="Organization not found")

    count = await auth_service.get_organization_member_count(org_id)
    return OrganizationOut(**auth_service.serialize_organization(updated, count))


@router.post("/organizations/{org_id}/approve", response_model=OrganizationOut)
async def approve_organization(
    org_id: str,
    user: dict = Depends(require_role("super_admin")),
):
    """Approuve une inscription en attente. Exige email + téléphone vérifiés."""
    org = await auth_service.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable.")
    if org.get("status") != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Statut actuel : {org.get('status')}. Seules les inscriptions en attente peuvent être approuvées.",
        )
    if not org.get("contact_email_verified") or not org.get("contact_phone_verified"):
        raise HTTPException(
            status_code=400,
            detail="Email et/ou téléphone du contact non vérifiés. Approbation impossible.",
        )

    now = datetime.now(timezone.utc)
    updated = await auth_service.update_organization(org_id, {
        "status": "active",
        "approved_at": now,
        "approved_by": str(user["_id"]),
        "rejection_reason": None,
    })

    # Notifier le demandeur (owner) que son compte est activé.
    await create_notification(
        mongo_db,
        alert_type="organization_approved",
        title="Compte entreprise activé",
        message=(
            f"L'inscription de « {updated['name']} » a été approuvée. "
            "Vous pouvez désormais vous connecter."
        ),
        details={
            "target_type": "organization",
            "organization_id": org_id,
            "organization_name": updated["name"],
            "approved_by": str(user["_id"]),
            "recipient_email": updated.get("requested_by_email"),
        },
    )

    count = await auth_service.get_organization_member_count(org_id)
    return OrganizationOut(**auth_service.serialize_organization(updated, count))


@router.post("/organizations/{org_id}/reject", response_model=OrganizationOut)
async def reject_organization(
    org_id: str,
    body: OrganizationRejectRequest,
    user: dict = Depends(require_role("super_admin")),
):
    """Refuse une inscription en attente avec un motif obligatoire."""
    org = await auth_service.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable.")
    if org.get("status") != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Statut actuel : {org.get('status')}. Seules les inscriptions en attente peuvent être refusées.",
        )

    updated = await auth_service.update_organization(org_id, {
        "status": "rejected",
        "rejection_reason": body.reason.strip(),
    })

    await create_notification(
        mongo_db,
        alert_type="organization_rejected",
        title="Inscription refusée",
        message=(
            f"L'inscription de « {updated['name']} » a été refusée. "
            f"Motif : {body.reason.strip()}"
        ),
        details={
            "target_type": "organization",
            "organization_id": org_id,
            "organization_name": updated["name"],
            "rejected_by": str(user["_id"]),
            "reason": body.reason.strip(),
            "recipient_email": updated.get("requested_by_email"),
        },
    )

    count = await auth_service.get_organization_member_count(org_id)
    return OrganizationOut(**auth_service.serialize_organization(updated, count))


@router.post("/organizations/{org_id}/renew", response_model=OrganizationOut)
async def renew_organization_subscription(
    org_id: str,
    body: OrganizationRenewRequest,
    user: dict = Depends(require_role("super_admin")),
):
    org = await auth_service.renew_organization_subscription(
        org_id,
        body.subscription_type,
    )
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
    if target["role"] == "owner" and "role" in updates and updates["role"] != "owner":
        raise HTTPException(status_code=400, detail="Cannot change organization owner role")
    try:
        updated = await auth_service.update_user(user_id, updates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

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
            "organization_id": target.get("organization_id"),
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
            "organization_id": target.get("organization_id"),
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
        # P13: do not leak whether the email exists or belongs to which org.
        # The detailed reason is logged server-side for the admin to inspect later.
        logger.info(
            "auth.invitation_rejected reason=email_exists target=%s same_org=%s by=%s",
            body.email,
            existing_user.get("organization_id") == org_id,
            str(user["_id"]),
        )
        raise HTTPException(
            status_code=409,
            detail="Invitation impossible pour cette adresse email.",
        )

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
async def accept_invitation(
    request: Request,
    response: Response,
    body: AcceptInvitationRequest,
    background_tasks: BackgroundTasks,
):
    inv = await auth_service.get_invitation_by_token(body.token)
    if not inv:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")
    if _as_utc(inv["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Invitation expired")

    existing = await auth_service.get_user_by_email(inv["email"])
    if existing:
        # P13: avoid revealing account-existence on the public accept endpoint.
        logger.info(
            "auth.invitation_accept_rejected reason=email_exists target=%s",
            inv["email"],
        )
        raise HTTPException(
            status_code=409,
            detail="Cette invitation ne peut plus être utilisée.",
        )

    # P7: atomically claim the invitation before creating the user. If a
    # concurrent request already claimed it, fail with 409 — never create
    # a second user (the unique email index would also block it).
    claimed = await auth_service.claim_invitation(str(inv["_id"]))
    if not claimed:
        raise HTTPException(
            status_code=409,
            detail="Cette invitation a déjà été utilisée.",
        )

    org_id = inv["organization_id"]
    try:
        password_hash = await asyncio.to_thread(auth_service.hash_password, body.password)
        user = await auth_service.create_user(
            email=inv["email"],
            password_hash=password_hash,
            full_name=body.full_name,
            role=inv["role"],
            organization_id=org_id,
        )
    except DuplicateKeyError:
        # Another flow created the user with this email between our checks.
        logger.warning(
            "auth.invitation_accept_race email=%s invitation_id=%s",
            inv["email"], str(inv["_id"]),
        )
        raise HTTPException(
            status_code=409,
            detail="Cette adresse email est déjà utilisée.",
        )

    user_id = str(user["_id"])
    background_tasks.add_task(auth_service.update_last_login, user_id)

    org = await auth_service.get_organization(org_id)
    org_name = org["name"] if org else None

    background_tasks.add_task(
        create_notification,
        mongo_db,
        alert_type="member_joined",
        title="Nouveau membre",
        message=(
            f"{body.full_name} a rejoint l'organisation « {org_name or 'N/A'} »."
        ),
        details={
            "target_type": "member_activity",
            "organization_id": org_id,
            "user_id": user_id,
            "email": inv["email"],
            "full_name": body.full_name,
        },
    )

    settings = get_settings()
    access_token = auth_service.create_access_token(user_id, inv["role"], org_id)
    refresh_token = auth_service.create_refresh_token(user_id)
    _set_refresh_cookie(response, request, refresh_token)

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
    org_scope = None if user["role"] == "super_admin" else user.get("organization_id")
    revoked = await auth_service.revoke_invitation(
        invitation_id,
        organization_id=org_scope,
    )
    if not revoked:
        raise HTTPException(status_code=404, detail="Invitation not found")

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
            "organization_id": org_scope,
            "revoked_by": str(user["_id"]),
        },
    )

    return {"message": "Invitation revoked"}
