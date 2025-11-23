// Client-side pagination for cards on Home
document.addEventListener('DOMContentLoaded', () => {
  const grid = document.getElementById('cardsGrid');
  if (!grid) return;
  const items = Array.from(grid.querySelectorAll('.card-item'));
  const prev = document.getElementById('prevPage');
  const next = document.getElementById('nextPage');
  const indicator = document.getElementById('pageIndicator');
  const pageSizeEl = document.getElementById('pageSize');
  const pageSize = pageSizeEl ? parseInt(pageSizeEl.value, 10) || 12 : 12;

  if (!items.length) {
    if (prev) prev.style.display = 'none';
    if (next) next.style.display = 'none';
    if (indicator) indicator.textContent = '';
    return;
  }

  // Read current page from query param if present
  const params = new URLSearchParams(window.location.search);
  let page = parseInt(params.get('page') || '1', 10);
  if (isNaN(page) || page < 1) page = 1;

  const totalPages = Math.max(1, Math.ceil(items.length / pageSize));

  const show = (p) => {
    page = Math.min(Math.max(1, p), totalPages);
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    items.forEach((el, idx) => {
      el.style.display = idx >= start && idx < end ? '' : 'none';
    });
    if (indicator) indicator.textContent = `Sahifa ${page} / ${totalPages}`;
    if (prev) prev.disabled = page <= 1;
    if (next) next.disabled = page >= totalPages;

    // Update URL without reload
    const u = new URL(window.location.href);
    u.searchParams.set('page', page);
    window.history.replaceState({}, '', u);
  };

  if (prev) prev.addEventListener('click', () => show(page - 1));
  if (next) next.addEventListener('click', () => show(page + 1));

  show(page);
});

