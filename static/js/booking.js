document.addEventListener('DOMContentLoaded', function() {
    const addressInput = document.getElementById('address');
    const latitudeInput = document.getElementById('latitude');
    const longitudeInput = document.getElementById('longitude');
    const timeSlotsContainer = document.getElementById('time-slots');

    // Initialize Leaflet map centered on Boston
    const map = L.map('map').setView([42.3601, -71.0589], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    let marker;

    // Geocoding function
    function geocodeAddress() {
        const address = addressInput.value;
        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
            .then(response => response.json())
            .then(data => {
                if (data.length > 0) {
                    const lat = parseFloat(data[0].lat);
                    const lon = parseFloat(data[0].lon);
                    latitudeInput.value = lat;
                    longitudeInput.value = lon;

                    if (marker) {
                        map.removeLayer(marker);
                    }
                    marker = L.marker([lat, lon]).addTo(map);
                    map.setView([lat, lon], 13);
                }
            });
    }

    addressInput.addEventListener('blur', geocodeAddress);

    // Fetch and display available time slots
    fetch('/get_available_slots')
        .then(response => response.json())
        .then(slots => {
            slots.forEach(slot => {
                const button = document.createElement('button');
                button.textContent = new Date(slot.start_time).toLocaleString();
                button.classList.add('bg-blue-500', 'hover:bg-blue-700', 'text-white', 'font-bold', 'py-2', 'px-4', 'rounded', 'm-2');
                button.addEventListener('click', () => bookSlot(slot.id));
                timeSlotsContainer.appendChild(button);
            });
        });

    function bookSlot(slotId) {
        const formData = new FormData();
        formData.append('slot_id', slotId);

        fetch('/book_slot', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Slot booked successfully!');
                location.reload();
            } else {
                alert('Failed to book slot. Please try again.');
            }
        });
    }
});

function generateICalFile(appointment) {
    const icalContent = `BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:${new Date(appointment.appointment_time).toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'}
DTEND:${new Date(new Date(appointment.appointment_time).getTime() + 60*60*1000).toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'}
SUMMARY:Haircut Appointment
DESCRIPTION:Appointment with The Clippership
LOCATION:${appointment.address}
END:VEVENT
END:VCALENDAR`;

    const blob = new Blob([icalContent], { type: 'text/calendar;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'haircut_appointment.ics';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
