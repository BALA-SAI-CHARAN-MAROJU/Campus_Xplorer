"""
Shared test fixtures for the RBAC modular refactor test suite.
"""

import uuid
import pytest
from datetime import date, time, datetime
from app import create_app, db as _db
from app.models import User, Event, Campus, Conversation


@pytest.fixture(scope='session')
def app():
    """Create application with testing config (in-memory SQLite)."""
    application = create_app('testing')
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Truncate all tables between tests."""
    with app.app_context():
        yield
        _db.session.remove()
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


# ── Helper factories ──────────────────────────────────────────────────────────

def make_user(role='user', email=None, name='Test User'):
    """Create and persist a User with the given role."""
    email = email or f'user_{uuid.uuid4().hex[:8]}@test.com'
    user = User(
        id=str(uuid.uuid4()),
        google_id=f'google_{uuid.uuid4().hex}',
        email=email,
        name=name,
        is_admin=(role == 'admin'),
        is_manager=(role == 'manager'),
        created_at=datetime.utcnow(),
    )
    _db.session.add(user)
    _db.session.commit()
    return user


def make_campus(campus_id=None, name='Test Campus', lat=13.0, lng=80.0):
    """Create and persist a Campus."""
    campus_id = campus_id or f'campus-{uuid.uuid4().hex[:6]}'
    campus = Campus(
        id=campus_id,
        name=name,
        display_name=name,
        center_latitude=lat,
        center_longitude=lng,
        locations_data={},
        timezone='UTC',
    )
    _db.session.add(campus)
    _db.session.commit()
    return campus


def make_event(creator_id, campus_id='test-campus', name='Test Event'):
    """Create and persist an Event."""
    event = Event(
        name=name,
        venue_name='Test Venue',
        campus_id=campus_id,
        date=date(2099, 1, 1),
        start_time=time(10, 0),
        created_by=creator_id,
    )
    _db.session.add(event)
    _db.session.commit()
    return event
