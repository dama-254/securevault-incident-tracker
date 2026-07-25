const API = "";

// ---------- Helpers ----------
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
  return {
    Critical: "badge-critical",
    High: "badge-high",
    Medium: "badge-medium",
    Low: "badge-low",
  }[sev] || "badge-low";
}

function statusClass(status) {
  return {
    Open: "status-open",
    "In Progress": "status-in-progress",
    Resolved: "status-resolved",
  }[status] || "";
}

// ---------- LOGIN PAGE ----------
if (document.getElementById("authForm")) {
  let mode = "login"; // or "register"

  const form = document.getElementById("authForm");
  const toggleLink = document.getElementById("toggleLink");
  const formTitle = document.getElementById("formTitle");
  const formSubtitle = document.getElementById("formSubtitle");
  const submitBtn = document.getElementById("submitBtn");
  const toggleText = document.getElementById("toggleText");
  const errorMsg = document.getElementById("errorMsg");

  toggleLink.addEventListener("click", () => {
    mode = mode === "login" ? "register" : "login";
    if (mode === "register") {
      formTitle.textContent = "Create an account";
      formSubtitle.textContent = "Register to start tracking security incidents";
      submitBtn.textContent = "Register";
      toggleText.innerHTML = 'Already have an account? <span id="toggleLink">Log In</span>';
    } else {
      formTitle.textContent = "Welcome back";
      formSubtitle.textContent = "Sign in to log and track security incidents";
      submitBtn.textContent = "Log In";
      toggleText.innerHTML = 'Don\'t have an account? <span id="toggleLink">Register</span>';
    }
    document.getElementById("toggleLink").addEventListener("click", () => toggleLink.click());
    errorMsg.textContent = "";
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorMsg.textContent = "";
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    try {
      await api(`/${mode}`, { method: "POST", body: JSON.stringify({ username, password }) });
      if (mode === "register") {
        await api("/login", { method: "POST", body: JSON.stringify({ username, password }) });
      }
      window.location.href = "/dashboard";
    } catch (err) {
      errorMsg.textContent = err.message;
    }
  });
}

// ---------- DASHBOARD PAGE ----------
if (document.getElementById("incidentsTableBody")) {
  let categories = [];
  let charts = {};

  async function init() {
    try {
      const me = await api("/me");
      document.getElementById("userLabel").textContent = me.username + " ▾";
    } catch {
      window.location.href = "/login";
      return;
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
    categories.forEach((c) => {
      filterCat.innerHTML += `<option value="${c.id}">${c.name}</option>`;
      incCat.innerHTML += `<option value="${c.id}">${c.name}</option>`;
    });
  }

  function setupTabs() {
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-section").forEach((s) => s.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById(btn.dataset.tab).classList.add("active");
        if (btn.dataset.tab === "analyticsTab") loadStats(true);
      });
    });
  }

  function setupFilters() {
    ["filterSeverity", "filterStatus", "filterCategory"].forEach((id) => {
      document.getElementById(id).addEventListener("change", loadIncidents);
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

    const incidents = await api("/incidents?" + params.toString());
    renderTable(incidents);
  }

  function renderTable(incidents) {
    const tbody = document.getElementById("incidentsTableBody");
    tbody.innerHTML = incidents.map((i) => `
      <tr>
        <td>${i.title}</td>
        <td>${i.category || "-"}</td>
        <td><span class="badge ${severityBadgeClass(i.severity)}">${i.severity}</span></td>
        <td class="${statusClass(i.status)}">${i.status}</td>
        <td>${new Date(i.date_reported).toLocaleDateString()}</td>
        <td class="row-actions">
          <button class="btn btn-outline" onclick="cycleStatus(${i.id}, '${i.status}')">Advance</button>
          <button class="btn btn-danger" onclick="deleteIncident(${i.id})">Delete</button>
        </td>
      </tr>
    `).join("");
  }

  window.cycleStatus = async (id, current) => {
    const next = { Open: "In Progress", "In Progress": "Resolved", Resolved: "Open" }[current];
    await api(`/incidents/${id}`, { method: "PATCH", body: JSON.stringify({ status: next }) });
    await loadIncidents();
    await loadStats();
  };

  window.deleteIncident = async (id) => {
    if (!confirm("Delete this incident?")) return;
    await api(`/incidents/${id}`, { method: "DELETE" });
    await loadIncidents();
    await loadStats();
  };

  function setupIncidentForm() {
    document.getElementById("incidentForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorEl = document.getElementById("incidentError");
      errorEl.textContent = "";

      const payload = {
        title: document.getElementById("incTitle").value.trim(),
        description: document.getElementById("incDescription").value.trim(),
        category_id: parseInt(document.getElementById("incCategory").value),
        severity: document.getElementById("incSeverity").value,
        affected_systems: [],
      };

      const sysName = document.getElementById("incSystemName").value.trim();
      const dept = document.getElementById("incDepartment").value.trim();
      if (sysName) payload.affected_systems.push({ system_name: sysName, department: dept });

      try {
        await api("/incidents", { method: "POST", body: JSON.stringify(payload) });
        e.target.reset();
        document.querySelector('[data-tab="dashboardTab"]').click();
        await loadIncidents();
        await loadStats();
      } catch (err) {
        errorEl.textContent = err.message;
      }
    });
  }

  async function loadStats(renderCharts = false) {
    const stats = await api("/incidents/stats");

    const statCounts = { Open: 0, "In Progress": 0, Resolved: 0 };
    stats.by_status.forEach((s) => (statCounts[s.status] = s.count));

    document.getElementById("statsGrid").innerHTML = `
      <div class="stat-card"><div class="value" style="color:var(--red)">${statCounts.Open}</div><div class="label">Open Incidents</div></div>
      <div class="stat-card"><div class="value" style="color:var(--orange)">${statCounts["In Progress"]}</div><div class="label">In Progress</div></div>
      <div class="stat-card"><div class="value" style="color:var(--green)">${statCounts.Resolved}</div><div class="label">Resolved</div></div>
      <div class="stat-card"><div class="value" style="color:var(--teal)">${stats.total_incidents}</div><div class="label">Total Incidents</div></div>
    `;

    if (renderCharts) renderAllCharts(stats);
  }

  function renderAllCharts(stats) {
    Object.values(charts).forEach((c) => c.destroy());

    charts.category = new Chart(document.getElementById("categoryChart"), {
      type: "doughnut",
      data: {
        labels: stats.by_category.map((c) => c.category),
        datasets: [{ data: stats.by_category.map((c) => c.count), backgroundColor: ["#00B4D8", "#0891B2", "#F59E0B", "#13294B", "#DC2626"] }],
      },
    });

    charts.severity = new Chart(document.getElementById("severityChart"), {
      type: "bar",
      data: {
        labels: stats.by_severity.map((s) => s.severity),
        datasets: [{ data: stats.by_severity.map((s) => s.count), backgroundColor: "#DC2626" }],
      },
      options: { plugins: { legend: { display: false } } },
    });

    charts.status = new Chart(document.getElementById("statusChart"), {
      type: "bar",
      data: {
        labels: stats.by_status.map((s) => s.status),
        datasets: [{ data: stats.by_status.map((s) => s.count), backgroundColor: "#00B4D8" }],
      },
      options: { indexAxis: "y", plugins: { legend: { display: false } } },
    });
  }

  init();
}
