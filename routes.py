from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db
from models import Appointment, TimeSlot, User
from utils import optimize_route
from datetime import datetime, timedelta
import json

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
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registered successfully')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully')
            if user.role == 'barber':
                return redirect(url_for('barber_view'))
            else:
                return redirect(url_for('client_dashboard'))
        flash('Invalid username or password')
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
