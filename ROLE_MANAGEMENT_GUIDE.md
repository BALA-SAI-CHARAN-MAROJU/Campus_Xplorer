# Role Management & Location Management Guide

## Overview
Successfully implemented role-based access control with Admin and Manager roles, plus location management system for Campus Explorer.

---

## New Features Implemented

### 1. Manager Role ✅
- Added new `is_manager` column to User model
- Managers can add/edit/delete events and locations
- Managers cannot manage users or system settings (Admin only)

### 2. Location Management System ✅
- Admin and Manager can add locations to any campus
- Edit existing locations (name and coordinates)
- Delete locations from campuses
- Dedicated location management interface at `/admin/locations`

### 3. Event Restrictions ✅
- Only Admin and Manager can create events
- Only Admin and Manager can edit events
- Only Admin and Manager can delete events
- Regular users can only view events

---

## User Roles

### Regular User
- Can view campus maps
- Can view events
- Can use AI chatbot
- Cannot create/edit/delete events
- Cannot manage locations

### Manager
- All Regular User permissions
- Can create/edit/delete events
- Can add/edit/delete locations for all campuses
- Cannot manage users
- Cannot change system settings
- Access to Location Management page

### Admin
- All Manager permissions
- Can manage users (promote to Admin/Manager)
- Can toggle campus active status
- Full system access
- Access to full Admin Dashboard

---

## How to Use

### For Admins: Promoting Users to Manager

1. Login as Admin
2. Go to Admin Dashboard (`/admin`)
3. Navigate to Users section
4. Find the user you want to promote
5. Click "Toggle Manager" button
6. User now has Manager privileges

### For Managers: Managing Locations

1. Login as Manager or Admin
2. Click "Manager" button in header (or go to `/admin/locations`)
3. Select a campus from dropdown
4. View all locations for that campus
5. Add new location:
   - Enter location name
   - Enter latitude and longitude
   - Click "Add Location"
6. Edit location:
   - Click "Edit" on location card
   - Update name or coordinates
   - Click "Save Changes"
7. Delete location:
   - Click "Delete" on location card
   - Confirm deletion

### For Managers: Managing Events

1. Login as Manager or Admin
2. Go to main page
3. Navigate to Events section
4. Click "Add Event" tab
5. Fill in event details:
   - Event name
   - Venue name
   - Date and time
   - Description (optional)
6. Click "Add Event"

---

## Database Migration

The `is_manager` column was added using the migration script:

```bash
python migrate_add_manager_role.py
```

This script:
- Adds `is_manager` column to users table
- Sets default value to False for all existing users
- Preserves all existing data

---

## API Endpoints

### Location Management (Manager/Admin only)

#### Add Location
```
POST /api/campuses/{campus_id}/locations
Body: {
  "name": "Location Name",
  "latitude": 13.263018,
  "longitude": 80.027427
}
```

#### Update Location
```
PUT /api/campuses/{campus_id}/locations/{location_name}
Body: {
  "name": "New Name",
  "latitude": 13.263018,
  "longitude": 80.027427
}
```

#### Delete Location
```
DELETE /api/campuses/{campus_id}/locations/{location_name}
```

### User Management (Admin only)

#### Toggle Manager Role
```
POST /admin/users/{user_id}/toggle-manager
```

#### Toggle Admin Role
```
POST /admin/users/{user_id}/toggle-admin
```

### Event Management (Manager/Admin only)

#### Create Event
```
POST /api/events
Body: {
  "name": "Event Name",
  "venue_name": "Venue",
  "date": "2026-03-15",
  "time": "14:00",
  "description": "Event description",
  "campus_id": "amrita-chennai"
}
```

#### Update Event
```
PUT /api/events/{event_id}
Body: { ... same as create ... }
```

#### Delete Event
```
DELETE /api/events/{event_id}
```

---

## Files Modified

### Models
- `app/models.py` - Added `is_manager` field and `can_manage_content()` method

### Routes
- `app/api/routes.py` - Added location management endpoints, restricted event endpoints
- `app/admin/routes.py` - Added manager decorator, location routes, manager toggle

### Templates
- `templates/admin/locations.html` - New location management interface
- `templates/index.html` - Updated header to show Manager badge

### Migration
- `migrate_add_manager_role.py` - Database migration script

---

## Security Features

1. **Role-Based Access Control**
   - Decorators enforce permissions at route level
   - `@admin_required` - Admin only
   - `@manager_required` - Manager or Admin
   - `@login_required` - Any authenticated user

2. **Permission Checks**
   - `user.can_manage_content()` - Returns True for Admin or Manager
   - Prevents unauthorized access to management features

3. **Data Validation**
   - Coordinate validation (-90 to 90 for latitude, -180 to 180 for longitude)
   - Duplicate location name checking
   - Required field validation

---

## Testing Checklist

✅ Regular user cannot create events
✅ Regular user cannot access location management
✅ Manager can create/edit/delete events
✅ Manager can add/edit/delete locations
✅ Manager cannot access user management
✅ Admin can do everything
✅ Admin can promote users to Manager
✅ Location changes persist in database
✅ Events restricted to Manager/Admin only

---

## Future Enhancements

Potential improvements:
1. Campus-specific managers (restrict manager to specific campus)
2. Bulk location import (CSV/JSON upload)
3. Location categories/tags
4. Location images
5. Audit log for location changes
6. Location approval workflow
7. Map preview when adding locations

---

## Troubleshooting

### Issue: "Operational Error" when accessing pages
**Solution:** Run the migration script:
```bash
python migrate_add_manager_role.py
```

### Issue: Manager cannot access location page
**Solution:** Check user's `is_manager` field in database:
```python
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='user@example.com').first()
    user.is_manager = True
    db.session.commit()
```

### Issue: Locations not saving
**Solution:** Check that `locations_data` is properly flagged as modified:
```python
from sqlalchemy.orm.attributes import flag_modified
flag_modified(campus, 'locations_data')
db.session.commit()
```

---

## Summary

All requested features have been successfully implemented:

✅ Added Manager role to User model
✅ Created location management interface for Admin/Manager
✅ Restricted event creation to Admin/Manager only
✅ Restricted location management to Admin/Manager only
✅ Added ability to add/edit/delete locations per campus
✅ Updated UI to show Manager badge
✅ Migrated database without data loss

The system now has proper role-based access control with three distinct user levels: Regular User, Manager, and Admin.
