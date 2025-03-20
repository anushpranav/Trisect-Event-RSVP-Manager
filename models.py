from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class Organizer(db.Model, UserMixin):
    __tablename__ = 'Organizers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    passwordHash = db.Column(db.String(255), nullable=False)
    createdAt = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    
    events = db.relationship('Event', backref='organizer', lazy=True)
    
    def is_admin(self):
        return False

class Event(db.Model):
    __tablename__ = 'Events'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255))
    organizerId = db.Column(db.Integer, db.ForeignKey('Organizers.id', ondelete='CASCADE'))
    customFields = db.Column(db.JSON)
    createdAt = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    
    guests = db.relationship('Guest', backref='event', lazy=True)
    
    def get_custom_fields(self):
        return json.loads(self.customFields) if self.customFields else {}
    
    def get_rsvp_stats(self):
        confirmed = sum(1 for g in self.guests if g.status == 'confirmed')
        declined = sum(1 for g in self.guests if g.status == 'declined')
        pending = sum(1 for g in self.guests if g.status == 'pending')
        total_plus_ones = sum(g.plusOneCount for g in self.guests if g.status == 'confirmed')
        
        return {
            'confirmed': confirmed,
            'declined': declined,
            'pending': pending,
            'total_attending': confirmed + total_plus_ones
        }

class Guest(db.Model):
    __tablename__ = 'Guests'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    eventId = db.Column(db.Integer, db.ForeignKey('Events.id', ondelete='CASCADE'))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    status = db.Column(db.Enum('pending', 'confirmed', 'declined'), default='pending')
    responses = db.Column(db.JSON)
    plusOneCount = db.Column(db.Integer, default=0)
    uniqueAccessToken = db.Column(db.String(255), unique=True, nullable=False)
    lastReminderSent = db.Column(db.TIMESTAMP, nullable=True)
    createdAt = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updatedAt = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                         onupdate=db.func.current_timestamp())
    
    def get_responses(self):
        return json.loads(self.responses) if self.responses else {}
    
    def update_status(self, status, plus_one_count=None, responses=None):
        self.status = status
        if plus_one_count is not None:
            self.plusOneCount = plus_one_count
        if responses:
            self.responses = json.dumps(responses)
        self.updatedAt = datetime.utcnow()