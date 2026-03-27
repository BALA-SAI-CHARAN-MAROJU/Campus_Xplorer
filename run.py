"""
Campus Explorer - Enhanced Application Entry Point
"""

import os
from app import create_app, db
from app.models import User, Event, Campus, Conversation

# Create application instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    """Make database models available in shell context."""
    return {
        'db': db,
        'User': User,
        'Event': Event,
        'Campus': Campus,
        'Conversation': Conversation
    }

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized successfully.')

@app.cli.command()
def create_admin():
    """Create an admin user."""
    from app.models import User
    import uuid
    
    admin_email = app.config.get('DEFAULT_ADMIN_EMAIL', 'admin@campusexplorer.com')
    
    # Check if admin already exists
    admin = User.query.filter_by(email=admin_email).first()
    if admin:
        print(f'Admin user {admin_email} already exists.')
        return
    
    # Create admin user
    admin = User(
        id=str(uuid.uuid4()),
        google_id=f'admin_{uuid.uuid4()}',
        email=admin_email,
        name='Campus Explorer Admin',
        is_admin=True
    )
    
    db.session.add(admin)
    db.session.commit()
    
    print(f'Admin user {admin_email} created successfully.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)