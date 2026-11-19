(() => {
  let tema = 'system';
  try { tema = localStorage.getItem('termcheck-tema') || tema; } catch {}
  const sistema = matchMedia('(prefers-color-scheme: dark)');
  window.aplicarTema = (valor) => {
    tema = ['light', 'dark', 'system'].includes(valor) ? valor : 'system';
    document.documentElement.dataset.theme = tema === 'system' ? (sistema.matches ? 'dark' : 'light') : tema;
    try { localStorage.setItem('termcheck-tema', tema); } catch {}
  };
  aplicarTema(tema);
  sistema.addEventListener('change', () => { if (tema === 'system') aplicarTema(tema); });
  document.addEventListener('DOMContentLoaded', () => {
    const control = document.querySelector('#tema');
    control.value = tema;
    control.addEventListener('change', () => aplicarTema(control.value));
  });
})();
