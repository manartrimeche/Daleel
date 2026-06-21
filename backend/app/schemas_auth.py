"""
Pydantic schemas for authentication, users, organizations, and invitations.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Enums as literals ──

ROLE_CHOICES = ("super_admin", "owner", "admin", "member", "viewer")
SECTOR_CHOICES = (
    "finance", "banque", "assurance",
    "industrie", "manufacturing",
    "technologie", "telecom",
    "sante", "pharma",
    "transport", "logistique",
    "btp", "immobilier",
    "commerce", "distribution",
    "energie", "environnement",
    "education", "formation",
    "agriculture", "agroalimentaire",
    "tourisme", "hotellerie",
    "services", "conseil",
    "autre",
)
ORG_STATUS_CHOICES = ("active", "inactive", "suspended", "pending_approval", "rejected")
INVITATION_STATUS_CHOICES = ("pending", "accepted", "expired", "revoked", "pending_approval", "rejected")
SUBSCRIPTION_TYPE_CHOICES = ("monthly", "annual")

# E.164 international phone format: optional leading "+", 8 to 15 digits.
_PHONE_REGEX = r"^\+?[1-9]\d{7,14}$"

NEED_CHOICES = (
    "conformite",          # suivi conformité réglementaire
    "veille",              # veille juridique
    "contrats",            # analyse / rédaction contrats
    "audit",               # audit & risques
    "amendements",         # suivi amendements
    "documentation",       # gestion documentaire
    "assistance",          # assistance juridique IA
    "formation",           # formation équipes
    "autre",
)


# ── Authentication ──

def _validate_password_strength(password: str) -> str:
    import re
    if not re.search(r"[A-Z]", password):
        raise ValueError("Le mot de passe doit contenir au moins une majuscule")
    if not re.search(r"[a-z]", password):
        raise ValueError("Le mot de passe doit contenir au moins une minuscule")
    if not re.search(r"\d", password):
        raise ValueError("Le mot de passe doit contenir au moins un chiffre")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Le mot de passe doit contenir au moins un caractère spécial")
    return password


class RegisterRequest(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=_PHONE_REGEX, description="Numéro E.164, ex: +21698123456")
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=128)
    organization_name: str = Field(..., min_length=2, max_length=256)
    sector: str = Field(..., min_length=2, max_length=64)
    size: Optional[str] = Field(None, pattern=r"^(micro|small|medium|large)$")
    employees: Optional[int] = Field(None, ge=1)
    activities: Optional[str] = Field(None, max_length=1000)
    country: str = Field(..., min_length=2, max_length=64, description="Pays d'opération principal")
    jurisdiction: str = Field(default="tunisia", max_length=64)
    needs: List[str] = Field(default_factory=list, max_length=10)
    subscription_type: str = Field(default="monthly", pattern=r"^(monthly|annual)$")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

    @field_validator("needs")
    @classmethod
    def validate_needs(cls, v: List[str]) -> List[str]:
        invalid = [n for n in v if n not in NEED_CHOICES]
        if invalid:
            raise ValueError(f"Besoins invalides : {', '.join(invalid)}")
        return v


class RegisterResponse(BaseModel):
    """Réponse à /auth/register : aucun token tant que la modération n'a pas eu lieu."""
    status: str = "pending_verification"
    user_id: str
    organization_id: str
    email: str
    phone: str
    message: str
    next_steps: List[str] = Field(
        default_factory=lambda: [
            "verify_email",
            "verify_phone",
            "await_super_admin_approval",
        ]
    )


class VerifyEmailRequest(BaseModel):
    token: str


class SendPhoneOTPRequest(BaseModel):
    user_id: str


class VerifyPhoneRequest(BaseModel):
    user_id: str
    code: str = Field(..., min_length=4, max_length=8)


class OrganizationRejectRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105  OAuth2 standard constant, not a credential
    expires_in: int
    user: "UserOut"

class RefreshRequest(BaseModel):
    refresh_token: str


# ── Organization ──

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=256)
    sector: str = Field(..., min_length=2, max_length=64)
    size: Optional[str] = Field(None, pattern=r"^(micro|small|medium|large)$")
    employees: Optional[int] = Field(None, ge=1)
    activities: Optional[str] = Field(None, max_length=1000)
    jurisdiction: str = Field(default="tunisia", max_length=64)
    logo_url: Optional[str] = None
    subscription_type: str = Field(default="monthly", pattern=r"^(monthly|annual)$")

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=256)
    sector: Optional[str] = Field(None, min_length=2, max_length=64)
    size: Optional[str] = Field(None, pattern=r"^(micro|small|medium|large)$")
    employees: Optional[int] = Field(None, ge=1)
    activities: Optional[str] = Field(None, max_length=1000)
    jurisdiction: Optional[str] = Field(None, max_length=64)
    logo_url: Optional[str] = None
    subscription_type: Optional[str] = Field(None, pattern=r"^(monthly|annual)$")

class OrganizationStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(active|inactive|suspended)$")

class OrganizationRenewRequest(BaseModel):
    subscription_type: str = Field(default="monthly", pattern=r"^(monthly|annual)$")

class OrganizationOut(BaseModel):
    id: str
    name: str
    sector: str
    size: Optional[str] = None
    employees: Optional[int] = None
    activities: Optional[str] = None
    country: Optional[str] = None
    jurisdiction: str
    needs: List[str] = Field(default_factory=list)
    logo_url: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    requested_by_email: Optional[str] = None
    requested_by_phone: Optional[str] = None
    contact_email_verified: bool = False
    contact_phone_verified: bool = False
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    subscription_type: Optional[str] = None
    subscription_started_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

class OrganizationListOut(BaseModel):
    organizations: List[OrganizationOut]
    total: int


# ── User ──

class UserOut(BaseModel):
    id: str
    email: str
    phone: Optional[str] = None
    full_name: str
    role: str
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    organization_status: Optional[str] = None
    is_active: bool
    email_verified: bool = False
    phone_verified: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=128)
    role: Optional[str] = Field(None, pattern=r"^(admin|member|viewer)$")
    is_active: Optional[bool] = None

class UserListOut(BaseModel):
    users: List[UserOut]
    total: int

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


# ── Invitation ──

class InvitationCreate(BaseModel):
    email: EmailStr

class InvitationOut(BaseModel):
    id: str
    email: str
    role: str
    organization_id: str
    organization_name: Optional[str] = None
    invited_by: str
    status: str
    created_at: datetime
    expires_at: datetime

class InvitationListOut(BaseModel):
    invitations: List[InvitationOut]
    total: int

class AcceptInvitationRequest(BaseModel):
    token: str
    full_name: str = Field(..., min_length=2, max_length=128)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


# ── Password reset ──

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


# ── Tenant selection ──

class SelectOrganizationRequest(BaseModel):
    organization_id: str


# Forward ref resolution
TokenResponse.model_rebuild()
