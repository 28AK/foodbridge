// Login and registration pages.

function afterLogin(data) {
  Auth.save(data.access_token, data.user);
  location.href = Auth.dashboardFor(data.user.role);
}

const loginForm = document.getElementById("login-form");
if (loginForm) {
  const error = document.getElementById("error");
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError(error, "");
    try {
      // OAuth2 password flow expects form-encoded username/password
      const body = new URLSearchParams(new FormData(loginForm));
      afterLogin(await api("/api/auth/login", { method: "POST", body }));
    } catch (err) {
      showError(error, err.message);
    }
  });
}

const registerForm = document.getElementById("register-form");
if (registerForm) {
  const error = document.getElementById("error");
  const donorFields = document.getElementById("donor-fields");
  const ngoFields = document.getElementById("ngo-fields");
  const picker = createLocationPicker("map", registerForm.lat, registerForm.lng);
  document.getElementById("locate-btn").addEventListener("click", picker.locate);

  function currentRole() {
    return registerForm.querySelector("input[name=role]:checked").value;
  }

  function updateRole() {
    const isNgo = currentRole() === "ngo";
    ngoFields.hidden = !isNgo;
    donorFields.hidden = isNgo;
    ngoFields.querySelectorAll("input[name=capacity_meals], input[name=address]")
      .forEach((input) => { input.required = isNgo; });
    document.querySelectorAll("[data-label-for]").forEach((el) => {
      el.hidden = el.dataset.labelFor !== currentRole();
    });
    // Leaflet needs a size refresh after its container becomes visible
    if (isNgo) setTimeout(() => picker.map.invalidateSize(), 0);
  }

  registerForm.querySelectorAll("input[name=role]").forEach((r) => r.addEventListener("change", updateRole));
  updateRole();

  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError(error, "");
    const f = registerForm;
    const role = currentRole();
    const body = {
      name: f.elements.name.value, // f.name would be the form's own name attribute
      email: f.email.value,
      phone: f.phone.value,
      password: f.password.value,
      role,
    };
    if (role === "donor") {
      body.donor_type = f.donor_type.value;
    } else {
      if (!picker.hasLocation()) {
        showError(error, "Please mark your organisation's location on the map.");
        return;
      }
      Object.assign(body, {
        org_type: f.org_type.value,
        capacity_meals: Number(f.capacity_meals.value),
        veg_only: f.veg_only.checked,
        address: f.address.value,
        lat: Number(f.lat.value),
        lng: Number(f.lng.value),
      });
    }
    try {
      afterLogin(await api("/api/auth/register", { method: "POST", body }));
    } catch (err) {
      showError(error, err.message);
    }
  });
}
