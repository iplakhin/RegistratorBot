from datetime import datetime, date

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, joinedload
from sqlalchemy import select, delete
from .models.models import User, Timeslot
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

async def get_timeslot_by_g_event_id(g_event_id: str):
    async with async_session() as session:
        timeslot = await session.execute(
            select(Timeslot).where(Timeslot.g_event_id == g_event_id))

    return timeslot.scalar_one_or_none()


async def create_timeslot(timeslot: Timeslot) -> Timeslot:
    async with async_session() as session:
        session.add(timeslot)
        try:
            await session.commit()
            await session.refresh(timeslot)
            return timeslot
        except Exception as e:
            await session.rollback()
            print("Ошибка при commit создания Timeslot:", e)
            raise


async def update_timeslot(timeslot: Timeslot) -> Timeslot:
    async with async_session() as session:
        try:
            session.add(timeslot)
            await session.commit()
            await session.refresh(timeslot)
            return timeslot
        except Exception as e:
            await session.rollback()
            print("Ошибка при commit обновления Timeslot:", e)
            raise

async def delete_timeslot(appointment_pk: int) -> None:
    pass


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
        pass

async def get_timeslot(weekday: int, start_time: str) -> Timeslot | None:
    async with async_session() as session:
        result = await session.execute(
            select(Timeslot).where(
                Timeslot.weekday == weekday,
                Timeslot.start_time == start_time
            )
        )
        return result.scalar_one_or_none()



async def get_appointment(appointment_pk: int):
    pass


async def get_user_appointments(user_pk: int):
    async with async_session() as session:
        pass


