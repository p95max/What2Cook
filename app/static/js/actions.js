// Handles like and bookmark UI and calls to API

function setBtnState(btn, active) {
  if (!btn) return;
  btn.classList.toggle('active', !!active);
  btn.setAttribute('aria-pressed', active ? 'true' : 'false');
}

function updateLikesCountOnPage(recipeId, count) {
  try {
    const el = document.getElementById(`likes-count-${recipeId}`);
    if (el) el.textContent = String(count);
  } catch (e) {
    console.warn('updateLikesCountOnPage', e);
  }
}

async function toggleLike(recipeId, btnEl) {
  if (!btnEl || btnEl.dataset.inflight === '1') return;
  btnEl.dataset.inflight = '1';
  btnEl.setAttribute('aria-busy', 'true');

  try {
    const res = await fetch(`/api/recipes/${encodeURIComponent(recipeId)}/like`, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    if (!res.ok) {
      console.warn('Like request failed', res.status);
      return;
    }
    const j = await res.json();
    setBtnState(btnEl, j.status === 'liked');
    if (typeof j.likes_count !== 'undefined') updateLikesCountOnPage(recipeId, j.likes_count);
  } catch (err) {
    console.error('toggleLike error', err);
  } finally {
    delete btnEl.dataset.inflight;
    btnEl.removeAttribute('aria-busy');
  }
}

async function toggleBookmark(recipeId, btnEl) {
  if (!btnEl || btnEl.dataset.inflight === '1') return;
  btnEl.dataset.inflight = '1';
  btnEl.setAttribute('aria-busy', 'true');

  try {
    const res = await fetch(`/api/recipes/${encodeURIComponent(recipeId)}/bookmark`, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    if (!res.ok) {
      console.warn('Bookmark request failed', res.status);
      return;
    }
    const j = await res.json();
    if (j.status === 'bookmarked') setBtnState(btnEl, true);
    else setBtnState(btnEl, false);
  } catch (err) {
    console.error('toggleBookmark error', err);
  } finally {
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

async function initActionButtons(scope = document) {
  const likeButtons = Array.from(scope.querySelectorAll('[data-like]'));
  const bookmarkButtons = Array.from(scope.querySelectorAll('[data-bookmark]'));
  const recipeIds = new Set([...likeButtons.map(b => b.getAttribute('data-like')), ...bookmarkButtons.map(b => b.getAttribute('data-bookmark'))]);

  for (const id of recipeIds) {
    if (!id) continue;
    const state = await fetchActionState(id);
    if (state) {

      likeButtons.filter(b => b.getAttribute('data-like') === id).forEach(b => setBtnState(b, !!state.liked));
      bookmarkButtons.filter(b => b.getAttribute('data-bookmark') === id).forEach(b => setBtnState(b, !!state.bookmarked));
      if (typeof state.likes_count !== 'undefined') updateLikesCountOnPage(id, state.likes_count);
    }
  }

  for (const b of likeButtons) {
    const id = b.getAttribute('data-like');
    if (!id) continue;
    b.addEventListener('click', (ev) => { ev.preventDefault(); toggleLike(id, b); });
  }
  for (const b of bookmarkButtons) {
    const id = b.getAttribute('data-bookmark');
    if (!id) continue;
    b.addEventListener('click', (ev) => { ev.preventDefault(); toggleBookmark(id, b); });
  }
}

// auto init on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  try { initActionButtons(); } catch (e) { console.debug('initActionButtons', e); }
});
