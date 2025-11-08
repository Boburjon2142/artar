// Apply Uzbek design classes automatically on common elements
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('input.form-control, select.form-select, textarea.form-control').forEach(el => {
    el.classList.add('uzbek-input');
  });
  document.querySelectorAll('button[type="submit"], .btn-primary').forEach(btn => {
    btn.classList.add('btn-gradient');
  });
  document.querySelectorAll('.card').forEach(card => {
    card.classList.add('uzbek-card');
  });

  // Footer cleanup: remove Admin line and columns titled 'Havolalar' or 'Yangiliklar'
  const footer = document.querySelector('footer');
  if (footer) {
    // Remove a standalone line that starts with "Admin:" (e.g., email line)
    footer.querySelectorAll('*').forEach(node => {
      if (node.childElementCount === 0) {
        const text = (node.textContent || '').trim();
        if (/^admin\s*[:：]/i.test(text)) {
          node.remove();
        }
      }
    });

    // Remove sections that have headings Havolalar or Yangiliklar
    const removeHeadingCols = ['havolalar', 'yangiliklar'];
    footer.querySelectorAll('h1,h2,h3,h4,h5,h6,strong').forEach(h => {
      const txt = (h.textContent || '').trim().toLowerCase();
      if (removeHeadingCols.includes(txt)) {
        const col = h.closest('[class*="col-"]') || h.closest('.col') || h.parentElement;
        if (col) col.remove();
      }
    });
  }
});
