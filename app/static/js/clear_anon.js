async function clearAnonData() {
  if (!confirm("Do you really want to delete your data?")) return;

  try {
    const res = await fetch("/api/recipes/clear", {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });

    if (res.status === 204 || res.ok) {
      alert("Data cleared!.");
      document.cookie = "anon_id=; Max-Age=0; path=/; SameSite=Lax";
      window.location.href = "/";
    } else {
      const j = await res.json().catch(()=>null);
      alert("Cant delete data: " + (j?.detail || JSON.stringify(j) || res.status));
    }
  } catch (err) {
    console.error("clearAnonData error", err);
    alert("Cleaning error!.");
  }
}
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById("clear-data-btn");
  if (btn) btn.addEventListener("click", ev => { ev.preventDefault(); clearAnonData(); });
});
