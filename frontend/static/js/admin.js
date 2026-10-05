// Admin dashboard: verify organisations.

const adminUser = Auth.requireRole("admin");

const ORG_TYPES = { ngo: "NGO", shelter: "Shelter", community_kitchen: "Community kitchen" };

if (adminUser) {
  async function loadNgos() {
    const container = document.getElementById("ngos");
    try {
      const ngos = await api("/api/admin/ngos");
      container.innerHTML = `
        <table class="table">
          <thead><tr><th>Name</th><th>Type</th><th>Address</th><th>Capacity</th><th>Veg only</th><th>Status</th><th></th></tr></thead>
          <tbody>${ngos.map((n) => `
            <tr>
              <td>${escapeHtml(n.name)}<br><span class="small">${escapeHtml(n.phone)}</span></td>
              <td>${ORG_TYPES[n.type] || escapeHtml(n.type)}</td>
              <td class="small">${escapeHtml(n.address)}</td>
              <td>${n.capacity_meals}</td>
              <td>${n.veg_only ? "Yes" : "No"}</td>
              <td><span class="badge ${n.verified ? "badge-delivered" : "badge-matched"}">${n.verified ? "Verified" : "Pending"}</span></td>
              <td><button class="btn btn-small ${n.verified ? "btn-outline" : ""}" data-id="${n.id}" data-verified="${!n.verified}">
                ${n.verified ? "Revoke" : "Verify"}</button></td>
            </tr>`).join("")}
          </tbody>
        </table>`;
    } catch (err) {
      container.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
    }
  }

  document.getElementById("ngos").addEventListener("click", async (e) => {
    const { id, verified } = e.target.dataset;
    if (!id) return;
    try {
      await api(`/api/admin/ngos/${id}/verify`, { method: "POST", body: { verified: verified === "true" } });
    } catch (err) {
      alert(err.message);
    }
    loadNgos();
  });

  loadNgos();
}
