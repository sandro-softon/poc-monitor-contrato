import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';

const BASE = 'http://localhost:5173';
const SS = '/tmp/teste-contrato-copia';
const CODIGO = '2007020999';
mkdirSync(SS, { recursive: true });

function dbCheck(label) {
  const out = execSync(
    `uv run python -c "import sys;sys.path.insert(0,'.');from sqlalchemy import create_engine,text;from src.config import Config;e=create_engine(Config.DATABASE_URL);c=e.connect();r=c.execute(text('SELECT NOME_INSTITUICAO,NUM_CONTRATO,STATUS,COD_COMPARTILHADO FROM TB_INSTITUICAO WHERE COD_INSTITUICAO=${CODIGO}')).fetchone();s=c.execute(text('SELECT SERVICOS_CONTRATADOS,NUM_AC_CONTRATADOS,FL_ACESSOS_ILIMITADOS,VALOR_EXCEDENTE,FL_MONITORAR_CONTRATO FROM TB_CONTRATO WHERE COD_INSTITUICAO=${CODIGO} ORDER BY SERVICOS_CONTRATADOS')).fetchall();print(f'Inst: {r[0]} / Contrato: {r[1]} / Status: {r[2]} / Comp: {r[3]}');print('Servicos:');[print(f'  {x[0]}: lim={x[1]} ilim={x[2]} val={x[3]} mon={x[4]}') for x in s]"`,
    { cwd: '/home/sandro/dev-python/poc-monitor-contrato-kity' }
  ).toString().trim();
  console.log(`[DB ${label}]\n${out}\n`);
}

async function shot(page, name) {
  await page.screenshot({ path: `${SS}/${name}.png` });
  console.log(`  Screenshot: ${name}.png`);
}

async function run() {
  console.log('=== TESTE CONTRATO COPIA ===\n');
  dbCheck('INICIAL');

  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // LOGIN
  console.log('1. Login e captura de tela...');
  await page.goto(BASE, { waitUntil: 'networkidle' });
  const inp = await page.locator('input').all();
  if (inp.length >= 2) { await inp[0].fill('admin'); await inp[1].fill('admin'); }
  await page.click('button:has-text("Entrar")');
  await page.waitForSelector('.app-shell', { timeout: 10000 });
  await shot(page, '01-logado');

  // VERIFICAR VIA API
  console.log('\n2. Verificando API (GET /api/contracts/2007020999)...');
  const apiRes = await page.request.fetch(`${BASE}/api/contracts/${CODIGO}`,
    { headers: { Authorization: 'Bearer dev-admin-token' } });
  const data = await apiRes.json();
  console.log(`   Nome: ${data.nome_instituicao}`);
  console.log(`   Contrato: ${data.numero_contrato}`);
  console.log(`   Servicos: ${data.servicos.map(s => `${s.servico}=${s.num_ac_contratados}`).join(', ')}`);
  console.log(`   Corte: ${data.dt_corte_inicial} | Freq: ${data.frequencia_corte}`);

  // VERIFICAR LISTAGEM COM FILTRO
  console.log('\n3. Verificando listagem filtrada...');
  const listRes = await page.request.fetch(`${BASE}/api/contracts?q=${CODIGO}&page=1&page_size=5`,
    { headers: { Authorization: 'Bearer dev-admin-token' } });
  const listData = await listRes.json();
  console.log(`   Total: ${listData.total}`);
  if (listData.total === 1) {
    const inst = listData.items[0];
    console.log(`   Instituicao: ${inst.nome_instituicao}`);
    console.log(`   Frequencia: ${inst.frequencia_corte}`);
    console.log(`   Status: ${inst.status}`);
  }

  // VERIFICAR TELA DE CONTRATOS (sem busca)
  console.log('\n4. Capturando tela de Contratos...');
  await page.click('text=Contratos');
  await page.waitForTimeout(2000);
  await shot(page, '04-contratos');
  console.log('   OK');

  // CAPTURAR TELA DE INSTITUICOES E VERIFICAR COPIA
  console.log('\n5. Verificando tela Instituicoes...');
  await page.click('text=Instituições');
  await page.waitForTimeout(2000);
  await shot(page, '05-instituicoes');

  // Buscar pelo codigo na tela de Instituicoes usando a API
  const instRes = await page.request.fetch(`${BASE}/api/institutions?q=${CODIGO}&page=1&page_size=5`,
    { headers: { Authorization: 'Bearer dev-admin-token' } });
  const instData = await instRes.json();
  console.log(`   Instituicoes encontradas: ${instData.total}`);
  if (instData.total > 0) {
    console.log(`   ${instData.items[0].nome_instituicao} - ${instData.items[0].numero_contrato}`);
  }

  dbCheck('FIM');
  console.log('\n=== TESTE CONCLUIDO ===');
  await browser.close();
}

run().catch((err) => {
  console.error(`FALHA: ${err.message}`);
  writeFileSync(`${SS}/ERRO.txt`, err.message);
  process.exit(1);
});
