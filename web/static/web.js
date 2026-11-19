'use strict';
const $ = (s) => document.querySelector(s);
let soloObservaciones = true;
function navegar(destino) {
  const verificar = destino === 'verificador';
  $('#workspace').hidden = !verificar;
  $('#browse-panel').hidden = verificar;
  document.querySelectorAll('nav [data-nav]').forEach(b => {
    b.classList.toggle('active', b.dataset.nav === destino);
    if (b.dataset.nav === destino) b.setAttribute('aria-current', 'page');
    else b.removeAttribute('aria-current');
  });
  if (!verificar) $('#browse-panel').focus();
}
function actualizarRevision() {
  const solo = $('#solo-observaciones')?.checked || false;
  const selector = $('#segmento');
  const opciones = selector ? [...selector.options] : [];
  opciones.forEach(o => { o.hidden = solo && Number(o.dataset.marked) === 0; o.disabled = o.hidden; });
  if (selector && selector.selectedOptions[0]?.disabled) selector.value = opciones.find(o => !o.disabled)?.value || '0';
  const elegibles = [...document.querySelectorAll('[data-segment]')].filter(s => !solo || Number(s.dataset.marked) > 0);
  const activo = selector ? selector.value : elegibles[0]?.dataset.segment;
  document.querySelectorAll('[data-segment]').forEach(s => {
    s.hidden = s.dataset.segment !== activo;
    s.querySelector('.view-all').hidden = solo;
    if (s.querySelector('.view-only')) s.querySelector('.view-only').hidden = !solo;
  });
}
function descartarResultado() { $('#resultado').replaceChildren(); $('#editor').open = true; $('#destacados').hidden = false; }
function modoEntrada() {
  const archivo = $('[name=modo]:checked').value === 'archivo';
  $('#text-fields').hidden = archivo;
  $('#file-fields').hidden = !archivo;
}
function glosarioEnUso() {
  const archivo = $('[name=glosario]').files[0];
  $('#glosario-en-uso').textContent = archivo ? 'Glosario: ' + archivo.name : 'Glosario O&G · 104 términos';
}
document.addEventListener('click', e => {
  const nav = e.target.closest('[data-nav]');
  if (nav) navegar(nav.dataset.nav);
  if (e.target.closest('#vaciar')) {
    $('#en').value = ''; $('#es').value = '';
    $('[name=archivo]').value = '';
    descartarResultado();
  }
  if (e.target.closest('#quitar-archivo')) { $('[name=archivo]').value = ''; descartarResultado(); }
  if (e.target.closest('#quitar-glosario')) { $('[name=glosario]').value = ''; glosarioEnUso(); descartarResultado(); }
  if (e.target.closest('#usar-ejemplo')) {
    $('[name=modo][value=texto]').checked = true;
    modoEntrada();
    $('#en').value = $('#ejemplo-en').content.textContent;
    $('#es').value = $('#ejemplo-es').content.textContent;
    descartarResultado();
    $('#verificar-form').requestSubmit();
  }
  const descarga = e.target.closest('[data-download]');
  if (descarga) {
    const tipo = descarga.dataset.download;
    const bytes = Uint8Array.from(atob(descarga.dataset.content), c => c.charCodeAt(0));
    const url = URL.createObjectURL(new Blob([bytes], {type: tipo === 'html' ? 'text/html;charset=utf-8' : 'text/csv;charset=utf-8'}));
    const a = document.createElement('a'); a.href = url; a.download = 'termcheck.' + tipo; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
});
document.addEventListener('change', e => {
  if (e.target.id === 'solo-observaciones') soloObservaciones = e.target.checked;
  if (e.target.matches('#solo-observaciones, #segmento')) actualizarRevision();
  if (e.target.name === 'modo') { modoEntrada(); descartarResultado(); }
  if (e.target.name === 'glosario') { glosarioEnUso(); descartarResultado(); }
  if (e.target.name === 'archivo') descartarResultado();
});
document.addEventListener('input', e => {
  if (e.target.matches('#en, #es')) descartarResultado();
});
document.addEventListener('htmx:beforeRequest', e => {
  $('#network-error').hidden = true;
  if (e.detail.elt.id === 'verificar-form') $('#resultado').replaceChildren();
});
document.addEventListener('htmx:afterSwap', e => {
  if (e.detail.target.id === 'resultado') {
    if ($('#solo-observaciones')) $('#solo-observaciones').checked = soloObservaciones;
    actualizarRevision();
    if ($('#resultado [data-result-ok]')) {
      $('#editor').open = false;
      $('.welcome').hidden = true;
      $('#destacados').hidden = true;
      $('#revision-titulo').focus({preventScroll:true});
      $('#verificador').scrollIntoView({behavior:'smooth', block:'start'});
    }
  }
});
for (const nombre of ['htmx:sendError', 'htmx:responseError']) {
  document.addEventListener(nombre, () => { $('#network-error').hidden = false; });
}
