from app import db
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import text, exc, Column, String
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import secrets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True)
    appointments = db.relationship('Appointment', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def generate_verification_token(self):
        self.verification_token = secrets.token_urlsafe(32)
        return self.verification_token

    def __repr__(self):
        return f'<User {self.username}>'

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
    try:
        db.create_all()
        logger.info("Tables created successfully")
    except exc.SQLAlchemyError as e:
        logger.error(f"Error creating tables: {str(e)}")
        return

    try:
        inspector = db.inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('user')]
        
        if 'created_at' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
                conn.commit()
            logger.info('Successfully added created_at column to user table')
        else:
            logger.info('Created_at column already exists in user table')

        if 'is_verified' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN is_verified BOOLEAN DEFAULT FALSE'))
                conn.commit()
            logger.info('Successfully added is_verified column to user table')

        if 'verification_token' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN verification_token VARCHAR(100) UNIQUE'))
                conn.commit()
            logger.info('Successfully added verification_token column to user table')

        logger.info("Current schema of 'user' table:")
        for column in inspector.get_columns('user'):
            logger.info(f"Column: {column['name']}, Type: {column['type']}")

    except exc.SQLAlchemyError as e:
        logger.error(f'Error updating database schema: {str(e)}')
        return

    try:
        default_barber = User.query.filter_by(username='barber').first()
        if not default_barber:
            default_barber = User(username='barber', email='barber@example.com', role='barber')
            default_barber.set_password('barber_password')
            db.session.add(default_barber)
            db.session.commit()
            logger.info('Created default barber user')
        else:
            logger.info('Default barber user already exists')
    except exc.SQLAlchemyError as e:
        logger.error(f'Error creating default barber user: {str(e)}')
        db.session.rollback()
        return

    logger.info("Database initialization completed successfully")