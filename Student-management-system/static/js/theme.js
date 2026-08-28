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
})();
