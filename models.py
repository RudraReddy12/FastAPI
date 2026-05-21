import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Index, Integer, String, Table, Text,
)
from sqlalchemy.orm import relationship

from database import Base


def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp — always prefer this over datetime.utcnow()."""
    return datetime.now(timezone.utc)


# ── Enums ─────────────────────────────────────────────────────────────────────
class DocumentTypeEnum(str, enum.Enum):
    invoice  = "invoice"
    report   = "report"
    contract = "contract"


# ── Association table: many users ↔ many roles ──────────────────────────────
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ── Role ──────────────────────────────────────────────────────────────────────
class Role(Base):
    __tablename__ = "roles"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    # Comma-separated: "upload,edit,delete,view,full_access"
    permissions = Column(String(500), nullable=False, default="view")
    created_at  = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    users = relationship("User", secondary=user_roles, back_populates="roles")

    def permissions_list(self) -> list[str]:
        """Return permissions as a deduplicated Python list."""
        return list({p.strip() for p in self.permissions.split(",") if p.strip()})

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"


# ── User ──────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    username        = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)
    created_at      = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at      = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    roles     = relationship("Role", secondary=user_roles, back_populates="users")
    documents = relationship("Document", back_populates="uploader")

    def has_permission(self, permission: str) -> bool:
        """True if ANY of the user's roles grants the requested permission."""
        for role in self.roles:
            perms = role.permissions_list()
            if "full_access" in perms or permission in perms:
                return True
        return False

    def role_names(self) -> list[str]:
        return [r.name for r in self.roles]

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


# ── Document ──────────────────────────────────────────────────────────────────
class Document(Base):
    __tablename__ = "documents"

    id            = Column(Integer, primary_key=True, index=True)
    title         = Column(String(255), nullable=False)
    company_name  = Column(String(255), nullable=False)
    document_type = Column(
        Enum(DocumentTypeEnum),
        nullable=False,
        default=DocumentTypeEnum.report,
    )
    file_path     = Column(String(512), nullable=False)
    file_name     = Column(String(255), nullable=False)
    file_size     = Column(Integer, nullable=True)   # bytes

    uploaded_by   = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    uploader      = relationship("User", back_populates="documents")

    is_indexed    = Column(Boolean, default=False, nullable=False)
    created_at    = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at    = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    # Composite index — the most common search: company + type
    __table_args__ = (
        Index("ix_documents_company_type", "company_name", "document_type"),
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} title={self.title!r}>"
