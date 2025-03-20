from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from models import Event, Guest, db

scheduler = BackgroundScheduler()

def send_reminder_email(guest):
    """Send reminder email to guest"""
    # Implement email sending logic here
    print(f"Sending reminder to {guest.email} for event {guest.event.title}")
    guest.lastReminderSent = datetime.utcnow()
    db.session.commit()

def check_and_send_reminders():
    """Check for upcoming events and send reminders"""
    # Create an app context
    with scheduler.app.app_context():
        try:
            now = datetime.utcnow()
            upcoming_events = Event.query.filter(
                Event.date > now,
                Event.date <= now + timedelta(days=7)
            ).all()
            
            for event in upcoming_events:
                for guest in event.guests:
                    if guest.status == 'pending':
                        days_until_event = (event.date - now).days
                        if days_until_event in [7, 3, 1]:
                            if not guest.lastReminderSent or \
                               (now - guest.lastReminderSent).days >= 1:
                                send_reminder_email(guest)
        except Exception as e:
            print(f"Reminder error: {e}")

def init_scheduler(app):
    """Initialize the scheduler with the Flask app"""
    scheduler.app = app
    scheduler.add_job(
        check_and_send_reminders,
        'interval',
        days=1,
        id='check_and_send_reminders',
        replace_existing=True
    )
    scheduler.start()

def start_reminder_scheduler():
    """Start the reminder scheduler - this should not be called directly"""
    pass  # The actual initialization happens in init_scheduler