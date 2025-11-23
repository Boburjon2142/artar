console.log("SITE.JS YUKLANDI ✅");


// site.js – ARTAR umumiy frontend logikasi

document.addEventListener("DOMContentLoaded", () => {
  initRatingStars();
  initFilterAccordionAutoExpand();
  initNavbarSearchClear();
  initFilterFormClear();
  initNewsletterForm();
  initChartAnimations();
  initChartBadges();
  initFilterToggle();
});

/* ===================== ⭐ Reyting yulduzlari ===================== */

function initRatingStars() {
  const group = document.querySelector(".star-group");
  if (!group) return;

  const targetId =
    (group.dataset && group.dataset.targetSelect) || "id_value";
  const select = document.getElementById(targetId);
  if (!select) return;

  select.style.position = "absolute";
  select.style.left = "-9999px";

  const current = parseInt(select.value || "0", 10);

  for (let i = 1; i <= 5; i++) {
    const el = document.createElement("span");
    el.className = "star" + (i <= current ? " active" : "");
    el.innerHTML = "★";
    el.dataset.value = String(i);

    el.addEventListener("mouseenter", () => {
      Array.from(group.children).forEach((s) =>
        s.classList.toggle(
          "hover",
          parseInt(s.dataset.value || "0", 10) <= i
        )
      );
    });

    el.addEventListener("mouseleave", () => {
      Array.from(group.children).forEach((s) =>
        s.classList.remove("hover")
      );
    });

    el.addEventListener("click", () => {
      select.value = String(i);
      Array.from(group.children).forEach((s) =>
        s.classList.toggle(
          "active",
          parseInt(s.dataset.value || "0", 10) <= i
        )
      );
    });

    group.appendChild(el);
  }
}

/* ===================== 📂 Filter accordion auto-open ===================== */

function initFilterAccordionAutoExpand() {
  const collapseEl = document.getElementById("collapseOne");
  const accBtn = document.querySelector("#headingOne .accordion-button");
  const filterBox = document.getElementById("filterBox");

  if (!collapseEl) return;

  const form = collapseEl.querySelector("form");
  if (!form) return;

  const names = [
    "title",
    "category",
    "min_price",
    "max_price",
    "rating_gte",
    "order_by",
  ];

  let hasValue = false;
  for (const n of names) {
    const el = form.elements[n];
    if (el && el.value && String(el.value).trim() !== "") {
      hasValue = true;
      break;
    }
  }

  if (!hasValue) return;

  // Filter ishlatilgan bo‘lsa – panelni avtomatik ochamiz
  try {
    if (typeof bootstrap !== "undefined" && bootstrap.Collapse) {
      const c = new bootstrap.Collapse(collapseEl, { toggle: false });
      c.show();
    } else {
      collapseEl.classList.add("show");
    }
  } catch (e) {
    // noop
  }

  if (accBtn) {
    accBtn.classList.remove("collapsed");
    accBtn.setAttribute("aria-expanded", "true");
  }

  // Filter ishlatilgan bo‘lsa, blokni ham ko‘rsatamiz
  if (filterBox) {
    filterBox.classList.remove("d-none");
  }
}

/* ===================== 🔍 Navbar qidiruvini tozalash ===================== */

function initNavbarSearchClear() {
  const navSearch = document.getElementById("navSearch");
  if (!navSearch) return;

  try {
    const params = new URLSearchParams(window.location.search);
    if (params.has("title")) {
      navSearch.value = "";
    }
  } catch (e) {
    // noop
  }
}

/* ===================== 🧹 Filter form qiymatlarini tozalash ===================== */

function initFilterFormClear() {
  try {
    const filterForm = document.querySelector("#collapseOne form");
    if (!filterForm) return;

    const params = new URLSearchParams(window.location.search);
    const names = [
      "title",
      "category",
      "min_price",
      "max_price",
      "rating_gte",
      "order_by",
    ];

    const hasAny = names.some((n) => params.has(n) && params.get(n));

    if (!hasAny) return;

    if (filterForm.elements["title"]) {
      filterForm.elements["title"].value = "";
    }

    ["category", "rating_gte", "order_by"].forEach((n) => {
      const el = filterForm.elements[n];
      if (el) el.value = "";
    });

    ["min_price", "max_price"].forEach((n) => {
      const el = filterForm.elements[n];
      if (el) el.value = "";
    });
  } catch (e) {
    // noop
  }
}

/* ===================== ✉ Newsletter ===================== */

function initNewsletterForm() {
  try {
    const emailInput = document.getElementById("newsletterEmail");
    const form = document.getElementById("newsletterForm");

    if (emailInput) emailInput.value = "";

    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        if (emailInput) emailInput.value = "";
        alert("Obuna saqlandi!");
      });
    }
  } catch (e) {
    // noop
  }
}

/* ===================== 📊 Grafik animatsiyasi ===================== */

function initChartAnimations() {
  const bars = document.querySelectorAll(".chart-bar");
  if (!bars.length) return;

  Array.from(bars).forEach((bar) => {
    const h = bar.style.height || "0%";
    bar.style.height = "0%";
    setTimeout(() => {
      bar.style.transition = "height 1.2s ease";
      bar.style.height = h;
    }, 200);
  });
}

/* ===================== 📊 Grafikdagi badge va caption ===================== */

function initChartBadges() {
  try {
    const charts = document.querySelectorAll(".stats-section .chart");
    if (!charts.length) return;

    Array.from(charts).forEach((chart) => {
      const caption = chart.parentElement.querySelector(".chart-caption");
      const bars = chart.querySelectorAll(".chart-bar");

      Array.from(bars).forEach((bar) => {
        bar.addEventListener("click", () => {
          const label = bar.dataset.label || "";

          if (caption) caption.textContent = label;

          let badge = bar.querySelector(".chart-badge");
          if (!badge) {
            badge = document.createElement("div");
            badge.className = "chart-badge";
            bar.appendChild(badge);
          }

          badge.textContent = label;
          bar.classList.add("show-badge");

          clearTimeout(bar._badgeTimer);
          bar._badgeTimer = setTimeout(() => {
            bar.classList.remove("show-badge");
          }, 1600);
        });
      });
    });
  } catch (e) {
    // noop
  }
}

/* ===================== 🧰 FILTER PANEL TOGGLE (Navbar tugmasi) ===================== */

function initFilterToggle() {
  const filterBtn = document.getElementById("filterToggleBtn");
  const filterBox = document.getElementById("filterBox");
  const collapseEl = document.getElementById("collapseOne");

  if (!filterBtn || !filterBox) return;

  filterBtn.addEventListener("click", () => {
    const willShow = filterBox.classList.contains("d-none");

    filterBox.classList.toggle("d-none");

    // Birinchi marta ko‘rinayotganda accordionni ham ochamiz
    if (willShow && collapseEl) {
      try {
        if (typeof bootstrap !== "undefined" && bootstrap.Collapse) {
          const c = new bootstrap.Collapse(collapseEl, { toggle: false });
          c.show();
        } else {
          collapseEl.classList.add("show");
        }
      } catch (e) {
        // noop
      }
    }
  });
}
