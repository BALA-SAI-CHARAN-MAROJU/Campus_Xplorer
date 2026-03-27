"""
Integration tests for API route → decorator → service wiring.
Feature: rbac-modular-refactor
"""

import json
import pytest
from tests.conftest import make_user, make_campus, make_event


def auth_session(client, user):
    """Set up a logged-in session for the given user."""
    with client.session_transaction() as sess:
        sess['_user_id'] = user.id
        sess['_fresh'] = True


def clear_session(client):
    with client.session_transaction() as sess:
        sess.clear()


class TestEventEndpoints:
    def test_post_events_unauthenticated_returns_redirect(self, app, client):
        clear_session(client)
        resp = client.post('/api/events', json={
            'name': 'X', 'venue_name': 'Y', 'date': '2099-01-01', 'time': '10:00'
        })
        # require_authenticated redirects
        assert resp.status_code == 302

    def test_post_events_user_role_returns_403(self, app, client):
        with app.app_context():
            user = make_user(role='user')
            auth_session(client, user)
        resp = client.post('/api/events', json={
            'name': 'X', 'venue_name': 'Y', 'date': '2099-01-01', 'time': '10:00'
        })
        assert resp.status_code == 403
        assert b'error' in resp.data

    def test_post_events_manager_returns_201(self, app, client):
        with app.app_context():
            user = make_user(role='manager')
            auth_session(client, user)
        resp = client.post('/api/events', json={
            'name': 'Fest', 'venue_name': 'Hall', 'date': '2099-06-01', 'time': '10:00'
        })
        assert resp.status_code == 201

    def test_delete_event_not_found_returns_404(self, app, client):
        with app.app_context():
            user = make_user(role='admin')
            auth_session(client, user)
        resp = client.delete('/api/events/99999')
        assert resp.status_code == 404
        assert b'error' in resp.data

    def test_put_events_user_role_returns_403(self, app, client):
        with app.app_context():
            user = make_user(role='user')
            auth_session(client, user)
        resp = client.put('/api/events/1', json={'name': 'X'})
        assert resp.status_code == 403


class TestCampusEndpoints:
    def test_post_admin_campuses_user_returns_403(self, app, client):
        with app.app_context():
            user = make_user(role='user')
            auth_session(client, user)
        resp = client.post('/admin/api/campuses', json={
            'id': 'x', 'name': 'X', 'display_name': 'X',
            'center_latitude': 13, 'center_longitude': 80
        })
        assert resp.status_code == 403

    def test_put_admin_campuses_user_returns_403(self, app, client):
        with app.app_context():
            user = make_user(role='user')
            auth_session(client, user)
        resp = client.put('/admin/api/campuses/some-id', json={'name': 'X'})
        assert resp.status_code == 403

    def test_delete_admin_campuses_user_returns_403(self, app, client):
        with app.app_context():
            user = make_user(role='user')
            auth_session(client, user)
        resp = client.delete('/admin/api/campuses/some-id')
        assert resp.status_code == 403

    def test_post_admin_campuses_manager_returns_201(self, app, client):
        with app.app_context():
            user = make_user(role='manager')
            auth_session(client, user)
        resp = client.post('/admin/api/campuses', json={
            'id': 'new-campus', 'name': 'New', 'display_name': 'New Campus',
            'center_latitude': 13.0, 'center_longitude': 80.0
        })
        assert resp.status_code == 201


class TestUserEndpoints:
    def test_get_admin_users_manager_returns_403(self, app, client):
        with app.app_context():
            user = make_user(role='manager')
            auth_session(client, user)
        resp = client.get('/admin/api/users')
        assert resp.status_code == 403

    def test_put_user_role_manager_returns_403(self, app, client):
        with app.app_context():
            manager = make_user(role='manager')
            target = make_user()
            manager_id = manager.id
            target_id = target.id
        auth_session(client, type('U', (), {'id': manager_id})())
        resp = client.put(f'/api/users/{target_id}/role', json={'role': 'admin'})
        assert resp.status_code == 403

    def test_delete_user_manager_returns_403(self, app, client):
        with app.app_context():
            manager = make_user(role='manager')
            target = make_user()
            manager_id = manager.id
            target_id = target.id
        auth_session(client, type('U', (), {'id': manager_id})())
        resp = client.delete(f'/admin/api/users/{target_id}')
        assert resp.status_code == 403


class TestLocationEndpoints:
    def test_post_location_user_returns_403(self, app, client):
        with app.app_context():
            user = make_user(role='user')
            campus = make_campus('loc-test')
            auth_session(client, user)
        resp = client.post('/api/campuses/loc-test/locations', json={
            'name': 'Hall', 'latitude': 13.0, 'longitude': 80.0
        })
        assert resp.status_code == 403

    def test_put_location_user_returns_403(self, app, client):
        with app.app_context():
            user = make_user(role='user')
            auth_session(client, user)
        resp = client.put('/api/campuses/loc-test/locations/Hall', json={'name': 'New Hall'})
        assert resp.status_code == 403

    def test_delete_location_user_returns_403(self, app, client):
        with app.app_context():
            user = make_user(role='user')
            auth_session(client, user)
        resp = client.delete('/api/campuses/loc-test/locations/Hall')
        assert resp.status_code == 403
