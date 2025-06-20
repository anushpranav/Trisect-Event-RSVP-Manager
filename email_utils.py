from flask_mail import Message, Attachment
from flask import render_template, url_for, current_app

def send_invitation_email(guest, event, qr_image_io=None):
    """Send invitation email to guest, with optional QR code attachment."""
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

        if qr_image_io:
            msg.attach(
                filename='rsvp_qr_code.png',
                content_type='image/png',
                data=qr_image_io.read(),
                disposition='inline',
                headers={'Content-ID': '<qrcode>'}
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

def send_password_reset_email(email, token):
    try:
        app = current_app
        mail = app.mail
        reset_url = url_for('routes.reset_password', token=token, _external=True)
        html = render_template('reset_email.html', reset_url=reset_url)
        sender = f"Trisect RSVP Manager <{app.config['MAIL_USERNAME']}>"
        msg = Message(
            subject="Password Reset Request",
            sender=sender,
            recipients=[email],
            html=html
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending password reset to {email}: {e}")
        return False 