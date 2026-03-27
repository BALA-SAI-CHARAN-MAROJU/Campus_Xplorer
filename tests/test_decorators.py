"""
Unit tests for RBAC decorators.
Feature: rbac-modular-refactor
"""

import pytest
import uuid
from flask import jsonify
from app.auth.decorators import require_authenticated, require_admin, require_manager_or_admin
from app import create_app, db as _db
from app.models import User
from datetime import datetime


# ── Dedicated app/client fixtures that register routes BEFORE first request ──

@pytest.fixture(scope='module')
def decorator_app():
    """Create a fresh app with test routes pre-registered (before any request)."""
    from app import create_app
    application = create_app('testing')

    # Register test routes BEFORE the app handles any request
    @application.route('/test/admin-only')
    @require_authenticated
    @require_admin
    def test_admin_only():
        return jsonify({'ok': True})

    @application.route('/test/manager-or-admin')
    @require_authenticated
    @require_manager_or_admin
    def test_manager_or_admin():
        return jsonify({'ok': True})

    @application.route('/test/authenticated-only')
    @require_authenticated
    def test_authenticated_only():
        return jsonify({'ok': True})

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture
def decorator_client(decorator_app):
    return decorator_app.test_client()


@pytest.fixture(autouse=True)
def clean_decorator_db(decorator_app):
    with decorator_app.app_context():
        yield
        _db.session.remove()
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


def _make_user_dec(app, role='user'):
    """Helper that creates a user within the decorator app context."""
    with app.app_context():
        user = User(
            id=str(uuid.uuid4()),
            google_id=f'google_{uuid.uuid4().hex}',
            email=f'user_{uuid.uuid4().hex[:8]}@test.com',
            name='Test User',
            is_admin=(role == 'admin'),
            is_manager=(role == 'manager'),
            created_at=datetime.utcnow(),
        )
        _db.session.add(user)
        _db.session.commit()
        return user.id  # return id, not object (to avoid detached state)


class TestRequireAdmin:
    def test_admin_allowed(self, decorator_app, decorator_client):
        user_id = _make_user_dec(decorator_app, role='admin')
        with decorator_client.session_transaction() as sess:
            sess['_user_id'] = user_id
            sess['_fresh'] = True
        resp = decorator_client.get('/test/admin-only')
        assert resp.status_code == 200

    def test_manager_blocked(self, decorator_app, decorator_client):
        user_id = _make_user_dec(decorator_app, role='manager')
        with decorator_client.session_transaction() as sess:
            sess['_user_id'] = user_id
            sess['_fresh'] = True
        resp = decorator_client.get('/test/admin-only')
        assert resp.status_code == 403
        assert b'error' in resp.data

    def test_user_blocked(self, decorator_app, decorator_client):
        user_id = _make_user_dec(decorator_app, role='user')
        with decorator_client.session_transaction() as sess:
            sess['_user_id'] = user_id
            sess['_fresh'] = True
        resp = decorator_client.get('/test/admin-only')
        assert resp.status_code == 403
        assert b'error' in resp.data


class TestRequireManagerOrAdmin:
    def test_admin_allowed(self, decorator_app, decorator_client):
        user_id = _make_user_dec(decorator_app, role='admin')
        with decorator_client.session_transaction() as sess:
            sess['_user_id'] = user_id
            sess['_fresh'] = True
        resp = decorator_client.get('/test/manager-or-admin')
        assert resp.status_code == 200

    def test_manager_allowed(self, decorator_app, decorator_client):
        user_id = _make_user_dec(decorator_app, role='manager')
        with decorator_client.session_transaction() as sess:
            sess['_user_id'] = user_id
            sess['_fresh'] = True
        resp = decorator_client.get('/test/manager-or-admin')
        assert resp.status_code == 200

    def test_user_blocked(self, decorator_app, decorator_client):
        user_id = _make_user_dec(decorator_app, role='user')
        with decorator_client.session_transaction() as sess:
            sess['_user_id'] = user_id
            sess['_fresh'] = True
        resp = decorator_client.get('/test/manager-or-admin')
        assert resp.status_code == 403
        assert b'error' in resp.data


class TestRequireAuthenticated:
    def test_unauthenticated_redirects_to_login(self, decorator_client):
        with decorator_client.session_transaction() as sess:
            sess.clear()
        resp = decorator_client.get('/test/authenticated-only')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers.get('Location', '') or 'login' in resp.headers.get('Location', '')
