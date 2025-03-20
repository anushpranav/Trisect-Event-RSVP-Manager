from models import Event, Guest
from datetime import datetime
import pandas as pd

def get_event_analytics(event_id):
    """Get analytics for a specific event"""
    try:
        event = Event.query.get(event_id)
        if not event:
            return None

        # Get all guests for the event
        guests = Guest.query.filter_by(eventId=event_id).all()
        
        # Convert guest data to DataFrame
        guest_data = [{
            'status': guest.status,
            'response_date': guest.updatedAt,
            'plus_ones': guest.plusOneCount
        } for guest in guests]
        
        df = pd.DataFrame(guest_data)
        
        # Response timeline
        if not df.empty and 'response_date' in df.columns:
            timeline = df['response_date'].value_counts().sort_index()
            # Convert Timestamps to string format
            timeline_dict = {
                date.strftime('%Y-%m-%d'): count 
                for date, count in timeline.items()
            }
        else:
            timeline_dict = {}

        # Calculate statistics
        stats = {
            'total_guests': len(guests),
            'response_rate': len(df[df['status'].isin(['confirmed', 'declined'])]) / len(df) if not df.empty else 0,
            'confirmation_rate': len(df[df['status'] == 'confirmed']) / len(df) if not df.empty else 0,
            'total_attending': df[df['status'] == 'confirmed']['plus_ones'].sum() + len(df[df['status'] == 'confirmed']) if not df.empty else 0
        }

        return {
            'timeline': timeline_dict,
            'stats': stats
        }
    except Exception as e:
        print(f"Analytics error: {e}")
        return {
            'timeline': {},
            'stats': {
                'total_guests': 0,
                'response_rate': 0,
                'confirmation_rate': 0,
                'total_attending': 0
            }
        }

def get_organizer_analytics(organizer_id):
    """Get analytics for all events of an organizer"""
    try:
        events = Event.query.filter_by(organizerId=organizer_id).all()
        
        total_guests = 0
        total_responses = 0
        total_confirmed = 0
        
        for event in events:
            guests = Guest.query.filter_by(eventId=event.id).all()
            total_guests += len(guests)
            total_responses += len([g for g in guests if g.status != 'pending'])
            total_confirmed += len([g for g in guests if g.status == 'confirmed'])
        
        return {
            'total_events': len(events),
            'total_guests': total_guests,
            'average_response_rate': total_responses / total_guests if total_guests > 0 else 0,
            'average_confirmation_rate': total_confirmed / total_guests if total_guests > 0 else 0
        }
    except Exception as e:
        print(f"Organizer analytics error: {e}")
        return {
            'total_events': 0,
            'total_guests': 0,
            'average_response_rate': 0,
            'average_confirmation_rate': 0
        }