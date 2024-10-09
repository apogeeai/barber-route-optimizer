from app import db
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import text, exc, Column, String
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='client')
    appointments = db.relationship('Appointment', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

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
        # Check if the 'role' column exists in the 'user' table
        inspector = db.inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('user')]
        if 'role' not in columns:
            # Add the 'role' column if it doesn't exist
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN role VARCHAR(20) DEFAULT \'client\''))
                conn.commit()
            logger.info('Successfully added role column to user table')
        else:
            logger.info('Role column already exists in user table')

        # Print the current schema of the 'user' table
        logger.info("Current schema of 'user' table:")
        for column in inspector.get_columns('user'):
            logger.info(f"Column: {column['name']}, Type: {column['type']}")

        # Add user_id column to appointment table if it doesn't exist
        appointment_columns = [c['name'] for c in inspector.get_columns('appointment')]
        if 'user_id' not in appointment_columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE appointment ADD COLUMN user_id INTEGER'))
                conn.execute(text('ALTER TABLE appointment ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES "user"(id)'))
                conn.commit()
            logger.info('Successfully added user_id column to appointment table')

    except exc.SQLAlchemyError as e:
        logger.error(f'Error updating database schema: {str(e)}')
        return

    # Create a default barber user if not exists
    try:
        default_barber = User.query.filter_by(username='barber').first()
        if not default_barber:
            default_barber = User(username='barber', role='barber')
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
