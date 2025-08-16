from typing import List

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime


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
    appointment_date: Mapped[datetime] = mapped_column()
    user_data: Mapped[str]
    #tag: Mapped[str] #Enum (glotka, prostata, anus) перечень услуг
    is_primary: Mapped[bool] = mapped_column(default=True)

    user_pk: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    timeslot_pk: Mapped[int] = mapped_column(ForeignKey("timeslot.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="appointments")
    timeslot: Mapped["Timeslot"] = relationship(back_populates="appointments")

    def __str__(self):
        return f"{self.appointment_date.strftime("%d-%m-%Y")} в {self.timeslot.start_time}"


class Timeslot(Base):
    __tablename__ = "timeslot"

    id: Mapped[int] = mapped_column(primary_key=True)
    weekday: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[str]
    end_time: Mapped[str]
    appointments: Mapped[List["Appointment"]] = relationship(back_populates="timeslot", cascade="all, delete-orphan")

    def __str__(self):
        return self.start_time


