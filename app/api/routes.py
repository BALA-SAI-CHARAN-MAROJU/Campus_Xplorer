"""
API routes for Campus Explorer.
Maintains compatibility with existing frontend while adding new features.
"""

from datetime import datetime, date, time
from flask import request, jsonify, current_app
from flask_login import current_user
from app.api import bp
from app.models import Event, Campus, User
from app import db
from app.auth.decorators import require_authenticated, require_manager_or_admin, require_admin
from app.services import event_service, place_service, user_service
import json
import os

# Legacy file-based events for backward compatibility
EVENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'events.json')

def load_legacy_events():
    """Load events from legacy JSON file."""
    if os.path.exists(EVENTS_FILE):
        try:
            with open(EVENTS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            current_app.logger.error(f"Error loading legacy events: {e}")
            return []
    return []

def migrate_legacy_events():
    """Migrate legacy events to database if needed."""
    legacy_events = load_legacy_events()
    if not legacy_events:
        return
    
    for event_data in legacy_events:
        # Check if event already exists
        existing_event = Event.query.filter_by(id=event_data.get('id')).first()
        if existing_event:
            continue
        
        try:
            # Parse date and time
            event_date = datetime.strptime(event_data['date'], '%Y-%m-%d').date()
            start_time = datetime.strptime(event_data['time'], '%H:%M').time()
            end_time = None
            if event_data.get('end_time'):
                end_time = datetime.strptime(event_data['end_time'], '%H:%M').time()
            
            # Create new event
            event = Event(
                id=event_data.get('id'),
                name=event_data['name'],
                description=event_data.get('description', ''),
                venue_name=event_data['venue_name'],
                campus_id='amrita-chennai',  # Default campus
                date=event_date,
                start_time=start_time,
                end_time=end_time,
                created_by='legacy',  # Placeholder for legacy events
                created_at=datetime.strptime(event_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')), '%Y-%m-%d %H:%M:%S')
            )
            
            db.session.add(event)
            
        except Exception as e:
            current_app.logger.error(f"Error migrating event {event_data.get('id')}: {e}")
            continue
    
    try:
        db.session.commit()
        current_app.logger.info(f"Migrated {len(legacy_events)} legacy events to database")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error committing migrated events: {e}")

@bp.route('/locations', methods=['GET'])
def get_locations():
    """Get locations for the current or specified campus."""
    campus_id = request.args.get('campus', 'amrita-chennai')
    
    # Get campus data
    campus = Campus.query.filter_by(id=campus_id, is_active=True).first()
    if not campus:
        # Return default Chennai campus locations for backward compatibility
        locations = [
            {'name': 'Academic Block', 'coordinates': [13.263018, 80.027427]},
            {'name': 'Library', 'coordinates': [13.262621, 80.026525]},
            {'name': 'Canteen', 'coordinates': [13.262856, 80.028401]},
            {'name': 'Pond', 'coordinates': [13.262198, 80.027673]},
            {'name': 'AVV Gym for Girls', 'coordinates': [13.262141, 80.026830]},
            {'name': 'Junior Girls Hostel', 'coordinates': [13.261993, 80.026421]},
            {'name': 'Junior Boys Hostel', 'coordinates': [13.261805, 80.028076]},
            {'name': 'Lab Block', 'coordinates': [13.262768, 80.028147]},
            {'name': 'Mechanical Lab', 'coordinates': [13.261205, 80.027488]},
            {'name': 'Volley Ball Court', 'coordinates': [13.261009, 80.027530]},
            {'name': 'Basket Ball Court', 'coordinates': [13.260909, 80.027256]},
            {'name': 'Senior Girls Hostel', 'coordinates': [13.260658, 80.028184]},
            {'name': 'Senior Boys Hostel', 'coordinates': [13.260550, 80.027272]},
            {'name': '2nd Year Boys Hostel', 'coordinates': [13.259570, 80.026694]},
            {'name': 'Amrita Indoor Stadium', 'coordinates': [13.259880, 80.025990]},
            {'name': 'AVV Gym for Boys', 'coordinates': [13.260146, 80.026143]},
            {'name': 'AVV Ground', 'coordinates': [13.259708, 80.025416]},
            {'name': 'Amrita Vishwa Vidyapeetham', 'coordinates': [13.2630, 80.0274]}
        ]
        return jsonify(locations)
    
    # Convert campus locations to expected format
    locations = []
    if campus.locations_data:
        for name, coordinates in campus.locations_data.items():
            locations.append({
                'name': name,
                'coordinates': coordinates
            })
    
    return jsonify(locations)

@bp.route('/campuses', methods=['GET'])
def get_campuses():
    """Get all available campuses."""
    campuses = Campus.query.filter_by(is_active=True).all()
    return jsonify({
        'campuses': [campus.to_dict() for campus in campuses]
    })

@bp.route('/events/counts', methods=['GET'])
def get_event_counts():
    """Get event counts per campus."""
    try:
        # Get event counts grouped by campus
        from sqlalchemy import func
        
        counts = db.session.query(
            Event.campus_id,
            func.count(Event.id).label('count')
        ).filter(
            Event.is_active == True,
            Event.date >= date.today()
        ).group_by(Event.campus_id).all()
        
        # Convert to dictionary
        event_counts = {}
        for campus_id, count in counts:
            event_counts[campus_id] = count
        
        return jsonify({
            'counts': event_counts
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting event counts: {str(e)}')
        return jsonify({'counts': {}})

@bp.route('/events', methods=['GET'])
def get_events():
    """Get events with filtering and sorting."""
    # Migrate legacy events if needed
    migrate_legacy_events()
    
    sort_by = request.args.get('sort_by', 'created_at')
    filter_type = request.args.get('filter', None)
    campus_id = request.args.get('campus', None)
    
    # Build query
    query = Event.query.filter_by(is_active=True)
    
    if campus_id:
        query = query.filter_by(campus_id=campus_id)
    
    events = query.all()
    
    # Convert to list of dictionaries
    events_data = []
    now = datetime.now()
    
    for event in events:
        event_dict = event.to_dict()
        
        # Calculate time left for sorting
        try:
            event_datetime = datetime.combine(event.date, event.start_time)
            event_dict['time_left'] = (event_datetime - now).total_seconds()
        except:
            event_dict['time_left'] = float('inf')
        
        events_data.append(event_dict)
    
    # Apply filters
    if filter_type == 'upcoming':
        events_data = [e for e in events_data if e['time_left'] > 0]
    elif filter_type == 'past':
        events_data = [e for e in events_data if e['time_left'] <= 0]
    
    # Apply sorting
    if sort_by == 'created_at':
        events_data.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_by == 'expiry':
        events_data.sort(key=lambda x: x['time_left'])
    
    # Remove temporary time_left field
    for event in events_data:
        if 'time_left' in event:
            del event['time_left']
    
    return jsonify(events_data)

@bp.route('/events', methods=['POST'])
@require_authenticated
@require_manager_or_admin
def add_event():
    """Add a new event - Manager and Admin only."""
    result, status = event_service.create_event(request.json, current_user.id)
    return jsonify(result), status

@bp.route('/events/<int:event_id>')
def get_event(event_id):
    """Get a single event by ID."""
    event = Event.query.get_or_404(event_id)
    return jsonify(event.to_dict())

@bp.route('/events/<int:event_id>', methods=['DELETE'])
@require_authenticated
@require_manager_or_admin
def delete_event(event_id):
    """Delete an event - Manager and Admin only."""
    result, status = event_service.delete_event(event_id)
    return jsonify(result), status

@bp.route('/events/<int:event_id>', methods=['PUT'])
@require_authenticated
@require_manager_or_admin
def update_event(event_id):
    """Update an event - Manager and Admin only."""
    result, status = event_service.update_event(event_id, request.json)
    return jsonify(result), status

@bp.route('/chat', methods=['POST'])
def chat():
    """Groq-powered AI chat endpoint with live campus/event context."""
    data = request.json or {}
    message = (data.get('message') or '').strip()

    if not message:
        return jsonify({'reply': 'Please type a message so I can help you.'}), 400

    # Build user context
    user_context = {}
    if current_user.is_authenticated:
        user_context = {
            'user_id': current_user.id,
            'campus': current_user.preferred_campus,
            'user_name': current_user.name,
        }
    else:
        user_context = {'campus': 'amrita-chennai', 'user_name': 'there'}

    # Conversation history sent from the frontend (list of {role, content})
    history = data.get('history') or []

    # Try Groq first; fall back to the rule-based assistant if key is missing
    try:
        from app.services.groq_chat import get_groq_reply
        reply = get_groq_reply(message, user_context, history)
    except Exception as e:
        current_app.logger.warning(f"Groq unavailable, falling back: {e}")
        from app.services.ai_assistant import ai_assistant
        reply = ai_assistant.process_query(message, user_context)

    return jsonify({'reply': reply})

# Location Management Endpoints

@bp.route('/campuses/<campus_id>/locations', methods=['POST'])
@require_authenticated
@require_manager_or_admin
def add_location(campus_id):
    """Add a new location to a campus - Manager and Admin only."""
    result, status = place_service.add_place(campus_id, request.json)
    return jsonify(result), status

@bp.route('/campuses/<campus_id>/locations/<location_name>', methods=['PUT'])
@require_authenticated
@require_manager_or_admin
def update_location(campus_id, location_name):
    """Update a location in a campus - Manager and Admin only."""
    result, status = place_service.edit_place(campus_id, location_name, request.json)
    return jsonify(result), status

@bp.route('/campuses/<campus_id>/locations/<location_name>', methods=['DELETE'])
@require_authenticated
@require_manager_or_admin
def delete_location(campus_id, location_name):
    """Delete a location from a campus - Manager and Admin only."""
    result, status = place_service.delete_place(campus_id, location_name)
    return jsonify(result), status

# User Management Endpoints (Admin only — see also /admin/api/users)

@bp.route('/users/<user_id>/role', methods=['PUT'])
@require_authenticated
@require_admin
def update_user_role(user_id):
    """Update user role - Admin only."""
    data = request.json or {}
    role = data.get('role')
    if not role:
        return jsonify({'error': 'Missing required field: role'}), 400
    result, status = user_service.assign_role(user_id, role)
    return jsonify(result), status

# Enhanced AI processing is now handled by the AIAssistant service

# Legacy compatibility endpoints
@bp.route('/paths', methods=['GET'])
def get_paths():
    """Legacy endpoint for backward compatibility."""
    return jsonify({'message': 'This endpoint is deprecated. Path finding is handled client-side.'}), 410

@bp.route('/shortest_path', methods=['GET'])
def get_shortest_path():
    """Legacy endpoint for backward compatibility."""
    return jsonify({'message': 'This endpoint is deprecated. Use the enhanced map features instead.'}), 410