"""
Authentication routes for Google OAuth integration.
"""

import uuid
import requests
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlencode
from app.auth import bp
from app.models import User
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(user_id)

@bp.route('/login')
def login():
    """Display login page with Google OAuth option."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Generate Google OAuth URL
    google_auth_url = get_google_auth_url()
    
    return render_template('auth/login.html', google_auth_url=google_auth_url)

@bp.route('/signup')
def signup():
    """Display signup page with Google OAuth option."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Generate Google OAuth URL
    google_auth_url = get_google_auth_url()
    
    return render_template('auth/signup.html', google_auth_url=google_auth_url)

@bp.route('/google')
def google_auth():
    """Initiate Google OAuth flow."""
    google_auth_url = get_google_auth_url()
    return redirect(google_auth_url)

@bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback."""
    try:
        # Get authorization code from callback
        code = request.args.get('code')
        if not code:
            flash('Authorization failed. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Exchange code for access token
        token_data = exchange_code_for_token(code)
        if not token_data:
            flash('Failed to get access token. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Get user info from Google
        user_info = get_google_user_info(token_data['access_token'])
        if not user_info:
            flash('Failed to get user information. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Find or create user
        user = User.query.filter_by(google_id=user_info['id']).first()
        
        if not user:
            # Create new user
            user = User(
                id=str(uuid.uuid4()),
                google_id=user_info['id'],
                email=user_info['email'],
                name=user_info['name'],
                profile_picture=user_info.get('picture', ''),
                is_admin=(user_info['email'] == current_app.config.get('DEFAULT_ADMIN_EMAIL', ''))
            )
            db.session.add(user)
        else:
            # Update existing user info
            user.name = user_info['name']
            user.profile_picture = user_info.get('picture', '')
            user.email = user_info['email']
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log in user
        login_user(user, remember=True)
        
        flash(f'Welcome, {user.name}!', 'success')
        
        # Redirect to next page or main page
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('main.index'))
        
    except Exception as e:
        current_app.logger.error(f'OAuth callback error: {str(e)}')
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    """Display user profile page."""
    return render_template('auth/profile.html', user=current_user)

@bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile preferences."""
    try:
        data = request.get_json()
        
        if 'preferred_campus' in data:
            current_user.preferred_campus = data['preferred_campus']
        
        if 'theme_preference' in data:
            current_user.theme_preference = data['theme_preference']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f'Profile update error: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to update profile'
        }), 500

def get_google_auth_url():
    """Generate Google OAuth authorization URL."""
    base_url = "https://accounts.google.com/o/oauth2/auth"
    params = {
        'client_id': current_app.config['GOOGLE_CLIENT_ID'],
        'redirect_uri': url_for('auth.google_callback', _external=True),
        'scope': 'openid email profile',
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    return f"{base_url}?{urlencode(params)}"

def exchange_code_for_token(code):
    """Exchange authorization code for access token."""
    try:
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': current_app.config['GOOGLE_CLIENT_ID'],
            'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('auth.google_callback', _external=True)
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        current_app.logger.error(f'Token exchange error: {str(e)}')
        return None

def get_google_user_info(access_token):
    """Get user information from Google API."""
    try:
        user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
        response = requests.get(user_info_url)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        current_app.logger.error(f'User info error: {str(e)}')
        return None