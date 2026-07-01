# OPENCODE.md - Instruções do Projeto

Este projeto é uma automação Python para monitoramento de contratos, leitura de planilha Excel, consulta MySQL e envio de relatórios por e-mail.

## Contexto obrigatório

- Antes de alterar cálculo, consulta SQL, relatório ou teste, leia `hints/PROJECT_CONTEXT.md`.
- Use `CLAUDE.md` como guia principal de comandos e padrões técnicos já consolidados.
- Não leia, copie ou exponha conteúdo de `.env`; use `src/config.py` e variáveis de ambiente como abstração.
- Não altere planilhas em `docs/` sem pedido explícito.

## Comandos seguros

- Sincronizar dependências: `uv sync`.
- Rodar testes neste ambiente: `uv run python -m pytest`.
- Executar rotina: `./run.sh [--debug] [--full] [--test CODIGO]`.
- Validar relatório/e-mail com segurança: mockar `smtplib.SMTP` e `smtplib.SMTP_SSL`.

## Regras críticas

- Consultas SQL de período usam intervalo aberto, sem `BETWEEN`.
- Para ciclos em andamento, a apuração de acessos usa dados menores que `TODAY()` porque a base consolidada fecha no dia anterior.
- As fontes de acesso devem usar corte superior consistente entre `API`, `Individual` e `Lote`.
- `acessos_realizados` soma somente os serviços contratados na linha da planilha.
- Serviços válidos no relatório: `Individual`, `Lote` e `API`; não use `.title()` para normalizar serviços.
- `ILIMITADO` deve permanecer ilimitado e aparecer como `∞` no relatório.
- Valores numéricos no relatório usam padrão brasileiro.

## Estado atual importante

- `src/readers/access_reader.py` calcula `effective_end_param` para aplicar o mesmo corte superior nas 3 consultas.
- `src/core/analyzer.py` diferencia o fim do ciclo contratual do fim efetivo usado na contagem.
- Próxima melhoria planejada: separar explicitamente no log e no relatório os conceitos `Data referência de corte`, `Início período de Corte`, `Fim período de Corte` e `Fim do Contrato`.
