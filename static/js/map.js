document.addEventListener('DOMContentLoaded', function() {
    const map = L.map('map').setView([0, 0], 2);
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
