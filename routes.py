from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from flask_socketio import emit
from app import app, db, socketio
from models import Appointment, TimeSlot, User
from utils import optimize_route, is_password_strong
from datetime import datetime, timedelta
import json
from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = 'smtp.example.com'  # Replace with your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@example.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your_email_password'  # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@example.com'  # Replace with your email

mail = Mail(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
        
        if not is_password_strong(password):
            flash('Password is not strong enough. It should be at least 8 characters long and contain uppercase, lowercase, digit, and special character.', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        new_user.generate_verification_token()
        db.session.add(new_user)
        db.session.commit()

        verification_link = url_for('verify_email', token=new_user.verification_token, _external=True)
        msg = Message('Verify Your Email', recipients=[new_user.email])
        msg.body = f'Click the following link to verify your email: {verification_link}'
        mail.send(msg)

        flash('Registered successfully. Please check your email for verification.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/verify_email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Your email has been verified. You can now log in.', 'success')
    else:
        flash('Invalid verification token.', 'error')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_verified:
                flash('Please verify your email before logging in.', 'error')
                return redirect(url_for('login'))
            login_user(user)
            flash('Logged in successfully', 'success')
            if user.role == 'barber':
                return redirect(url_for('barber_view'))
            else:
                return redirect(url_for('client_dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'barber':
        return redirect(url_for('barber_view'))
    else:
        return redirect(url_for('client_dashboard'))

@app.route('/client_dashboard')
@login_required
def client_dashboard():
    if current_user.role != 'client':
        flash('Access denied')
        return redirect(url_for('index'))
    appointments = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.appointment_time).all()
    return render_template('client_dashboard.html', appointments=appointments)

@app.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    if current_user.role != 'client':
        flash('Only clients can book appointments')
        return redirect(url_for('index'))
    if request.method == 'POST':
        client_name = request.form['client_name']
        address = request.form['address']
        latitude = float(request.form['latitude'])
        longitude = float(request.form['longitude'])
        appointment_time = datetime.strptime(request.form['appointment_time'], '%Y-%m-%dT%H:%M')

        new_appointment = Appointment(
            client_name=client_name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            appointment_time=appointment_time,
            user_id=current_user.id
        )
        db.session.add(new_appointment)
        db.session.commit()

        flash('Appointment booked successfully')
        return redirect(url_for('client_dashboard'))

    available_slots = TimeSlot.query.filter_by(is_available=True).all()
    return render_template('booking.html', available_slots=available_slots)

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/barber_view')
@login_required
def barber_view():
    if current_user.role != 'barber':
        flash('Only barbers can access this page')
        return redirect(url_for('index'))
    appointments = Appointment.query.order_by(Appointment.appointment_time).all()
    optimized_route = optimize_route(appointments)
    return render_template('barber_view.html', appointments=appointments, optimized_route=json.dumps(optimized_route))

@app.route('/get_available_slots')
@login_required
def get_available_slots():
    available_slots = TimeSlot.query.filter_by(is_available=True).all()
    slots = [{'id': slot.id, 'start_time': slot.start_time.isoformat()} for slot in available_slots]
    return json.dumps(slots)

@app.route('/book_slot', methods=['POST'])
@login_required
def book_slot():
    slot_id = request.form['slot_id']
    slot = TimeSlot.query.get(slot_id)
    if slot and slot.is_available:
        slot.is_available = False
        db.session.commit()
        return json.dumps({'success': True})
    return json.dumps({'success': False})

@app.route('/update_appointment_status', methods=['POST'])
@login_required
def update_appointment_status():
    if current_user.role != 'barber':
        return jsonify({'success': False, 'message': 'Only barbers can update appointment status'}), 403
    
    appointment_id = request.json.get('appointment_id')
    new_status = request.json.get('status')
    
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found'}), 404
    
    appointment.status = new_status
    db.session.commit()
    
    socketio.emit('appointment_status_updated', {'appointment_id': appointment_id, 'status': new_status}, room=str(appointment.user_id))
    return jsonify({'success': True, 'message': 'Appointment status updated'})

@app.route('/update_barber_location', methods=['POST'])
@login_required
def update_barber_location():
    if current_user.role != 'barber':
        return jsonify({'success': False, 'message': 'Only barbers can update their location'}), 403
    
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')
    
    socketio.emit('barber_location_updated', {'latitude': latitude, 'longitude': longitude}, broadcast=True)
    return jsonify({'success': True, 'message': 'Barber location updated'})

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        socketio.emit('user_connected', {'user_id': current_user.id, 'username': current_user.username})

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        socketio.emit('user_disconnected', {'user_id': current_user.id, 'username': current_user.username})

def initialize_time_slots():
    if TimeSlot.query.first() is None:
        start_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        for _ in range(14):  # Two weeks of slots
            current_date = start_date
            while current_date.hour < 17:
                new_slot = TimeSlot(start_time=current_date)
                db.session.add(new_slot)
                current_date += timedelta(minutes=30)
            start_date += timedelta(days=1)
        db.session.commit()

with app.app_context():
    initialize_time_slots()