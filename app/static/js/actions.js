function setBtnState(btn, liked) {
  if (!btn) return;
  btn.classList.toggle('active', !!liked);
  btn.setAttribute('aria-pressed', liked ? 'true' : 'false');
}

async function toggleLike(recipeId, btnEl) {
  if (!btnEl || btnEl.dataset.inflight === '1') return;
  btnEl.dataset.inflight = '1';
  btnEl.setAttribute('aria-busy', 'true');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);

  try {
    const res = await fetch(`/api/recipes/${encodeURIComponent(recipeId)}/like`, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      signal: controller.signal,
    });

    if (!res.ok) {
      console.warn('Like request failed', res.status);
      return;
    }

    let j = null;
    try { j = await res.json(); } catch (err) { console.warn('Invalid JSON', err); return; }

    if (j && j.status === 'liked') setBtnState(btnEl, true); else setBtnState(btnEl, false);
  } catch (err) {
    if (err.name === 'AbortError') console.warn('Like request aborted (timeout)');
    else console.error('toggleLike error', err);
  } finally {
    clearTimeout(timeout);
    delete btnEl.dataset.inflight;
    btnEl.removeAttribute('aria-busy');
  }
}

async function fetchActionState(recipeId) {
  try {
    const res = await fetch(`/api/recipes/${encodeURIComponent(recipeId)}/actions`, {
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn('fetchActionState error', err);
    return null;
  }
}

async function initLikeButtons(scope = document) {
  const buttons = Array.from(scope.querySelectorAll('[data-like]'));
  if (buttons.length === 0) return;
  for (const btn of buttons) {
    const id = btn.getAttribute('data-like');
    if (!id) continue;
    const state = await fetchActionState(id);
    if (state && state.liked) setBtnState(btn, true);
    btn.addEventListener('click', (ev) => { ev.preventDefault(); toggleLike(id, btn); });
  }
}

document.addEventListener('DOMContentLoaded', () => initLikeButtons());
