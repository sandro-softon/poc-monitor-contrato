# CLAUDE.md - Project Context for AI Agents

Este arquivo fornece diretrizes técnicas e comandos básicos para auxiliar agentes de IA no desenvolvimento deste projeto.

## Comandos Úteis

### Ambiente e Dependências
Este projeto utiliza o `uv` para gerenciamento de ambiente virtual e dependências.

- `uv sync`: Sincroniza o ambiente com as dependências do `pyproject.toml`.
- `uv add <pacote>`: Adiciona uma nova dependência.
- `./run.sh [--debug] [--full] [--test CODIGO]`: Executa a rotina de monitoramento, repassando argumentos para o Python.
- `uv run src/main.py [--debug] [--full] [--test CODIGO]`: Executa o ponto de entrada principal diretamente.
- `uv pip install -e .`: Instala o projeto em modo editável (permite rodar `python3 src/main.py` sem PYTHONPATH).

### Qualidade de Código
- `uv run ruff format .`: Formata o código seguindo as regras do projeto. Não execute para ajustes estéticos sem solicitação explícita.
- `uv run ruff check .`: Roda o linter para identificar problemas, quando a dependência estiver disponível.
- `uv run pytest`: Executa a suíte de testes.

## Diretrizes de Código

- **Contexto Complementar**: Antes de alterar regras de cálculo, relatórios, consultas SQL ou testes, consulte `hints/PROJECT_CONTEXT.md`.
- **Padrões de Nomenclatura**: use `snake_case` para variáveis, funções e arquivos; `PascalCase` para classes.
- **Tipagem**: Sempre que possível, utilize Type Hints (ex: `def func(a: int) -> str:`).
- **Tratamento de Erros**: Utilize blocos `try-except` em pontos críticos, especialmente em operações de I/O (leitura de arquivos, banco de dados, envio de e-mails).
- **Configuração**: Nunca coloque strings sensíveis (senhas, hosts) diretamente no código. Utilize a classe `Config` em `src/config.py`, que lê do arquivo `.env`.
- **Imports**: Prefira caminhos absolutos baseados na raiz `src` (ex: `from src.config import Config`). Após `uv pip install -e .`, o Python reconhecerá a pasta `src` automaticamente.
- **Intervalos de Data**: Para consultas SQL, evite `BETWEEN`. Use a lógica de intervalo aberto: `DATA >= inicio_ciclo AND DATA < fim_ciclo_exclusivo`. A data final exibida ao usuário deve ser `fim_ciclo_exclusivo - 1 dia`.
- **Banco de Dados**: O consumo é consultado em MySQL via `mysql-connector-python`. A classe `AccessReader` mantém nome legado, mas não acessa banco Access.
- **Planilha**: A entrada vem do Excel em `Config.EXCEL_PATH`; `Config.EXCEL_SHEET` pode fixar a aba, senão o leitor escolhe a primeira aba com colunas relevantes.
- **Logs**: O projeto grava logs em console e arquivo (`LOG_DIR`), com retenção configurável por `LOG_RETENTION_DAYS`.
- **Modo Teste**: `--test CODIGO` filtra contratos por `Codigo Instituicao` (e também `Cod Compartilhado`), força relatório completo para o filtro e envia e-mail normalmente.
- **Serviços Contratados**: Normalize serviços para as chaves exatas `Individual`, `Lote` e `API`. Não use `.title()` para serviços, pois `API` viraria `Api`.
- **Total de Acessos**: `acessos_realizados` deve somar apenas os serviços contratados na linha da planilha. O `acessos_breakdown` usado pelo relatório deve ser filtrado para esses serviços.
- **Limites Ilimitados**: Preserve `ILIMITADO` como limite ilimitado. Não converta para `0`; nesse caso, não calcule percentual de consumo, exiba limite como `∞` e `Consumo do Limite` como `-`.
- **Valores Vazios**: `NaN` ou vazio em `Valor Excedente` deve ser exibido como `-` no relatório.
- **Formatação Numérica**: No relatório, formate contadores, limites e percentuais no padrão brasileiro: milhar com `.` e decimal com `,`.
- **Relatório HTML**: A linha `Total` deve manter o alinhamento dos valores de `Individual`, `Lote` e `API`; para limite ilimitado, o símbolo `∞` deve aparecer em negrito e maior que o texto, sem deslocar a linha.
- **Relatório de Período**: A query SQL usa limite superior exclusivo, mas a data final exibida no relatório é apresentada como o dia anterior (limite inclusivo humano).
- **Testes de Relatório**: Ao validar e-mails, prefira mockar `smtplib.SMTP`/`SMTP_SSL` para não enviar e-mail real.

## Estrutura do Projeto
- `src/main.py`: Orquestrador da rotina de monitoramento.
- `src/core/analyzer.py`: Contém a lógica de comparação entre limites e uso.
- `src/core/date_utils.py`: Calcula ciclos de contrato conforme frequência.
- `src/readers/`: Classes especializadas em extrair dados de fontes externas (Excel e MySQL).
- `src/notifications/`: Módulos para disparo de alertas.
- `tests/`: Testes automatizados de leitura da planilha e regras de datas.

## Casos Validados Nesta Sessão
- `2013032602`: contrato `Individual, API` com limite `ILIMITADO` soma apenas `Individual + API`, exibe limite `∞`; contrato `Lote` exibe apenas `Lote`.
- `2010062401`: contrato `Individual, Lote, API` validado com total `71.525`, limite `180.000` e consumo `39,74%` no relatório.
- Amostra de 10 instituições validada com SMTP mockado, totalizando 14 contratos processados, com somas e percentuais consistentes.
