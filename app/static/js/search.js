// app/static/js/search.js
// Safe, robust client-side search + rendering for What2Cook.
// Guards against missing DOM elements (e.g. recipe detail page).

(function debugElems() {
  const names = ["search-form","ingredients-input","results","spinner","alerts","clear-btn"];
  const found = {};
  for (const n of names) {
    found[n] = !!document.getElementById(n);
  }
  console.debug("search.js DOM presence:", found);
})();

const form = document.getElementById("search-form");
const input = document.getElementById("ingredients-input");
const resultsEl = document.getElementById("results");
const spinner = document.getElementById("spinner");
const alerts = document.getElementById("alerts");
const clearBtn = document.getElementById("clear-btn");

function showAlert(message, type = "danger", timeout = 4000) {
  if (!alerts) {
    console[type === "danger" ? "error" : "log"](message);
    return;
  }
  alerts.innerHTML = `<div class="alert alert-${type} alert-sm" role="alert">${message}</div>`;
  setTimeout(() => { if (alerts) alerts.innerHTML = ""; }, timeout);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/[&<>"']/g, function(m) {
    return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[m];
  });
}

function renderRecipeCard(r) {
  const imgSrc = r.thumbnail_url || r.image_url || '/static/img/placeholder.png';
  const ingList = r.ingredients ? r.ingredients.map(i => escapeHtml(i)).join(", ") : "";
  const scoreText = (typeof r.score === "number") ? `Score: ${(r.score*100).toFixed(0)}%` : "";

  return `
  <div class="col-12">
    <div class="card shadow-sm position-relative mb-3">
      <div class="row g-0">
        <div class="col-md-4">
          <a href="${escapeHtml(r.image_url || '#')}" target="_blank" rel="noopener">
            <img src="${escapeHtml(imgSrc)}"
                 alt="${escapeHtml(r.title)}"
                 loading="lazy"
                 decoding="async"
                 onerror="this.onerror=null;this.src='/static/img/placeholder.png';"
                 class="img-fluid rounded-start w-100"
                 style="height:180px; object-fit:cover;">
          </a>
        </div>
        <div class="col-md-8">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title mb-1">${escapeHtml(r.title)}</h5>
            <div class="text-muted small mb-2">${escapeHtml(scoreText)}</div>
            <p class="mb-2">${escapeHtml((r.instructions || "").slice(0, 160))}${(r.instructions && r.instructions.length > 160) ? '...' : ''}</p>
            <p class="mb-1"><strong>Ingredients:</strong> ${ingList}</p>

            <div class="mt-auto d-flex justify-content-between align-items-center">
              <a class="stretched-link" href="/recipes/${encodeURIComponent(r.id)}" aria-label="Open recipe details"></a>
            </div>

          </div>
        </div>
      </div>
    </div>
  </div>
  `;
}

function renderResults(list) {
  if (!resultsEl) return;
  if (!Array.isArray(list) || list.length === 0) {
    resultsEl.innerHTML = `<div class="col-12"><div class="alert alert-warning">No recipes found for your ingredients.</div></div>`;
    return;
  }
  resultsEl.innerHTML = list.map(r => renderRecipeCard(r)).join("\n");

  try {
    if (typeof initActionButtons === "function") initActionButtons(resultsEl);
    else if (typeof initLikeButtons === "function") initLikeButtons(resultsEl);
  } catch (err) {
    console.debug("initActionButtons/initLikeButtons failed:", err);
  }
}

function showSpinner(show = true) {
  if (!spinner) return;
  spinner.style.display = show ? "" : "none";
}

function parseInputToString(text) {
  if (!text) return "";
  const tokens = text.split(/[,\\n]+/).map(s => s.trim()).filter(Boolean);
  return tokens.join(", ");
}

async function performSearch(rawIngredients, limit = 50) {
  if (!rawIngredients || !rawIngredients.trim()) {
    showAlert("Please enter at least one ingredient", "warning");
    return;
  }
  showSpinner(true);
  const params = new URLSearchParams();
  params.set("ingredients", rawIngredients);
  params.set("limit", String(limit));

  try {
    const res = await fetch(`/api/recipes/search?${params.toString()}`, {
      method: "GET",
      credentials: "same-origin",
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });

    if (!res.ok) {
      if (res.status === 400) {
        const text = await res.text().catch(() => "");
        showAlert("Bad request: " + text, "warning");
      } else {
        showAlert("Search failed (server error).", "danger");
      }
      return;
    }

    const json = await res.json().catch(() => { showAlert("Failed to parse response", "danger"); return []; });
    renderResults(json);
  } catch (err) {
    console.error("performSearch error", err);
    showAlert("Network error while searching.", "danger");
  } finally {
    showSpinner(false);
  }
}

/* --- safe DOM wiring --- */

if (clearBtn) {
  clearBtn.addEventListener("click", () => {
    if (input) input.value = "";
    if (resultsEl) resultsEl.innerHTML = "";
  });
}

if (form) {
  form.addEventListener("submit", async (ev) => {

    if (ev.ctrlKey || ev.metaKey || ev.shiftKey) return;
    ev.preventDefault();
    const raw = input ? input.value || "" : "";
    const norm = parseInputToString(raw);
    if (!norm) {
      showAlert("Please enter at least one ingredient", "warning");
      return;
    }
    await performSearch(norm);
  });
}

if (input && input.value && input.value.trim().length > 0 && resultsEl) {
  setTimeout(() => {
    const raw = parseInputToString(input.value);
    if (raw) performSearch(raw);
  }, 120);
}
