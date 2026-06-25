/**
 * theme.js — MyBot SaaS
 * Gestion du thème light / dark avec persistance localStorage.
 * A inclure sur toutes les pages avant la fermeture </body>.
 *
 * IMPORTANT : Les SVG icon-sun / icon-moon ne doivent PAS avoir
 * de style="display:..." inline dans le HTML — c'est ce script
 * qui gère entièrement leur visibilité.
 */

(function () {
  const STORAGE_KEY = 'mybot-theme';
  const root = document.documentElement;

  // -- Applique le thème au <html> et met à jour les icônes ----------------
  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);

    const btn = document.getElementById('theme-toggle');
    if (!btn) return;

    btn.setAttribute(
      'aria-label',
      theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'
    );

    // On masque les deux, puis on affiche seulement celle qui correspond
    const sun  = btn.querySelector('.icon-sun');
    const moon = btn.querySelector('.icon-moon');
    if (sun)  sun.style.display  = theme === 'dark'  ? 'block' : 'none';
    if (moon) moon.style.display = theme === 'light' ? 'block' : 'none';
  }

  // -- Lecture de la préférence sauvegardée ou système ---------------------
  function getInitialTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'light' || saved === 'dark') return saved;
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  // -- Toggle public --------------------------------------------------------
  function toggleTheme() {
    const current = root.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  }

  // -- Init -----------------------------------------------------------------
  const initialTheme = getInitialTheme();
  applyTheme(initialTheme);

  // Attache le bouton dès que le DOM est prêt
  function bindButton() {
    const btn = document.getElementById('theme-toggle');
    if (btn) {
      // Re-applique pour forcer l'état correct des icônes avec le DOM complet
      applyTheme(root.getAttribute('data-theme') || 'dark');
      btn.addEventListener('click', toggleTheme);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindButton);
  } else {
    bindButton();
  }

  // Ecoute les changements de préférence système (si pas de choix manuel)
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', function (e) {
    if (!localStorage.getItem(STORAGE_KEY)) {
      applyTheme(e.matches ? 'light' : 'dark');
    }
  });

  // Expose globalement pour usage optionnel depuis d'autres scripts
  window.MybotTheme = { toggle: toggleTheme, apply: applyTheme };
})();