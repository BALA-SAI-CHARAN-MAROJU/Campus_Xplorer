"""
User service — all user CRUD and role assignment logic.
"""

import uuid
from datetime import datetime
from flask import current_app
from app import db
from app.models import User, Event, Conversation

VALID_ROLES = {"admin", "manager", "user"}


def create_user(data: dict) -> tuple:
    """
    Create a new user.
    Required fields: name, email
    Returns (user_dict, 201) on success, error tuple otherwise.
    """
    if not data or not all(k in data for k in ['name', 'email']):
        return {'error': 'Missing required fields: name, email'}, 400

    if User.query.filter_by(email=data['email']).first():
        return {'error': 'A user with this email already exists.'}, 409

    try:
        user = User(
            id=str(uuid.uuid4()),
            google_id=f'admin_created_{uuid.uuid4()}',
            email=data['email'],
            name=data['name'],
            is_admin=False,
            is_manager=False,
            preferred_campus=data.get('preferred_campus', 'amrita-chennai'),
            created_at=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.commit()
        return user.to_dict(), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'create_user error: {e}')
        return {'error': 'Internal server error'}, 500


def update_user(user_id: str, data: dict) -> tuple:
    """
    Update mutable user fields: name, preferred_campus, theme_preference.
    Returns (user_dict, 200) on success, error tuple otherwise.
    """
    user = User.query.get(user_id)
    if not user:
        return {'error': 'User not found.'}, 404

    try:
        if 'name' in data:
            user.name = data['name']
        if 'preferred_campus' in data:
            user.preferred_campus = data['preferred_campus']
        if 'theme_preference' in data:
            user.theme_preference = data['theme_preference']
        db.session.commit()
        return user.to_dict(), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'update_user error: {e}')
        return {'error': 'Internal server error'}, 500


def delete_user(user_id: str, requesting_user_id: str) -> tuple:
    """
    Delete a user and cascade to their events and conversations.
    Prevents self-deletion.
    Returns ({'message': ...}, 200) on success, error tuple otherwise.
    """
    if user_id == requesting_user_id:
        return {'error': 'Cannot delete your own account.'}, 400

    user = User.query.get(user_id)
    if not user:
        return {'error': 'User not found.'}, 404

    try:
        Event.query.filter_by(created_by=user_id).delete()
        Conversation.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        return {'message': f'User "{user.name}" deleted successfully.'}, 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'delete_user error: {e}')
        return {'error': 'Internal server error'}, 500


def assign_role(user_id: str, role: str) -> tuple:
    """
    Assign a role to a user, enforcing mutual exclusivity.
    role must be one of: "admin", "manager", "user"
    Returns (user_dict, 200) on success, error tuple otherwise.
    """
    if role not in VALID_ROLES:
        return {'error': f'Invalid role "{role}". Must be one of: admin, manager, user.'}, 400

    user = User.query.get(user_id)
    if not user:
        return {'error': 'User not found.'}, 404

    try:
        if role == 'admin':
            user.is_admin = True
            user.is_manager = False
        elif role == 'manager':
            user.is_admin = False
            user.is_manager = True
        else:  # 'user'
            user.is_admin = False
            user.is_manager = False
        db.session.commit()
        return user.to_dict(), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'assign_role error: {e}')
        return {'error': 'Internal server error'}, 500
