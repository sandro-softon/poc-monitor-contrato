# Project Context - Monitor de Contratos

Este arquivo registra regras específicas deste projeto para agentes de IA. Ele complementa `CLAUDE.md` e evita regressões nas regras de cálculo do relatório.

## Resumo Funcional

- O processo lê contratos de uma planilha Excel definida em `Config.EXCEL_PATH`.
- Para cada linha da planilha, consulta consumo no MySQL por tipo de serviço.
- Gera alertas por vencimento de ciclo ou consumo acima do threshold.
- Envia relatório por e-mail via SMTP configurado no `.env`.

## Comandos Principais

```bash
./run.sh
./run.sh --debug
./run.sh --full
./run.sh --test CODIGO
./run.sh --debug --test CODIGO
uv run pytest
```

## Regras Criticas De Calculo

- Cada linha da planilha representa uma unidade contratual: `Codigo Instituicao` + `Numero Contrato` + `Serviços Contratados`.
- Serviços aceitos no cálculo: `Individual`, `Lote`, `API`.
- Normalize `api`, `Api` e `API` para `API`.
- Nao use `.title()` para serviços, pois isso quebra a chave `API`.
- O banco pode retornar acessos para todos os tipos, mas o relatório deve exibir e somar somente os serviços contratados naquela linha.
- `acessos_realizados` deve ser igual à soma de `acessos_breakdown` filtrado.
- `ILIMITADO` em `acessos contratados` deve permanecer ilimitado, não `0`.
- Para limite ilimitado, exibir limite `∞` e consumo `-`.
- `Valor Excedente` vazio ou `NaN` deve aparecer como `-`.
- Contadores, limites e percentuais devem ser exibidos no padrão brasileiro: milhar com `.` e decimal com `,`.
- No HTML, a linha `Total` deve manter o alinhamento dos valores de serviço; o `∞` deve ser maior e em negrito, sem deslocar a linha.

## Periodo SQL

- Nao use `BETWEEN`.
- Use limite aberto: `DATA >= inicio_ciclo AND DATA < fim_ciclo_exclusivo`.
- A data final exibida no relatório é humana/inclusiva: `fim_ciclo_exclusivo - 1 dia`.
- `AccessReader.get_accesses_by_service()` recebe `end_date` como limite superior exclusivo; não some mais um dia nesse método.
- Frequências de ciclo suportadas: mensal (1 mês), trimestral (3 meses), semestral (6 meses) e anual (12 meses).

## Fontes De Dados

- `TB_LOG_ACESSOS_CONSOL`: serviços `Individual` e `API`.
- `COD_PRODUTO IS NULL`: `Individual`.
- `COD_PRODUTO IS NOT NULL`: `API`.
- `TB_POWERMATCH_PROC`: serviço `Lote`, somando `QT_LINES`.
- `Cod Compartilhado`, quando preenchido, deve entrar no filtro `IN` junto com `Codigo Instituicao`.

## Validacao Segura

- Para testes automatizados, use `uv run pytest`.
- Para validar corpo de e-mail, mocke `smtplib.SMTP` e `smtplib.SMTP_SSL`.
- Nao envie e-mail real durante verificações locais, salvo pedido explícito.
- Nao altere planilhas em `docs/` sem autorização explícita.
- Nao rode `ruff format` para ajustes esteticos sem autorização explícita.

## Casos Ja Validados

- `2013032602`: `Individual, API` com limite `ILIMITADO` soma `Individual + API`; `Lote` fica em linha separada e exibe apenas `Lote`.
- `2010062401`: `Individual=7.718`, `Lote=1.202`, `API=62.605`, total `71.525`, limite `180.000`, consumo `39,74%` no relatório.
- Amostra de 10 instituições: 14 contratos processados; somas e percentuais validados; relatório gerado com SMTP mockado.
