const form = document.getElementById("search-form");
const input = document.getElementById("ingredients-input");
const resultsEl = document.getElementById("results");
const spinner = document.getElementById("spinner");
const alerts = document.getElementById("alerts");
const clearBtn = document.getElementById("clear-btn");

function showAlert(message, type = "danger") {
  alerts.innerHTML = `<div class="alert alert-${type} alert-sm" role="alert">${message}</div>`;
  setTimeout(() => { alerts.innerHTML = ""; }, 4000);
}

function parseInput(text) {
  return text
    .split(/[,\\n]/)
    .map(s => s.trim())
    .filter(s => s.length > 0);
}

function renderRecipeCard(r) {
  const missingList = r.missing.map(i => `<span class="badge bg-danger me-1">${i}</span>`).join(" ");
  const haveList = r.have.map(i => `<span class="badge bg-success me-1">${i}</span>`).join(" ");
  const ingList = r.ingredients.join(", ");

  return `
  <div class="col-12">
    <div class="card">
      <div class="card-body">
        <div class="d-flex align-items-start">
          <div class="flex-grow-1">
            <h5 class="card-title mb-1">${escapeHtml(r.title)}</h5>
            <div class="text-muted small mb-2">Score: ${(r.score*100).toFixed(0)}% — have ${r.match_count}/${r.ingredients.length}</div>
            <p class="mb-1"><strong>Ingredients:</strong> ${escapeHtml(ingList)}</p>
            <p class="mb-1"><strong>Have:</strong> ${haveList || '<span class="text-muted">none</span>'}</p>
            <p class="mb-1"><strong>Missing:</strong> ${missingList || '<span class="text-muted">none</span>'}</p>
          </div>
          <div class="ms-3 text-end">
            <button class="btn btn-outline-primary btn-sm" onclick="copyIngredients(${JSON.stringify(r.ingredients)})">Copy ingredients</button>
          </div>
        </div>
      </div>
    </div>
  </div>
  `;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/[&<>"']/g, function(m) {
    return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[m];
  });
}

function copyIngredients(arr) {
  const text = arr.join(", ");
  navigator.clipboard?.writeText(text).then(() => {
    showAlert("Ingredients copied to clipboard", "success");
  }).catch(() => {
    showAlert("Could not copy to clipboard", "warning");
  });
}

clearBtn.addEventListener("click", () => {
  input.value = "";
  resultsEl.innerHTML = "";
});

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const raw = input.value || "";
  const ingredients = parseInput(raw);
  if (ingredients.length === 0) {
    showAlert("Please enter at least one ingredient", "warning");
    return;
  }

  spinner.style.display = "";
  resultsEl.innerHTML = "";
  try {
    const resp = await fetch("/api/recipes/search", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({ ingredients, limit: 50 })
    });
    if (!resp.ok) {
      const txt = await resp.text();
      showAlert(`Server error: ${resp.status} ${txt}`);
      return;
    }
    const data = await resp.json();
    if (!Array.isArray(data) || data.length === 0) {
      resultsEl.innerHTML = `<div class="col-12"><div class="alert alert-info">No matching recipes found.</div></div>`;
    } else {
      resultsEl.innerHTML = data.map(renderRecipeCard).join("");
    }
  } catch (e) {
    showAlert("Network error: " + (e.message || e), "danger");
  } finally {
    spinner.style.display = "none";
  }
});
