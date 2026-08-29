(function () {
  const key = 'studentsPortal-theme';
  const root = document.documentElement;
  const saved = localStorage.getItem(key);
  const preferredDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initialTheme = saved || (preferredDark ? 'dark' : 'light');

  root.dataset.theme = initialTheme;

  document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
    button.addEventListener('click', () => {
      const nextTheme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      root.dataset.theme = nextTheme;
      localStorage.setItem(key, nextTheme);
    });
  });

  // Mobile sidebar drawer: opens on hamburger click, closes on backdrop
  // click or when a nav link is chosen.
  const body = document.body;
  document.querySelectorAll('[data-sidebar-toggle]').forEach((button) => {
    button.addEventListener('click', () => {
      body.classList.toggle('sidebar-open');
    });
  });
  document.querySelectorAll('[data-sidebar-close]').forEach((el) => {
    el.addEventListener('click', () => body.classList.remove('sidebar-open'));
  });
  document.querySelectorAll('.sidebar .nav-link').forEach((link) => {
    link.addEventListener('click', () => body.classList.remove('sidebar-open'));
  });
})();
