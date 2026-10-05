// NGO dashboard: today's capacity, incoming matches, pickup lifecycle and route map.

const ngoUser = Auth.requireRole("ngo");

if (ngoUser) {
  const map = L.map("map").setView([26.8467, 80.9462], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
  const layer = L.layerGroup().addTo(map);

  const pin = (html, cls) => L.divIcon({ html, className: `pin ${cls}`, iconSize: [28, 28], iconAnchor: [14, 14] });

  function matchCard(l, actions) {
    const accepted = Boolean(l.match?.accepted_at);
    return `
      <div class="match-card">
        <img class="thumb-lg" src="${escapeHtml(l.images.processed)}" alt="">
        <div class="match-body">
          <div><b>${escapeHtml(l.food_name)}</b> · ${l.quantity_servings} servings
            <span class="small">${l.food_category === "veg" ? "🟢 Veg" : "🔴 Non-veg"}</span>
            ${riskBadge(l.freshness)}</div>
          <div class="small">Pick up by <b>${formatDateTime(l.pickup_deadline)}</b> (${timeLeft(l.pickup_deadline)})
            · ${l.match.distance_km} km · ~${l.match.eta_minutes} min</div>
          <div class="small">${escapeHtml(l.donor_name)} · ${escapeHtml(l.address)}
            ${accepted ? ` · 📞 <a href="tel:${escapeHtml(l.donor_phone)}">${escapeHtml(l.donor_phone)}</a>` : ""}</div>
          ${l.pickup_notes ? `<div class="small">📝 ${escapeHtml(l.pickup_notes)}</div>` : ""}
          <div class="small" title="distance ${l.match.breakdown.distance} · capacity ${l.match.breakdown.capacity} · demand ${l.match.breakdown.demand} · time ${l.match.breakdown.time}">
            Match score <b>${l.match.score}</b>/100${l.ai ? ` · AI: ${escapeHtml(l.ai.dish.name)}` : ""}</div>
          <div class="match-actions">${actions}</div>
        </div>
      </div>`;
  }

  const button = (action, id, label, cls = "btn btn-small") =>
    `<button class="${cls}" data-action="${action}" data-id="${id}">${label}</button>`;

  function renderList(elId, items, actionsFor, empty) {
    document.getElementById(elId).innerHTML = items.length
      ? items.map((l) => matchCard(l, actionsFor(l))).join("")
      : `<p class="small">${empty}</p>`;
  }

  function renderProfile(ngo) {
    document.getElementById("ngo-name").textContent = ngo.name;
    document.getElementById("unverified").hidden = ngo.verified;
    const t = ngo.today;
    document.getElementById("stat-received").textContent = `${t.received_servings} meals`;
    document.getElementById("stat-capacity").textContent = `of ${ngo.capacity_meals} capacity · ${t.free_capacity} free`;
    document.getElementById("capacity-meter").style.width = `${Math.min(100, (t.received_servings / ngo.capacity_meals) * 100)}%`;
    document.getElementById("stat-unmet").textContent = `${t.unmet_demand} meals`;
    const input = document.querySelector("#demand-form input");
    if (document.activeElement !== input) input.value = ngo.current_demand;
  }

  function renderMap(ngo, active, route) {
    layer.clearLayers();
    const [lng, lat] = ngo.location.coordinates;
    const points = [[lat, lng]];
    L.marker([lat, lng], { icon: pin("🏠", "pin-home") }).bindPopup(`<b>${escapeHtml(ngo.name)}</b>`).addTo(layer);

    const order = Object.fromEntries(route.stops.map((s) => [s.id, s.order]));
    for (const l of active) {
      const [plng, plat] = l.location.coordinates;
      points.push([plat, plng]);
      const label = order[l.id] ?? (l.status === "picked_up" ? "✓" : "•");
      const cls = order[l.id] ? "pin-stop" : l.status === "picked_up" ? "pin-done" : "pin-new";
      L.marker([plat, plng], { icon: pin(label, cls) })
        .bindPopup(`<b>${escapeHtml(l.food_name)}</b><br>${l.quantity_servings} servings · ${escapeHtml(l.donor_name)}`)
        .addTo(layer);
    }
    if (route.stops.length) {
      const path = [[route.origin.lat, route.origin.lng], ...route.stops.map((s) => [s.lat, s.lng]),
        [route.origin.lat, route.origin.lng]];
      L.polyline(path, { color: "#2e7d32", weight: 4, opacity: 0.8, dashArray: "8 6" }).addTo(layer);
    }
    if (points.length > 1) map.fitBounds(points, { padding: [40, 40], maxZoom: 15 });
    else map.setView(points[0], 13);

    document.getElementById("route-summary").innerHTML = route.stops.length
      ? `<p>Suggested order: ${route.stops.map((s) => `<b>${s.order}.</b> ${escapeHtml(s.food_name)} (by ${formatDateTime(s.eta)}${s.on_time ? "" : " ⚠️ late"})`).join(" → ")} → back to kitchen</p>
         <p>Total ≈ <b>${route.total_km} km</b> · finish ≈ ${formatDateTime(route.estimated_finish)}
         ${route.all_on_time ? "" : " · ⚠️ some pickups may miss their deadline"}</p>
         <a class="btn btn-small" target="_blank" rel="noopener" href="${escapeHtml(route.maps_url)}">Open route in Google Maps</a>`
      : "Accept matches to get a suggested pickup route.";
  }

  async function load() {
    try {
      const [ngo, active, history, route] = await Promise.all([
        api("/api/ngo/me"),
        api("/api/ngo/matches?scope=active"),
        api("/api/ngo/matches?scope=history"),
        api("/api/ngo/route"),
      ]);
      renderProfile(ngo);

      const fresh = active.filter((l) => l.status === "matched" && !l.match.accepted_at);
      const toCollect = active.filter((l) => l.status === "matched" && l.match.accepted_at);
      const inTransit = active.filter((l) => l.status === "picked_up");
      const order = Object.fromEntries(route.stops.map((s) => [s.id, s.order]));
      toCollect.sort((a, b) => (order[a.id] ?? 99) - (order[b.id] ?? 99));

      renderList("new-matches", fresh,
        (l) => button("accept", l.id, "Accept") + button("decline", l.id, "Decline", "btn btn-small btn-outline"),
        "No new matches right now.");
      renderList("to-collect", toCollect,
        (l) => `<span class="small">Stop ${order[l.id] ?? "–"}</span> ` + button("picked-up", l.id, "Mark picked up"),
        "Nothing to collect.");
      renderList("in-transit", inTransit, (l) => button("delivered", l.id, "Mark delivered"), "Nothing in transit.");
      renderList("history", history.slice(-10).reverse(), () => "", "No deliveries yet.");

      document.getElementById("stat-pickups").textContent = `${active.length} active`;
      document.getElementById("stat-pickups-detail").textContent =
        `${fresh.length} new · ${toCollect.length} to collect · ${inTransit.length} in transit · ${history.length} delivered`;
      renderMap(ngo, active, route);
    } catch (err) {
      document.getElementById("new-matches").innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
    }
  }

  document.addEventListener("click", async (e) => {
    const { action, id } = e.target.dataset;
    if (!action || !id) return;
    if (action === "decline" && !confirm("Decline this donation? It will be offered to another NGO.")) return;
    e.target.disabled = true;
    try {
      await api(`/api/ngo/matches/${id}/${action}`, { method: "POST" });
    } catch (err) {
      alert(err.message);
    }
    load();
  });

  document.getElementById("demand-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const value = Number(e.target.current_demand.value);
    try {
      renderProfile(await api("/api/ngo/me", { method: "PATCH", body: { current_demand: value } }));
    } catch (err) {
      alert(err.message);
    }
  });

  load();
  setInterval(load, 30000); // live updates arrive via WebSockets in the next step
}
