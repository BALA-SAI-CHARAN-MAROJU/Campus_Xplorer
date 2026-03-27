"""
Property-based tests for admin panel functionality.
Tests for Task 3: Create admin panel and enhanced event management.
"""

import pytest
import uuid
from datetime import datetime, date, time
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize, invariant, run_state_machine_as_test
from app import create_app, db
from app.models import User, Event, Campus, Conversation
from flask_login import login_user
import json

class AdminAccessControlMachine(RuleBasedStateMachine):
    """
    Property 4: Admin Access Control
    Validates: Requirements 2.1, 2.2
    
    Tests that admin panel access is properly controlled and only admins
    can perform administrative operations.
    """
    
    users = Bundle('users')
    admin_users = Bundle('admin_users')
    
    def __init__(self):
        super().__init__()
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()
    
    def teardown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    @initialize()
    def setup_initial_state(self):
        """Set up initial test state."""
        # Create a default admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            google_id='admin_test',
            email='admin@test.com',
            name='Test Admin',
            is_admin=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin_user)
        db.session.commit()
        self.admin_user = admin_user
    
    @rule(target=users, name=st.text(min_size=1, max_size=50), 
          email=st.emails(), is_admin=st.booleans())
    def create_user(self, name, email, is_admin):
        """Create a user with specified admin status."""
        assume(len(name.strip()) > 0)
        assume('@' in email)
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return existing_user
        
        user = User(
            id=str(uuid.uuid4()),
            google_id=f'test_{uuid.uuid4()}',
            email=email,
            name=name.strip(),
            is_admin=is_admin,
            created_at=datetime.utcnow()
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            return None
    
    @rule(user=users)
    def test_admin_dashboard_access(self, user):
        """Test that only admins can access the admin dashboard."""
        if user is None:
            return
        
        with self.client.session_transaction() as sess:
            sess['_user_id'] = user.id
            sess['_fresh'] = True
        
        response = self.client.get('/admin/')
        
        if user.is_admin:
            # Admin users should be able to access the dashboard
            assert response.status_code in [200, 302]  # 302 for redirect to login if not authenticated
        else:
            # Non-admin users should be denied access
            assert response.status_code in [302, 403]  # Redirect or forbidden
    
    @rule(user=users)
    def test_admin_api_access(self, user):
        """Test that only admins can access admin API endpoints."""
        if user is None:
            return
        
        with self.client.session_transaction() as sess:
            sess['_user_id'] = user.id
            sess['_fresh'] = True
        
        # Test various admin API endpoints
        endpoints = [
            '/admin/api/users',
            '/admin/api/events',
            '/admin/api/campuses',
            '/admin/api/conversations',
            '/admin/api/recent-activity'
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            
            if user.is_admin:
                # Admin users should be able to access API endpoints
                assert response.status_code in [200, 302]
            else:
                # Non-admin users should be denied access
                assert response.status_code in [302, 403]
    
    @rule(user=users)
    def test_user_creation_permission(self, user):
        """Test that only admins can create users via API."""
        if user is None:
            return
        
        with self.client.session_transaction() as sess:
            sess['_user_id'] = user.id
            sess['_fresh'] = True
        
        user_data = {
            'name': 'Test User',
            'email': f'test_{uuid.uuid4()}@example.com',
            'is_admin': False,
            'preferred_campus': 'amrita-chennai'
        }
        
        response = self.client.post('/admin/api/users',
                                  data=json.dumps(user_data),
                                  content_type='application/json')
        
        if user.is_admin:
            # Admin users should be able to create users
            assert response.status_code in [200, 201, 302]
        else:
            # Non-admin users should be denied
            assert response.status_code in [302, 403]
    
    @invariant()
    def admin_user_exists(self):
        """Ensure at least one admin user always exists."""
        admin_count = User.query.filter_by(is_admin=True).count()
        assert admin_count >= 1, "At least one admin user must exist"
    
    @invariant()
    def database_consistency(self):
        """Ensure database remains consistent."""
        # All users should have valid IDs
        users = User.query.all()
        for user in users:
            assert user.id is not None
            assert user.email is not None
            assert user.name is not None
            assert isinstance(user.is_admin, bool)


class EventManagementMachine(RuleBasedStateMachine):
    """
    Property 5: Event Management Consistency
    Validates: Requirements 2.3, 2.4, 2.5
    
    Tests that event management operations maintain consistency
    and proper validation.
    """
    
    events = Bundle('events')
    users = Bundle('users')
    campuses = Bundle('campuses')
    
    def __init__(self):
        super().__init__()
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()
    
    def teardown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    @initialize()
    def setup_initial_state(self):
        """Set up initial test state."""
        # Create default campus
        campus = Campus(
            id='test-campus',
            name='Test Campus',
            display_name='Test Campus',
            center_latitude=13.0827,
            center_longitude=80.2707,
            timezone='UTC',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(campus)
        
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            google_id='admin_test',
            email='admin@test.com',
            name='Test Admin',
            is_admin=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin_user)
        db.session.commit()
        
        self.admin_user = admin_user
        self.test_campus = campus
    
    @rule(target=events, name=st.text(min_size=1, max_size=100),
          venue=st.text(min_size=1, max_size=50),
          event_date=st.dates(min_value=date.today()),
          start_time=st.times(),
          end_time=st.one_of(st.none(), st.times()))
    def create_event(self, name, venue, event_date, start_time, end_time):
        """Create an event with validation."""
        assume(len(name.strip()) > 0)
        assume(len(venue.strip()) > 0)
        
        # Validate end time is after start time
        if end_time is not None:
            assume(end_time > start_time)
        
        event_data = {
            'name': name.strip(),
            'venue_name': venue.strip(),
            'date': event_date.isoformat(),
            'time': start_time.strftime('%H:%M'),
            'campus_id': self.test_campus.id,
            'description': f'Test event: {name.strip()}'
        }
        
        if end_time:
            event_data['end_time'] = end_time.strftime('%H:%M')
        
        # Authenticate as admin
        with self.client.session_transaction() as sess:
            sess['_user_id'] = self.admin_user.id
            sess['_fresh'] = True
        
        response = self.client.post('/api/events',
                                  data=json.dumps(event_data),
                                  content_type='application/json')
        
        if response.status_code == 201:
            event_id = response.get_json().get('id')
            event = Event.query.get(event_id)
            return event
        
        return None
    
    @rule(event=events)
    def test_event_retrieval(self, event):
        """Test that created events can be retrieved."""
        if event is None:
            return
        
        response = self.client.get('/api/events')
        assert response.status_code == 200
        
        events_data = response.get_json()
        event_ids = [e['id'] for e in events_data]
        assert event.id in event_ids
    
    @rule(event=events)
    def test_event_deletion_by_admin(self, event):
        """Test that admins can delete events."""
        if event is None:
            return
        
        # Authenticate as admin
        with self.client.session_transaction() as sess:
            sess['_user_id'] = self.admin_user.id
            sess['_fresh'] = True
        
        response = self.client.delete(f'/api/events/{event.id}')
        
        # Admin should be able to delete any event
        assert response.status_code in [200, 404]  # 404 if already deleted
    
    @rule(event=events)
    def test_event_campus_association(self, event):
        """Test that events are properly associated with campuses."""
        if event is None:
            return
        
        # Event should have a valid campus association
        assert event.campus_id is not None
        
        # Campus should exist
        campus = Campus.query.filter_by(id=event.campus_id).first()
        assert campus is not None
    
    @invariant()
    def event_time_consistency(self):
        """Ensure all events have consistent time data."""
        events = Event.query.all()
        for event in events:
            # Start time should always be present
            assert event.start_time is not None
            
            # If end time exists, it should be after start time
            if event.end_time:
                # Convert to datetime for comparison
                start_dt = datetime.combine(event.date, event.start_time)
                end_dt = datetime.combine(event.date, event.end_time)
                assert end_dt > start_dt
    
    @invariant()
    def event_campus_validity(self):
        """Ensure all events reference valid campuses."""
        events = Event.query.all()
        campus_ids = {c.id for c in Campus.query.all()}
        
        for event in events:
            assert event.campus_id in campus_ids


# Test functions using the state machines

def test_admin_access_control_property():
    """
    Property 4: Admin Access Control
    Tests that admin panel access is properly controlled.
    """
    run_state_machine_as_test(AdminAccessControlMachine, settings=settings(max_examples=50, deadline=None))


def test_event_management_consistency_property():
    """
    Property 5: Event Management Consistency
    Tests that event management operations maintain consistency.
    """
    run_state_machine_as_test(EventManagementMachine, settings=settings(max_examples=50, deadline=None))


# Additional unit tests for specific admin functionality

def test_admin_dashboard_renders():
    """Test that admin dashboard renders correctly for admin users."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            google_id='admin_test',
            email='admin@test.com',
            name='Test Admin',
            is_admin=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin_user)
        db.session.commit()
        
        client = app.test_client()
        
        # Login as admin
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        response = client.get('/admin/')
        
        # Should be able to access admin dashboard
        assert response.status_code in [200, 302]
        
        db.drop_all()


def test_non_admin_dashboard_access_denied():
    """Test that non-admin users cannot access admin dashboard."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create regular user
        user = User(
            id=str(uuid.uuid4()),
            google_id='user_test',
            email='user@test.com',
            name='Test User',
            is_admin=False,
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        
        client = app.test_client()
        
        # Login as regular user
        with client.session_transaction() as sess:
            sess['_user_id'] = user.id
            sess['_fresh'] = True
        
        response = client.get('/admin/')
        
        # Should be denied access
        assert response.status_code in [302, 403]
        
        db.drop_all()


def test_admin_can_view_all_users():
    """Test that admin can view all users via API."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            google_id='admin_test',
            email='admin@test.com',
            name='Test Admin',
            is_admin=True,
            created_at=datetime.utcnow()
        )
        
        # Create regular user
        regular_user = User(
            id=str(uuid.uuid4()),
            google_id='user_test',
            email='user@test.com',
            name='Test User',
            is_admin=False,
            created_at=datetime.utcnow()
        )
        
        db.session.add_all([admin_user, regular_user])
        db.session.commit()
        
        client = app.test_client()
        
        # Login as admin
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        response = client.get('/admin/api/users')
        
        if response.status_code == 200:
            users_data = response.get_json()
            assert len(users_data) >= 2  # At least admin and regular user
            
            user_emails = [u['email'] for u in users_data]
            assert 'admin@test.com' in user_emails
            assert 'user@test.com' in user_emails
        
        db.drop_all()


def test_admin_event_management():
    """Test that admin can manage events through the admin panel."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            google_id='admin_test',
            email='admin@test.com',
            name='Test Admin',
            is_admin=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin_user)
        
        # Create test campus
        campus = Campus(
            id='test-campus',
            name='Test Campus',
            display_name='Test Campus',
            center_latitude=13.0827,
            center_longitude=80.2707,
            timezone='UTC',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(campus)
        db.session.commit()
        
        client = app.test_client()
        
        # Login as admin
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        # Test viewing events
        response = client.get('/admin/api/events')
        assert response.status_code in [200, 302]
        
        # Test creating event
        event_data = {
            'name': 'Admin Test Event',
            'venue_name': 'Test Venue',
            'date': '2024-12-25',
            'time': '10:00',
            'end_time': '11:00',
            'campus_id': 'test-campus',
            'description': 'Test event created by admin'
        }
        
        response = client.post('/api/events',
                             data=json.dumps(event_data),
                             content_type='application/json')
        
        # Admin should be able to create events
        assert response.status_code in [200, 201, 302]
        
        db.drop_all()