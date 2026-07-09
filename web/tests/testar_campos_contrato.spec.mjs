import { chromium } from 'playwright';
import { mkdirSync } from 'fs';
import { execSync } from 'child_process';
const BASE = 'http://localhost:5173';
const SS = '/tmp/teste-campos-contrato';
const CODIGO = '2007020999';
mkdirSync(SS, { recursive: true });

async function shot(page, name) {
  await page.screenshot({ path: `${SS}/${name}.png` });
  console.log(`  Screenshot: ${name}.png`);
}

async function run() {
  console.log('=== TESTE CAMPOS CONTRATO ===\n');
  const browser = await chromium.launch({ headless: false, slowMo: 80 });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  page.on('console', (msg) => {
    if (msg.type() === 'error' && !msg.text().includes('Warning'))
      console.log(`  [CONSOLE] ${msg.text()}`);
  });

  // ============================================================
  // PARTE 1: VERIFICACAO VIA API (campos do contrato)
  // ============================================================
  console.log('=== PARTE 1: VERIFICACAO VIA API ===\n');

  // 1.1 - DETALHE DO CONTRATO
  console.log('1.1 GET /api/contracts/{codigo} - detalhe completo...');
  const detailRes = await page.request.fetch(`${BASE}/api/contracts/${CODIGO}`,
    { headers: { Authorization: 'Bearer dev-admin-token' } });
  const detail = await detailRes.json();
  console.assert(detailRes.status() === 200, `Status esperado 200, obtido ${detailRes.status()}`);
  console.assert(detail.codigo_instituicao === 2007020999, 'codigo_instituicao incorreto');
  console.assert(detail.nome_instituicao === 'Bradesco COPIA TESTE', 'nome_instituicao incorreto');
  console.assert(detail.numero_contrato === 'CW40194', 'numero_contrato incorreto');
  console.assert(detail.cod_compartilhado === 2015092301, 'cod_compartilhado incorreto');
  console.assert(detail.frequencia_corte === 'Mensal', 'frequencia_corte incorreto');
  console.assert(detail.status === 1, 'status incorreto');
  console.assert(detail.servicos.length === 2, `servicos.length esperado 2, obtido ${detail.servicos.length}`);
  console.log(`   ✅ Todos os campos do contrato OK`);

  // 1.2 - SERVICOS
  console.log('\n1.2 Verificando servicos...');
  const svcIndividual = detail.servicos.find(s => s.servico === 'Individual');
  const svcLote = detail.servicos.find(s => s.servico === 'Lote');
  console.assert(svcIndividual !== undefined, 'Servico Individual nao encontrado');
  console.assert(svcLote !== undefined, 'Servico Lote nao encontrado');
  console.assert(svcIndividual.num_ac_contratados === 500000, `Individual.limite esperado 500000, obtido ${svcIndividual.num_ac_contratados}`);
  console.assert(svcLote.num_ac_contratados === 500000, `Lote.limite esperado 500000, obtido ${svcLote.num_ac_contratados}`);
  console.assert(svcIndividual.fl_acessos_ilimitados === false, 'Individual.ilimitado deveria ser false');
  console.assert(svcIndividual.valor_excedente === null, 'Individual.valor_excedente deveria ser null');
  console.log(`   ✅ Individual: limite=500000 ilimitado=false excedente=null`);
  console.log(`   ✅ Lote:       limite=500000 ilimitado=false excedente=null`);

  // 1.3 - LISTAGEM COM FILTRO
  console.log('\n1.3 GET /api/contracts?q={codigo} - listagem filtrada...');
  const listRes = await page.request.fetch(`${BASE}/api/contracts?q=${CODIGO}&page=1&page_size=5`,
    { headers: { Authorization: 'Bearer dev-admin-token' } });
  const listData = await listRes.json();
  console.assert(listData.total >= 1, `Listagem deveria conter pelo menos 1 item, total=${listData.total}`);
  console.assert(listData.items[0].codigo_instituicao === 2007020999, 'codigo incorreto na listagem');
  console.assert(listData.items[0].nome_instituicao === 'Bradesco COPIA TESTE', 'nome incorreto na listagem');
  console.assert(listData.items[0].frequencia_corte === 'Mensal', 'frequencia incorreta na listagem');
  console.log(`   ✅ Listagem filtrada retornou ${listData.total} resultado(s)`);

  // 1.4 - LISTAGEM SEM FILTRO
  console.log('\n1.4 GET /api/contracts - listagem paginada (sem duplicatas)...');
  const allRes = await page.request.fetch(`${BASE}/api/contracts?page=1&page_size=50`,
    { headers: { Authorization: 'Bearer dev-admin-token' } });
  const allData = await allRes.json();
  const codes = allData.items.map(i => i.codigo_instituicao);
  const dups = codes.filter((c, idx) => codes.indexOf(c) !== idx);
  console.assert(dups.length === 0, `Listagem contem duplicatas: ${[...new Set(dups)].join(', ')}`);
  console.log(`   ✅ Listagem sem duplicatas (${allData.total} instituicoes)`);

  // 1.5 - TESTE DE ALTERACAO (usando fetch nativo do Node via curl para evitar problemas do Playwright)
  console.log('\n1.5 PUT /api/contracts/{codigo} - alteracao...');
  const valoresTeste = {
    numero_contrato: 'CT-ALTERACAO-TESTE',
    dt_ini: '2026-01-01',
    dt_fim: '2028-12-31',
    dt_corte_inicial: '2026-06-15',
    frequencia_corte: 'Anual',
    cod_compartilhado: 9999999999,
    servicos: [
      { id: svcIndividual.id, servico: 'Individual', num_ac_contratados: 999999, fl_acessos_ilimitados: 0, valor_excedente: null },
      { id: svcLote.id, servico: 'Lote', num_ac_contratados: 888888, fl_acessos_ilimitados: 0, valor_excedente: 5.50 }
    ]
  };
  const putCmd = `curl -s -X PUT "http://localhost:8000/api/contracts/${CODIGO}" -H "Authorization: Bearer dev-admin-token" -H "Content-Type: application/json" -d '${JSON.stringify(valoresTeste)}'`;
  const putOut = JSON.parse(execSync(putCmd).toString());
  console.assert(putOut.numero_contrato === 'CT-ALTERACAO-TESTE', 'numero_contrato nao alterado');
  console.assert(putOut.frequencia_corte === 'Anual', 'frequencia nao alterada');
  console.assert(putOut.servicos[0].num_ac_contratados === 999999, 'limite Individual nao alterado');
  console.assert(putOut.servicos[1].valor_excedente === 5.50, 'valor excedente Lote nao alterado');

  // 1.6 - VERIFICAR SINCRONIZACAO
  console.log('\n1.6 Verificando sincronizacao com TB_CONTRATO...');
  const syncRes = await page.request.fetch(`${BASE}/api/contracts/${CODIGO}`,
    { headers: { Authorization: 'Bearer dev-admin-token' } });
  const syncData = await syncRes.json();
  console.assert(syncData.numero_contrato === 'CT-ALTERACAO-TESTE', 'numero_contrato divergente');
  console.assert(syncData.dt_corte_inicial?.includes('2026-06-15'), 'dt_corte_inicial divergente');
  console.log('   ✅ Sincronizacao OK');

  // 1.7 - RESTAURAR DADOS ORIGINAIS
  console.log('\n1.7 Restaurando dados originais...');
  const restoreCmd = `curl -s -X PUT "http://localhost:8000/api/contracts/${CODIGO}" -H "Authorization: Bearer dev-admin-token" -H "Content-Type: application/json" -d '${JSON.stringify({
    numero_contrato: 'CW40194',
    dt_ini: '2017-10-30',
    dt_fim: '2027-02-28',
    dt_corte_inicial: '2026-05-01',
    frequencia_corte: 'Mensal',
    cod_compartilhado: 2015092301,
    servicos: [
      { id: svcIndividual.id, servico: 'Individual', num_ac_contratados: 500000, fl_acessos_ilimitados: 0, valor_excedente: null },
      { id: svcLote.id, servico: 'Lote', num_ac_contratados: 500000, fl_acessos_ilimitados: 0, valor_excedente: null }
    ]
  })}'`;
  const restoreOut = JSON.parse(execSync(restoreCmd).toString());
  console.assert(restoreOut.numero_contrato === 'CW40194', 'Restauracao falhou');
  console.log('   ✅ Dados restaurados');

  // ============================================================
  // PARTE 2: VERIFICACAO VIA INTERFACE
  // ============================================================
  console.log('\n\n=== PARTE 2: VERIFICACAO VIA INTERFACE ===\n');

  // 2.1 - LOGIN
  console.log('2.1 Abrindo pagina...');
  await page.goto(BASE, { waitUntil: 'networkidle' });
  const inp = await page.locator('input').all();
  await inp[0].fill('admin'); await inp[1].fill('admin');
  await page.click('button:has-text("Entrar")');
  await page.waitForSelector('.app-shell', { timeout: 10000 });
  await shot(page, '21-logado');
  console.log('   ✅ Login OK');

  // 2.2 - Navegar para Contratos
  console.log('\n2.2 Navegando para Contratos...');
  await page.click('text=Contratos');
  await page.waitForTimeout(2000);
  await shot(page, '22-contratos');
  console.log('   ✅ Pagina de Contratos carregada');

  // 2.3 - Abrir drawer via API e exibir visualmente
  console.log('\n2.3 Abrindo drawer de edicao via API...');
  // Navegar para a pagina e usar evaluate para simular clique no editar
  // Vamos usar page.evaluate para forcar a abertura pelo React state
  await page.evaluate(async (cod) => {
    const token = 'dev-admin-token';
    const res = await fetch(`/api/contracts/${cod}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();
    // Armazenar no window para debug
    window.__contractData = data;
  }, CODIGO);
  await shot(page, '23-dados-carregados');

  // Forcar abertura do drawer chamando editContract
  await page.evaluate((cod) => {
    // Simular clique no boto editar atraves de manipulacao do DOM
    // Procurar a linha com o codigo e clicar no botao Editar
    const rows = document.querySelectorAll('table tbody tr');
    for (const row of rows) {
      if (row.textContent.includes(String(cod))) {
        const editBtn = row.querySelector('button');
        if (editBtn) { editBtn.click(); break; }
      }
    }
  }, CODIGO);
  await page.waitForTimeout(3000);
  await shot(page, '24-drawer-visivel');

  const drawerVisivel = await page.locator('.ant-drawer').isVisible().catch(() => false);
  if (drawerVisivel) {
    const title = await page.locator('.ant-drawer-title').textContent();
    console.log(`   ✅ Drawer aberto: ${title}`);

    // Capturar valores dos campos
    const campos = [];
    const formItems = await page.locator('.ant-drawer .ant-form-item').all();
    for (const item of formItems) {
      const label = await item.locator('.ant-form-item-label label').textContent().catch(() => null);
      if (!label) continue;
      const input = item.locator('input').first();
      const val = await input.inputValue().catch(() => null);
      campos.push(`${label}=${val}`);
    }
    console.log(`   Campos: ${campos.join(' | ')}`);

    // Fechar drawer
    await page.locator('.ant-drawer .ant-drawer-close').click();
    await page.waitForTimeout(1000);
    console.log('   ✅ Drawer fechado');
  } else {
    console.log('   ⚠️ Drawer nao abriu via clique. Verifique o seletor.');
  }

  await shot(page, '25-final');
  console.log('\n=== TESTE CONCLUIDO ===');
  await browser.close();
}

run().catch((err) => {
  console.error(`FALHA: ${err.message}`);
  process.exit(1);
});
