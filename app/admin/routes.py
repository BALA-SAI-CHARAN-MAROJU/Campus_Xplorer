"""
Admin panel routes for Campus Explorer.
"""

from flask import render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import current_user
from sqlalchemy import desc
from app.admin import bp
from app.models import User, Event, Campus, Conversation
from app import db
from app.auth.decorators import require_authenticated, require_admin, require_manager_or_admin
from app.services import user_service, college_service
from datetime import datetime, timedelta

@bp.route('/')
@require_authenticated
@require_admin
def dashboard():
    """Admin dashboard."""
    return render_template('admin/dashboard.html')

@bp.route('/events')
@require_authenticated
@require_admin
def events():
    """Admin events management."""
    page = request.args.get('page', 1, type=int)
    campus_filter = request.args.get('campus', '')
    
    query = Event.query.filter_by(is_active=True)
    
    if campus_filter:
        query = query.filter_by(campus_id=campus_filter)
    
    events = query.order_by(Event.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    campuses = Campus.query.filter_by(is_active=True).all()
    
    return render_template('admin/events.html',
                         events=events,
                         campuses=campuses,
                         campus_filter=campus_filter)

@bp.route('/events/<int:event_id>/toggle', methods=['POST'])
@require_authenticated
@require_admin
def toggle_event(event_id):
    """Toggle event active status."""
    event = Event.query.get_or_404(event_id)
    
    try:
        event.is_active = not event.is_active
        event.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = 'activated' if event.is_active else 'deactivated'
        return jsonify({
            'success': True,
            'message': f'Event "{event.name}" {status} successfully',
            'is_active': event.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update event status'
        }), 500

@bp.route('/users')
@require_authenticated
@require_admin
def users():
    """Admin users management."""
    page = request.args.get('page', 1, type=int)
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users)

@bp.route('/users/<user_id>/toggle-admin', methods=['POST'])
@require_authenticated
@require_admin
def toggle_user_admin(user_id):
    """Toggle user admin status."""
    if user_id == current_user.id:
        return jsonify({
            'success': False,
            'error': 'Cannot modify your own admin status'
        }), 400
    
    user = User.query.get_or_404(user_id)
    
    try:
        user.is_admin = not user.is_admin
        db.session.commit()
        
        status = 'granted' if user.is_admin else 'revoked'
        return jsonify({
            'success': True,
            'message': f'Admin privileges {status} for {user.name}',
            'is_admin': user.is_admin
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update user privileges'
        }), 500

@bp.route('/users/<user_id>/toggle-manager', methods=['POST'])
@require_authenticated
@require_admin
def toggle_user_manager(user_id):
    """Toggle user manager status - Admin only."""
    user = User.query.get_or_404(user_id)
    
    try:
        user.is_manager = not user.is_manager
        db.session.commit()
        
        status = 'granted' if user.is_manager else 'revoked'
        return jsonify({
            'success': True,
            'message': f'Manager privileges {status} for {user.name}',
            'is_manager': user.is_manager
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update user privileges'
        }), 500

@bp.route('/campuses')
@require_authenticated
@require_manager_or_admin
def campuses():
    """Campus management - Admin and Manager access."""
    campuses = Campus.query.order_by(Campus.created_at.desc()).all()
    return render_template('admin/campuses.html', campuses=campuses)

@bp.route('/locations')
@require_authenticated
@require_manager_or_admin
def locations():
    """Location management page - Admin and Manager access."""
    campuses = Campus.query.filter_by(is_active=True).order_by(Campus.display_name).all()
    return render_template('admin/locations.html', campuses=campuses)

@bp.route('/campuses/<campus_id>/toggle', methods=['POST'])
@require_authenticated
@require_admin
def toggle_campus(campus_id):
    """Toggle campus active status."""
    campus = Campus.query.get_or_404(campus_id)
    
    try:
        campus.is_active = not campus.is_active
        db.session.commit()
        
        status = 'activated' if campus.is_active else 'deactivated'
        return jsonify({
            'success': True,
            'message': f'Campus "{campus.display_name}" {status} successfully',
            'is_active': campus.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update campus status'
        }), 500

@bp.route('/system')
@require_authenticated
@require_admin
def system():
    """System information and settings."""
    # Get system statistics
    stats = {
        'total_users': User.query.count(),
        'admin_users': User.query.filter_by(is_admin=True).count(),
        'total_events': Event.query.count(),
        'active_events': Event.query.filter_by(is_active=True).count(),
        'total_campuses': Campus.query.count(),
        'active_campuses': Campus.query.filter_by(is_active=True).count()
    }
    
    return render_template('admin/system.html', stats=stats)

# API Routes for Admin Dashboard

@bp.route('/api/users')
@require_authenticated
@require_admin
def api_users():
    """Get all users."""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@bp.route('/api/users/<user_id>')
@require_authenticated
@require_admin
def api_get_user(user_id):
    """Get a single user by ID."""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@bp.route('/api/users', methods=['POST'])
@require_authenticated
@require_admin
def api_create_user():
    """Create a new user."""
    result, status = user_service.create_user(request.get_json())
    return jsonify(result), status

@bp.route('/api/users/<user_id>', methods=['DELETE'])
@require_authenticated
@require_admin
def api_delete_user(user_id):
    """Delete a user."""
    result, status = user_service.delete_user(user_id, current_user.id)
    return jsonify(result), status

@bp.route('/api/users/<user_id>', methods=['PUT'])
@require_authenticated
@require_admin
def api_update_user(user_id):
    """Update a user's profile fields."""
    result, status = user_service.update_user(user_id, request.get_json())
    return jsonify(result), status

@bp.route('/api/events')
@require_authenticated
@require_admin
def api_events():
    """Get all events with creator information."""
    events = db.session.query(Event, User.name.label('creator_name')).join(
        User, Event.created_by == User.id, isouter=True
    ).all()
    
    events_data = []
    for event, creator_name in events:
        event_dict = event.to_dict()
        event_dict['creator_name'] = creator_name
        events_data.append(event_dict)
    
    return jsonify(events_data)

@bp.route('/api/campuses')
@require_authenticated
@require_admin
def api_campuses():
    """Get all campuses."""
    campuses = Campus.query.all()
    return jsonify([campus.to_dict() for campus in campuses])

@bp.route('/api/campuses/<campus_id>')
@require_authenticated
@require_manager_or_admin
def api_get_campus(campus_id):
    """Get a single campus by ID."""
    campus = Campus.query.get_or_404(campus_id)
    return jsonify(campus.to_dict())

@bp.route('/api/campuses', methods=['POST'])
@require_authenticated
@require_manager_or_admin
def api_create_campus():
    """Add a new campus."""
    result, status = college_service.add_college(request.get_json())
    return jsonify(result), status

@bp.route('/api/campuses/<campus_id>', methods=['PUT'])
@require_authenticated
@require_manager_or_admin
def api_update_campus(campus_id):
    """Update an existing campus."""
    result, status = college_service.edit_college(campus_id, request.get_json())
    return jsonify(result), status

@bp.route('/api/campuses/<campus_id>', methods=['DELETE'])
@require_authenticated
@require_manager_or_admin
def api_delete_campus(campus_id):
    """Delete a campus."""
    result, status = college_service.delete_college(campus_id)
    return jsonify(result), status

@bp.route('/api/conversations')
@require_authenticated
@require_admin
def api_conversations():
    """Get all conversations with user information."""
    conversations = db.session.query(Conversation, User.name.label('user_name')).join(
        User, Conversation.user_id == User.id, isouter=True
    ).all()
    
    conversations_data = []
    for conversation, user_name in conversations:
        conversation_dict = conversation.to_dict()
        conversation_dict['user_name'] = user_name
        conversation_dict['message_count'] = len(conversation.messages) if conversation.messages else 0
        conversations_data.append(conversation_dict)
    
    return jsonify(conversations_data)

@bp.route('/api/conversations/<conversation_id>', methods=['DELETE'])
@require_authenticated
@require_admin
def api_delete_conversation(conversation_id):
    """Delete a conversation."""
    conversation = Conversation.query.get_or_404(conversation_id)
    
    try:
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({'message': 'Conversation deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting conversation: {str(e)}')
        return jsonify({'error': 'Failed to delete conversation'}), 500

@bp.route('/api/recent-activity')
@require_authenticated
@require_admin
def api_recent_activity():
    """Get recent activity for dashboard."""
    activities = []
    
    try:
        # Recent users (last 7 days)
        recent_users = User.query.filter(
            User.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(desc(User.created_at)).limit(5).all()
        
        for user in recent_users:
            activities.append({
                'description': f'New user registered: {user.name}',
                'timestamp': user.created_at.isoformat(),
                'type': 'user'
            })
        
        # Recent events (last 7 days)
        recent_events = Event.query.filter(
            Event.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(desc(Event.created_at)).limit(5).all()
        
        for event in recent_events:
            activities.append({
                'description': f'New event created: {event.name}',
                'timestamp': event.created_at.isoformat(),
                'type': 'event'
            })
        
        # Recent conversations (last 7 days)
        recent_conversations = Conversation.query.filter(
            Conversation.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(desc(Conversation.created_at)).limit(5).all()
        
        for conversation in recent_conversations:
            activities.append({
                'description': f'New AI conversation started',
                'timestamp': conversation.created_at.isoformat(),
                'type': 'conversation'
            })
        
        # Sort all activities by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify(activities[:10])  # Return top 10 most recent
        
    except Exception as e:
        current_app.logger.error(f'Error loading recent activity: {str(e)}')
        return jsonify({'error': 'Failed to load recent activity'}), 500

@bp.route('/api/stats')
@require_authenticated
@require_admin
def api_stats():
    """Get system statistics."""
    try:
        stats = {
            'total_users': User.query.count(),
            'admin_users': User.query.filter_by(is_admin=True).count(),
            'manager_users': User.query.filter_by(is_manager=True).count(),
            'total_events': Event.query.count(),
            'active_events': Event.query.filter_by(is_active=True).count(),
            'total_campuses': Campus.query.count(),
            'active_campuses': Campus.query.filter_by(is_active=True).count(),
            'total_conversations': Conversation.query.count()
        }
        return jsonify(stats)
    except Exception as e:
        current_app.logger.error(f'Error loading stats: {str(e)}')
        return jsonify({'error': 'Failed to load statistics'}), 500