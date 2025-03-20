from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Organizer, Event, Guest
from qr_generator import generate_rsvp_qr
from analytics import get_event_analytics, get_organizer_analytics
import bcrypt
import secrets
from datetime import datetime
import json

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
        
        # Generate QR code
        qr_code = generate_rsvp_qr(new_guest.uniqueAccessToken)
        return jsonify({
            'success': True,
            'guest_id': new_guest.id,
            'rsvp_link': url_for('routes.rsvp_page', token=new_guest.uniqueAccessToken, _external=True)
        })
    
    guests = Guest.query.filter_by(eventId=event_id).all()
    return render_template('/guest_list.html', event=event, guests=guests)

# RSVP handling
@routes.route('/rsvp/<token>', methods=['GET', 'POST'])
def rsvp_page(token):
    guest = Guest.query.filter_by(uniqueAccessToken=token).first_or_404()
    event = guest.event
    
    if request.method == 'POST':
        data = request.get_json()
        guest.update_status(
            status=data['status'],
            plus_one_count=data.get('plus_one_count', 0),
            responses=data.get('responses', {})
        )
        db.session.commit()
        return jsonify({'success': True})
    
    return render_template('/rsvp_page.html', guest=guest, event=event)

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