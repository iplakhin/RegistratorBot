from datetime import datetime, date

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, joinedload
from sqlalchemy import select, delete
from typing import Optional, List
from .models.models import User, Appointment, Timeslot
from config.config import settings


engine = create_async_engine(settings.db, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

async def get_or_create_user(telegram_id: int) -> User:
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        print(user)

        if user is None:
            print("User НЕ найден в базе")
            user = User(telegram_id=telegram_id)
            session.add(user)
            try:
                await session.commit()
                await session.refresh(user)
                print("User created")
            except Exception as e:
                await session.rollback()
                print("Ошибка при commit:", e)
                raise
        return user

async def get_available_timeslots(selected_date: datetime) -> List[Timeslot]:
    print("Выбрана дата: " + selected_date.strftime("%d-%m-%Y"))
    async with async_session() as session:
        weekday = selected_date.weekday()
        result = await session.execute(
            select(Timeslot)
            .where(Timeslot.weekday == weekday))
        all_timeslots = list(result.scalars().all())
        print(all_timeslots)

        if not all_timeslots:
            print("Не получил таймслотов вообще")
            return []

        booked_stmt = select(Appointment.timeslot_pk).where(Appointment.appointment_date == selected_date)
        booked_result = await session.execute(booked_stmt)
        booked_timeslot_ids = booked_result.scalars().all()

        # Фильтруем только свободные слоты
        available_timeslots = [slot for slot in all_timeslots if slot.id not in booked_timeslot_ids]

        print("Отфильтрованные таймслоты:")
        for slot in available_timeslots:
            print(slot)

        return available_timeslots

async def get_timeslot_by_id(timeslot_id: int) -> Timeslot:
    async with async_session() as session:
        timeslot = await session.execute(
            select(Timeslot)
            .where(Timeslot.id == timeslot_id))
        if timeslot:
            print("Получил таймслот")
        else:
            print("Не получил таймслот")
        return timeslot.scalar_one_or_none()

async def is_timeslot_available(appointment_date: date, timeslot_pk) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Appointment).where(Appointment.appointment_date == appointment_date,
                Appointment.timeslot_pk == timeslot_pk
            )
        )
        print("Функция is_timeslot_available выполнилась")
        appointment = result.scalar_one_or_none()
        return appointment is None

async def get_timeslot(weekday: int, start_time: str) -> Timeslot | None:
    async with async_session() as session:
        result = await session.execute(
            select(Timeslot).where(
                Timeslot.weekday == weekday,
                Timeslot.start_time == start_time
            )
        )
        return result.scalar_one_or_none()

async def create_appointment(appointment: Appointment) -> Appointment:
    async with async_session() as session:
        session.add(appointment)
        await session.commit()
        await session.refresh(appointment)
        print("Appointment создан и возвращается обратно: " + appointment.__str__())
        return appointment

async def get_appointment(appointment_pk: int) -> Optional[Appointment]:
    async with async_session() as session:
        result = await session.execute(
            select(Appointment).where(Appointment.id == appointment_pk)
        )
        return result.scalar_one_or_none()


async def get_user_appointments(user_pk: int) -> List[Appointment]:
    async with async_session() as session:
        result = await session.execute(
            select(Appointment)
            .options(joinedload(Appointment.timeslot))
            .where(Appointment.user_pk == user_pk)
            .order_by(Appointment.appointment_date)
        )
        return result.scalars().all()

async def update_appointment(appointment_pk: int, new_visit_date: datetime, new_timeslot_pk: int) -> Optional[Appointment]:
    async with async_session() as session:
        if not await is_timeslot_available(new_visit_date, new_timeslot_pk):
            raise ValueError("Новый слот уже занят")

        result = await session.execute(
            select(Appointment).where(Appointment.id == appointment_pk)
        )
        appointment = result.scalar_one_or_none()
        if appointment:
            appointment.visit_date = new_visit_date
            appointment.timeslot = new_timeslot_pk
            await session.commit()
            await session.refresh(appointment)
        return appointment


async def delete_appointment(appointment_pk: int) -> None:
    async with async_session() as session:
        await session.execute(
            delete(Appointment).where(Appointment.id == appointment_pk)
        )
        await session.commit()

