document.addEventListener('DOMContentLoaded', function() {
    const addressInput = document.getElementById('address');
    const latitudeInput = document.getElementById('latitude');
    const longitudeInput = document.getElementById('longitude');
    const timeSlotsContainer = document.getElementById('time-slots');

    // Initialize Leaflet map
    const map = L.map('map').setView([0, 0], 2);
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
