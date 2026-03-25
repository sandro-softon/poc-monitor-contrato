# CLAUDE.md - Project Context for AI Agents

Este arquivo fornece diretrizes técnicas e comandos básicos para auxiliar agentes de IA no desenvolvimento deste projeto.

## Comandos Úteis

### Ambiente e Dependências
Este projeto utiliza o `uv` para gerenciamento de ambiente virtual e dependências.

- `uv sync`: Sincroniza o ambiente com as dependências do `pyproject.toml`.
- `uv add <pacote>`: Adiciona uma nova dependência.
- `./run.sh [--full]`: Executa a rotina de monitoramento (opcionalmente com relatório completo).
- `uv run src/main.py [--full]`: Executa o ponto de entrada principal diretamente.
- `uv pip install -e .`: Instala o projeto em modo editável (permite rodar `python3 src/main.py` sem PYTHONPATH).

### Qualidade de Código
- `uv run ruff format .`: Formata o código seguindo as regras do projeto.
- `uv run ruff check .`: Roda o linter para identificar problemas.

## Diretrizes de Código

- **Padrões de Nomenclatura**: use `snake_case` para variáveis, funções e arquivos; `PascalCase` para classes.
- **Tipagem**: Sempre que possível, utilize Type Hints (ex: `def func(a: int) -> str:`).
- **Tratamento de Erros**: Utilize blocos `try-except` em pontos críticos, especialmente em operações de I/O (leitura de arquivos, banco de dados, envio de e-mails).
- **Configuração**: Nunca coloque strings sensíveis (senhas, hosts) diretamente no código. Utilize a classe `Config` em `src/config.py`, que lê do arquivo `.env`.
- **Imports**: Prefira caminhos absolutos baseados na raiz `src` (ex: `from src.config import Config`). Após `uv pip install -e .`, o Python reconhecerá a pasta `src` automaticamente.
- **Intervalos de Data**: Para consultas SQL, evite `BETWEEN`. Use a lógica de intervalo aberto: `DATA >= inicio AND DATA < dia_seguinte_ao_fim`. Isso garante inclusividade total sem depender da precisão de tempo (HH:MM:SS) do DB.

## Estrutura do Projeto
- `src/main.py`: Orquestrador da rotina de monitoramento.
- `src/core/analyzer.py`: Contém a lógica de comparação entre limites e uso.
- `src/readers/`: Classes especializadas em extrair dados de fontes externas (Excel, Access).
- `src/notifications/`: Módulos para disparo de alertas.
