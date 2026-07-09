import { chromium } from 'playwright';

const BASE = 'http://localhost:5173';
const SCREENSHOTS = '/tmp/test-screenshots';

import { mkdirSync, writeFileSync } from 'fs';
mkdirSync(SCREENSHOTS, { recursive: true });

async function shot(page, name) {
  await page.screenshot({ path: `${SCREENSHOTS}/${name}.png`, fullPage: true });
  console.log(`  Screenshot: ${name}.png`);
}

async function run() {
  const browser = await chromium.launch({ headless: false, slowMo: 300 });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // Capturar console errors
  page.on('console', (msg) => {
    if (msg.type() === 'error') console.log(`  [CONSOLE ERROR] ${msg.text()}`);
  });
  page.on('pageerror', (err) => console.log(`  [PAGE ERROR] ${err.message}`));

  // 1. Login
  console.log('1. Abrindo pagina de login...');
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await shot(page, '01-login');

  const inputs = await page.locator('input').all();
  if (inputs.length >= 2) {
    await inputs[0].fill('admin');
    await inputs[1].fill('admin');
  }
  await page.click('button:has-text("Entrar")');
  await page.waitForSelector('.app-shell', { timeout: 10000 });
  await shot(page, '02-logado');
  console.log('Login OK');

  // 2. Navegar para Instituições
  console.log('2. Clicando em Instituições...');
  await page.click('text=Instituições');
  await page.waitForTimeout(2000);
  await shot(page, '03-instituicoes');

  // 3. Clicar Editar
  console.log('3. Clicando em Editar...');
  const editButton = page.locator('button:has-text("Editar")').first();
  await editButton.waitFor({ state: 'visible', timeout: 5000 });
  await editButton.click();
  await page.waitForTimeout(2000);
  await shot(page, '04-drawer-aberto');

  // 4. Modificar nome
  console.log('4. Preenchendo formulario...');
  const nomeField = page.locator('.ant-drawer .ant-form-item').filter({ hasText: 'Nome' }).locator('input');
  if (await nomeField.isVisible()) {
    await nomeField.clear();
    await nomeField.fill('Instituicao Teste Playwright');
  }

  const contratoField = page.locator('.ant-drawer .ant-form-item').filter({ hasText: 'Número do Contrato' }).locator('input');
  if (await contratoField.isVisible()) {
    await contratoField.clear();
    await contratoField.fill('CT-0001');
  }

  await shot(page, '05-formulario-preenchido');

  // 5. Salvar
  console.log('5. Salvando...');
  const salvarBtn = page.locator('.ant-drawer button:has-text("Salvar")');
  await salvarBtn.click();
  await page.waitForTimeout(3000);
  await shot(page, '06-pos-salvar');

  // 6. Verificar mensagem
  const msg = page.locator('.ant-message-notice-content');
  if (await msg.isVisible({ timeout: 5000 }).catch(() => false)) {
    const text = await msg.textContent();
    console.log(`Mensagem: ${text}`);
  } else {
    console.log('Nenhuma mensagem visivel');
  }

  await shot(page, '07-final');

  await browser.close();
  console.log(`\nScreenshots salvos em: ${SCREENSHOTS}/`);
  console.log('Teste concluido');
}

run().catch((err) => {
  console.error('Teste falhou:', err.message);
  process.exit(1);
});
