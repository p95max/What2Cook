// Adds copy-to-clipboard behaviour to elements with [data-copy-link].
// Fallback for older browsers uses a temporary textarea.

function fallbackCopyTextToClipboard(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.style.position = "fixed";
  textArea.style.top = "-1000px";
  textArea.style.left = "-1000px";
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  let success = false;
  try {
    success = document.execCommand('copy');
  } catch (err) {
    console.warn('fallback copy failed', err);
    success = false;
  }
  document.body.removeChild(textArea);
  return success;
}

async function copyTextToClipboard(text) {
  if (!text) return false;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.warn('navigator.clipboard.writeText failed', err);
      return fallbackCopyTextToClipboard(text);
    }
  } else {
    return fallbackCopyTextToClipboard(text);
  }
}

function attachCopyHandlers(scope = document) {
  const buttons = Array.from(scope.querySelectorAll('[data-copy-link]'));
  for (const btn of buttons) {
    if (btn.__copyAttached) continue;
    btn.__copyAttached = true;

    btn.addEventListener('click', async (ev) => {
      ev.preventDefault();
      const link = btn.getAttribute('data-copy-link') || window.location.href;
      if (!link) return;

      btn.setAttribute('aria-busy', 'true');
      const origHtml = btn.innerHTML;
      const origLabel = btn.getAttribute('aria-label');

      const showCopied = () => {
        btn.innerHTML = '<i class="bi bi-clipboard-check"></i> Copied';
        btn.classList.add('active');
        btn.setAttribute('aria-label', 'Link copied to clipboard');
        setTimeout(() => {
          btn.innerHTML = origHtml;
          if (origLabel) btn.setAttribute('aria-label', origLabel);
          btn.classList.remove('active');
        }, 1800);
      };

      const ok = await copyTextToClipboard(link);
      if (ok) {
        showCopied();
      } else {
        if (navigator.share) {
          try {
            await navigator.share({ url: link });
          } catch (e) {
            console.debug('navigator.share canceled or failed', e);
            alert('Could not copy link automatically. URL: ' + link);
          }
        } else {
          alert('Could not copy automatically. Here is the link:\n\n' + link);
        }
      }
      btn.removeAttribute('aria-busy');
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  try { attachCopyHandlers(); } catch(e){ console.debug('attachCopyHandlers', e); }
});

window.what2cook_attachCopyHandlers = attachCopyHandlers;
