"""
Initialize database with default campus data.
"""

from app import create_app, db
from app.models import Campus
from datetime import datetime

def init_campus_data():
    """Initialize campus data."""
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if campuses already exist
        if Campus.query.count() > 0:
            print("Campus data already exists. Skipping initialization.")
            return
        
        # Default campus data
        campuses_data = [
            {
                'id': 'amrita-chennai',
                'name': 'amrita-chennai',
                'display_name': 'Amrita Chennai Campus',
                'center_latitude': 13.263018,
                'center_longitude': 80.027427,
                'timezone': 'Asia/Kolkata',
                'locations_data': {
                    'Academic Block': [13.263018, 80.027427],
                    'Library': [13.262621, 80.026525],
                    'Canteen': [13.262856, 80.028401],
                    'Pond': [13.262198, 80.027673],
                    'AVV Gym for Girls': [13.262141, 80.026830],
                    'Junior Girls Hostel': [13.261993, 80.026421],
                    'Junior Boys Hostel': [13.261805, 80.028076],
                    'Lab Block': [13.262768, 80.028147],
                    'Mechanical Lab': [13.261205, 80.027488],
                    'Volley Ball Court': [13.261009, 80.027530],
                    'Basket Ball Court': [13.260909, 80.027256],
                    'Senior Girls Hostel': [13.260658, 80.028184],
                    'Senior Boys Hostel': [13.260550, 80.027272],
                    '2nd Year Boys Hostel': [13.259570, 80.026694],
                    'Amrita Indoor Stadium': [13.259880, 80.025990],
                    'AVV Gym for Boys': [13.260146, 80.026143],
                    'AVV Ground': [13.259708, 80.025416],
                    'Amrita Vishwa Vidyapeetham': [13.2630, 80.0274]
                },
                'map_bounds': {
                    'north': 13.265,
                    'south': 13.259,
                    'east': 80.030,
                    'west': 80.025
                }
            },
            {
                'id': 'amrita-coimbatore',
                'name': 'amrita-coimbatore',
                'display_name': 'Amrita Coimbatore Campus',
                'center_latitude': 10.9027,
                'center_longitude': 76.9024,
                'timezone': 'Asia/Kolkata',
                'locations_data': {
                    'Main Building': [10.9027, 76.9024],
                    'Engineering Block': [10.9030, 76.9020],
                    'Library': [10.9025, 76.9028],
                    'Canteen': [10.9020, 76.9025],
                    'Hostel Block A': [10.9015, 76.9030],
                    'Hostel Block B': [10.9010, 76.9035],
                    'Sports Complex': [10.9035, 76.9015],
                    'Auditorium': [10.9028, 76.9022]
                },
                'map_bounds': {
                    'north': 10.905,
                    'south': 10.900,
                    'east': 76.905,
                    'west': 76.900
                }
            },
            {
                'id': 'amrita-bengaluru',
                'name': 'amrita-bengaluru',
                'display_name': 'Amrita Bengaluru Campus',
                'center_latitude': 12.9716,
                'center_longitude': 77.5946,
                'timezone': 'Asia/Kolkata',
                'locations_data': {
                    'Academic Block': [12.9716, 77.5946],
                    'Research Center': [12.9720, 77.5950],
                    'Library': [12.9712, 77.5942],
                    'Cafeteria': [12.9714, 77.5948],
                    'Student Center': [12.9718, 77.5944],
                    'Parking Area': [12.9710, 77.5940],
                    'Conference Hall': [12.9722, 77.5952]
                },
                'map_bounds': {
                    'north': 12.975,
                    'south': 12.968,
                    'east': 77.600,
                    'west': 77.590
                }
            },
            {
                'id': 'amrita-amritapuri',
                'name': 'amrita-amritapuri',
                'display_name': 'Amrita Amritapuri Campus',
                'center_latitude': 9.0982,
                'center_longitude': 76.4951,
                'timezone': 'Asia/Kolkata',
                'locations_data': {
                    'Main Campus': [9.0982, 76.4951],
                    'Engineering Block': [9.0985, 76.4955],
                    'Biotechnology Block': [9.0980, 76.4948],
                    'Hostel Complex': [9.0975, 76.4945],
                    'Sports Ground': [9.0988, 76.4958],
                    'Ashram': [9.0990, 76.4960]
                },
                'map_bounds': {
                    'north': 9.100,
                    'south': 9.095,
                    'east': 76.500,
                    'west': 76.490
                }
            }
        ]
        
        # Create campus records
        for campus_data in campuses_data:
            campus = Campus(
                id=campus_data['id'],
                name=campus_data['name'],
                display_name=campus_data['display_name'],
                center_latitude=campus_data['center_latitude'],
                center_longitude=campus_data['center_longitude'],
                locations_data=campus_data['locations_data'],
                map_bounds=campus_data['map_bounds'],
                timezone=campus_data['timezone'],
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(campus)
        
        # Commit changes
        db.session.commit()
        print(f"Successfully initialized {len(campuses_data)} campuses.")

if __name__ == '__main__':
    init_campus_data()