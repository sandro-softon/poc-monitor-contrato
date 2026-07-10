# OPENCODE.md - Instruções do Projeto

Este projeto é uma automação Python para monitoramento de contratos, com interface web para CRUD e envio de relatórios por e-mail.

## Stack

```text
Frontend: React + Vite + Ant Design v6
Backend:  FastAPI + SQLAlchemy 2.x + pymysql
Banco:    MySQL
Batch:    Python CLI (mysql-connector-python)
Estado:   Dockerizado (docker compose)
```

## Contexto obrigatório

- Antes de alterar cálculo, consulta SQL, relatório ou teste, leia `hints/PROJECT_CONTEXT.md`.
- Use `CLAUDE.md` como guia principal de comandos e padrões técnicos já consolidados.
- Não leia, copie ou exponha conteúdo de `.env`; use `src/config.py` e variáveis de ambiente como abstração.
- Não altere planilhas em `docs/` sem pedido explícito.

## Comandos seguros

- Sincronizar dependências: `uv sync`.
- Rodar testes neste ambiente: `uv run python -m pytest`.
- Executar rotina: `./run.sh [--src excel|db] [--debug] [--full] [--test CODIGO]`.
- Build frontend: `cd web && npm run build`.
- Docker: `docker compose up --build -d`.

## Regras críticas

- `TB_INSTITUICAO` é fonte de verdade para dados gerais do contrato.
- `TB_CONTRATO` contém apenas atributos por serviço.
- Consultas SQL de período usam intervalo aberto, sem `BETWEEN`.
- Serviços válidos: `Individual`, `Lote`, `API`; não use `.title()`.
- `acessos_realizados` soma serviços contratados agrupados por instituição.
- Limite efetivo do grupo = `MAX(limite)` dos serviços da instituição.
- `ILIMITADO` permanece como `∞` no relatório.
- Login via `TB_USUARIOS` (COD_INSTITUICAO=2007011801, STATUS=1).
- Token UUID com 2h de validade.
- Valores numéricos no relatório usam padrão brasileiro.
- Após normalização (Fase 2), serviços são linhas individuais em TB_CONTRATO.
