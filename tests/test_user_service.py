"""
Unit and property tests for user_service.
Feature: rbac-modular-refactor
"""

import pytest
from hypothesis import given, settings, strategies as st
from app import db
from app.models import User, Event, Conversation
from app.services import user_service
from tests.conftest import make_user, make_campus, make_event


# ── Unit tests ────────────────────────────────────────────────────────────────

class TestCreateUser:
    def test_happy_path(self, app):
        with app.app_context():
            result, status = user_service.create_user({'name': 'Alice', 'email': 'alice@test.com'})
            assert status == 201
            assert result['email'] == 'alice@test.com'
            assert result['is_admin'] is False
            assert result['is_manager'] is False
            assert result['role'] == 'user'

    def test_missing_fields(self, app):
        with app.app_context():
            result, status = user_service.create_user({'name': 'Bob'})
            assert status == 400
            assert 'error' in result

    def test_duplicate_email(self, app):
        with app.app_context():
            make_user(email='dup@test.com')
            result, status = user_service.create_user({'name': 'Dup', 'email': 'dup@test.com'})
            assert status == 409
            assert 'error' in result


class TestUpdateUser:
    def test_happy_path(self, app):
        with app.app_context():
            user = make_user()
            result, status = user_service.update_user(user.id, {'name': 'Updated'})
            assert status == 200
            assert result['name'] == 'Updated'

    def test_not_found(self, app):
        with app.app_context():
            result, status = user_service.update_user('nonexistent', {'name': 'X'})
            assert status == 404


class TestDeleteUser:
    def test_happy_path(self, app):
        with app.app_context():
            admin = make_user(role='admin')
            target = make_user()
            result, status = user_service.delete_user(target.id, admin.id)
            assert status == 200
            assert User.query.get(target.id) is None

    def test_self_deletion_prevented(self, app):
        with app.app_context():
            user = make_user()
            result, status = user_service.delete_user(user.id, user.id)
            assert status == 400
            assert User.query.get(user.id) is not None

    def test_not_found(self, app):
        with app.app_context():
            result, status = user_service.delete_user('ghost', 'other')
            assert status == 404

    def test_cascade_deletes_events_and_conversations(self, app):
        with app.app_context():
            admin = make_user(role='admin')
            campus = make_campus()
            target = make_user()
            make_event(creator_id=target.id, campus_id=campus.id)
            conv = Conversation(
                id='conv-1', user_id=target.id, messages=[]
            )
            db.session.add(conv)
            db.session.commit()

            user_service.delete_user(target.id, admin.id)

            assert Event.query.filter_by(created_by=target.id).count() == 0
            assert Conversation.query.filter_by(user_id=target.id).count() == 0


class TestAssignRole:
    def test_assign_admin(self, app):
        with app.app_context():
            user = make_user()
            result, status = user_service.assign_role(user.id, 'admin')
            assert status == 200
            assert result['is_admin'] is True
            assert result['is_manager'] is False

    def test_assign_manager(self, app):
        with app.app_context():
            user = make_user(role='admin')
            result, status = user_service.assign_role(user.id, 'manager')
            assert status == 200
            assert result['is_admin'] is False
            assert result['is_manager'] is True

    def test_assign_user(self, app):
        with app.app_context():
            user = make_user(role='admin')
            result, status = user_service.assign_role(user.id, 'user')
            assert status == 200
            assert result['is_admin'] is False
            assert result['is_manager'] is False

    def test_invalid_role(self, app):
        with app.app_context():
            user = make_user()
            result, status = user_service.assign_role(user.id, 'superuser')
            assert status == 400
            assert 'error' in result

    def test_not_found(self, app):
        with app.app_context():
            result, status = user_service.assign_role('ghost', 'admin')
            assert status == 404


# ── Property tests ────────────────────────────────────────────────────────────

# Feature: rbac-modular-refactor, Property 1: Role Mutual Exclusivity
@given(role=st.sampled_from(['admin', 'manager', 'user']))
@settings(max_examples=200)
def test_role_mutual_exclusivity(app, role):
    """is_admin and is_manager must never both be True after assign_role."""
    with app.app_context():
        user = make_user()
        result, status = user_service.assign_role(user.id, role)
        assert status == 200
        db.session.refresh(user)
        assert not (user.is_admin and user.is_manager)
        db.session.delete(user)
        db.session.commit()


# Feature: rbac-modular-refactor, Property 2: Invalid Role Rejection
@given(role=st.text().filter(lambda r: r not in {'admin', 'manager', 'user'}))
@settings(max_examples=100)
def test_invalid_role_rejected(app, role):
    """Any string not in valid set must return a non-200 error."""
    with app.app_context():
        user = make_user()
        result, status = user_service.assign_role(user.id, role)
        assert status != 200
        assert 'error' in result
        db.session.delete(user)
        db.session.commit()


# Feature: rbac-modular-refactor, Property 13: Duplicate User Email Returns Conflict
@given(email=st.emails())
@settings(max_examples=50)
def test_duplicate_email_returns_409(app, email):
    """create_user with an existing email must return 409."""
    with app.app_context():
        existing = User.query.filter_by(email=email).first()
        if not existing:
            make_user(email=email)
        result, status = user_service.create_user({'name': 'Dup', 'email': email})
        assert status == 409
        assert 'error' in result
        User.query.filter_by(email=email).delete()
        db.session.commit()


# Feature: rbac-modular-refactor, Property 14: Self-Deletion Is Prevented
@given(name=st.text(min_size=1, max_size=50))
@settings(max_examples=50)
def test_self_deletion_prevented(app, name):
    """delete_user(uid, uid) must return error and user must still exist."""
    with app.app_context():
        user = make_user(name=name)
        result, status = user_service.delete_user(user.id, user.id)
        assert status != 200
        assert 'error' in result
        assert User.query.get(user.id) is not None
        db.session.delete(user)
        db.session.commit()


# Feature: rbac-modular-refactor, Property 15: Delete User Cascades to Owned Records
def test_cascade_delete_property(app):
    """After delete_user, owned events and conversations must be gone."""
    with app.app_context():
        admin = make_user(role='admin')
        campus = make_campus()
        target = make_user()
        make_event(creator_id=target.id, campus_id=campus.id)
        conv = Conversation(id='conv-prop', user_id=target.id, messages=[])
        db.session.add(conv)
        db.session.commit()

        user_service.delete_user(target.id, admin.id)

        assert Event.query.filter_by(created_by=target.id).count() == 0
        assert Conversation.query.filter_by(user_id=target.id).count() == 0
