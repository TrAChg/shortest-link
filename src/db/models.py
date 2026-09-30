"""SQLAlchemy ORM models for URL Shortener and Click Analytics."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    def __repr__(self) -> str:
        return f"Infor {self.__class__.__name__}(id = {self.id})"


class URL(Base):
    """Represents a shortened URL."""

    __tablename__ = "urls"

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

    # Relationships cascade: automatically clean up
    analytics: Mapped[list["ClickAnalytics"]] = relationship(
        "ClickAnalytics", back_populates="url", cascade="all, delete-orphan"
    )


class ClickAnalytics(Base):
    """Records individual redirection events for metrics and auditing."""

    __tablename__ = "click_analytics"

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
