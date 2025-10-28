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
  const imgSrc = r.thumbnail_url || r.image_url || '/static/img/placeholder.png';
  const ingList = r.ingredients ? r.ingredients.map(i => escapeHtml(i)).join(", ") : "";
  const scoreText = (typeof r.score === "number") ? `Score: ${(r.score*100).toFixed(0)}%` : "";

  return `
  <div class="col-12">
    <div class="card shadow-sm position-relative"> 
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
          <div class="card-body">
            <h5 class="card-title mb-1">${escapeHtml(r.title)}</h5>
            <div class="text-muted small mb-2">${escapeHtml(scoreText)}</div>
            <p class="mb-2">${escapeHtml((r.instructions || "").slice(0, 160))}${(r.instructions && r.instructions.length > 160) ? '...' : ''}</p>
            <p class="mb-1"><strong>Ingredients:</strong> ${ingList}</p>

            <a class="stretched-link" href="/recipes/${encodeURIComponent(r.id)}" aria-label="Open recipe details"></a>
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

clearBtn.addEventListener("click", () => {
  input.value = "";
  resultsEl.innerHTML = "";
});

if ((form.method || "").toLowerCase() === "post") {
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const raw = input.value || "";
    const ingredients = parseInput(raw);
    if (ingredients.length === 0) {
      showAlert("Please enter at least one ingredient", "warning");
      return;
    }
    await performSearch(raw);
  });
}

