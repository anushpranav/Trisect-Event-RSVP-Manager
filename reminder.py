from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app, url_for
from models import Event, Guest, db
from flask_mail import Message
from flask import render_template
from email_utils import send_reminder_email

scheduler = BackgroundScheduler()

def send_reminder_email(guest):
    """Send reminder email to guest"""
    try:
        app = current_app
        mail = app.mail
        event = guest.event
        rsvp_url = url_for('routes.rsvp_page', token=guest.uniqueAccessToken, _external=True)
        html = render_template('reminder.html', guest=guest, event=event, rsvp_url=rsvp_url)
        msg = Message(
            subject=f"Reminder: {event.title} is coming up!",
            recipients=[guest.email],
            html=html
        )
        mail.send(msg)
        guest.lastReminderSent = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        print(f"Error sending reminder to {guest.email}: {e}")

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
                                if send_reminder_email(guest):
                                    guest.lastReminderSent = datetime.utcnow()
                                    db.session.commit()
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