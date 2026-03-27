from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """User model for authentication and profile management."""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    profile_picture = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_manager = db.Column(db.Boolean, default=False, nullable=False)
    preferred_campus = db.Column(db.String(50), default='amrita-chennai')
    theme_preference = db.Column(db.String(20), default='light')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    events = db.relationship('Event', backref='creator', lazy='dynamic')
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    @property
    def role(self):
        """Derive effective role string from boolean flags."""
        if self.is_admin:
            return 'admin'
        if self.is_manager:
            return 'manager'
        return 'user'

    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'profile_picture': self.profile_picture,
            'is_admin': self.is_admin,
            'is_manager': self.is_manager,
            'role': self.role,
            'preferred_campus': self.preferred_campus,
            'theme_preference': self.theme_preference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Event(db.Model):
    """Enhanced Event model with campus relationships."""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    venue_name = db.Column(db.String(100), nullable=False)
    campus_id = db.Column(db.String(50), nullable=False, default='amrita-chennai')
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f'<Event {self.name}>'
    
    def to_dict(self):
        """Convert event object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'venue_name': self.venue_name,
            'campus_id': self.campus_id,
            'date': self.date.isoformat() if self.date else None,
            'time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'created_by': self.created_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'is_active': self.is_active
        }

class Campus(db.Model):
    """Campus model for managing multiple campus locations."""
    __tablename__ = 'campuses'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    center_latitude = db.Column(db.Float, nullable=False)
    center_longitude = db.Column(db.Float, nullable=False)
    locations_data = db.Column(db.JSON)  # Store location coordinates as JSON
    map_bounds = db.Column(db.JSON)  # Store map bounds as JSON
    timezone = db.Column(db.String(50), default='UTC')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Campus {self.display_name}>'
    
    def to_dict(self):
        """Convert campus object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'center_coordinates': [self.center_latitude, self.center_longitude],
            'locations': self.locations_data or {},
            'map_bounds': self.map_bounds or {},
            'timezone': self.timezone,
            'is_active': self.is_active
        }

class Conversation(db.Model):
    """Conversation model for AI chat history."""
    __tablename__ = 'conversations'
    
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    campus_context = db.Column(db.String(50))
    messages = db.Column(db.JSON)  # Store conversation messages as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Conversation {self.id}>'
    
    def to_dict(self):
        """Convert conversation object to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'campus_context': self.campus_context,
            'messages': self.messages or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }