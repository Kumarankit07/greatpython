// NeuroCare AI — main.js

document.addEventListener('DOMContentLoaded', () => {

  // ── THEME TOGGLE ───────────────────────────────────────────────────
  const root   = document.documentElement;
  const toggle = document.getElementById('themeToggle');
  const saved  = localStorage.getItem('ncTheme') || 'dark';
  applyTheme(saved);

  if (toggle) {
    toggle.addEventListener('click', () => {
      const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem('ncTheme', next);
    });
  }

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    if (toggle) toggle.textContent = theme === 'dark' ? '☀️ Light' : '🌙 Dark';
  }

  // ── FIX: Reset submit buttons on page load / back-button ───────────
  window.addEventListener('pageshow', (event) => {
    document.querySelectorAll('button[type="submit"]').forEach(btn => {
      btn.disabled = false;
      if (btn.dataset.originalText) {
        btn.innerHTML = btn.dataset.originalText;
      }
    });
  });

  // Intercept ALL forms to show loading state
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function () {
      const btn = form.querySelector('button[type="submit"]');
      if (!btn) return;
      if (!btn.dataset.originalText) btn.dataset.originalText = btn.innerHTML;
      btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;margin:0;border-width:2px;display:inline-block;vertical-align:middle;"></div> Please wait…';
      btn.disabled = true;
    });
  });

  // ── AUTO-DISMISS FLASH ALERTS ──────────────────────────────────────
  document.querySelectorAll('.alert').forEach(a => {
    setTimeout(() => {
      a.style.transition = 'opacity .5s ease, transform .5s ease';
      a.style.opacity    = '0';
      a.style.transform  = 'translateX(20px)';
      setTimeout(() => a.remove(), 500);
    }, 5000);
  });

  // ── SCROLL ANIMATIONS ──────────────────────────────────────────────
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.opacity   = '1';
        e.target.style.transform = 'translateY(0)';
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.animate-fade-up').forEach(el => {
    el.style.opacity   = '0';
    el.style.transform = 'translateY(22px)';
    el.style.transition = 'opacity .6s ease, transform .6s ease';
    observer.observe(el);
  });

  // ── PROGRESS BAR ANIMATE ───────────────────────────────────────────
  document.querySelectorAll('.progress-bar').forEach(bar => {
    const w = bar.style.width;
    bar.style.width = '0%';
    setTimeout(() => { bar.style.width = w; }, 400);
  });

  // ── CARD HOVER ─────────────────────────────────────────────────────
  document.querySelectorAll('.stat-card, .disease-info-card').forEach(c => {
    c.addEventListener('mouseenter', () => c.style.transform = 'translateY(-3px)');
    c.addEventListener('mouseleave', () => c.style.transform = 'translateY(0)');
  });

});
