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
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=128)
    organization_name: str = Field(..., min_length=2, max_length=256)
    sector: str = Field(..., min_length=2, max_length=64)
    size: Optional[str] = Field(None, pattern=r"^(micro|small|medium|large)$")
    employees: Optional[int] = Field(None, ge=1)
    jurisdiction: str = Field(default="tunisia", max_length=64)
    subscription_type: str = Field(default="monthly", pattern=r"^(monthly|annual)$")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
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
    status: Optional[str] = Field(None, pattern=r"^(active|inactive|suspended|pending_approval|rejected)$")
    subscription_type: Optional[str] = Field(None, pattern=r"^(monthly|annual)$")

class OrganizationRenewRequest(BaseModel):
    subscription_type: str = Field(default="monthly", pattern=r"^(monthly|annual)$")

class OrganizationOut(BaseModel):
    id: str
    name: str
    sector: str
    size: Optional[str] = None
    employees: Optional[int] = None
    activities: Optional[str] = None
    jurisdiction: str
    logo_url: Optional[str] = None
    status: str
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
    full_name: str
    role: str
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    organization_status: Optional[str] = None
    is_active: bool
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
