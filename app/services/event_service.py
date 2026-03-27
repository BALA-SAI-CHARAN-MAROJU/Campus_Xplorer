"""
Event service — all event CRUD logic.
"""

from datetime import datetime, date as date_type, time as time_type
from flask import current_app
from app import db
from app.models import Event


def _parse_date(value: str):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _parse_time(value: str):
    try:
        return datetime.strptime(value, '%H:%M').time()
    except (ValueError, TypeError):
        return None


def create_event(data: dict, creator_id: str) -> tuple:
    """
    Create a new event.
    Required: name, venue_name, date (YYYY-MM-DD), time (HH:MM)
    Optional: description, end_time (HH:MM), campus_id
    Trims whitespace from name and venue_name.
    """
    if not data:
        return {'error': 'Request body is required.'}, 400

    missing = [f for f in ['name', 'venue_name', 'date', 'time'] if not data.get(f)]
    if missing:
        return {'error': f'Missing required fields: {", ".join(missing)}'}, 400

    event_date = _parse_date(data['date'])
    if event_date is None:
        return {'error': 'Invalid date format. Use YYYY-MM-DD.'}, 400

    start_time = _parse_time(data['time'])
    if start_time is None:
        return {'error': 'Invalid time format. Use HH:MM.'}, 400

    end_time = None
    if data.get('end_time'):
        end_time = _parse_time(data['end_time'])
        if end_time is None:
            return {'error': 'Invalid end_time format. Use HH:MM.'}, 400
        if end_time <= start_time:
            return {'error': 'end_time must be after start_time.'}, 400

    try:
        event = Event(
            name=data['name'].strip(),
            description=data.get('description', ''),
            venue_name=data['venue_name'].strip(),
            campus_id=data.get('campus_id', 'amrita-chennai'),
            date=event_date,
            start_time=start_time,
            end_time=end_time,
            created_by=creator_id,
        )
        db.session.add(event)
        db.session.commit()
        return event.to_dict(), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'create_event error: {e}')
        return {'error': 'Internal server error'}, 500


def update_event(event_id: int, data: dict) -> tuple:
    """
    Update an existing event. Empty body returns existing event unchanged (200).
    Trims whitespace from name and venue_name if provided.
    """
    event = Event.query.get(event_id)
    if not event:
        return {'error': 'Event not found.'}, 404

    if not data:
        return event.to_dict(), 200

    try:
        if 'name' in data:
            event.name = data['name'].strip()
        if 'description' in data:
            event.description = data['description']
        if 'venue_name' in data:
            event.venue_name = data['venue_name'].strip()
        if 'campus_id' in data:
            event.campus_id = data['campus_id']

        if 'date' in data:
            parsed = _parse_date(data['date'])
            if parsed is None:
                return {'error': 'Invalid date format. Use YYYY-MM-DD.'}, 400
            event.date = parsed

        if 'time' in data:
            parsed = _parse_time(data['time'])
            if parsed is None:
                return {'error': 'Invalid time format. Use HH:MM.'}, 400
            event.start_time = parsed

        if 'end_time' in data:
            if data['end_time']:
                parsed = _parse_time(data['end_time'])
                if parsed is None:
                    return {'error': 'Invalid end_time format. Use HH:MM.'}, 400
                event.end_time = parsed
            else:
                event.end_time = None

        if event.end_time and event.end_time <= event.start_time:
            return {'error': 'end_time must be after start_time.'}, 400

        event.updated_at = datetime.utcnow()
        db.session.commit()
        return event.to_dict(), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'update_event error: {e}')
        return {'error': 'Internal server error'}, 500


def delete_event(event_id: int) -> tuple:
    """Delete an event by ID. Returns 404 if not found."""
    event = Event.query.get(event_id)
    if not event:
        return {'error': 'Event not found.'}, 404

    try:
        name = event.name
        db.session.delete(event)
        db.session.commit()
        return {'message': f'Event "{name}" deleted successfully.'}, 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'delete_event error: {e}')
        return {'error': 'Internal server error'}, 500


def get_events(filters: dict) -> tuple:
    """
    Return events matching filters.
    Supported: campus_id (str), filter ("upcoming" | "past")
    """
    filters = filters or {}
    query = Event.query.filter_by(is_active=True)

    if filters.get('campus_id'):
        query = query.filter_by(campus_id=filters['campus_id'])

    events = query.all()
    now = datetime.now()

    result = []
    for event in events:
        d = event.to_dict()
        try:
            event_dt = datetime.combine(event.date, event.start_time)
            d['_time_left'] = (event_dt - now).total_seconds()
        except Exception:
            d['_time_left'] = float('inf')
        result.append(d)

    filter_type = filters.get('filter')
    if filter_type == 'upcoming':
        result = [e for e in result if e['_time_left'] > 0]
    elif filter_type == 'past':
        result = [e for e in result if e['_time_left'] <= 0]

    for e in result:
        e.pop('_time_left', None)

    return result, 200
