const API = "";

async function api(path, options = {}) {
  const res = await fetch(API + path, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "request failed" }));
    throw new Error(err.error || "request failed");
  }

  return res.status === 204 ? null : res.json();
}

function severityBadgeClass(sev) {
  return { Critical: "badge-critical", High: "badge-high", Medium: "badge-medium", Low: "badge-low" }[sev] || "badge-low";
}

function statusClass(status) {
  return { Open: "status-open", "In Progress": "status-in-progress", Resolved: "status-resolved" }[status] || "";
}

if (document.getElementById("authForm")) {
  let mode = "login";
  const form = document.getElementById("authForm");
  const toggleLink = document.getElementById("toggleLink");
  const formTitle = document.getElementById("formTitle");
  const formSubtitle = document.getElementById("formSubtitle");
  const submitBtn = document.getElementById("submitBtn");
  const toggleText = document.getElementById("toggleText");
  const errorMsg = document.getElementById("errorMsg");

  function syncAuthMode() {
    const isRegister = mode === "register";
    formTitle.textContent = isRegister ? "Create an account" : "Welcome back";
    formSubtitle.textContent = isRegister
      ? "Register to start tracking security incidents"
      : "Sign in to log and track security incidents";
    submitBtn.textContent = isRegister ? "Register" : "Log In";
    toggleText.innerHTML = isRegister
      ? "Already have an account? <span id=\"toggleLink\">Log In</span>"
      : "Don't have an account? <span id=\"toggleLink\">Register</span>";
    errorMsg.textContent = "";

    const newToggleLink = document.getElementById("toggleLink");
    if (newToggleLink) {
      newToggleLink.addEventListener("click", () => {
        mode = mode === "login" ? "register" : "login";
        syncAuthMode();
      });
    }
  }

  toggleLink.addEventListener("click", () => {
    mode = mode === "login" ? "register" : "login";
    syncAuthMode();
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorMsg.textContent = "";

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    try {
      await api("/" + mode, { method: "POST", body: JSON.stringify({ username, password }) });
      if (mode === "register") {
        await api("/login", { method: "POST", body: JSON.stringify({ username, password }) });
      }
      window.location.href = "/dashboard";
    } catch (err) {
      errorMsg.textContent = err.message;
    }
  });
}

if (document.getElementById("incidentsTableBody")) {
  let categories = [];
  let charts = {};
  let currentPage = 1;
  const perPage = 10;

  async function initDashboard() {
    try {
      const me = await api("/me");
      const userLabel = document.getElementById("userLabel");
      if (userLabel) userLabel.textContent = me.username + " ▾";
    } catch {
      window.location.href = "/login";
      return;
    }

    const userLabel = document.getElementById("userLabel");
    if (userLabel) {
      userLabel.addEventListener("click", async () => {
        if (confirm("Log out?")) {
          await api("/logout", { method: "POST" });
          window.location.href = "/login";
        }
      });
    }

    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", async () => {
        if (confirm("Are you sure you want to logout?")) {
          await api("/logout", { method: "POST" });
          window.location.href = "/login";
        }
      });
    }

    categories = await api("/categories");
    populateCategorySelects();
    await loadStats();
    await loadIncidents();
    setupTabs();
    setupFilters();
    setupIncidentForm();
  }

  function populateCategorySelects() {
    const filterCat = document.getElementById("filterCategory");
    const incCat = document.getElementById("incCategory");
    filterCat.innerHTML = "<option value=\"\">Category: All</option>";
    incCat.innerHTML = "";

    categories.forEach((c) => {
      filterCat.innerHTML += "<option value=\"" + c.id + "\">" + c.name + "</option>";
      incCat.innerHTML += "<option value=\"" + c.id + "\">" + c.name + "</option>";
    });
  }

  function setupTabs() {
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-section").forEach((s) => s.classList.remove("active"));
        btn.classList.add("active");
        const tab = document.getElementById(btn.dataset.tab);
        if (tab) tab.classList.add("active");
        if (btn.dataset.tab === "analyticsTab") loadStats(true);
      });
    });
  }

  function setupFilters() {
    ["filterSeverity", "filterStatus", "filterCategory"].forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener("change", () => {
        currentPage = 1;
        loadIncidents();
      });
    });
  }

  async function loadIncidents() {
    const severity = document.getElementById("filterSeverity").value;
    const status = document.getElementById("filterStatus").value;
    const category_id = document.getElementById("filterCategory").value;

    const params = new URLSearchParams();
    if (severity) params.set("severity", severity);
    if (status) params.set("status", status);
    if (category_id) params.set("category_id", category_id);
    params.set("page", currentPage);
    params.set("per_page", perPage);

    try {
      const data = await api("/incidents?" + params.toString());
      const incidents = Array.isArray(data) ? data : (data.incidents || []);
      const total = Array.isArray(data) ? incidents.length : (data.total || 0);
      const pages = Array.isArray(data) ? 1 : (data.pages || 1);
      renderTable(incidents);
      renderPagination(total, pages);
    } catch (err) {
      console.error("Failed to load incidents:", err);
    }
  }

  function renderTable(incidents) {
    const tbody = document.getElementById("incidentsTableBody");
    if (incidents.length === 0) {
      tbody.innerHTML = "<tr><td colspan='6' style='text-align:center;color:#888;padding:30px;'>No incidents found. Log your first incident.</td></tr>";
      return;
    }

    tbody.innerHTML = incidents.map((i) => (
      "<tr>" +
      "<td><a href='/incident/" + i.id + "' style='color:var(--teal);font-weight:600;'>" + i.title + "</a></td>" +
      "<td>" + (i.category || "-") + "</td>" +
      "<td><span class='badge " + severityBadgeClass(i.severity) + "'>" + i.severity + "</span></td>" +
      "<td class='" + statusClass(i.status) + "'>" + i.status + "</td>" +
      "<td>" + new Date(i.date_reported).toLocaleDateString() + "</td>" +
      "<td class='row-actions'><button class='btn btn-outline' onclick=\"cycleStatus(" + i.id + ", '" + i.status + "')\">Advance</button> <button class='btn btn-danger' onclick=\"deleteIncident(" + i.id + ")\">Delete</button></td>" +
      "</tr>"
    )).join("");
  }

  function renderPagination(total, pages) {
    let el = document.getElementById("pagination");
    if (!el) {
      el = document.createElement("div");
      el.id = "pagination";
      el.style.cssText = "display:flex;gap:8px;margin-top:12px;align-items:center;";
      const card = document.querySelector(".card");
      if (card) card.appendChild(el);
    }

    if (!el || pages <= 1) {
      if (el) el.innerHTML = "";
      return;
    }

    let html = "<span style='font-size:12px;color:#888;'>Page " + currentPage + " of " + pages + "</span>";
    if (currentPage > 1) html += "<button class='btn btn-outline' onclick=\"changePage(" + (currentPage - 1) + ")\">Prev</button>";
    if (currentPage < pages) html += "<button class='btn btn-outline' onclick=\"changePage(" + (currentPage + 1) + ")\">Next</button>";
    el.innerHTML = html;
  }

  window.changePage = (page) => {
    currentPage = page;
    loadIncidents();
  };

  window.cycleStatus = async (id, current) => {
    const next = { Open: "In Progress", "In Progress": "Resolved", Resolved: "Open" }[current];
    try {
      await api("/incidents/" + id, { method: "PATCH", body: JSON.stringify({ status: next }) });
      await loadIncidents();
      await loadStats();
    } catch (err) {
      alert("Failed to update: " + err.message);
    }
  };

  window.deleteIncident = async (id) => {
    if (!confirm("Delete this incident? This cannot be undone.")) return;
    try {
      await api("/incidents/" + id, { method: "DELETE" });
      await loadIncidents();
      await loadStats();
    } catch (err) {
      alert("Failed to delete: " + err.message);
    }
  };

  function setupIncidentForm() {
    const form = document.getElementById("incidentForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorEl = document.getElementById("incidentError");
      errorEl.textContent = "";

      const title = document.getElementById("incTitle").value.trim();
      const description = document.getElementById("incDescription").value.trim();
      const category_id = parseInt(document.getElementById("incCategory").value, 10);
      const severity = document.getElementById("incSeverity").value;
      const sysName = document.getElementById("incSystemName").value.trim();
      const dept = document.getElementById("incDepartment").value.trim();

      if (!title || !description || !category_id) {
        errorEl.textContent = "Please fill in all required fields.";
        return;
      }

      const payload = {
        title,
        description,
        category_id,
        severity,
        affected_systems: sysName ? [{ system_name: sysName, department: dept }] : [],
      };

      try {
        await api("/incidents", { method: "POST", body: JSON.stringify(payload) });
        form.reset();
        const dashboardTab = document.querySelector("[data-tab='dashboardTab']");
        if (dashboardTab) dashboardTab.click();
        await loadIncidents();
        await loadStats();
        alert("Incident logged successfully!");
      } catch (err) {
        errorEl.textContent = err.message;
      }
    });
  }

  async function loadStats(renderCharts = false) {
    try {
      const stats = await api("/incidents/stats");
      const statCounts = { Open: 0, "In Progress": 0, Resolved: 0 };
      stats.by_status.forEach((s) => (statCounts[s.status] = s.count));

      const statsGrid = document.getElementById("statsGrid");
      if (statsGrid) {
        statsGrid.innerHTML =
          "<div class='stat-card'><div class='value' style='color:var(--red);'>" + statCounts.Open + "</div><div class='label'>Open Incidents</div></div>" +
          "<div class='stat-card'><div class='value' style='color:var(--orange);'>" + statCounts["In Progress"] + "</div><div class='label'>In Progress</div></div>" +
          "<div class='stat-card'><div class='value' style='color:var(--green);'>" + statCounts.Resolved + "</div><div class='label'>Resolved</div></div>" +
          "<div class='stat-card'><div class='value' style='color:var(--teal);'>" + stats.total_incidents + "</div><div class='label'>Total Incidents</div></div>";
      }

      if (renderCharts) renderAllCharts(stats);
    } catch (err) {
      console.error("Failed to load stats:", err);
    }
  }

  function renderAllCharts(stats) {
    Object.values(charts).forEach((c) => c.destroy());
    charts = {};

    const catCanvas = document.getElementById("categoryChart");
    const sevCanvas = document.getElementById("severityChart");
    const statCanvas = document.getElementById("statusChart");

    if (catCanvas && stats.by_category.length > 0) {
      charts.category = new Chart(catCanvas, {
        type: "doughnut",
        data: {
          labels: stats.by_category.map((c) => c.category),
          datasets: [{ data: stats.by_category.map((c) => c.count), backgroundColor: ["#00B4D8", "#0891B2", "#F59E0B", "#DC2626", "#16A34A", "#7C3AED"] }],
        },
        options: { plugins: { legend: { position: "bottom" } } },
      });
    }

    if (sevCanvas && stats.by_severity.length > 0) {
      charts.severity = new Chart(sevCanvas, {
        type: "bar",
        data: {
          labels: stats.by_severity.map((s) => s.severity),
          datasets: [{ label: "Count", data: stats.by_severity.map((s) => s.count), backgroundColor: ["#DC2626", "#F59E0B", "#CA8A04", "#16A34A"] }],
        },
        options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } },
      });
    }

    if (statCanvas && stats.by_status.length > 0) {
      charts.status = new Chart(statCanvas, {
        type: "bar",
        data: {
          labels: stats.by_status.map((s) => s.status),
          datasets: [{ label: "Count", data: stats.by_status.map((s) => s.count), backgroundColor: "#00B4D8" }],
        },
        options: { indexAxis: "y", plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } } } },
      });
    }
  }

  initDashboard();
}
