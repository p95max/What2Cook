// app/static/js/search.js
// Safe, robust client-side search + rendering for What2Cook.
// - Guards against missing DOM elements (e.g. on recipe detail page).
// - Uses GET /api/recipes/search?ingredients=... to fetch JSON results.
// - Renders simple cards and supports lazy image fallback.
//
// Note: actions.js handles like/bookmark buttons. This file only renders cards.

const form = document.getElementById("search-form");
const input = document.getElementById("ingredients-input");
const resultsEl = document.getElementById("results");
const spinner = document.getElementById("spinner");
const alerts = document.getElementById("alerts");
const clearBtn = document.getElementById("clear-btn");

// Show a short alert message in page (non-blocking)
function showAlert(message, type = "danger", timeout = 4000) {
  if (!alerts) {
    // console fallback if no alert container present
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

// Render single recipe card (keeps markup compact)
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
              <div class="ms-2">
                <button type="button" class="btn btn-sm btn-outline-primary like-btn" data-like="${escapeHtml(r.id)}" aria-pressed="false" title="Like / Unlike">
                  ❤️ <span class="visually-hidden">Like</span>
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  </div>
  `;
}

// Render list of recipes into resultsEl. If empty -> friendly message.
function renderResults(list) {
  if (!resultsEl) return;
  if (!Array.isArray(list) || list.length === 0) {
    resultsEl.innerHTML = `<div class="col-12"><div class="alert alert-warning">No recipes found for your ingredients.</div></div>`;
    return;
  }

  const html = list.map(r => renderRecipeCard(r)).join("\n");
  resultsEl.innerHTML = html;

  // If actions.js is present and exports initLikeButtons global, try to initialize like buttons
  try {
    if (typeof initLikeButtons === "function") {
      initLikeButtons(resultsEl);
    }
  } catch (err) {
    // silent - actions.js may not be loaded on the page
    console.debug("initLikeButtons not available or failed:", err);
  }
}

function showSpinner(show = true) {
  if (!spinner) return;
  spinner.style.display = show ? "" : "none";
}

// Perform AJAX search via API endpoint.
// rawIngredients: raw string from textarea (commas/newlines separated)
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

    let json = [];
    try {
      json = await res.json();
    } catch (err) {
      showAlert("Failed to parse server response.", "danger");
      console.error("JSON parse error", err);
      return;
    }

    renderResults(json);
  } catch (err) {
    if (err.name === "AbortError") {
      showAlert("Search timeout, please try again.", "warning");
    } else {
      console.error("performSearch error", err);
      showAlert("Network error while searching.", "danger");
    }
  } finally {
    showSpinner(false);
  }
}

// Utility to parse textarea into normalized comma-separated string (keeps original formatting for query)
function parseInputToString(text) {
  if (!text) return "";
  const tokens = text.split(/[,\\n]+/).map(s => s.trim()).filter(Boolean);
  return tokens.join(", ");
}

// --- Safeguarded DOM wiring ---
// clear button
if (clearBtn) {
  clearBtn.addEventListener("click", () => {
    if (input) input.value = "";
    if (resultsEl) resultsEl.innerHTML = "";
  });
}

// If the site uses server-rendered GET form (action="/search"), we still support JS-enhanced POST-like handling
if (form) {
  // If form.method == "post" (legacy), intercept submit and use AJAX
  if ((form.method || "").toLowerCase() === "post") {
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const raw = input ? input.value || "" : "";
      const norm = parseInputToString(raw);
      if (!norm) {
        showAlert("Please enter at least one ingredient", "warning");
        return;
      }
      await performSearch(norm);
    });
  } else {
    // If form uses GET (standard), we can optionally intercept and do client-side search instead of full page reload
    form.addEventListener("submit", async (ev) => {
      // If user pressed Ctrl/Cmd to open in new tab or form is used as navigation, let default happen.
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
}

// Auto-run: if page has a prefilled query (server-side GET), perform search automatically
(function autoRunPrefilled() {
  try {
    if (input && input.value && input.value.trim().length > 0) {
      // perform small delay so page can finish loading other scripts (like actions.js)
      setTimeout(() => {
        const raw = parseInputToString(input.value);
        if (raw) performSearch(raw);
      }, 150);
    }
  } catch (err) {
    // ignore
    console.debug("autoRunPrefilled error", err);
  }
})();
