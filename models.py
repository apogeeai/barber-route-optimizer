from app import db
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import text

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    appointments = db.relationship('Appointment', backref='user', lazy=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    appointment_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Appointment {self.id}: {self.client_name} at {self.appointment_time}>'

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    is_available = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<TimeSlot {self.id}: {self.start_time} - Available: {self.is_available}>'

def init_db():
    db.create_all()
    try:
        # Check if the alteration is necessary
        result = db.session.execute(text("SELECT character_maximum_length FROM information_schema.columns WHERE table_name='user' AND column_name='password'"))
        current_length = result.scalar()
        
        if current_length != 255:
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN password TYPE VARCHAR(255)'))
            db.session.commit()
            print('Successfully updated password column length to 255')
        else:
            print('Password column length is already 255, no update needed')
    except Exception as e:
        print(f'Error updating password column length: {str(e)}')
        db.session.rollback()
