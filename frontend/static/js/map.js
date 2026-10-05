// Leaflet location picker: click / drag a marker, or use browser geolocation.

const LUCKNOW = [26.8467, 80.9462];

function createLocationPicker(elementId, latInput, lngInput) {
  const map = L.map(elementId).setView(LUCKNOW, 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  let marker = null;

  function set(lat, lng) {
    latInput.value = lat.toFixed(6);
    lngInput.value = lng.toFixed(6);
    if (marker) {
      marker.setLatLng([lat, lng]);
    } else {
      marker = L.marker([lat, lng], { draggable: true }).addTo(map);
      marker.on("dragend", () => {
        const p = marker.getLatLng();
        set(p.lat, p.lng);
      });
    }
  }

  map.on("click", (e) => set(e.latlng.lat, e.latlng.lng));

  function locate() {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported – click on the map instead.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        set(pos.coords.latitude, pos.coords.longitude);
        map.setView([pos.coords.latitude, pos.coords.longitude], 15);
      },
      () => alert("Could not get your location – click on the map instead."),
    );
  }

  return { map, set, locate, hasLocation: () => Boolean(latInput.value && lngInput.value) };
}
