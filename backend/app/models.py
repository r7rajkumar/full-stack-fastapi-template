import uuid
from datetime import datetime, timezone
from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel
import sqlalchemy as sa
import enum
from typing import Optional, List
from sqlalchemy import Text, Column
from sqlalchemy import Enum as SAEnum

def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore[assignment]
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore[assignment]


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ─────────────────────────────────────────────
# Insurance Domain Models
# ─────────────────────────────────────────────


class IndustryType(str, enum.Enum):
    retail = "retail"
    hospitality = "hospitality"
    construction = "construction"
    technology = "technology"
    healthcare = "healthcare"
    manufacturing = "manufacturing"
    professional_services = "professional_services"
    other = "other"

    class Config:
        use_enum_values = True


class ProductType(str, enum.Enum):
    public_liability = "public_liability"
    professional_indemnity = "professional_indemnity"
    cyber = "cyber"
    business_interruption = "business_interruption"
    property = "property"
    employers_liability = "employers_liability"

    class Config:
        use_enum_values = True


class QuoteStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    accepted = "accepted"

    class Config:
        use_enum_values = True


# ── Client ────────────────────────────────────


class ClientBase(SQLModel):
    name: str = Field(max_length=255)
    industry: str
    annual_turnover_nzd: float
    notes: str | None = Field(default=None, sa_column=Column(Text))

class ClientCreate(ClientBase):
    pass


class ClientUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    industry: IndustryType | None = None
    annual_turnover_nzd: float | None = None
    notes: str | None = None


class Client(ClientBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    quotes: list["Quote"] = Relationship(back_populates="client", cascade_delete=True)


class ClientPublic(ClientBase):
    id: int


class ClientsPublic(SQLModel):
    data: list[ClientPublic]
    count: int


# ── Policy ────────────────────────────────────
class PolicyBase(SQLModel):
    product_type: str
    insurer: str = Field(max_length=255)
    sum_insured_nzd: float
    description: str = Field(sa_column=Column(Text))


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(SQLModel):
    product_type: ProductType | None = None
    insurer: str | None = Field(default=None, max_length=255)
    sum_insured_nzd: float | None = None
    description: str | None = None


class Policy(PolicyBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # embedding column added via raw SA Column in migration (pgvector)
    quotes: list["Quote"] = Relationship(back_populates="policy")


class PolicyPublic(PolicyBase):
    id: int


class PolicyWithScore(PolicyPublic):
    score: float


class PoliciesPublic(SQLModel):
    data: list[PolicyPublic]
    count: int


# ── Quote ─────────────────────────────────────

class QuoteBase(SQLModel):
    premium_nzd: float
    status: str = "draft"

class QuoteCreate(QuoteBase):
    client_id: int
    policy_id: int


class QuoteUpdate(SQLModel):
    premium_nzd: float | None = None
    status: QuoteStatus | None = None


class Quote(QuoteBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id", ondelete="CASCADE")
    policy_id: int = Field(foreign_key="policy.id")
    client: Client | None = Relationship(back_populates="quotes")
    policy: Policy | None = Relationship(back_populates="quotes")


class QuotePublic(QuoteBase):
    id: int
    client_id: int
    policy_id: int


class QuotesPublic(SQLModel):
    data: list[QuotePublic]
    count: int