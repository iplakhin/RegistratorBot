from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from dateutil import parser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
import os

from db.db import get_timeslot_by_g_event_id, create_timeslot, update_timeslot
from db.models.models import Timeslot

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def get_gcalendar_service(token_path="token.json", creds_path="credentials.json") -> Resource:
    """
    credentials.json — файл клиента OAuth (from Google Cloud Console).
    token.json — сохранённые user credentials (refresh token включён).
    """
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())


    service: Resource = build("calendar", "v3", credentials=creds)
    return service

def get_next_week_events(service: Resource, 
                         calendar_id="primary", 
                         query: Optional[str] = None,
                         time_zone: str = "UTC",
                         days_ahead: int = 7) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)

    # Определяем начало и конец периода
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    # Формируем параметры запроса
    params = {
        'calendarId': calendar_id,
        'timeMin': time_min,
        'timeMax': time_max,
        'singleEvents': True,
        'orderBy': 'startTime',
        'timeZone': time_zone,
        'maxResults': 100  # Можно настроить по необходимости
    }

    # Добавляем поисковый запрос, если он задан
    if query:
        params['q'] = query

    try:
        # Выполняем запрос к API
        events_result = service.events().list(**params).execute()

        # Получаем список событий
        events = events_result.get('items', [])

        # Добавляем ID календаря к каждому событию для удобства
        for event in events:
            event['calendarId'] = calendar_id

        return events
    except Exception as e:
        print(f"Ошибка при получении событий из календаря: {e}")
        return []


def serialize_event_to_timeslot(event: dict) -> dict:
    """
    Преобразует событие из Google Calendar API в словарь с данными для модели Timeslot.

    :param event: Событие из Google Calendar API.
    :return: Словарь с данными для создания Timeslot.
    """
    # Извлекаем g_event_id (идентификатор события)
    g_event_id = event.get('id')

    # Извлекаем calendar_id (идентификатор календаря)
    calendar_id = event.get('calendarId', 'primary')

    # Обработка времени начала и окончания
    start_time = None
    if 'start' in event:
        if 'dateTime' in event['start']:
            # Если событие с конкретным временем
            start_time = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
        elif 'date' in event['start']:
            # Если событие на весь день
            start_time = datetime.fromisoformat(f"{event['start']['date']}T00:00:00+00:00")

    end_time = None
    if 'end' in event:
        if 'dateTime' in event['end']:
            end_time = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
        elif 'date' in event['end']:
            end_time = datetime.fromisoformat(f"{event['end']['date']}T23:59:59+00:00")

    # Прочие данные события
    summary = event.get('summary')
    description = event.get('description')
    location = event.get('location')

    # Определение статуса (свободен/занят)
    # По умолчанию считаем слот свободным (status=False)
    status = False

    # Этот тег используется для синхронизации с Google Calendar
    g_etag = event.get('etag')

    # Создаем словарь с данными для Timeslot
    timeslot_data = {
        'g_event_id': g_event_id,
        'calendar_id': calendar_id,
        'start': start_time,
        'end': end_time,
        'summary': summary,
        'description': description,
        'location': location,
        'raw': event,  # Сохраняем исходное событие полностью
        'status': status,
        'g_etag': g_etag,
    }

    return timeslot_data


async def process_calendar_events(events: List[dict], session) -> List[Timeslot]:
    """
    Обрабатывает список событий из календаря и сохраняет их в базу данных.

    :param events: Список событий из Google Calendar API.
    :param session: Сессия SQLAlchemy.
    :return: Список созданных или обновленных объектов Timeslot.
    """
    from sqlalchemy.exc import IntegrityError

    if not events:
        print("Список событий пуст. Обработка событий прекращена.")
        return []

    result_timeslots = []

    for event in events:
        # Преобразуем событие в данные для Timeslot
        timeslot_data = serialize_event_to_timeslot(event)

        # Проверяем, существует ли уже такой timeslot по g_event_id
        existing_timeslot = await get_timeslot_by_g_event_id(event["g_event_id"])

        if existing_timeslot:
            # Если такой timeslot уже существует, обновляем его
            for key, value in timeslot_data.items():
                setattr(existing_timeslot, key, value)
                updated_timeslot = await update_timeslot(existing_timeslot)
                result_timeslots.append(updated_timeslot)
        else:
            # Если timeslot не существует, создаем новый
            new_timeslot = await create_timeslot(Timeslot(**timeslot_data))
            result_timeslots.append(new_timeslot)

    return result_timeslots


def sync_calendar_events(session):
    """
    Синхронизирует события из календаря с базой данных.

    :param session: Сессия SQLAlchemy.
    :return: Список обработанных объектов Timeslot.
    """
    # Предполагается, что get_next_events() - это функция,
    # которая возвращает список событий из Google Calendar API

    # Получаем список событий из календаря
    service = get_gcalendar_service();
    events = get_next_week_events(service)

    # Обрабатываем события и сохраняем их в базе данных
    return process_calendar_events(events, session)

