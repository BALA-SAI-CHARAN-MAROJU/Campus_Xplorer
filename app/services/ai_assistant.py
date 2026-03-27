"""
Enhanced AI Assistant Service for Campus Explorer.
Provides intelligent responses about campus information, events, and navigation.
"""

import re
import json
import uuid
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from flask import current_app
from app.models import Event, Campus, User, Conversation
from app import db


class AIAssistant:
    """
    Enhanced AI Assistant with natural language processing capabilities.
    Provides contextual responses about campus information, events, and navigation.
    """
    
    def __init__(self):
        self.context_manager = ContextManager()
        self.response_generator = ResponseGenerator()
        self.query_processor = QueryProcessor()
    
    def process_query(self, message: str, user_context: Optional[Dict] = None) -> str:
        """
        Process user query and generate intelligent response.
        
        Args:
            message: User's input message
            user_context: Optional user context (campus, user_id, etc.)
        
        Returns:
            AI-generated response string
        """
        try:
            # Clean and normalize the message
            normalized_message = self._normalize_message(message)
            
            # Determine query intent
            intent = self.query_processor.classify_intent(normalized_message)
            
            # Get relevant context
            context = self.context_manager.get_context(normalized_message, user_context)
            
            # Generate response based on intent
            response = self._generate_response(intent, normalized_message, context, user_context)
            
            # Store conversation if user is authenticated
            if user_context and user_context.get('user_id'):
                self._store_conversation(user_context['user_id'], message, response, user_context)
            
            return response
            
        except Exception as e:
            current_app.logger.error(f"AI Assistant error: {str(e)}")
            return self.response_generator.get_fallback_response()
    
    def _normalize_message(self, message: str) -> str:
        """Normalize user message for processing."""
        return message.strip().lower()
    
    def _generate_response(self, intent: str, message: str, context: Dict, user_context: Optional[Dict]) -> str:
        """Generate response based on intent and context."""
        user_name = user_context.get('user_name', 'there') if user_context else 'there'
        campus = user_context.get('campus', 'amrita-chennai') if user_context else 'amrita-chennai'
        
        if intent == 'greeting':
            return self.response_generator.generate_greeting(user_name, campus)
        elif intent == 'navigation':
            return self.response_generator.generate_navigation_response(message, context, campus)
        elif intent == 'events':
            return self.response_generator.generate_events_response(message, context, campus)
        elif intent == 'facilities':
            return self.response_generator.generate_facilities_response(message, context, campus)
        elif intent == 'campus_info':
            return self.response_generator.generate_campus_info_response(message, context, campus)
        elif intent == 'help':
            return self.response_generator.generate_help_response(user_name)
        else:
            return self.response_generator.generate_clarification_response(message, user_name)
    
    def _store_conversation(self, user_id: str, user_message: str, ai_response: str, user_context: Dict):
        """Store conversation in database."""
        try:
            # Find or create conversation
            conversation = Conversation.query.filter_by(user_id=user_id).order_by(
                Conversation.updated_at.desc()
            ).first()
            
            if not conversation or self._should_create_new_conversation(conversation):
                conversation = Conversation(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    campus_context=user_context.get('campus'),
                    messages=[],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(conversation)
            
            # Add messages to conversation
            if not conversation.messages:
                conversation.messages = []
            
            conversation.messages.extend([
                {
                    'role': 'user',
                    'content': user_message,
                    'timestamp': datetime.utcnow().isoformat()
                },
                {
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': datetime.utcnow().isoformat()
                }
            ])
            
            conversation.updated_at = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error storing conversation: {str(e)}")
            db.session.rollback()
    
    def _should_create_new_conversation(self, conversation: Conversation) -> bool:
        """Determine if a new conversation should be created."""
        if not conversation.updated_at:
            return True
        
        # Create new conversation if last one is older than 1 hour
        time_diff = datetime.utcnow() - conversation.updated_at
        return time_diff.total_seconds() > 3600


class QueryProcessor:
    """Processes and classifies user queries."""
    
    def __init__(self):
        self.intent_patterns = {
            'greeting': [
                r'\b(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))\b',
                r'\bwhat\'?s\s+up\b',
                r'\bhow\s+are\s+you\b'
            ],
            'navigation': [
                r'\b(route|direction|navigate|how\s+to\s+get|how\s+do\s+i\s+get)\b',
                r'\b(way|path)\s+(to|from)\b',
                r'\b(from\s+.+\s+to\s+.+|go\s+to|find\s+.+\s+location)\b',
                r'\b(shortest\s+path|best\s+route|quickest\s+way)\b',
                r'\bdirections\s+to\b'
            ],
            'events': [
                r'\b(event|schedule|happening|activities|program|function)\b',
                r'\b(what\'?s\s+on|upcoming|today|tomorrow|this\s+week)\b',
                r'\b(when\s+is|time\s+of|date\s+of)\b'
            ],
            'facilities': [
                r'\b(library|canteen|gym|hostel|lab|auditorium|cafeteria)\b',
                r'\b(facilities|amenities|services|buildings)\b',
                r'\b(open|close|hours|timing|available)\b',
                r'\bwhere\s+is\b'
            ],
            'campus_info': [
                r'\b(campus|college|university|amrita)\b',
                r'\b(about|information|tell\s+me|details)\b',
                r'\b(location|address|contact)\b'
            ],
            'help': [
                r'\b(help|assist|support|guide)\b',
                r'\b(what\s+can\s+you\s+do|how\s+to\s+use|commands)\b',
                r'\b(confused|don\'?t\s+understand|lost)\b'
            ]
        }
    
    def classify_intent(self, message: str) -> str:
        """Classify user message intent."""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return intent
        
        return 'unknown'


class ContextManager:
    """Manages conversation context and retrieves relevant data."""
    
    def get_context(self, message: str, user_context: Optional[Dict] = None) -> Dict:
        """Get relevant context for the user's query."""
        context = {
            'campus_data': self._get_campus_data(user_context),
            'events_data': self._get_events_data(message, user_context),
            'locations_data': self._get_locations_data(message, user_context),
            'user_preferences': user_context or {}
        }
        
        return context
    
    def _get_campus_data(self, user_context: Optional[Dict]) -> Dict:
        """Get campus information."""
        campus_id = user_context.get('campus', 'amrita-chennai') if user_context else 'amrita-chennai'
        
        campus = Campus.query.filter_by(id=campus_id, is_active=True).first()
        if campus:
            return campus.to_dict()
        
        return {}
    
    def _get_events_data(self, message: str, user_context: Optional[Dict]) -> List[Dict]:
        """Get relevant events data."""
        campus_id = user_context.get('campus', 'amrita-chennai') if user_context else 'amrita-chennai'
        
        # Get upcoming events for the campus
        events = Event.query.filter_by(
            campus_id=campus_id,
            is_active=True
        ).filter(
            Event.date >= date.today()
        ).order_by(Event.date, Event.start_time).limit(5).all()
        
        return [event.to_dict() for event in events]
    
    def _get_locations_data(self, message: str, user_context: Optional[Dict]) -> List[Dict]:
        """Get relevant locations data."""
        campus_id = user_context.get('campus', 'amrita-chennai') if user_context else 'amrita-chennai'
        
        campus = Campus.query.filter_by(id=campus_id, is_active=True).first()
        if campus and campus.locations_data:
            locations = []
            for name, coordinates in campus.locations_data.items():
                locations.append({
                    'name': name,
                    'coordinates': coordinates
                })
            return locations
        
        return []


class ResponseGenerator:
    """Generates AI responses based on intent and context."""
    
    def generate_greeting(self, user_name: str, campus: str) -> str:
        """Generate greeting response."""
        campus_display = campus.replace('-', ' ').title()
        
        greetings = [
            f"Hello {user_name}! I'm your enhanced Campus Explorer AI assistant. I can help you with navigation, events, and campus information for {campus_display}. What would you like to know?",
            f"Hi {user_name}! Welcome to the enhanced Campus Explorer. I'm here to help you navigate {campus_display}, find events, and answer questions about campus facilities. How can I assist you today?",
            f"Greetings {user_name}! I'm your intelligent campus guide for {campus_display}. I can provide directions, event information, facility details, and much more. What can I help you with?"
        ]
        
        import random
        return random.choice(greetings)
    
    def generate_navigation_response(self, message: str, context: Dict, campus: str) -> str:
        """Generate navigation-related response."""
        locations = context.get('locations_data', [])
        campus_display = campus.replace('-', ' ').title()
        
        # Extract location names from message
        location_names = [loc['name'] for loc in locations]
        mentioned_locations = []
        
        for location in location_names:
            if location.lower() in message.lower():
                mentioned_locations.append(location)
        
        if mentioned_locations:
            if len(mentioned_locations) == 1:
                location = mentioned_locations[0]
                return f"I can help you navigate to {location} on {campus_display}! Use the Campus Map section to get detailed directions. You can also click 'Explore Now' to see an optimized campus tour that includes {location}. Would you like me to show you the route?"
            else:
                locations_str = ', '.join(mentioned_locations[:-1]) + f" and {mentioned_locations[-1]}"
                return f"I found multiple locations you mentioned: {locations_str}. I can help you plan a route between these locations on {campus_display}. Use the route finder in the Campus Map section to get turn-by-turn directions!"
        
        available_locations = ', '.join(location_names[:8])  # Show first 8 locations
        return f"I can help you navigate around {campus_display}! Available locations include: {available_locations}{'...' if len(location_names) > 8 else ''}. Try asking 'How do I get from the Academic Block to the Library?' or use the interactive map to explore all locations."
    
    def generate_events_response(self, message: str, context: Dict, campus: str) -> str:
        """Generate events-related response."""
        events = context.get('events_data', [])
        campus_display = campus.replace('-', ' ').title()
        
        if not events:
            return f"There are currently no upcoming events scheduled for {campus_display}. You can add new events using the 'Add Event' tab in the Events section. Check back later for updates!"
        
        if len(events) == 1:
            event = events[0]
            return f"I found an upcoming event at {campus_display}: **{event['name']}** on {event['date']} at {event['start_time']} in {event['venue_name']}. {event.get('description', '')} You can find more details in the Events section!"
        
        event_list = []
        for event in events[:3]:  # Show first 3 events
            event_list.append(f"• **{event['name']}** - {event['date']} at {event['start_time']} ({event['venue_name']})")
        
        events_text = '\n'.join(event_list)
        more_text = f"\n\n...and {len(events) - 3} more events!" if len(events) > 3 else ""
        
        return f"Here are the upcoming events at {campus_display}:\n\n{events_text}{more_text}\n\nVisit the Events section to see all details and add events to your calendar!"
    
    def generate_facilities_response(self, message: str, context: Dict, campus: str) -> str:
        """Generate facilities-related response."""
        locations = context.get('locations_data', [])
        campus_display = campus.replace('-', ' ').title()
        
        # Common facility keywords and their related locations
        facility_mapping = {
            'library': ['Library', 'Academic Block'],
            'canteen': ['Canteen', 'Cafeteria'],
            'gym': ['AVV Gym for Boys', 'AVV Gym for Girls', 'Sports Complex'],
            'hostel': ['Junior Girls Hostel', 'Junior Boys Hostel', 'Senior Girls Hostel', 'Senior Boys Hostel', '2nd Year Boys Hostel'],
            'lab': ['Lab Block', 'Mechanical Lab'],
            'sports': ['Volley Ball Court', 'Basket Ball Court', 'AVV Ground', 'Amrita Indoor Stadium']
        }
        
        # Find relevant facilities
        relevant_facilities = []
        for keyword, facility_locations in facility_mapping.items():
            if keyword in message.lower():
                available_facilities = [loc['name'] for loc in locations if loc['name'] in facility_locations]
                if available_facilities:
                    relevant_facilities.extend(available_facilities)
        
        if relevant_facilities:
            facilities_text = ', '.join(relevant_facilities)
            return f"At {campus_display}, you can find these facilities: {facilities_text}. Use the Campus Map to get directions to any of these locations. I can also help you plan the best route if you need to visit multiple facilities!"
        
        # General facilities response
        all_facilities = [loc['name'] for loc in locations]
        facilities_sample = ', '.join(all_facilities[:10])
        
        return f"{campus_display} offers various facilities including: {facilities_sample}{'...' if len(all_facilities) > 10 else ''}. You can explore all locations using the interactive campus map. What specific facility are you looking for?"
    
    def generate_campus_info_response(self, message: str, context: Dict, campus: str) -> str:
        """Generate campus information response."""
        campus_data = context.get('campus_data', {})
        campus_display = campus.replace('-', ' ').title()
        
        if campus_data:
            center_coords = campus_data.get('center_coordinates', [])
            timezone = campus_data.get('timezone', 'UTC')
            
            return f"{campus_data.get('display_name', campus_display)} is one of the campuses in the Amrita Vishwa Vidyapeetham network. The campus is located at coordinates {center_coords[0]:.4f}, {center_coords[1]:.4f} and operates in the {timezone} timezone. You can explore the campus using our interactive map, check upcoming events, and get AI-powered assistance for navigation and information!"
        
        return f"Campus Explorer supports multiple Amrita campuses including Chennai, Coimbatore, Bengaluru, and Amritapuri. You're currently viewing {campus_display}. You can switch campuses using the campus selector and explore each campus's unique locations, events, and facilities!"
    
    def generate_help_response(self, user_name: str) -> str:
        """Generate help response."""
        return f"""Hi {user_name}! I'm your enhanced Campus Explorer AI assistant. Here's what I can help you with:

🗺️ **Navigation & Directions**
• "How do I get from the Academic Block to the Library?"
• "Where is the canteen?"
• "Show me the shortest route to the gym"

📅 **Events & Activities**
• "What events are happening today?"
• "Tell me about upcoming programs"
• "When is the next function?"

🏢 **Campus Facilities**
• "Where can I find the library?"
• "What sports facilities are available?"
• "Tell me about the hostels"

🎓 **Campus Information**
• "Tell me about this campus"
• "What campuses are available?"
• "Switch to a different campus"

Just ask me anything in natural language, and I'll do my best to help! You can also use the interactive map and events sections for more detailed information."""
    
    def generate_clarification_response(self, message: str, user_name: str) -> str:
        """Generate clarification response for unclear queries."""
        suggestions = [
            "Try asking about campus directions: 'How do I get to the library?'",
            "Ask about events: 'What's happening today?'",
            "Inquire about facilities: 'Where is the canteen?'",
            "Get campus information: 'Tell me about this campus'"
        ]
        
        import random
        suggestion = random.choice(suggestions)
        
        return f"I'm not quite sure what you're looking for, {user_name}. Could you please rephrase your question? For example, you could {suggestion.lower()} I'm here to help with navigation, events, facilities, and campus information!"
    
    def get_fallback_response(self) -> str:
        """Get fallback response for errors."""
        return "I apologize, but I'm experiencing some technical difficulties right now. Please try again in a moment, or use the Campus Map and Events sections directly. I'll be back to full functionality soon!"


# Singleton instance
ai_assistant = AIAssistant()