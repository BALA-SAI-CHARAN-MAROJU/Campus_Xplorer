"""
College (campus) service — all campus CRUD logic.
"""

from flask import current_app
from app import db
from app.models import Campus, Event


def _validate_coords(lat, lng):
    """Return error string if coordinates are out of range, else None."""
    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        return 'Coordinates must be numeric.'
    if not (-90 <= lat <= 90):
        return 'Latitude must be between -90 and 90.'
    if not (-180 <= lng <= 180):
        return 'Longitude must be between -180 and 180.'
    return None


def add_college(data: dict) -> tuple:
    """
    Add a new campus.
    Required: id, name, display_name, center_latitude, center_longitude
    Trims whitespace from name and display_name.
    Returns (campus_dict, 201) on success, error tuple otherwise.
    """
    if not data:
        return {'error': 'Request body is required.'}, 400

    missing = [f for f in ['id', 'name', 'display_name', 'center_latitude', 'center_longitude']
               if f not in data or data[f] is None]
    if missing:
        return {'error': f'Missing required fields: {", ".join(missing)}'}, 400

    coord_err = _validate_coords(data['center_latitude'], data['center_longitude'])
    if coord_err:
        return {'error': coord_err}, 400

    if Campus.query.get(data['id']):
        return {'error': f'Campus with id "{data["id"]}" already exists.'}, 409

    try:
        campus = Campus(
            id=data['id'],
            name=data['name'].strip(),
            display_name=data['display_name'].strip(),
            center_latitude=float(data['center_latitude']),
            center_longitude=float(data['center_longitude']),
            locations_data=data.get('locations_data', {}),
            map_bounds=data.get('map_bounds', {}),
            timezone=data.get('timezone', 'UTC'),
        )
        db.session.add(campus)
        db.session.commit()
        return campus.to_dict(), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'add_college error: {e}')
        return {'error': 'Internal server error'}, 500


def edit_college(college_id: str, data: dict) -> tuple:
    """
    Update an existing campus.
    Validates coordinate ranges; trims whitespace from name/display_name.
    Returns (campus_dict, 200) on success, error tuple otherwise.
    """
    campus = Campus.query.get(college_id)
    if not campus:
        return {'error': 'Campus not found.'}, 404

    if not data:
        return campus.to_dict(), 200

    try:
        if 'name' in data:
            campus.name = data['name'].strip()
        if 'display_name' in data:
            campus.display_name = data['display_name'].strip()
        if 'timezone' in data:
            campus.timezone = data['timezone']

        lat = data.get('center_latitude', campus.center_latitude)
        lng = data.get('center_longitude', campus.center_longitude)
        coord_err = _validate_coords(lat, lng)
        if coord_err:
            return {'error': coord_err}, 400
        campus.center_latitude = float(lat)
        campus.center_longitude = float(lng)

        db.session.commit()
        return campus.to_dict(), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'edit_college error: {e}')
        return {'error': 'Internal server error'}, 500


def delete_college(college_id: str) -> tuple:
    """
    Delete a campus. Fails if active events reference this campus.
    Returns ({'message': ...}, 200) on success, error tuple otherwise.
    """
    campus = Campus.query.get(college_id)
    if not campus:
        return {'error': 'Campus not found.'}, 404

    active_events = Event.query.filter_by(campus_id=college_id, is_active=True).count()
    if active_events > 0:
        return {'error': f'Cannot delete campus: {active_events} active event(s) reference it.'}, 400

    try:
        name = campus.display_name
        db.session.delete(campus)
        db.session.commit()
        return {'message': f'Campus "{name}" deleted successfully.'}, 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'delete_college error: {e}')
        return {'error': 'Internal server error'}, 500


def get_colleges() -> tuple:
    """Return all active campuses."""
    campuses = Campus.query.filter_by(is_active=True).all()
    return [c.to_dict() for c in campuses], 200
