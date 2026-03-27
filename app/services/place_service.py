"""
Place service — manages named locations within a campus (stored in Campus.locations_data JSON).
"""

from flask import current_app
from sqlalchemy.orm.attributes import flag_modified
from app import db
from app.models import Campus


def _validate_coords(lat, lng):
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


def add_place(college_id: str, data: dict) -> tuple:
    """
    Add a named place to a campus.
    Required: name, latitude, longitude
    Rejects whitespace-only names.
    Returns (place_dict, 201) on success, error tuple otherwise.
    """
    campus = Campus.query.get(college_id)
    if not campus:
        return {'error': 'Campus not found.'}, 404

    if not data or not all(k in data for k in ['name', 'latitude', 'longitude']):
        return {'error': 'Missing required fields: name, latitude, longitude'}, 400

    name = data['name']
    if not isinstance(name, str) or not name.strip():
        return {'error': 'Place name must be a non-empty, non-whitespace string.'}, 400

    coord_err = _validate_coords(data['latitude'], data['longitude'])
    if coord_err:
        return {'error': coord_err}, 400

    locations = campus.locations_data or {}
    if name in locations:
        return {'error': f'Place "{name}" already exists in this campus.'}, 409

    try:
        locations[name] = [float(data['latitude']), float(data['longitude'])]
        campus.locations_data = locations
        flag_modified(campus, 'locations_data')
        db.session.commit()
        return {'name': name, 'coordinates': locations[name]}, 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'add_place error: {e}')
        return {'error': 'Internal server error'}, 500


def edit_place(college_id: str, place_name: str, data: dict) -> tuple:
    """
    Update a place's name and/or coordinates.
    Returns (place_dict, 200) on success, error tuple otherwise.
    """
    campus = Campus.query.get(college_id)
    if not campus:
        return {'error': 'Campus not found.'}, 404

    locations = campus.locations_data or {}
    if place_name not in locations:
        return {'error': f'Place "{place_name}" not found.'}, 404

    new_name = data.get('name', place_name).strip() if data else place_name
    if not new_name:
        return {'error': 'Place name must be a non-empty string.'}, 400

    if new_name != place_name and new_name in locations:
        return {'error': f'Place "{new_name}" already exists in this campus.'}, 409

    if data and ('latitude' in data or 'longitude' in data):
        lat = data.get('latitude', locations[place_name][0])
        lng = data.get('longitude', locations[place_name][1])
        coord_err = _validate_coords(lat, lng)
        if coord_err:
            return {'error': coord_err}, 400
        coords = [float(lat), float(lng)]
    else:
        coords = locations[place_name]

    try:
        if new_name != place_name:
            del locations[place_name]
        locations[new_name] = coords
        campus.locations_data = locations
        flag_modified(campus, 'locations_data')
        db.session.commit()
        return {'name': new_name, 'coordinates': coords}, 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'edit_place error: {e}')
        return {'error': 'Internal server error'}, 500


def delete_place(college_id: str, place_name: str) -> tuple:
    """Remove a place from a campus. Returns 404 if college or place not found."""
    campus = Campus.query.get(college_id)
    if not campus:
        return {'error': 'Campus not found.'}, 404

    locations = campus.locations_data or {}
    if place_name not in locations:
        return {'error': f'Place "{place_name}" not found.'}, 404

    try:
        del locations[place_name]
        campus.locations_data = locations
        flag_modified(campus, 'locations_data')
        db.session.commit()
        return {'message': f'Place "{place_name}" deleted successfully.'}, 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'delete_place error: {e}')
        return {'error': 'Internal server error'}, 500


def get_places(college_id: str) -> tuple:
    """Return all places for a campus as a list of {name, coordinates}."""
    campus = Campus.query.get(college_id)
    if not campus:
        return {'error': 'Campus not found.'}, 404

    locations = campus.locations_data or {}
    result = [{'name': name, 'coordinates': coords} for name, coords in locations.items()]
    return result, 200
