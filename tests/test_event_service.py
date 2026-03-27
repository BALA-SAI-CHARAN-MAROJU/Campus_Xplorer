"""
Unit and property tests for event_service.
Feature: rbac-modular-refactor
"""

import pytest
from datetime import date, time, datetime, timedelta
from hypothesis import given, settings, strategies as st
from app import db
from app.models import Event
from app.services import event_service
from tests.conftest import make_user, make_campus, make_event


# ── Unit tests ────────────────────────────────────────────────────────────────

class TestCreateEvent:
    def test_happy_path(self, app):
        with app.app_context():
            user = make_user()
            result, status = event_service.create_event({
                'name': 'Fest',
                'venue_name': 'Hall A',
                'date': '2099-06-01',
                'time': '10:00',
            }, user.id)
            assert status == 201
            assert result['name'] == 'Fest'

    def test_whitespace_trimmed(self, app):
        with app.app_context():
            user = make_user()
            result, status = event_service.create_event({
                'name': '  Fest  ',
                'venue_name': '  Hall A  ',
                'date': '2099-06-01',
                'time': '10:00',
            }, user.id)
            assert status == 201
            assert result['name'] == 'Fest'
            assert result['venue_name'] == 'Hall A'

    def test_missing_fields(self, app):
        with app.app_context():
            user = make_user()
            result, status = event_service.create_event({'name': 'X'}, user.id)
            assert status == 400

    def test_invalid_date_format(self, app):
        with app.app_context():
            user = make_user()
            result, status = event_service.create_event({
                'name': 'X', 'venue_name': 'Y', 'date': '01-06-2099', 'time': '10:00'
            }, user.id)
            assert status == 400

    def test_end_time_after_start_time(self, app):
        with app.app_context():
            user = make_user()
            result, status = event_service.create_event({
                'name': 'X', 'venue_name': 'Y', 'date': '2099-06-01',
                'time': '10:00', 'end_time': '09:00'
            }, user.id)
            assert status == 400


class TestUpdateEvent:
    def test_happy_path(self, app):
        with app.app_context():
            user = make_user()
            campus = make_campus()
            event = make_event(user.id, campus.id)
            result, status = event_service.update_event(event.id, {'name': 'Updated'})
            assert status == 200
            assert result['name'] == 'Updated'

    def test_empty_body_returns_unchanged(self, app):
        with app.app_context():
            user = make_user()
            campus = make_campus()
            event = make_event(user.id, campus.id, name='Original')
            result, status = event_service.update_event(event.id, {})
            assert status == 200
            assert result['name'] == 'Original'

    def test_not_found(self, app):
        with app.app_context():
            result, status = event_service.update_event(99999, {'name': 'X'})
            assert status == 404


class TestDeleteEvent:
    def test_happy_path(self, app):
        with app.app_context():
            user = make_user()
            campus = make_campus()
            event = make_event(user.id, campus.id)
            eid = event.id
            result, status = event_service.delete_event(eid)
            assert status == 200
            assert Event.query.get(eid) is None

    def test_not_found(self, app):
        with app.app_context():
            result, status = event_service.delete_event(99999)
            assert status == 404
            assert 'error' in result


class TestGetEvents:
    def test_campus_filter(self, app):
        with app.app_context():
            user = make_user()
            c1 = make_campus('c1')
            c2 = make_campus('c2')
            make_event(user.id, 'c1')
            make_event(user.id, 'c2')
            result, status = event_service.get_events({'campus_id': 'c1'})
            assert status == 200
            assert all(e['campus_id'] == 'c1' for e in result)

    def test_upcoming_filter(self, app):
        with app.app_context():
            user = make_user()
            campus = make_campus()
            # future event
            future = Event(
                name='Future', venue_name='V', campus_id=campus.id,
                date=date(2099, 1, 1), start_time=time(10, 0), created_by=user.id
            )
            # past event
            past = Event(
                name='Past', venue_name='V', campus_id=campus.id,
                date=date(2000, 1, 1), start_time=time(10, 0), created_by=user.id
            )
            db.session.add_all([future, past])
            db.session.commit()
            result, status = event_service.get_events({'filter': 'upcoming'})
            assert status == 200
            names = [e['name'] for e in result]
            assert 'Future' in names
            assert 'Past' not in names


# ── Property tests ────────────────────────────────────────────────────────────

REQUIRED_FIELDS = ['name', 'venue_name', 'date', 'time']

# Feature: rbac-modular-refactor, Property 5: Event Creation Rejects Missing Required Fields
@given(missing=st.lists(st.sampled_from(REQUIRED_FIELDS), min_size=1, unique=True))
@settings(max_examples=100)
def test_missing_required_fields_rejected(app, missing):
    """Any subset missing at least one required field must return 400."""
    with app.app_context():
        user = make_user()
        data = {'name': 'X', 'venue_name': 'Y', 'date': '2099-01-01', 'time': '10:00'}
        for field in missing:
            del data[field]
        result, status = event_service.create_event(data, user.id)
        assert status == 400
        db.session.delete(user)
        db.session.commit()


# Feature: rbac-modular-refactor, Property 6: Event End Time Must Follow Start Time
@given(
    start_h=st.integers(min_value=1, max_value=23),
    start_m=st.integers(min_value=0, max_value=59),
    delta=st.integers(min_value=1, max_value=1439)
)
@settings(max_examples=100)
def test_end_time_must_follow_start_time(app, start_h, start_m, delta):
    """end_time <= start_time must return 400.
    
    Strategy: start is always >= 01:00, end = start - delta (clamped to same day).
    This guarantees end_time < start_time without wrapping past midnight.
    """
    with app.app_context():
        user = make_user()
        start_minutes = start_h * 60 + start_m
        # Subtract delta but clamp to 0 so end is always strictly before start
        end_minutes = max(0, start_minutes - delta)
        end_h, end_m = divmod(end_minutes, 60)
        result, status = event_service.create_event({
            'name': 'X', 'venue_name': 'Y', 'date': '2099-01-01',
            'time': f'{start_h:02d}:{start_m:02d}',
            'end_time': f'{end_h:02d}:{end_m:02d}'
        }, user.id)
        assert status == 400
        db.session.delete(user)
        db.session.commit()


# Feature: rbac-modular-refactor, Property 7: Campus Filter Returns Only Matching Events
@given(campus_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-')))
@settings(max_examples=50)
def test_campus_filter_returns_only_matching(app, campus_id):
    """get_events with campus_id filter must return only matching events."""
    with app.app_context():
        user = make_user()
        campus = make_campus(campus_id)
        make_event(user.id, campus_id)
        result, status = event_service.get_events({'campus_id': campus_id})
        assert status == 200
        assert all(e['campus_id'] == campus_id for e in result)
        # cleanup
        Event.query.filter_by(campus_id=campus_id).delete()
        db.session.delete(campus)
        db.session.delete(user)
        db.session.commit()


# Feature: rbac-modular-refactor, Property 8: Upcoming Filter Returns Only Future Events
def test_upcoming_filter_only_future(app):
    """get_events upcoming must return only events after now."""
    with app.app_context():
        user = make_user()
        campus = make_campus()
        future = Event(
            name='FutureP8', venue_name='V', campus_id=campus.id,
            date=date(2099, 12, 31), start_time=time(23, 59), created_by=user.id
        )
        past = Event(
            name='PastP8', venue_name='V', campus_id=campus.id,
            date=date(2000, 1, 1), start_time=time(0, 0), created_by=user.id
        )
        db.session.add_all([future, past])
        db.session.commit()
        result, status = event_service.get_events({'filter': 'upcoming'})
        assert status == 200
        names = [e['name'] for e in result]
        assert 'FutureP8' in names
        assert 'PastP8' not in names
