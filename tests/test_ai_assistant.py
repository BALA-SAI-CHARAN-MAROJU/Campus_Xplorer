"""
Property-based tests for AI Assistant functionality.
Tests for Task 4: Integrate AI assistant with enhanced capabilities.
"""

import pytest
import uuid
from datetime import datetime, date, time
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize, invariant, run_state_machine_as_test
from app import create_app, db
from app.models import User, Event, Campus, Conversation
from app.services.ai_assistant import AIAssistant, QueryProcessor, ContextManager, ResponseGenerator
import json

class AIInterfaceMachine(RuleBasedStateMachine):
    """
    Property 6: AI Interface Initialization
    Validates: Requirements 3.1
    
    Tests that the AI interface initializes properly and provides
    natural language processing capabilities.
    """
    
    users = Bundle('users')
    campuses = Bundle('campuses')
    
    def __init__(self):
        super().__init__()
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()
        self.ai_assistant = AIAssistant()
    
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
            locations_data={
                'Library': [13.0830, 80.2710],
                'Canteen': [13.0825, 80.2705],
                'Academic Block': [13.0827, 80.2707]
            },
            created_at=datetime.utcnow()
        )
        db.session.add(campus)
        db.session.commit()
        self.test_campus = campus
    
    @rule(target=users, name=st.text(min_size=1, max_size=50), 
          email=st.emails())
    def create_user(self, name, email):
        """Create a user for testing."""
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
            is_admin=False,
            preferred_campus=self.test_campus.id,
            created_at=datetime.utcnow()
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            return None
    
    @rule(message=st.text(min_size=1, max_size=200))
    def test_ai_interface_responds(self, message):
        """Test that AI interface always provides a response."""
        assume(len(message.strip()) > 0)
        
        # Test without user context
        response = self.ai_assistant.process_query(message.strip())
        
        # AI should always provide a non-empty response
        assert response is not None
        assert len(response.strip()) > 0
        assert isinstance(response, str)
    
    @rule(user=users, message=st.text(min_size=1, max_size=200))
    def test_ai_interface_with_user_context(self, user, message):
        """Test AI interface with authenticated user context."""
        if user is None:
            return
        
        assume(len(message.strip()) > 0)
        
        user_context = {
            'user_id': user.id,
            'user_name': user.name,
            'campus': user.preferred_campus,
            'is_admin': user.is_admin
        }
        
        response = self.ai_assistant.process_query(message.strip(), user_context)
        
        # AI should provide personalized response
        assert response is not None
        assert len(response.strip()) > 0
        assert isinstance(response, str)
        
        # Response should be contextual (contain user name or campus info)
        response_lower = response.lower()
        assert (user.name.lower() in response_lower or 
                user.preferred_campus.replace('-', ' ') in response_lower or
                'campus' in response_lower)
    
    @rule(greeting=st.sampled_from(['hello', 'hi', 'hey', 'good morning', 'greetings']))
    def test_greeting_recognition(self, greeting):
        """Test that AI recognizes and responds to greetings appropriately."""
        response = self.ai_assistant.process_query(greeting)
        
        # Should recognize as greeting and respond appropriately
        response_lower = response.lower()
        assert any(word in response_lower for word in ['hello', 'hi', 'welcome', 'greetings'])
        assert 'assistant' in response_lower or 'help' in response_lower
    
    @rule(navigation_query=st.sampled_from([
        'how do I get to the library',
        'where is the canteen',
        'directions to academic block',
        'route from library to canteen'
    ]))
    def test_navigation_query_recognition(self, navigation_query):
        """Test that AI recognizes navigation queries."""
        user_context = {
            'campus': self.test_campus.id,
            'user_name': 'Test User'
        }
        
        response = self.ai_assistant.process_query(navigation_query, user_context)
        
        # Should recognize as navigation query
        response_lower = response.lower()
        assert any(word in response_lower for word in [
            'navigate', 'direction', 'route', 'map', 'location'
        ])
    
    @invariant()
    def ai_assistant_available(self):
        """Ensure AI assistant is always available."""
        assert self.ai_assistant is not None
        assert hasattr(self.ai_assistant, 'process_query')
        assert callable(self.ai_assistant.process_query)


class AIResponseMachine(RuleBasedStateMachine):
    """
    Property 7: Contextual AI Responses
    Validates: Requirements 3.2, 3.3, 3.4
    
    Tests that AI provides contextual responses for directions,
    events, and campus facilities.
    """
    
    events = Bundle('events')
    queries = Bundle('queries')
    
    def __init__(self):
        super().__init__()
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()
        self.ai_assistant = AIAssistant()
    
    def teardown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    @initialize()
    def setup_initial_state(self):
        """Set up initial test state."""
        # Create campus with locations
        campus = Campus(
            id='test-campus',
            name='Test Campus',
            display_name='Test Campus',
            center_latitude=13.0827,
            center_longitude=80.2707,
            timezone='UTC',
            is_active=True,
            locations_data={
                'Library': [13.0830, 80.2710],
                'Canteen': [13.0825, 80.2705],
                'Academic Block': [13.0827, 80.2707],
                'Gym': [13.0820, 80.2700],
                'Hostel': [13.0835, 80.2715]
            },
            created_at=datetime.utcnow()
        )
        db.session.add(campus)
        
        # Create test user
        user = User(
            id=str(uuid.uuid4()),
            google_id='test_user',
            email='test@example.com',
            name='Test User',
            is_admin=False,
            preferred_campus='test-campus',
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        
        self.test_campus = campus
        self.test_user = user
    
    @rule(target=events, name=st.text(min_size=1, max_size=50),
          venue=st.sampled_from(['Library', 'Canteen', 'Academic Block', 'Gym']),
          event_date=st.dates(min_value=date.today()))
    def create_event(self, name, venue, event_date):
        """Create test events."""
        assume(len(name.strip()) > 0)
        
        event = Event(
            name=name.strip(),
            description=f'Test event: {name.strip()}',
            venue_name=venue,
            campus_id=self.test_campus.id,
            date=event_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            created_by=self.test_user.id,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        try:
            db.session.add(event)
            db.session.commit()
            return event
        except Exception:
            db.session.rollback()
            return None
    
    @rule(location=st.sampled_from(['Library', 'Canteen', 'Academic Block', 'Gym', 'Hostel']))
    def test_facility_query_response(self, location):
        """Test AI responses to facility queries."""
        query = f"Where is the {location}?"
        
        user_context = {
            'user_id': self.test_user.id,
            'user_name': self.test_user.name,
            'campus': self.test_campus.id
        }
        
        response = self.ai_assistant.process_query(query, user_context)
        
        # Should provide contextual information about the facility
        response_lower = response.lower()
        assert location.lower() in response_lower
        assert any(word in response_lower for word in [
            'campus', 'location', 'find', 'navigate', 'map'
        ])
    
    @rule(event=events)
    def test_event_query_response(self, event):
        """Test AI responses to event queries."""
        if event is None:
            return
        
        query = "What events are happening?"
        
        user_context = {
            'user_id': self.test_user.id,
            'user_name': self.test_user.name,
            'campus': self.test_campus.id
        }
        
        response = self.ai_assistant.process_query(query, user_context)
        
        # Should provide information about events
        response_lower = response.lower()
        assert any(word in response_lower for word in [
            'event', 'upcoming', 'schedule', event.name.lower()
        ])
    
    @rule(start_location=st.sampled_from(['Library', 'Canteen', 'Academic Block']),
          end_location=st.sampled_from(['Gym', 'Hostel']))
    def test_direction_query_response(self, start_location, end_location):
        """Test AI responses to direction queries."""
        assume(start_location != end_location)
        
        query = f"How do I get from {start_location} to {end_location}?"
        
        user_context = {
            'user_id': self.test_user.id,
            'user_name': self.test_user.name,
            'campus': self.test_campus.id
        }
        
        response = self.ai_assistant.process_query(query, user_context)
        
        # Should provide navigation information
        response_lower = response.lower()
        assert start_location.lower() in response_lower or end_location.lower() in response_lower
        assert any(word in response_lower for word in [
            'navigate', 'route', 'direction', 'map', 'get'
        ])
    
    @invariant()
    def campus_data_available(self):
        """Ensure campus data is available for context."""
        campus = Campus.query.filter_by(id='test-campus').first()
        assert campus is not None
        assert campus.locations_data is not None
        assert len(campus.locations_data) > 0


class AIFallbackMachine(RuleBasedStateMachine):
    """
    Property 8: AI Fallback Behavior
    Validates: Requirements 3.5
    
    Tests that AI provides helpful suggestions when it cannot
    understand a query.
    """
    
    def __init__(self):
        super().__init__()
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.ai_assistant = AIAssistant()
    
    def teardown(self):
        self.app_context.pop()
    
    @rule(unclear_message=st.text(min_size=1, max_size=100).filter(
        lambda x: not any(word in x.lower() for word in [
            'hello', 'hi', 'route', 'event', 'where', 'library', 'canteen'
        ])
    ))
    def test_fallback_response(self, unclear_message):
        """Test AI fallback behavior for unclear queries."""
        assume(len(unclear_message.strip()) > 0)
        assume(unclear_message.strip() not in ['', ' ', '\n', '\t'])
        
        response = self.ai_assistant.process_query(unclear_message.strip())
        
        # Should provide helpful fallback response
        assert response is not None
        assert len(response.strip()) > 0
        
        response_lower = response.lower()
        # Should contain helpful suggestions or clarification requests
        assert any(phrase in response_lower for phrase in [
            'try asking', 'for example', 'help', 'rephrase', 
            'not sure', 'could you', 'suggestion'
        ])
    
    @rule(gibberish=st.text(alphabet='xyzqwerty123!@#', min_size=5, max_size=20))
    def test_gibberish_handling(self, gibberish):
        """Test AI handling of gibberish input."""
        response = self.ai_assistant.process_query(gibberish)
        
        # Should handle gracefully and provide helpful response
        assert response is not None
        assert len(response.strip()) > 0
        
        # Should not crash or return error messages
        response_lower = response.lower()
        assert 'error' not in response_lower
        assert 'exception' not in response_lower
        assert 'traceback' not in response_lower


# Test functions using the state machines

def test_ai_interface_initialization_property():
    """
    Property 6: AI Interface Initialization
    Tests that AI interface initializes and provides NLP capabilities.
    """
    run_state_machine_as_test(AIInterfaceMachine, settings=settings(max_examples=30, deadline=None))


def test_contextual_ai_responses_property():
    """
    Property 7: Contextual AI Responses
    Tests that AI provides contextual responses for various queries.
    """
    run_state_machine_as_test(AIResponseMachine, settings=settings(max_examples=30, deadline=None))


def test_ai_fallback_behavior_property():
    """
    Property 8: AI Fallback Behavior
    Tests that AI provides helpful suggestions for unclear queries.
    """
    run_state_machine_as_test(AIFallbackMachine, settings=settings(max_examples=30, deadline=None))


# Additional unit tests for specific AI functionality

def test_query_processor_intent_classification():
    """Test that QueryProcessor correctly classifies intents."""
    processor = QueryProcessor()
    
    # Test greeting classification
    assert processor.classify_intent("hello") == "greeting"
    assert processor.classify_intent("hi there") == "greeting"
    assert processor.classify_intent("good morning") == "greeting"
    
    # Test navigation classification
    assert processor.classify_intent("how do I get to the library") == "navigation"
    assert processor.classify_intent("where is the canteen") == "navigation"
    assert processor.classify_intent("directions to gym") == "navigation"
    
    # Test events classification
    assert processor.classify_intent("what events are happening") == "events"
    assert processor.classify_intent("upcoming activities") == "events"
    assert processor.classify_intent("schedule for today") == "events"
    
    # Test facilities classification
    assert processor.classify_intent("where is the library") == "navigation"
    assert processor.classify_intent("gym hours") == "facilities"
    assert processor.classify_intent("canteen timing") == "facilities"
    
    # Test unknown classification
    assert processor.classify_intent("random gibberish text") == "unknown"


def test_context_manager_data_retrieval():
    """Test that ContextManager retrieves relevant data."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create test campus
        campus = Campus(
            id='test-campus',
            name='Test Campus',
            display_name='Test Campus',
            center_latitude=13.0827,
            center_longitude=80.2707,
            timezone='UTC',
            is_active=True,
            locations_data={'Library': [13.0830, 80.2710]},
            created_at=datetime.utcnow()
        )
        db.session.add(campus)
        db.session.commit()
        
        context_manager = ContextManager()
        user_context = {'campus': 'test-campus'}
        
        context = context_manager.get_context("where is library", user_context)
        
        # Should retrieve campus data
        assert 'campus_data' in context
        assert context['campus_data']['id'] == 'test-campus'
        
        # Should retrieve locations data
        assert 'locations_data' in context
        assert len(context['locations_data']) > 0
        assert context['locations_data'][0]['name'] == 'Library'
        
        db.drop_all()


def test_response_generator_personalization():
    """Test that ResponseGenerator provides personalized responses."""
    generator = ResponseGenerator()
    
    # Test greeting personalization
    response = generator.generate_greeting("John", "amrita-chennai")
    assert "John" in response
    assert "Chennai" in response
    assert "assistant" in response.lower()
    
    # Test help response personalization
    response = generator.generate_help_response("Alice")
    assert "Alice" in response
    assert "help" in response.lower()
    assert "navigation" in response.lower()


def test_ai_assistant_conversation_storage():
    """Test that AI assistant stores conversations for authenticated users."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create test user
        user = User(
            id=str(uuid.uuid4()),
            google_id='test_user',
            email='test@example.com',
            name='Test User',
            is_admin=False,
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        
        ai_assistant = AIAssistant()
        user_context = {
            'user_id': user.id,
            'user_name': user.name,
            'campus': 'amrita-chennai'
        }
        
        # Process a query
        response = ai_assistant.process_query("Hello", user_context)
        
        # Check that conversation was stored
        conversation = Conversation.query.filter_by(user_id=user.id).first()
        assert conversation is not None
        assert conversation.messages is not None
        assert len(conversation.messages) >= 2  # User message + AI response
        
        db.drop_all()