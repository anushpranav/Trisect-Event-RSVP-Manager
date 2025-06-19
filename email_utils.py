from flask_mail import Message
from flask import render_template, url_for, current_app

def send_invitation_email(guest, event, organizer_email):
    """Send invitation email to guest, using the dedicated RSVP email as sender."""
    try:
        app = current_app
        mail = app.mail
        rsvp_url = url_for('routes.rsvp_page', token=guest.uniqueAccessToken, _external=True)
        html = render_template('invite.html', guest=guest, event=event, rsvp_url=rsvp_url)
        
        # Use a friendly display name with the email
        sender = f"RSVP Manager <{app.config['MAIL_USERNAME']}>"
        
        msg = Message(
            subject=f"You're Invited: {event.title}",
            sender=sender,
            recipients=[guest.email],
            html=html
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending invite to {guest.email}: {e}")
        return False

def send_reminder_email(guest, event):
    """Send reminder email to guest using the dedicated RSVP email as sender."""
    try:
        app = current_app
        mail = app.mail
        rsvp_url = url_for('routes.rsvp_page', token=guest.uniqueAccessToken, _external=True)
        html = render_template('reminder.html', guest=guest, event=event, rsvp_url=rsvp_url)
        
        # Use a friendly display name with the email
        sender = f"RSVP Manager <{app.config['MAIL_USERNAME']}>"
        
        msg = Message(
            subject=f"Reminder: {event.title} is coming up!",
            sender=sender,
            recipients=[guest.email],
            html=html
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending reminder to {guest.email}: {e}")
        return False 