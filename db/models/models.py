from typing import List

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, date


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    appointments: Mapped[List["Appointment"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Appointment(Base):
    __tablename__ = "appointment"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    comment: Mapped[str] = mapped_column(nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    timeslot_id: Mapped[int] = mapped_column(ForeignKey("timeslot.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="appointments", lazy="selectin")
    timeslot: Mapped["Timeslot"] = relationship(back_populates="appointments", lazy="selectin")

    def __str__(self):
        return f"{self.timeslot.start_datetime.strftime(format="%d-%m-%Y %H:%M")}"


class Timeslot(Base):
    __tablename__ = "timeslot"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_datetime: Mapped[datetime] = mapped_column(nullable=False, index=True)
    end_datetime: Mapped[datetime] = mapped_column(nullable=False)
    occupied: Mapped[bool] = mapped_column(default=False)

    appointments: Mapped[List["Appointment"]] = relationship(back_populates="timeslot",
                                                             cascade="all, delete-orphan",
                                                             uselist=False)

    def __str__(self):
        return self.start_datetime.strftime(format="%d-%m-%Y %H:%M")


