"""
RBAC decorators for Campus Explorer.
Centralized authorization middleware — import from here, never redefine locally.
"""

from functools import wraps
from flask import jsonify, redirect, url_for
from flask_login import current_user


def require_authenticated(f):
    """Redirect unauthenticated users to the login page."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Return HTTP 403 JSON if the current user is not Admin_Role.
    Compose after require_authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Admin privileges required.'}), 403
        return f(*args, **kwargs)
    return decorated


def require_manager_or_admin(f):
    """Return HTTP 403 JSON if the current user is User_Role.
    Compose after require_authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not (current_user.is_admin or current_user.is_manager):
            return jsonify({'error': 'Manager or Admin privileges required.'}), 403
        return f(*args, **kwargs)
    return decorated
