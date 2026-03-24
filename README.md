# Monitor de Contratos (POC)

Ferramenta de automação para monitoramento de vencimento e consumo de contratos, com notificações via e-mail.

## Descrição

O projeto realiza a leitura de uma planilha Excel contendo metadados de contratos e consulta um banco de dados Access para obter o consumo atualizado de cada contrato. Com base em thresholds configuráveis, o sistema identifica contratos próximos do vencimento ou com uso excessivo e envia alertas para os administradores.

## Estrutura do Projeto

- `src/main.py`: Ponto de entrada da aplicação.
- `src/core/analyzer.py`: Lógica central de comparação entre limites e uso real.
- `src/readers/`: Módulos para leitura de dados (Excel e Access).
- `src/notifications/`: Gerenciamento de alertas e envio de e-mails.
- `src/config.py`: Centralização de variáveis de ambiente e configurações.
- `docs/`: Documentação adicional e arquivos de suporte.

## Requisitos

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) para gerenciamento de pacotes.

## Instalação

1. Clone o repositório.
2. Certifique-se de ter o `uv` instalado.
3. Sincronize as dependências:
   ```bash
   uv sync
   ```

## Configuração

Crie um arquivo `.env` na raiz do projeto seguindo o modelo `.env.example`:

```bash
# Banco de Dados
DB_HOST=localhost
DB_DATABASE=meubanco

# Email
SMTP_HOST=127.0.0.1
SMTP_PORT=25
EMAIL_FROM=monitor@localhost
EMAIL_TO="admin@localhost,diretor@localhost,responsavel@localhost"

# Caminhos
EXCEL_PATH=docs/Softon_Controle de acessos_clientes_VF.xlsx

# Parâmetros de Alerta
ALERT_DAYS_BEFORE_EXPIRATION=30
ALERT_USAGE_PERCENTAGE=0.8
DEBUG=False
```

## Estrutura de Banco de Dados

Cada linha da planilha Excel representa uma unidade de contrato única (`Codigo Instituicao` + `Numero Contrato` + `Serviços Contratados`).
Para cada linha, o sistema executa uma query `UNION ALL` que apura a volumetria de acesso separada por tipo de serviço.

### Tabela: `TB_LOG_ACESSOS_CONSOL`

Usada para os serviços **API** e **Individual**:

| Campo | Uso |
|---|---|
| `COD_CONTA` | Código da instituição. Se houver *Cod Compartilhado*, ambos os códigos são filtrados via `IN`. |
| `DATA_ACESSO` | Filtra o período (operadores `>=` início e `<` o dia seguinte ao fim para inclusividade). |
| `QT_ACESSOS` | Quantidade somada no período. |
| `COD_PRODUTO` | `IS NOT NULL` → contabilizado como **API**; `IS NULL` → contabilizado como **Individual**. |

### Tabela: `TB_POWERMATCH_PROC`

Usada para o serviço **Lote**:

| Campo | Uso |
|---|---|
| `COD_INSTITUICAO` | Código da instituição (mesmo filtro de `IN` da outra tabela). |
| `DT_CONCLUSAO` | Filtra o período (`IS NOT NULL` e operadores `>=` e `<`). |
| `QT_LINES` | Quantidade de linhas processadas, somadas como acessos do tipo Lote. |

## Uso

Para rodar a rotina de monitoramento:

```bash
./run.sh
```

Ou diretamente via `uv`:

```bash
uv run src/main.py
```

## Desenvolvimento

Para formatar o código:
```bash
uv run ruff format .
```

Para rodar o linter:
```bash
uv run ruff check .
```
