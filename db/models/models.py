from typing import List, Optional

from sqlalchemy import ForeignKey, func, String, Text, JSON, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, date, timezone


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True)
    is_admin: Mapped[bool] = mapped_column(default=False)

    booked_timeslots: Mapped[List["Timeslot"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Timeslot(Base):
    __tablename__ = "timeslot"

    id: Mapped[int] = mapped_column(primary_key=True)
    g_event_id: Mapped[str] = mapped_column(String, index=True, nullable=False, unique=True)
    calendar_id: Mapped[str] = mapped_column(String, nullable=False, default="primary")

    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    summary: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[Text] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(String, nullable=True)

    raw: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) # True=booked, False=free
    client_data: Mapped[str] = mapped_column(String, nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    user: Mapped["User"] = relationship(back_populates="booked_timeslots")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    g_etag: Mapped[str] = mapped_column(nullable=True)


    def __str__(self):
        return self.start.strftime(format="%d-%m-%Y %H:%M")

# DEPRECATED
#class Appointment(Base):
#    __tablename__ = "appointment"
#
#    id: Mapped[int] = mapped_column(primary_key=True)
#    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
#    comment: Mapped[str] = mapped_column(nullable=True)
#    is_primary: Mapped[bool] = mapped_column(default=True)
#
#    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
#    timeslot_id: Mapped[int] = mapped_column(ForeignKey("timeslot.id", ondelete="CASCADE"))
#
#    user: Mapped["User"] = relationship(back_populates="appointments", lazy="selectin")
#    timeslot: Mapped["Timeslot"] = relationship(back_populates="appointments", lazy="selectin")
#
#    def __str__(self):
#        return f"{self.timeslot.start_datetime.strftime(format="%d-%m-%Y %H:%M")}"



