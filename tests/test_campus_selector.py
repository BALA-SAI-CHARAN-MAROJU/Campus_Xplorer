"""
Property-based tests for enhanced campus selection system.
Feature: campus-explorer-enhancement, Property 9: Campus Selector Functionality
Feature: campus-explorer-enhancement, Property 10: Campus State Consistency
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, date, time
from app import create_app, db
from app.models import Campus, Event, User
from tests.test_setup import BaseTestCase
import json


class TestCampusSelectorFunctionality(BaseTestCase):
    """
    Feature: campus-explorer-enhancement, Property 9: Campus Selector Functionality
    Tests that campus selector displays all available campus options with clear identification.
    """
    
    def setUp(self):
        super().setUp()
        self.create_test_campuses()
    
    def create_test_campuses(self):
        """Create test campuses for testing."""
        campuses_data = [
            {
                'id': 'amrita-chennai',
                'name': 'chennai',
                'display_name': 'Amrita Chennai Campus',
                'center_latitude': 13.2630,
                'center_longitude': 80.0274,
                'locations_data': {
                    'Academic Block': [13.263018, 80.027427],
                    'Library': [13.262621, 80.026525],
                    'Canteen': [13.262856, 80.028401]
                },
                'timezone': 'Asia/Kolkata'
            },
            {
                'id': 'amrita-coimbatore',
                'name': 'coimbatore',
                'display_name': 'Amrita Coimbatore Campus',
                'center_latitude': 10.9020,
                'center_longitude': 76.9020,
                'locations_data': {
                    'Main Building': [10.9020, 76.9020],
                    'Library': [10.9025, 76.9025],
                    'Cafeteria': [10.9015, 76.9015]
                },
                'timezone': 'Asia/Kolkata'
            }
        ]
        
        for campus_data in campuses_data:
            campus = Campus(**campus_data)
            db.session.add(campus)
        
        db.session.commit()
    
    @given(
        campus_count=st.integers(min_value=1, max_value=10),
        include_inactive=st.booleans()
    )
    @settings(max_examples=100)
    def test_campus_selector_displays_all_active_campuses(self, campus_count, include_inactive):
        """
        Feature: campus-explorer-enhancement, Property 9: Campus Selector Functionality
        
        Property: For any campus selector access, the system should display 
        all available campus options with clear identification.
        
        Test that the campus API returns all active campuses and excludes inactive ones.
        """
        # Clear existing campuses
        Campus.query.delete()
        
        # Create test campuses
        active_campuses = []
        inactive_campuses = []
        
        for i in range(campus_count):
            campus_id = f'test-campus-{i}'
            campus = Campus(
                id=campus_id,
                name=f'campus{i}',
                display_name=f'Test Campus {i}',
                center_latitude=10.0 + i,
                center_longitude=76.0 + i,
                locations_data={'Location1': [10.0 + i, 76.0 + i]},
                is_active=True
            )
            db.session.add(campus)
            active_campuses.append(campus)
        
        # Add inactive campuses if requested
        if include_inactive:
            for i in range(2):  # Add 2 inactive campuses
                campus_id = f'inactive-campus-{i}'
                campus = Campus(
                    id=campus_id,
                    name=f'inactive{i}',
                    display_name=f'Inactive Campus {i}',
                    center_latitude=20.0 + i,
                    center_longitude=86.0 + i,
                    locations_data={'Location1': [20.0 + i, 86.0 + i]},
                    is_active=False
                )
                db.session.add(campus)
                inactive_campuses.append(campus)
        
        db.session.commit()
        
        # Test API endpoint
        response = self.client.get('/api/campuses')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        returned_campuses = data['campuses']
        
        # Verify all active campuses are returned
        self.assertEqual(len(returned_campuses), len(active_campuses))
        
        # Verify each campus has required fields
        for campus_data in returned_campuses:
            self.assertIn('id', campus_data)
            self.assertIn('display_name', campus_data)
            self.assertIn('center_coordinates', campus_data)
            self.assertIn('locations', campus_data)
            self.assertIn('is_active', campus_data)
            self.assertTrue(campus_data['is_active'])
        
        # Verify campus IDs match
        returned_ids = {c['id'] for c in returned_campuses}
        expected_ids = {c.id for c in active_campuses}
        self.assertEqual(returned_ids, expected_ids)
    
    @given(
        display_name=st.text(min_size=1, max_size=100),
        location_count=st.integers(min_value=0, max_value=20)
    )
    @settings(max_examples=100)
    def test_campus_data_structure_consistency(self, display_name, location_count):
        """
        Feature: campus-explorer-enhancement, Property 9: Campus Selector Functionality
        
        Property: Campus data should have consistent structure with clear identification.
        
        Test that campus data maintains consistent structure regardless of content.
        """
        # Clear existing campuses to avoid ID conflicts
        Campus.query.delete()
        db.session.commit()
        
        # Generate unique campus ID
        import uuid
        campus_id = f'test-campus-{str(uuid.uuid4())[:8]}'
        
        # Create locations data
        locations_data = {}
        for i in range(location_count):
            locations_data[f'Location {i}'] = [10.0 + i * 0.001, 76.0 + i * 0.001]
        
        # Create campus
        campus = Campus(
            id=campus_id,
            name=campus_id.lower(),
            display_name=display_name,
            center_latitude=10.0,
            center_longitude=76.0,
            locations_data=locations_data,
            is_active=True
        )
        
        db.session.add(campus)
        db.session.commit()
        
        # Test campus data conversion
        campus_dict = campus.to_dict()
        
        # Verify required fields exist
        required_fields = ['id', 'name', 'display_name', 'center_coordinates', 'locations', 'is_active']
        for field in required_fields:
            self.assertIn(field, campus_dict)
        
        # Verify data types
        self.assertIsInstance(campus_dict['id'], str)
        self.assertIsInstance(campus_dict['display_name'], str)
        self.assertIsInstance(campus_dict['center_coordinates'], list)
        self.assertIsInstance(campus_dict['locations'], dict)
        self.assertIsInstance(campus_dict['is_active'], bool)
        
        # Verify coordinates format
        self.assertEqual(len(campus_dict['center_coordinates']), 2)
        self.assertIsInstance(campus_dict['center_coordinates'][0], float)
        self.assertIsInstance(campus_dict['center_coordinates'][1], float)
        
        # Verify locations format
        self.assertEqual(len(campus_dict['locations']), location_count)
        for location_name, coordinates in campus_dict['locations'].items():
            self.assertIsInstance(location_name, str)
            self.assertIsInstance(coordinates, list)
            self.assertEqual(len(coordinates), 2)


class TestCampusStateConsistency(BaseTestCase):
    """
    Feature: campus-explorer-enhancement, Property 10: Campus State Consistency
    Tests that campus selection changes update all related components consistently.
    """
    
    def setUp(self):
        super().setUp()
        self.create_test_data()
    
    def create_test_data(self):
        """Create test campuses, users, and events."""
        # Create campuses
        campuses_data = [
            {
                'id': 'campus-a',
                'name': 'campusa',
                'display_name': 'Campus A',
                'center_latitude': 10.0,
                'center_longitude': 76.0,
                'locations_data': {
                    'Building A1': [10.001, 76.001],
                    'Building A2': [10.002, 76.002],
                    'Library A': [10.003, 76.003]
                }
            },
            {
                'id': 'campus-b',
                'name': 'campusb',
                'display_name': 'Campus B',
                'center_latitude': 11.0,
                'center_longitude': 77.0,
                'locations_data': {
                    'Building B1': [11.001, 77.001],
                    'Building B2': [11.002, 77.002],
                    'Cafeteria B': [11.003, 77.003]
                }
            }
        ]
        
        for campus_data in campuses_data:
            campus = Campus(**campus_data)
            db.session.add(campus)
        
        # Create test user
        self.test_user = User(
            id='test-user-1',
            google_id='google-123',
            email='test@example.com',
            name='Test User',
            preferred_campus='campus-a'
        )
        db.session.add(self.test_user)
        
        db.session.commit()
    
    @given(
        campus_changes=st.lists(
            st.sampled_from(['campus-a', 'campus-b']),
            min_size=1,
            max_size=10
        ),
        event_count_per_campus=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=100)
    def test_campus_change_updates_event_filters(self, campus_changes, event_count_per_campus):
        """
        Feature: campus-explorer-enhancement, Property 10: Campus State Consistency
        
        Property: For any campus selection change, the system should update 
        event filters to reflect the selected campus.
        
        Test that events are properly filtered by campus when campus changes.
        """
        # Clear any existing events to ensure clean test
        Event.query.delete()
        db.session.commit()
        
        # Create events for each campus
        for campus_id in ['campus-a', 'campus-b']:
            for i in range(event_count_per_campus):
                event = Event(
                    name=f'Event {i} - {campus_id}',
                    description=f'Test event {i} for {campus_id}',
                    venue_name=f'Venue {i}',
                    campus_id=campus_id,
                    date=date.today(),
                    start_time=time(10, 0),
                    created_by=self.test_user.id
                )
                db.session.add(event)
        
        db.session.commit()
        
        # Test event filtering for each campus change
        for campus_id in campus_changes:
            response = self.client.get(f'/api/events?campus={campus_id}')
            self.assertEqual(response.status_code, 200)
            
            events_data = json.loads(response.data)
            
            # Verify all returned events belong to the selected campus
            for event in events_data:
                self.assertEqual(event['campus_id'], campus_id)
            
            # Verify correct number of events
            self.assertEqual(len(events_data), event_count_per_campus)
    
    @given(
        campus_id=st.sampled_from(['campus-a', 'campus-b']),
        location_requests=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_campus_change_updates_location_data(self, campus_id, location_requests):
        """
        Feature: campus-explorer-enhancement, Property 10: Campus State Consistency
        
        Property: For any campus selection change, the system should update 
        location dropdowns to reflect campus-specific venues.
        
        Test that location API returns campus-specific locations.
        """
        # Get campus data
        campus = Campus.query.filter_by(id=campus_id).first()
        self.assertIsNotNone(campus)
        
        # Test location API multiple times to ensure consistency
        for _ in range(location_requests):
            response = self.client.get(f'/api/locations?campus={campus_id}')
            self.assertEqual(response.status_code, 200)
            
            locations_data = json.loads(response.data)
            
            # Verify locations match campus data
            expected_locations = set(campus.locations_data.keys())
            returned_locations = {loc['name'] for loc in locations_data}
            
            self.assertEqual(returned_locations, expected_locations)
            
            # Verify coordinate consistency
            for location in locations_data:
                expected_coords = campus.locations_data[location['name']]
                self.assertEqual(location['coordinates'], expected_coords)
    
    @given(
        initial_campus=st.sampled_from(['campus-a', 'campus-b']),
        target_campus=st.sampled_from(['campus-a', 'campus-b']),
        event_counts=st.dictionaries(
            keys=st.sampled_from(['campus-a', 'campus-b']),
            values=st.integers(min_value=0, max_value=10),
            min_size=2,
            max_size=2
        )
    )
    @settings(max_examples=100)
    def test_campus_state_consistency_across_components(self, initial_campus, target_campus, event_counts):
        """
        Feature: campus-explorer-enhancement, Property 10: Campus State Consistency
        
        Property: For any campus selection change, all components should 
        maintain consistent state with the selected campus.
        
        Test that campus changes maintain consistency across all data sources.
        """
        # Clear any existing events to ensure clean test
        Event.query.delete()
        db.session.commit()
        
        # Create events according to event_counts
        for campus_id, count in event_counts.items():
            for i in range(count):
                event = Event(
                    name=f'Event {i} - {campus_id}',
                    description=f'Test event for {campus_id}',
                    venue_name=f'Venue {i}',
                    campus_id=campus_id,
                    date=date.today(),
                    start_time=time(9, 0),
                    created_by=self.test_user.id
                )
                db.session.add(event)
        
        db.session.commit()
        
        # Test initial campus state
        self._verify_campus_state_consistency(initial_campus, event_counts.get(initial_campus, 0))
        
        # Test target campus state
        self._verify_campus_state_consistency(target_campus, event_counts.get(target_campus, 0))
    
    def _verify_campus_state_consistency(self, campus_id, expected_event_count):
        """Helper method to verify campus state consistency."""
        # Test campus data
        campus_response = self.client.get('/api/campuses')
        self.assertEqual(campus_response.status_code, 200)
        
        campuses_data = json.loads(campus_response.data)['campuses']
        campus_data = next((c for c in campuses_data if c['id'] == campus_id), None)
        self.assertIsNotNone(campus_data)
        
        # Test locations data
        locations_response = self.client.get(f'/api/locations?campus={campus_id}')
        self.assertEqual(locations_response.status_code, 200)
        
        locations_data = json.loads(locations_response.data)
        expected_location_count = len(campus_data['locations'])
        self.assertEqual(len(locations_data), expected_location_count)
        
        # Test events data
        events_response = self.client.get(f'/api/events?campus={campus_id}')
        self.assertEqual(events_response.status_code, 200)
        
        events_data = json.loads(events_response.data)
        self.assertEqual(len(events_data), expected_event_count)
        
        # Verify all events belong to the campus
        for event in events_data:
            self.assertEqual(event['campus_id'], campus_id)
        
        # Test event counts API
        counts_response = self.client.get('/api/events/counts')
        self.assertEqual(counts_response.status_code, 200)
        
        counts_data = json.loads(counts_response.data)['counts']
        actual_count = counts_data.get(campus_id, 0)
        self.assertEqual(actual_count, expected_event_count)
    
    @given(
        user_preferences=st.lists(
            st.sampled_from(['campus-a', 'campus-b']),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_campus_preference_persistence(self, user_preferences):
        """
        Feature: campus-explorer-enhancement, Property 10: Campus State Consistency
        
        Property: Campus preferences should be consistently saved and loaded.
        
        Test that user campus preferences are properly persisted and retrieved.
        """
        # Test each preference change
        for preferred_campus in user_preferences:
            # Update user preference
            self.test_user.preferred_campus = preferred_campus
            db.session.commit()
            
            # Verify preference is saved
            updated_user = User.query.get(self.test_user.id)
            self.assertEqual(updated_user.preferred_campus, preferred_campus)
            
            # Verify user data includes preference
            user_dict = updated_user.to_dict()
            self.assertEqual(user_dict['preferred_campus'], preferred_campus)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])