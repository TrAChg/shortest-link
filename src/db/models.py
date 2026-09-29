"""SQLAlchemy ORM models for URL Shortener and Click Analytics."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""


class URL(Base):
    """Represents a shortened URL and its metadata.

    Attributes:
        id: Primary key (auto-incrementing integer).
        original_url: The destination target URL.
        short_code: Unique alphanumeric alias (Base62 or custom).
        is_custom: True if the alias was requested by the user.
        is_active: Can be toggled to disable a link without deletion.
        created_at: Creation timestamp with timezone.
        expires_at: Optional expiration timestamp.
    """

    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    short_code: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    analytics: Mapped[list["ClickAnalytics"]] = relationship(
        "ClickAnalytics", back_populates="url", cascade="all, delete-orphan"
    )


class ClickAnalytics(Base):
    """Records individual redirection events for metrics and auditing.

    Attributes:
        id: Primary key.
        url_id: Foreign key pointing to urls.id.
        clicked_at: Timestamp of the click event.
        ip_address: Client IP address (anonymized if needed).
        user_agent: Browser / client user-agent string.
        referrer: Referrer header (where the click originated).
    """

    __tablename__ = "click_analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("urls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    url: Mapped["URL"] = relationship("URL", back_populates="analytics")
