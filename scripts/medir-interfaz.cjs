// Medición descriptiva en el mismo servidor; no evalúa calidad ni capacidad de carga.
const fs = require('node:fs');
const {performance} = require('node:perf_hooks');
const {execFileSync} = require('node:child_process');
const {loadPlaywright, installedBrowser} = require('/home/ubuntu/tools/codex-toolkit/browser.cjs');
async function main() {
  const modo = process.argv[2];
  if (!['streamlit','fastapi'].includes(modo)) throw new Error('Elegí streamlit o fastapi');
  const base = process.env.TERMCHECK_URL || 'http://127.0.0.1:8502/demo/';
  const {chromium} = loadPlaywright();
  const browser = await chromium.launch({executablePath:installedBrowser(chromium),headless:true});
  const mediciones = [];
  try {
    for (let i=0;i<4;i++) {
      const contexto = await browser.newContext();
      const page = await contexto.newPage();
      let inicio = performance.now();
      await page.goto(base);
      const original = modo === 'fastapi' ? page.locator('#en') : page.getByLabel('Original · inglés',{exact:true});
      const traduccion = modo === 'fastapi' ? page.locator('#es') : page.getByLabel('Traducción · español',{exact:true});
      await original.waitFor();
      const lista_ms = performance.now() - inicio;
      await original.fill('Inspect the elevator.');
      await traduccion.fill('Inspeccioná el elevador.');
      inicio = performance.now();
      await page.getByRole('button',{name:'Verificar',exact:true}).click();
      await page.getByText('Sin observaciones en los términos reconocidos.',{exact:true}).waitFor();
      const verificar_ms = performance.now() - inicio;
      mediciones.push({ronda:i,lista_ms:Math.round(lista_ms),verificar_ms:Math.round(verificar_ms)});
      await contexto.close();
    }
    const memoria = Number(execFileSync('systemctl',['show','termcheck-demo','-p','MemoryCurrent','--value'],{encoding:'utf8'}).trim());
    const cuota = execFileSync('systemctl',['show','termcheck-demo','-p','CPUQuotaPerSecUSec','--value'],{encoding:'utf8'}).trim();
    const resultado = {modo,base,fecha:new Date().toISOString(),mediciones,memoria_cgroup_bytes:memoria,cuota_cpu:cuota,
      alcance:'Cuatro visitas con contextos nuevos, un caso corto, proceso existente; primera ronda separada. No mide arranque del servicio ni carga sostenida. Memoria cgroup incluye cachés; no solo RSS.'};
    fs.mkdirSync('salida/web/mediciones',{recursive:true});
    fs.writeFileSync(`salida/web/mediciones/${modo}.json`,JSON.stringify(resultado,null,2));
    console.log(JSON.stringify(resultado));
  } finally { await browser.close(); }
}
main().catch(e=>{console.error(e);process.exitCode=1});
