let map;
let barberMarker;

document.addEventListener('DOMContentLoaded', function() {
    map = L.map('map').setView([0, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    const optimizedRoute = JSON.parse(document.getElementById('optimized-route').textContent);

    if (optimizedRoute.length > 0) {
        const bounds = L.latLngBounds(optimizedRoute.map(point => [point.lat, point.lng]));
        map.fitBounds(bounds);

        const polyline = L.polyline(optimizedRoute.map(point => [point.lat, point.lng]), {color: 'red'}).addTo(map);

        optimizedRoute.forEach((point, index) => {
            L.marker([point.lat, point.lng])
                .addTo(map)
                .bindPopup(`Stop ${index + 1}: ${point.client_name}<br>Address: ${point.address}<br>Time: ${new Date(point.appointment_time).toLocaleString()}`);
        });
    }
});

function updateBarberLocation(latitude, longitude) {
    if (!barberMarker) {
        barberMarker = L.marker([latitude, longitude], {
            icon: L.icon({
                iconUrl: '/static/images/barber-icon.png',
                iconSize: [32, 32],
                iconAnchor: [16, 32],
                popupAnchor: [0, -32]
            })
        }).addTo(map);
    } else {
        barberMarker.setLatLng([latitude, longitude]);
    }
    
    map.setView([latitude, longitude], 15);
    barberMarker.bindPopup("Barber's current location").openPopup();
}
