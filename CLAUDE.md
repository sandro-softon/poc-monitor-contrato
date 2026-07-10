# CLAUDE.md - Project Context for AI Agents

Este arquivo fornece diretrizes técnicas para auxiliar agentes de IA no desenvolvimento deste projeto.

## Stack Atual

```text
Frontend: React + Vite + Ant Design v6
Backend:  FastAPI + SQLAlchemy 2.x + pymysql
Banco:    MySQL
Batch:    Python CLI (mysql-connector-python)
```

## Comandos Úteis

### Ambiente
- `uv sync`: Sincroniza dependências.
- `npm install` (em `web/`): Instala dependências do frontend.

### Execução
- `./run.sh [--src excel|db] [--debug] [--full] [--test CODIGO]`: Processo batch.
- `docker compose up --build -d`: Sobe API + Web.
- `uv run uvicorn src.web_api.app:app --host 0.0.0.0 --port 8000`: API manual.
- `cd web && npm run dev`: Frontend manual.

### Qualidade
- `uv run python -m pytest`: Testes Python.
- `cd web && npm run build`: Build frontend.
- `uv run ruff format .`: Formatação (só quando solicitado).

## Arquitetura

### Web API (`src/web_api/`)
```text
app.py              → FastAPI app, CORS, rotas
auth.py             → Login via TB_USUARIOS + token UUID (2h expiry)
contracts.py        → Contratos agregados por instituição
institutions.py     → CRUD de instituições
```

### DB Layer (`src/db/`)
```text
session.py          → engine + SessionLocal + get_db
models.py           → Instituicao, Contrato (SQLAlchemy mapped)
```

### CLI Batch (`src/`)
```text
main.py             → Orquestrador, --src excel|db
readers/            → ContractReader (Excel), ContractDbReader (MySQL), AccessReader
core/analyzer.py    → Lógica de alertas, agrupa por instituição
notifications/      → EmailSender (SMTP)
```

### Frontend (`web/`)
```text
src/App.jsx         → SPA completa (login, contratos, instituições, temas)
src/styles.css      → Tema escuro + temas (grafana, datadog, cartoon)
```

## Regras Críticas

### Banco de Dados
- **Fonte de verdade**: `TB_INSTITUICAO` para dados gerais do contrato (NUM_CONTRATO, DT_INI, DT_FIM, COD_COMPARTILHADO, DT_CORTE_INICIAL, FREQUENCIA_CORTE).
- **TB_CONTRATO**: apenas atributos por serviço (SERVICOS_CONTRATADOS, NUM_AC_CONTRATADOS, VL_EXCEDENTE).
- Consultas SQL de período usam intervalo aberto: `DATA >= inicio AND DATA < fim_exclusivo`.
- Evite `BETWEEN`.

### Serviços
- Serviços válidos: `Individual`, `Lote`, `API`.
- **Não use `.title()`** — `API` viraria `Api`.
- Após normalização (Fase 2), cada linha de `TB_CONTRATO` contém um único serviço.
- `acessos_realizados` soma os serviços contratados da instituição (agrupado).
- Limite efetivo do grupo = `MAX(limite)` entre os serviços da instituição.

### Autenticação
- Login consulta `TB_USUARIOS` com `COD_INSTITUICAO = 2007011801` e `STATUS = 1`.
- Token UUID gerado dinamicamente, expira em 2 horas.
- `require_auth` via `Depends()` — nenhum endpoint fixo.

### Frontend
- Drawers de edição com `ServicoInput` (estado local + onBlur) para evitar perda de foco.
- DatePicker com `allowClear={false}` para preservar valor ao fechar.
- Sider auto-retátil ao hover (expande/recolhe).
- Seletor de temas no header (6 temas, persistência em localStorage).

## Estrutura do Projeto
```text
src/
  main.py
  config.py
  db/
    models.py, session.py
  core/
    analyzer.py, date_utils.py
  readers/
    access_reader.py, contract_db_reader.py, excel_reader.py
  notifications/
    email_sender.py
  web_api/
    app.py, auth.py, contracts.py, institutions.py
web/
  src/App.jsx, src/styles.css
  tests/ (Playwright)
sql/
  tb_contrato_migration.sql, normalizar_servicos.sql
scripts/
  export_contracts_excel.py
tests/
  test_*.py
```

## Casos Validados
- `2007020905`: Individual=0, Lote=1095, API=0 → Total=1095/500000=0,2%
- `2015092301`: Individual=0, Lote=1095, API=0 → Total=0/500000=0,0%
- `2021093001`: Individual=5816, Lote=48541, API=14339870 → Total=14394227/3600000=399,8%
- `2010062401`: Individual=7.718, Lote=1.202, API=62.605 → Total=71.525/180.000=39,74%
