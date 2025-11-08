document.addEventListener('DOMContentLoaded', function(){
  // Enhance rating select into stars if present
  const group = document.querySelector('.star-group');
  const select = document.getElementById((group && group.dataset && group.dataset.targetSelect) ? group.dataset.targetSelect : 'id_value');
  if(group && select){
    select.style.position = 'absolute';
    select.style.left = '-9999px';
    const current = parseInt(select.value || '0', 10);
    for(let i=1;i<=5;i++){
      const el = document.createElement('span');
      el.className = 'star' + (i <= current ? ' active' : '');
      el.innerHTML = '★';
      el.dataset.value = String(i);
      el.addEventListener('mouseenter',()=>{
        Array.from(group.children).forEach(s=>s.classList.toggle('hover', parseInt(s.dataset.value,10)<=i));
      });
      el.addEventListener('mouseleave',()=>{
        Array.from(group.children).forEach(s=>s.classList.remove('hover'));
      });
      el.addEventListener('click',()=>{
        select.value = String(i);
        Array.from(group.children).forEach(s=>s.classList.toggle('active', parseInt(s.dataset.value,10)<=i));
      });
      group.appendChild(el);
    }
  }

  // Auto-expand filter accordion if any filter value present
  const collapseEl = document.getElementById('collapseOne');
  const accBtn = document.querySelector('#headingOne .accordion-button');
  if (collapseEl) {
    const form = collapseEl.querySelector('form');
    if (form) {
      const names = ['title','category','min_price','max_price','rating_gte','order_by'];
      let hasValue = false;
      for (const n of names) {
        const el = form.elements[n];
        if (el && el.value && String(el.value).trim() !== '') { hasValue = true; break; }
      }
      if (hasValue) {
        try {
          if (typeof bootstrap !== 'undefined' && bootstrap.Collapse) {
            const c = new bootstrap.Collapse(collapseEl, { toggle: false });
            c.show();
          } else {
            collapseEl.classList.add('show');
          }
          if (accBtn) { accBtn.classList.remove('collapsed'); accBtn.setAttribute('aria-expanded','true'); }
        } catch(e) { /* noop */ }
      }
    }
  }

  // Clear navbar search input after search (do not repopulate on reload)
  const navSearch = document.getElementById('navSearch');
  if (navSearch) {
    try {
      const params = new URLSearchParams(window.location.search);
      if (params.has('title')) {
        navSearch.value = '';
      }
    } catch (e) { /* noop */ }
  }

  // Clear filter form inputs after search
  try {
    const filterForm = document.querySelector('#collapseOne form');
    if (filterForm) {
      const params = new URLSearchParams(window.location.search);
      const names = ['title','category','min_price','max_price','rating_gte','order_by'];
      const hasAny = names.some(n => params.has(n) && params.get(n));
      if (hasAny) {
        if (filterForm.elements['title']) filterForm.elements['title'].value = '';
        ['category','rating_gte','order_by'].forEach(n => { const el = filterForm.elements[n]; if (el) el.value = ''; });
        ['min_price','max_price'].forEach(n => { const el = filterForm.elements[n]; if (el) el.value = ''; });
      }
    }
  } catch (e) { /* noop */ }

  // Newsletter: clear on load and on submit
  try {
    const emailInput = document.getElementById('newsletterEmail');
    const form = document.getElementById('newsletterForm');
    if (emailInput) emailInput.value = '';
    if (form) {
      form.addEventListener('submit', function(e){
        e.preventDefault();
        if (emailInput) emailInput.value = '';
        alert('Obuna saqlandi!');
      });
    }
  } catch(e) { /* noop */ }

  // Animate chart bars on load
  Array.from(document.querySelectorAll('.chart-bar')).forEach(function(bar){
    const h = bar.style.height; bar.style.height = '0%';
    setTimeout(()=>{ bar.style.transition='height 1.2s ease'; bar.style.height = h; }, 200);
  });

  // Chart caption shows label on click
  try {
    Array.from(document.querySelectorAll('.stats-section .chart')).forEach(function(chart){
      const caption = chart.parentElement.querySelector('.chart-caption');
      Array.from(chart.querySelectorAll('.chart-bar')).forEach(function(bar){
        bar.addEventListener('click', function(){
          const label = bar.dataset.label || '';
          if (caption) caption.textContent = label;
          // floating badge above the bar
          let badge = bar.querySelector('.chart-badge');
          if (!badge) {
            badge = document.createElement('div');
            badge.className = 'chart-badge';
            bar.appendChild(badge);
          }
          badge.textContent = label;
          bar.classList.add('show-badge');
          clearTimeout(bar._badgeTimer);
          bar._badgeTimer = setTimeout(()=>{ bar.classList.remove('show-badge'); }, 1600);
        });
      });
    });
  } catch(e) { /* noop */ }
});
