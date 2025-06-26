from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Organizer, Event, Guest
from qr_generator import generate_rsvp_qr
from analytics import get_event_analytics, get_organizer_analytics
from email_utils import send_invitation_email, send_reminder_email, send_password_reset_email
import bcrypt
import secrets
from datetime import datetime
import json
from flask_mail import Message
from flask import current_app
import csv
from io import StringIO
from itsdangerous import URLSafeTimedSerializer

routes = Blueprint('routes', __name__)

# Index route
@routes.route('/')
def index():
    return render_template('index.html')

# Homepage route (alternative)
@routes.route('/home')
def home():
    return render_template('index.html')

# Authentication routes
@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        organizer = Organizer.query.filter_by(email=email).first()
        if organizer and bcrypt.checkpw(password.encode('utf-8'), 
                                      organizer.passwordHash.encode('utf-8')):
            login_user(organizer)
            return redirect(url_for('routes.dashboard'))
            
        flash('Invalid email or password')
    return render_template('/login.html')

@routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if Organizer.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('routes.register'))
            
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_organizer = Organizer(
            name=name,
            email=email,
            passwordHash=hashed_pw.decode('utf-8')
        )
        
        db.session.add(new_organizer)
        db.session.commit()
        
        login_user(new_organizer)
        return redirect(url_for('routes.dashboard'))
    return render_template('/register.html')

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

# Dashboard and event management
@routes.route('/dashboard')
@login_required
def dashboard():
    events = Event.query.filter_by(organizerId=current_user.id).all()
    analytics = get_organizer_analytics(current_user.id)
    return render_template('/organizer.html', events=events, analytics=analytics)

@routes.route('/event/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        custom_fields = {
            'meal_options': request.form.getlist('meal_options[]'),
            'dress_code': request.form.get('dress_code'),
            'additional_info': request.form.get('additional_info')
        }
        
        new_event = Event(
            title=request.form.get('title'),
            description=request.form.get('description'),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M'),
            location=request.form.get('location'),
            organizerId=current_user.id,
            customFields=json.dumps(custom_fields)
        )
        
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for('routes.event_details', event_id=new_event.id))
    
    return render_template('/create.html')

@routes.route('/event/<int:event_id>')
@login_required
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizerId != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('routes.dashboard'))
        
    analytics = get_event_analytics(event_id)
    return render_template('/view.html', event=event, analytics=analytics)

@routes.route('/event/<int:event_id>/guests', methods=['GET', 'POST'])
@login_required
def manage_guests(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizerId != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    if request.method == 'POST':
        data = request.get_json()
        new_guest = Guest(
            eventId=event_id,
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            uniqueAccessToken=secrets.token_urlsafe(32)
        )
        db.session.add(new_guest)
        db.session.commit()
        
        qr_image_io = None
        if data.get('sendInvite', False):
            # Generate QR code
            qr_image_io = generate_rsvp_qr(new_guest.uniqueAccessToken)
            # Send invitation email
            send_invitation_email(new_guest, event, qr_image_io=qr_image_io)
            
        return jsonify({
            'success': True,
            'guest': {
                'id': new_guest.id,
                'name': new_guest.name,
                'email': new_guest.email,
                'phone': new_guest.phone,
                'status': new_guest.status,
                'plusOneCount': new_guest.plusOneCount,
                'updatedAt': new_guest.updatedAt.strftime('%Y-%m-%d %H:%M'),
                'uniqueAccessToken': new_guest.uniqueAccessToken
            }
        })
    
    guests = Guest.query.filter_by(eventId=event_id).all()
    return render_template('/guest_list.html', event=event, guests=guests)

# RSVP handling
@routes.route('/rsvp/<token>', methods=['GET', 'POST'])
def rsvp_page(token):
    try:
        guest = Guest.query.filter_by(uniqueAccessToken=token).first_or_404()
        event = guest.event
        
        if request.method == 'POST':
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Invalid request data'}), 400
                
                guest.update_status(
                    status=data['status'],
                    plus_one_count=data.get('plus_one_count', 0),
                    responses=data.get('responses', {})
                )
                db.session.commit()
                return jsonify({'success': True})
            except Exception as e:
                db.session.rollback()
                print(f"Error updating RSVP: {e}")
                return jsonify({'success': False, 'error': 'Failed to update RSVP'}), 500
        
        return render_template('/rsvp_page.html', guest=guest, event=event)
    except Exception as e:
        print(f"Error in RSVP page: {e}")
        return jsonify({'success': False, 'error': 'Invalid RSVP link'}), 404

@routes.route('/event/<int:event_id>/guest/<int:guest_id>/qr')
@login_required
def get_guest_qr(event_id, guest_id):
    event = Event.query.get_or_404(event_id)
    if event.organizerId != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    guest = Guest.query.get_or_404(guest_id)
    if guest.eventId != event_id:
        return jsonify({'error': 'Guest not found for this event'}), 404
    
    qr_image = generate_rsvp_qr(guest.uniqueAccessToken)
    if qr_image:
        return send_file(
            qr_image,
            mimetype='image/png',
            as_attachment=False,
            download_name=f'rsvp_qr_{guest.name}.png'
        )
    return jsonify({'error': 'Failed to generate QR code'}), 500

@routes.route('/event/<int:event_id>/guest/<int:guest_id>/qr/download')
@login_required
def download_guest_qr(event_id, guest_id):
    event = Event.query.get_or_404(event_id)
    if event.organizerId != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    guest = Guest.query.get_or_404(guest_id)
    if guest.eventId != event_id:
        return jsonify({'error': 'Guest not found for this event'}), 404
    
    qr_image = generate_rsvp_qr(guest.uniqueAccessToken)
    if qr_image:
        response = make_response(send_file(
            qr_image,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'rsvp_qr_{guest.name}.png'
        ))
        response.headers['Content-Disposition'] = f'attachment; filename=rsvp_qr_{guest.name}.png'
        return response
    return jsonify({'error': 'Failed to generate QR code'}), 500

@routes.route('/event/<int:event_id>/guests/remind', methods=['POST'])
@login_required
def send_bulk_reminders(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizerId != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    data = request.get_json()
    recipient_type = data.get('recipientType', 'pending')
    if recipient_type == 'pending':
        guests = [g for g in event.guests if g.status == 'pending']
    elif recipient_type == 'confirmed':
        guests = [g for g in event.guests if g.status == 'confirmed']
    else:
        guests = [g for g in event.guests if g.status in ('pending', 'confirmed')]
    count = 0
    for guest in guests:
        if send_reminder_email(guest, event, recipient_type=guest.status):
            count += 1
    return jsonify({'success': True, 'message': f'Reminders sent to {count} {recipient_type} guests.'})

@routes.route('/event/<int:event_id>/guests/export')
@login_required
def export_guest_list(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizerId != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Create CSV data
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Name', 'Email', 'Phone', 'Status', 'Plus Ones', 'Last Updated', 'Responses'])
    
    for guest in event.guests:
        responses = guest.get_responses()
        response_str = ', '.join([f"{k}: {v}" for k, v in responses.items()]) if responses else ''
        cw.writerow([
            guest.name,
            guest.email,
            guest.phone or '',
            guest.status,
            guest.plusOneCount,
            guest.updatedAt.strftime('%Y-%m-%d %H:%M'),
            response_str
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=guests_{event.title.replace(' ', '_')}.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@routes.route('/event/<int:event_id>/guest/<int:guest_id>', methods=['GET', 'PUT'])
@login_required
def manage_single_guest(event_id, guest_id):
    event = Event.query.get_or_404(event_id)
    if event.organizerId != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    guest = Guest.query.get_or_404(guest_id)
    if guest.eventId != event_id:
        return jsonify({'error': 'Guest not found for this event'}), 404

    if request.method == 'GET':
        return jsonify({
            'id': guest.id,
            'name': guest.name,
            'email': guest.email,
            'phone': guest.phone
        })

    if request.method == 'PUT':
        data = request.get_json()
        guest.name = data.get('name', guest.name)
        guest.email = data.get('email', guest.email)
        guest.phone = data.get('phone', guest.phone)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Guest updated successfully.'})

@routes.route('/event/<int:event_id>/guest/<int:guest_id>', methods=['DELETE'])
@login_required
def delete_guest(event_id, guest_id):
    event = Event.query.get_or_404(event_id)
    if event.organizerId != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    guest = Guest.query.get_or_404(guest_id)
    if guest.eventId != event_id:
        return jsonify({'error': 'Guest not found for this event'}), 404
    
    db.session.delete(guest)
    db.session.commit()
    return jsonify({'success': True})

@routes.route('/event/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizerId != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('routes.dashboard'))
    
    if request.method == 'POST':
        custom_fields = {
            'meal_options': request.form.getlist('meal_options[]'),
            'dress_code': request.form.get('dress_code'),
            'additional_info': request.form.get('additional_info')
        }
        
        event.title = request.form.get('title')
        event.description = request.form.get('description')
        event.date = datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M')
        event.location = request.form.get('location')
        event.customFields = json.dumps(custom_fields)
        
        db.session.commit()
        flash('Event updated successfully!')
        return redirect(url_for('routes.event_details', event_id=event.id))
    
    return render_template('/edit.html', event=event)

@routes.route('/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizerId != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!')
    return redirect(url_for('routes.dashboard'))

@routes.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Here you could add logic to send the message via email or store it
        flash('Thank you for contacting us! We will get back to you soon.')
        return redirect(url_for('routes.contact'))
    return render_template('contact.html')

@routes.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Organizer.query.filter_by(email=email).first()
        if user:
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='password-reset-salt')
            send_password_reset_email(user.email, token)
            flash('A password reset link has been sent to your email.')
        else:
            flash('If that email is registered, a reset link has been sent.')
        return redirect(url_for('routes.forgot_password'))
    return render_template('forgot_password.html')

@routes.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception:
        flash('The password reset link is invalid or has expired.')
        return redirect(url_for('routes.forgot_password'))
    user = Organizer.query.filter_by(email=email).first()
    if not user:
        flash('Invalid user.')
        return redirect(url_for('routes.forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        if password:
            import bcrypt
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user.passwordHash = hashed_pw.decode('utf-8')
            db.session.commit()
            flash('Your password has been reset. You can now log in.')
            return redirect(url_for('routes.login'))
        else:
            flash('Please enter a new password.')
    return render_template('reset_password.html', token=token)