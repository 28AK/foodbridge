// Donor dashboard: AI photo check, create listings, list my donations.

// Card summarising what the AI found + the spoilage risk.
function aiSummaryHtml({ ai, ai_error: aiError, freshness, warnings }) {
  let html = "";
  if (ai) {
    const others = ai.top_predictions.slice(1).map((p) => escapeHtml(p.name)).join(", ");
    const spoiledPct = Math.round(ai.freshness.spoiled_probability * 100);
    html += `
      <div class="ai-grid">
        <div><span class="small">Detected food</span>
          <b>${escapeHtml(ai.dish.name)}</b> <span class="small">${Math.round(ai.dish.confidence * 100)}%</span>
          <div class="small">${escapeHtml(ai.category.name)}${others ? ` · or: ${others}` : ""}</div></div>
        <div><span class="small">Looks</span>
          <b>${spoiledPct >= 50 ? "⚠️ Spoiled" : "✅ Fresh"}</b>
          <div class="small">${spoiledPct}% spoilage signal</div></div>
        <div><span class="small">Quantity in photo</span>
          <b>${escapeHtml(ai.quantity_estimate.label)}</b>
          <div class="small">~${ai.quantity_estimate.min_servings}–${ai.quantity_estimate.max_servings} servings</div></div>
      </div>`;
  } else if (aiError) {
    html += `<p class="small">⚠️ ${escapeHtml(aiError)}</p>`;
  }
  if (freshness) {
    html += `
      <div class="risk-row">
        <div><span class="small">Spoilage risk</span> ${riskBadge(freshness)}</div>
        <div class="meter"><div class="meter-fill risk-bg-${freshness.risk_level}" style="width:${freshness.risk_score}%"></div></div>
        <div class="small">${freshness.safe_to_donate
          ? `Pick up by <b>${formatDateTime(freshness.pickup_deadline)}</b> (within ${formatHours(freshness.remaining_hours)})`
          : "<b>Not safe to donate</b>"}</div>
      </div>
      <ul class="small reasons">${freshness.reasons.map((r) => `<li>${escapeHtml(r)}</li>`).join("")}</ul>`;
  }
  if (warnings && warnings.length) {
    html += `<ul class="warnings">${warnings.map((w) => `<li>⚠️ ${escapeHtml(w)}</li>`).join("")}</ul>`;
  }
  return html;
}

const donor = Auth.requireRole("donor");

if (donor) {
  const form = document.getElementById("listing-form");
  const error = document.getElementById("error");
  const submitBtn = document.getElementById("submit-btn");
  const preview = document.getElementById("photo-preview");
  const aiPreview = document.getElementById("ai-preview");
  const picker = createLocationPicker("map", form.lat, form.lng);
  document.getElementById("locate-btn").addEventListener("click", picker.locate);
  let analyzeRun = 0;

  // Default "prepared at" to now, in local time
  function resetPreparedAt() {
    const now = new Date();
    form.prepared_at.value = new Date(now - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  }
  resetPreparedAt();

  async function analyzePhoto() {
    const file = form.photo.files[0];
    if (!file) {
      aiPreview.hidden = true;
      return;
    }
    const run = ++analyzeRun;
    aiPreview.hidden = false;
    aiPreview.innerHTML = `<p class="small">🧠 Analysing photo…</p>`;
    const body = new FormData();
    body.append("photo", file);
    body.append("prepared_at", form.prepared_at.value);
    body.append("food_category", form.food_category.value);
    if (form.quantity_servings.value) body.append("quantity_servings", form.quantity_servings.value);
    try {
      const result = await api("/api/listings/analyze", { method: "POST", body });
      if (run !== analyzeRun) return; // a newer photo was chosen meanwhile
      aiPreview.innerHTML = `<h3>🧠 AI check</h3>${aiSummaryHtml(result)}`;
      if (result.ai && !form.food_name.value) form.food_name.value = result.ai.dish.name;
    } catch (err) {
      if (run !== analyzeRun) return;
      aiPreview.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
    }
  }

  form.photo.addEventListener("change", () => {
    const file = form.photo.files[0];
    if (preview.src) URL.revokeObjectURL(preview.src);
    preview.hidden = !file;
    if (file) preview.src = URL.createObjectURL(file);
    analyzePhoto();
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError(error, "");
    if (!picker.hasLocation()) {
      showError(error, "Please mark the pickup location on the map.");
      return;
    }
    submitBtn.disabled = true;
    submitBtn.textContent = "Uploading & analysing…";
    try {
      const listing = await api("/api/listings", { method: "POST", body: new FormData(form) });
      showResult(listing);
      form.reset();
      preview.hidden = true;
      aiPreview.hidden = true;
      resetPreparedAt();
      loadListings();
    } catch (err) {
      showError(error, err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit listing";
    }
  });

  function showResult(listing) {
    document.getElementById("result-title").textContent = {
      rejected: "❌ Not accepted – food is not safe to donate",
      matched: `✅ Matched with ${listing.match?.ngo_name} (${listing.match?.distance_km} km away)`,
    }[listing.status] || "✅ Listed – looking for a nearby NGO";
    document.getElementById("result-ai").innerHTML = aiSummaryHtml(listing);

    const r = listing.preprocessing;
    document.getElementById("img-original").src = listing.images.original;
    document.getElementById("img-processed").src = listing.images.processed;
    document.getElementById("img-model").src = listing.images.model_input;
    const rows = [
      ["Original size", `${r.original_size[0]} × ${r.original_size[1]}`],
      ["Brightness", `${r.before.brightness} → ${r.after.brightness}`],
      ["Contrast", `${r.before.contrast} → ${r.after.contrast}`],
      ["Sharpness", r.before.sharpness],
      ["Enhancement steps", r.steps.length ? r.steps.join(", ") : "None needed (good quality photo)"],
    ];
    document.getElementById("report").innerHTML = rows
      .map(([k, v]) => `<tr><th>${k}</th><td>${escapeHtml(v)}</td></tr>`)
      .join("");
    const result = document.getElementById("result");
    result.hidden = false;
    result.scrollIntoView({ behavior: "smooth" });
  }

  async function loadListings() {
    const container = document.getElementById("listings");
    try {
      const listings = await api("/api/listings/mine");
      if (!listings.length) {
        container.innerHTML = `<p class="small">No listings yet. Your donations will appear here.</p>`;
        return;
      }
      container.innerHTML = `
        <table class="table">
          <thead><tr><th></th><th>Food</th><th>Servings</th><th>Risk</th><th>Pick up by</th><th>Status</th></tr></thead>
          <tbody>${listings.map((l) => `
            <tr>
              <td><img class="thumb" src="${escapeHtml(l.images.processed)}" alt=""></td>
              <td>${escapeHtml(l.food_name)}<br><span class="small">${l.food_category === "veg" ? "🟢 Veg" : "🔴 Non-veg"}${l.ai ? ` · AI: ${escapeHtml(l.ai.dish.name)}` : ""}</span></td>
              <td>${l.quantity_servings}</td>
              <td>${riskBadge(l.freshness)}</td>
              <td class="small">${l.status === "rejected" ? "—" : formatDateTime(l.pickup_deadline)}</td>
              <td><span class="badge badge-${l.status}">${STATUS_LABELS[l.status] || l.status}</span>
                ${l.match ? `<div class="small">→ ${escapeHtml(l.match.ngo_name)} (${l.match.distance_km} km)${l.match.accepted_at ? " ✓" : ""}</div>` : ""}
                ${l.status === "listed" ? `<div class="small">Looking for a nearby NGO…</div>` : ""}
                ${["listed", "matched"].includes(l.status) ? `<button class="btn-link small" data-cancel="${l.id}">Cancel</button>` : ""}</td>
            </tr>`).join("")}
          </tbody>
        </table>`;
    } catch (err) {
      container.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
    }
  }

  document.getElementById("listings").addEventListener("click", async (e) => {
    const id = e.target.dataset.cancel;
    if (!id || !confirm("Cancel this donation?")) return;
    try {
      await api(`/api/listings/${id}/cancel`, { method: "POST" });
    } catch (err) {
      alert(err.message);
    }
    loadListings();
  });

  loadListings();
  setInterval(loadListings, 30000); // pick up status changes from NGOs
}
