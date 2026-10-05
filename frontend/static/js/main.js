async function loadHealth() {
  const status = document.getElementById("status");
  const counts = document.getElementById("counts");
  try {
    const data = await api("/api/health");
    status.textContent = "✅ Online";
    counts.textContent = ` (${data.counts.ngos} NGOs · ${data.counts.listings} listings)`;
  } catch (err) {
    status.textContent = "❌ Backend or database not reachable";
  }
}

loadHealth();
