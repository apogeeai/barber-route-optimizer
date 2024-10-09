from app import db
from datetime import datetime

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    appointment_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Appointment {self.id}: {self.client_name} at {self.appointment_time}>'

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    is_available = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<TimeSlot {self.id}: {self.start_time} - Available: {self.is_available}>'
