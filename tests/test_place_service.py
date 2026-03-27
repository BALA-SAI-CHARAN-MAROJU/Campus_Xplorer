"""
Unit and property tests for place_service.
Feature: rbac-modular-refactor
"""

import pytest
from hypothesis import given, settings, strategies as st
from app import db
from app.models import Campus
from app.services import place_service
from tests.conftest import make_campus


# ── Unit tests ────────────────────────────────────────────────────────────────

class TestAddPlace:
    def test_happy_path(self, app):
        with app.app_context():
            campus = make_campus('p-add')
            result, status = place_service.add_place('p-add', {
                'name': 'Library', 'latitude': 13.0, 'longitude': 80.0
            })
            assert status == 201
            assert result['name'] == 'Library'

    def test_missing_fields(self, app):
        with app.app_context():
            campus = make_campus('p-miss')
            result, status = place_service.add_place('p-miss', {'name': 'X'})
            assert status == 400

    def test_whitespace_only_name(self, app):
        with app.app_context():
            campus = make_campus('p-ws')
            result, status = place_service.add_place('p-ws', {
                'name': '   ', 'latitude': 13.0, 'longitude': 80.0
            })
            assert status == 400

    def test_duplicate_name(self, app):
        with app.app_context():
            campus = make_campus('p-dup')
            place_service.add_place('p-dup', {'name': 'Lib', 'latitude': 13.0, 'longitude': 80.0})
            result, status = place_service.add_place('p-dup', {'name': 'Lib', 'latitude': 14.0, 'longitude': 81.0})
            assert status == 409

    def test_college_not_found(self, app):
        with app.app_context():
            result, status = place_service.add_place('ghost', {'name': 'X', 'latitude': 0, 'longitude': 0})
            assert status == 404


class TestEditPlace:
    def test_happy_path(self, app):
        with app.app_context():
            campus = make_campus('p-edit')
            place_service.add_place('p-edit', {'name': 'Old', 'latitude': 13.0, 'longitude': 80.0})
            result, status = place_service.edit_place('p-edit', 'Old', {'name': 'New'})
            assert status == 200
            assert result['name'] == 'New'

    def test_place_not_found(self, app):
        with app.app_context():
            campus = make_campus('p-enf')
            result, status = place_service.edit_place('p-enf', 'Ghost', {'name': 'X'})
            assert status == 404

    def test_name_conflict(self, app):
        with app.app_context():
            campus = make_campus('p-conf')
            place_service.add_place('p-conf', {'name': 'A', 'latitude': 13.0, 'longitude': 80.0})
            place_service.add_place('p-conf', {'name': 'B', 'latitude': 14.0, 'longitude': 81.0})
            result, status = place_service.edit_place('p-conf', 'A', {'name': 'B'})
            assert status == 409


class TestDeletePlace:
    def test_happy_path(self, app):
        with app.app_context():
            campus = make_campus('p-del')
            place_service.add_place('p-del', {'name': 'Gym', 'latitude': 13.0, 'longitude': 80.0})
            result, status = place_service.delete_place('p-del', 'Gym')
            assert status == 200
            campus_fresh = Campus.query.get('p-del')
            assert 'Gym' not in (campus_fresh.locations_data or {})

    def test_place_not_found(self, app):
        with app.app_context():
            campus = make_campus('p-dnf')
            result, status = place_service.delete_place('p-dnf', 'Ghost')
            assert status == 404
            assert 'error' in result

    def test_college_not_found(self, app):
        with app.app_context():
            result, status = place_service.delete_place('ghost', 'X')
            assert status == 404


class TestGetPlaces:
    def test_happy_path(self, app):
        with app.app_context():
            campus = make_campus('p-get')
            place_service.add_place('p-get', {'name': 'Hall', 'latitude': 13.0, 'longitude': 80.0})
            result, status = place_service.get_places('p-get')
            assert status == 200
            assert any(p['name'] == 'Hall' for p in result)

    def test_college_not_found(self, app):
        with app.app_context():
            result, status = place_service.get_places('ghost')
            assert status == 404


# ── Property tests ────────────────────────────────────────────────────────────

# Feature: rbac-modular-refactor, Property 9: Coordinate Validation (place)
@given(
    lat=st.one_of(st.floats(max_value=-90.01, allow_nan=False), st.floats(min_value=90.01, allow_nan=False)),
    lng=st.floats(min_value=-180, max_value=180, allow_nan=False)
)
@settings(max_examples=100)
def test_invalid_lat_rejected_for_place(app, lat, lng):
    """Latitude outside [-90,90] must return 400 for add_place."""
    with app.app_context():
        campus = make_campus('prop9p-lat')
        result, status = place_service.add_place('prop9p-lat', {
            'name': 'X', 'latitude': lat, 'longitude': lng
        })
        assert status == 400
        db.session.delete(campus)
        db.session.commit()


# Feature: rbac-modular-refactor, Property 12: Duplicate Place Name Returns Conflict
@given(name=st.text(min_size=1, max_size=30).filter(lambda s: s.strip()))
@settings(max_examples=50)
def test_duplicate_place_name_returns_409(app, name):
    """add_place with existing name must return 409."""
    with app.app_context():
        campus = make_campus('prop12-c')
        place_service.add_place('prop12-c', {'name': name, 'latitude': 13.0, 'longitude': 80.0})
        result, status = place_service.add_place('prop12-c', {'name': name, 'latitude': 14.0, 'longitude': 81.0})
        assert status == 409
        assert 'error' in result
        db.session.delete(campus)
        db.session.commit()


# Feature: rbac-modular-refactor, Property 17: Whitespace-Only Place Name Is Rejected
@given(name=st.text(alphabet=' \t\n\r', min_size=1, max_size=20))
@settings(max_examples=50)
def test_whitespace_only_name_rejected(app, name):
    """add_place with whitespace-only name must return 400."""
    with app.app_context():
        campus = make_campus('prop17-c')
        result, status = place_service.add_place('prop17-c', {
            'name': name, 'latitude': 13.0, 'longitude': 80.0
        })
        assert status == 400
        assert 'error' in result
        db.session.delete(campus)
        db.session.commit()
