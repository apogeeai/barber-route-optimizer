from flask import render_template, request, redirect, url_for, jsonify
from app import app, db
from models import Appointment, TimeSlot
from utils import optimize_route
from datetime import datetime, timedelta
import json

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/booking', methods=['GET', 'POST'])
def booking():
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
            appointment_time=appointment_time
        )
        db.session.add(new_appointment)
        db.session.commit()

        return redirect(url_for('index'))

    available_slots = TimeSlot.query.filter_by(is_available=True).all()
    return render_template('booking.html', available_slots=available_slots)

@app.route('/barber_view')
def barber_view():
    appointments = Appointment.query.order_by(Appointment.appointment_time).all()
    optimized_route = optimize_route(appointments)
    return render_template('barber_view.html', appointments=appointments, optimized_route=json.dumps(optimized_route))

@app.route('/get_available_slots')
def get_available_slots():
    available_slots = TimeSlot.query.filter_by(is_available=True).all()
    slots = [{'id': slot.id, 'start_time': slot.start_time.isoformat()} for slot in available_slots]
    return jsonify(slots)

@app.route('/book_slot', methods=['POST'])
def book_slot():
    slot_id = request.form['slot_id']
    slot = TimeSlot.query.get(slot_id)
    if slot and slot.is_available:
        slot.is_available = False
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

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

# Call initialize_time_slots when the app starts
with app.app_context():
    initialize_time_slots()
