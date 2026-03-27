"""
Main routes for Campus Explorer.
"""

from flask import render_template, redirect, url_for
from flask_login import current_user, login_required
from app.main import bp


@bp.route('/')
@login_required
def index():
    """Main application page - requires authentication."""
    return render_template('index.html', user=current_user)


@bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@bp.route('/contact')
def contact():
    """Contact page."""
    return render_template('contact.html')