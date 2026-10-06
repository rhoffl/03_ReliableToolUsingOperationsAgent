import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def now(): return datetime.now(timezone.utc)

class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200)); service: Mapped[str] = mapped_column(String(80), index=True)
    environment: Mapped[str] = mapped_column(String(20)); severity: Mapped[str] = mapped_column(String(10))
    scenario: Mapped[str] = mapped_column(String(50), default="bad_deployment")
    status: Mapped[str] = mapped_column(String(40), default="alert_received", index=True)
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True); confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True); proposed_action: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0); accumulated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    events: Mapped[list["AuditEvent"]] = relationship(back_populates="incident", cascade="all, delete-orphan")

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer); event_type: Mapped[str] = mapped_column(String(60)); actor: Mapped[str] = mapped_column(String(80))
    state_before: Mapped[str | None] = mapped_column(String(40), nullable=True); state_after: Mapped[str | None] = mapped_column(String(40), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    incident: Mapped[Incident] = relationship(back_populates="events")

class ActionLedger(Base):
    __tablename__ = "action_ledger"; __table_args__ = (UniqueConstraint("idempotency_key"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True); incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"))
    idempotency_key: Mapped[str] = mapped_column(String(128)); action_hash: Mapped[str] = mapped_column(String(64)); action: Mapped[dict] = mapped_column(JSON)
    approved: Mapped[bool] = mapped_column(Boolean, default=False); approver: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending"); result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now); executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
