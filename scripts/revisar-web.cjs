const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {loadPlaywright, installedBrowser} = require('/home/ubuntu/tools/codex-toolkit/browser.cjs');
const base = process.env.TERMCHECK_URL || 'http://127.0.0.1:8530/demo/';
const out = path.resolve(process.env.TERMCHECK_SALIDA_WEB || 'salida/web');
async function main() {
  fs.mkdirSync(out, {recursive:true});
  const {chromium} = loadPlaywright();
  const browser = await chromium.launch({executablePath:installedBrowser(chromium), headless:true});
  const errors = [];
  const context = await browser.newContext({viewport:{width:1280,height:900},acceptDownloads:true});
  const page = await context.newPage();
  page.on('pageerror', e => errors.push(e.message));
  page.on('response', r => { if (r.status() >= 400) errors.push(`${r.status()} ${r.url()}`); });
  let verificaciones = 0;
  page.on('request', r => { if (r.url().endsWith('/verificar')) verificaciones++; });
  const llenar = async (en,es) => {
    await page.locator('#editor').evaluate(el => el.open = true);
    await page.locator('[name=modo][value=texto]').check();
    await page.locator('#en').fill(en); await page.locator('#es').fill(es);
    await page.getByRole('button',{name:'Verificar',exact:true}).click();
    await page.locator('[data-result-ok]').waitFor();
  };
  const overflow = async () => assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'desborde');
  try {
    await page.goto(base);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({path:path.join(out,'entrada-pc.png'),fullPage:true});
    await page.getByRole('button',{name:'Usar ejemplo',exact:true}).click();
    await page.locator('[data-result-ok]').waitFor();
    assert.equal(await page.locator('#editor').evaluate(el=>el.open),false);
    assert.equal(await page.locator('.review-segment:visible').count(),1);
    const inicial = verificaciones;
    await page.locator('#solo-observaciones').uncheck();
    await page.locator('#segmento').selectOption('1');
    assert.equal(verificaciones,inicial);
    await page.screenshot({path:path.join(out,'revision-pc.png'),fullPage:true});
    const descarga = await Promise.all([page.waitForEvent('download'), (async () => {
      await page.locator('.downloads summary').click();
      await page.getByRole('button',{name:'Tabla CSV',exact:true}).click();
    })()]);
    await descarga[0].saveAs(path.join(out,'descarga.csv'));
    assert(fs.readFileSync(path.join(out,'descarga.csv'),'utf8').includes('seg_id,system,term_id'));
    const html = await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'Reporte HTML',exact:true}).click()]);
    await html[0].saveAs(path.join(out,'descarga.html'));
    assert(fs.readFileSync(path.join(out,'descarga.html'),'utf8').includes('SHA-256'));
    const previo = await page.locator('#en').inputValue();
    await page.locator('nav [data-nav=glosario]').click();
    await page.locator('.catalog-search').waitFor();
    await page.getByRole('searchbox').fill('elevator');
    await page.getByRole('button',{name:'Buscar',exact:true}).click();
    await page.getByRole('heading',{name:'elevator',exact:true}).waitFor();
    await page.screenshot({path:path.join(out,'glosario-pc.png'),fullPage:true});
    const csv = await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'Descargar CSV'}).click()]);
    await csv[0].saveAs(path.join(out,'glosario.csv'));
    assert.equal(fs.readFileSync(path.join(out,'glosario.csv'),'utf8'),fs.readFileSync('data/glossary/glossary_v1_4.csv','utf8'));
    await page.locator('nav [data-nav=ejemplos]').click();
    await page.locator('.example').first().waitFor();
    await page.getByRole('button',{name:'Probar traducción',exact:true}).first().click();
    await page.locator('#ejemplo-0 .tc-report').waitFor();
    await page.locator('nav [data-nav=verificador]').click();
    assert.equal(await page.locator('#en').inputValue(),previo);
    await page.locator('[data-result-ok]').waitFor();
    await llenar('Inspect the elevator.','Inspeccioná el elevador.');
    assert((await page.locator('#resultado').innerText()).includes('Sin observaciones'));
    await llenar('Inspect the elevators.','Inspeccioná los elevadores.');
    assert((await page.locator('#resultado').innerText()).includes('Sin observaciones'));
    await llenar('Hello everyone.','Hola a todos.');
    assert(!(await page.locator('#resultado').innerText()).includes('Sin observaciones'));
    await page.locator('#editor').evaluate(el=>el.open=true);
    await page.locator('#en').fill('Casing.\nWell.'); await page.locator('#es').fill('Casing.');
    await page.getByRole('button',{name:'Verificar',exact:true}).click();
    await page.locator('[data-validation-error]').waitFor();
    await page.locator('[name=modo][value=archivo]').check();
    await page.locator('[name=archivo]').setInputFiles({name:'x.xlf',mimeType:'application/xml',buffer:Buffer.from('<xliff version="1.2"><file source-language="en" target-language="es"><body><trans-unit id="a"><source>Casing.</source><target>Casing.</target></trans-unit></body></file></xliff>')});
    await page.getByRole('button',{name:'Verificar',exact:true}).click();
    await page.locator('[data-result-ok]').waitFor();
    await page.locator('nav [data-nav=glosario]').click();
    await page.locator('.catalog-search').waitFor();
    await page.locator('nav [data-nav=verificador]').click();
    assert.equal(await page.locator('[name=archivo]').evaluate(el=>el.files[0].name),'x.xlf');
    await page.locator('#editor').evaluate(el=>el.open=true);
    await page.locator('[name=archivo]').setInputFiles({name:'roto.csv',mimeType:'text/csv',buffer:Buffer.from('source_en,target_es\nCasing.')});
    await page.getByRole('button',{name:'Verificar',exact:true}).click();
    await page.locator('[data-validation-error]').waitFor();
    // Vistas, temas y conservación de la revisión al cambiar apariencia.
    await llenar('Drill pipe.','Tubo de perforación.');
    for (const width of [1280,390]) {
      await page.setViewportSize({width,height:900});
      for (const tema of ['light','dark']) {
        await page.locator('#tema').selectOption(tema);
        await overflow();
        await page.screenshot({path:path.join(out,`revision-${width}-${tema}.png`),fullPage:true});
        await page.locator('nav [data-nav=glosario]').click();
        await page.locator('.catalog-search').waitFor();
        await overflow();
        await page.screenshot({path:path.join(out,`glosario-${width}-${tema}.png`),fullPage:true});
        await page.locator('nav [data-nav=verificador]').click();
      }
    }
    await page.locator('#editor').evaluate(el=>el.open=true);
    await page.getByRole('button',{name:'Vaciar',exact:true}).click();
    assert.equal(await page.locator('#en').inputValue(),'');
    assert.equal(await page.locator('#resultado').innerText(),'');
    await page.screenshot({path:path.join(out,'entrada-telefono-oscuro.png'),fullPage:true});
    await page.reload();
    assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
    await page.locator('#tema').selectOption('system');
    await page.emulateMedia({colorScheme:'light'});
    assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
    await page.emulateMedia({colorScheme:'dark'});
    await page.waitForFunction(() => document.documentElement.dataset.theme === 'dark');
    await page.emulateMedia({colorScheme:'light'});
    await page.locator('#tema').selectOption('light');
    await page.screenshot({path:path.join(out,'entrada-telefono.png'),fullPage:true});
    await llenar('Drill pipe.','Tubo de perforación.');
    await page.pdf({path:path.join(out,'revision.pdf'),format:'A4',printBackground:true});
    // Las URLs compartidas también muestran una página completa bajo /demo/.
    for (const ruta of ['glosario?q=elevator', 'ejemplos']) {
      await page.goto(new URL(ruta, base).href);
      await page.locator('#tema').waitFor();
      await page.locator('#browse-panel:visible').waitFor();
      await overflow();
      if (ruta.startsWith('glosario')) await page.getByRole('heading',{name:'elevator',exact:true}).waitFor();
      await page.locator('nav [data-nav=verificador]').click();
      await llenar('Inspect the elevator.', 'Inspeccioná el elevador.');
    }
    // Tres visitantes independientes.
    await Promise.all([0,1,2].map(async i => {
      const c = await browser.newContext(); const p = await c.newPage();
      await p.goto(base); await p.locator('#en').fill('Casing.');
      await p.locator('#es').fill(`Casing. Visitante ${i}.`);
      await p.getByRole('button',{name:'Verificar',exact:true}).click();
      await p.locator('[data-result-ok]').waitFor();
      const texto = await p.locator('#resultado').innerText();
      assert(texto.includes(`Visitante ${i}.`));
      for(let j=0;j<3;j++) if(j!==i) assert(!texto.includes(`Visitante ${j}.`));
      await c.close();
    }));
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(out,'navegador.json'),JSON.stringify({ok:true,base,verificaciones,errors,fecha:new Date().toISOString()},null,2));
    console.log('Flujo, archivos, descargas, catálogo, temas, PC/teléfono y sesiones independientes: OK.');
  } finally { await browser.close(); }
}
main().catch(e=>{console.error(e);process.exitCode=1});
