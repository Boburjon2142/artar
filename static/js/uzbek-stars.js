// Simple star rating enhancer for the Detail page
document.addEventListener('DOMContentLoaded', () => {
  const groups = document.querySelectorAll('.uzbek-star-group');
  groups.forEach(group => {
    const selectId = group.getAttribute('data-target-select') || 'id_value';
    const select = document.getElementById(selectId);
    if (!select) return;
    const max = 5;
    const stars = [];
    group.innerHTML = '';
    for (let i = 1; i <= max; i++) {
      const s = document.createElement('span');
      s.className = 'star';
      s.textContent = '★';
      s.dataset.value = String(i);
      s.addEventListener('mouseenter', () => update(i, true));
      s.addEventListener('mouseleave', () => update(Number(select.value || 0), false));
      s.addEventListener('click', () => { select.value = String(i); update(i, false); });
      group.appendChild(s);
      stars.push(s);
    }
    const update = (val, hover) => {
      stars.forEach((s, idx) => {
        const on = idx < val;
        s.classList.toggle('active', on);
        s.classList.toggle('hover', hover && on);
      });
    };
    update(Number(select.value || 0), false);
  });
});

