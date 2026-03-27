"""
Unit and property tests for college_service.
Feature: rbac-modular-refactor
"""

import pytest
from hypothesis import given, settings, strategies as st
from app import db
from app.models import Campus, Event
from app.services import college_service
from tests.conftest import make_user, make_campus, make_event


# ── Unit tests ────────────────────────────────────────────────────────────────

class TestAddCollege:
    def test_happy_path(self, app):
        with app.app_context():
            result, status = college_service.add_college({
                'id': 'test-c', 'name': 'Test', 'display_name': 'Test Campus',
                'center_latitude': 13.0, 'center_longitude': 80.0
            })
            assert status == 201
            assert result['id'] == 'test-c'

    def test_whitespace_trimmed(self, app):
        with app.app_context():
            result, status = college_service.add_college({
                'id': 'trim-c', 'name': '  Trimmed  ', 'display_name': '  Display  ',
                'center_latitude': 13.0, 'center_longitude': 80.0
            })
            assert status == 201
            assert result['name'] == 'Trimmed'

    def test_missing_fields(self, app):
        with app.app_context():
            result, status = college_service.add_college({'id': 'x', 'name': 'X'})
            assert status == 400

    def test_duplicate_id(self, app):
        with app.app_context():
            make_campus('dup-c')
            result, status = college_service.add_college({
                'id': 'dup-c', 'name': 'X', 'display_name': 'X',
                'center_latitude': 0, 'center_longitude': 0
            })
            assert status == 409


class TestEditCollege:
    def test_happy_path(self, app):
        with app.app_context():
            campus = make_campus('edit-c')
            result, status = college_service.edit_college('edit-c', {'name': 'Updated'})
            assert status == 200
            assert result['name'] == 'Updated'

    def test_not_found(self, app):
        with app.app_context():
            result, status = college_service.edit_college('ghost', {'name': 'X'})
            assert status == 404

    def test_invalid_coords(self, app):
        with app.app_context():
            campus = make_campus('coord-c')
            result, status = college_service.edit_college('coord-c', {
                'center_latitude': 999, 'center_longitude': 80
            })
            assert status == 400


class TestDeleteCollege:
    def test_happy_path(self, app):
        with app.app_context():
            campus = make_campus('del-c')
            result, status = college_service.delete_college('del-c')
            assert status == 200
            assert Campus.query.get('del-c') is None

    def test_not_found(self, app):
        with app.app_context():
            result, status = college_service.delete_college('ghost')
            assert status == 404

    def test_blocked_by_active_events(self, app):
        with app.app_context():
            user = make_user()
            campus = make_campus('block-c')
            make_event(user.id, 'block-c')
            result, status = college_service.delete_college('block-c')
            assert status == 400
            assert Campus.query.get('block-c') is not None


class TestGetColleges:
    def test_returns_active_only(self, app):
        with app.app_context():
            c = make_campus('active-c')
            result, status = college_service.get_colleges()
            assert status == 200
            ids = [r['id'] for r in result]
            assert 'active-c' in ids


# ── Property tests ────────────────────────────────────────────────────────────

# Feature: rbac-modular-refactor, Property 9: Coordinate Validation Rejects Out-of-Range Values
@given(
    lat=st.one_of(st.floats(max_value=-90.01, allow_nan=False), st.floats(min_value=90.01, allow_nan=False)),
    lng=st.floats(min_value=-180, max_value=180, allow_nan=False)
)
@settings(max_examples=100)
def test_invalid_latitude_rejected(app, lat, lng):
    """Latitude outside [-90,90] must return 400 for add_college."""
    with app.app_context():
        result, status = college_service.add_college({
            'id': 'prop9-lat', 'name': 'X', 'display_name': 'X',
            'center_latitude': lat, 'center_longitude': lng
        })
        assert status == 400
        assert 'error' in result


@given(
    lat=st.floats(min_value=-90, max_value=90, allow_nan=False),
    lng=st.one_of(st.floats(max_value=-180.01, allow_nan=False), st.floats(min_value=180.01, allow_nan=False))
)
@settings(max_examples=100)
def test_invalid_longitude_rejected(app, lat, lng):
    """Longitude outside [-180,180] must return 400 for add_college."""
    with app.app_context():
        result, status = college_service.add_college({
            'id': 'prop9-lng', 'name': 'X', 'display_name': 'X',
            'center_latitude': lat, 'center_longitude': lng
        })
        assert status == 400
        assert 'error' in result


# Feature: rbac-modular-refactor, Property 10: Duplicate College ID Returns Conflict
@given(campus_id=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz-'))
@settings(max_examples=50)
def test_duplicate_college_id_returns_409(app, campus_id):
    """add_college with existing id must return 409."""
    with app.app_context():
        existing = Campus.query.get(campus_id)
        if not existing:
            make_campus(campus_id)
        result, status = college_service.add_college({
            'id': campus_id, 'name': 'X', 'display_name': 'X',
            'center_latitude': 0, 'center_longitude': 0
        })
        assert status == 409
        assert 'error' in result
        Campus.query.filter_by(id=campus_id).delete()
        db.session.commit()


# Feature: rbac-modular-refactor, Property 11: College With Active Events Cannot Be Deleted
def test_college_with_active_events_not_deleted(app):
    """delete_college with active events must fail and college must still exist."""
    with app.app_context():
        user = make_user()
        campus = make_campus('prop11-c')
        make_event(user.id, 'prop11-c')
        result, status = college_service.delete_college('prop11-c')
        assert status != 200
        assert 'error' in result
        assert Campus.query.get('prop11-c') is not None
