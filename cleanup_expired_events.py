"""
Cleanup script to automatically delete expired events after 24 hours.
This script should be run periodically (e.g., via cron job or task scheduler).
"""

from datetime import datetime, timedelta
from app import create_app, db
from app.models import Event

def cleanup_expired_events():
    """Delete events that expired more than 24 hours ago."""
    app = create_app()
    
    with app.app_context():
        try:
            # Calculate the cutoff time (24 hours ago)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Find expired events
            expired_events = Event.query.filter(
                Event.is_active == True
            ).all()
            
            deleted_count = 0
            for event in expired_events:
                # Combine date and time to get event datetime
                event_datetime = datetime.combine(event.date, event.start_time)
                
                # Use end_time if available, otherwise use start_time
                if event.end_time:
                    event_end_datetime = datetime.combine(event.date, event.end_time)
                else:
                    event_end_datetime = event_datetime
                
                # Check if event ended more than 24 hours ago
                if event_end_datetime < cutoff_time:
                    print(f"Deleting expired event: {event.name} (ended at {event_end_datetime})")
                    db.session.delete(event)
                    deleted_count += 1
            
            # Commit all deletions
            if deleted_count > 0:
                db.session.commit()
                print(f"✓ Successfully deleted {deleted_count} expired event(s)")
            else:
                print("No expired events to delete")
                
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error cleaning up expired events: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("Expired Events Cleanup")
    print("=" * 60)
    cleanup_expired_events()
