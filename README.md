# Monitor de Contratos (POC)

Ferramenta de automação para monitoramento de vencimento e consumo de contratos, com notificações via e-mail.

## Descrição

O projeto realiza a leitura de uma planilha Excel contendo metadados de contratos e consulta um banco de dados MySQL para obter o consumo atualizado de cada contrato. Com base em thresholds configuráveis, o sistema identifica contratos próximos do vencimento ou com uso excessivo e envia alertas para os administradores.

## Estrutura do Projeto

- `src/main.py`: Ponto de entrada da aplicação.
- `src/core/analyzer.py`: Lógica central de comparação entre limites e uso real.
- `src/readers/`: Módulos para leitura de dados (Excel e MySQL).
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
DB_USER=root
DB_PASS=
DB_DATABASE=meubanco

# Email
SMTP_HOST=127.0.0.1
SMTP_PORT=25
SMTP_USER=
SMTP_PASS=
SMTP_USE_TLS=False
EMAIL_FROM=monitor@localhost
EMAIL_TO="admin@localhost,diretor@localhost,responsavel@localhost"

# Caminhos
EXCEL_PATH=docs/Softon_Controle de acessos_clientes_VF.xlsx
EXCEL_SHEET=

# Parâmetros de Alerta
ALERT_DAYS_BEFORE_EXPIRATION=30
ALERT_USAGE_PERCENTAGE=0.8
DEBUG=False
```

## Estrutura de Banco de Dados

Cada linha da planilha Excel representa uma unidade de contrato única (`Codigo Instituicao` + `Numero Contrato` + `Serviços Contratados`).
Para cada linha, o sistema executa uma query `UNION ALL` que apura a volumetria de acesso separada por tipo de serviço.
O total exibido no relatório é a soma apenas dos serviços contratados naquela linha da planilha.

### Tabela: `TB_LOG_ACESSOS_CONSOL`

Usada para os serviços **API** e **Individual**:

| Campo | Uso |
|---|---|
| `COD_CONTA` | Código da instituição. Se houver *Cod Compartilhado*, ambos os códigos são filtrados via `IN`. |
| `DATA_ACESSO` | Filtra o período com limite superior exclusivo: `>= inicio_ciclo` e `< fim_ciclo_exclusivo`. |
| `QT_ACESSOS` | Quantidade somada no período. |
| `COD_PRODUTO` | `IS NOT NULL` → contabilizado como **API**; `IS NULL` → contabilizado como **Individual**. |

### Tabela: `TB_POWERMATCH_PROC`

Usada para o serviço **Lote**:

| Campo | Uso |
|---|---|
| `COD_INSTITUICAO` | Código da instituição (mesmo filtro de `IN` da outra tabela). |
| `DT_CONCLUSAO` | Filtra o período (`IS NOT NULL`, `>= inicio_ciclo` e `< fim_ciclo_exclusivo`). |
| `QT_LINES` | Quantidade de linhas processadas, somadas como acessos do tipo Lote. |

## Regras de Cálculo

- Os serviços da planilha são normalizados para as chaves `Individual`, `Lote` e `API`.
- Não use `.title()` para normalizar serviços, pois `API` viraria `Api` e deixaria de somar corretamente.
- O relatório mostra somente os serviços contratados naquela linha, mesmo que a consulta retorne acessos de outros tipos para a mesma instituição.
- `acessos_realizados` deve ser igual à soma do `acessos_breakdown` filtrado pelos serviços contratados.
- Limite `ILIMITADO` na planilha é preservado como ilimitado, não vira `0`.
- Para contratos ilimitados, o relatório mostra limite `∞` e `Consumo do Limite` como `-`.
- Campos vazios ou `NaN` em `Valor Excedente` são exibidos como `-`.
- A data final exibida ao usuário é inclusiva (`fim_ciclo_exclusivo - 1 dia`), mas a query usa o limite superior exclusivo.
- Contadores, limites e percentuais são formatados no padrão brasileiro: milhar com `.` e decimal com `,`.
- No relatório HTML, a linha `Total` mantém o alinhamento dos valores de serviço e o símbolo `∞` é destacado em negrito.

## Uso

Para rodar a rotina de monitoramento:

```bash
./run.sh
```

Execução normal: processa todos os contratos e envia e-mail apenas se houver alerta de vencimento ou consumo.

Para ativar logs detalhados:

```bash
./run.sh --debug
```

Para enviar relatório completo de todos os contratos processados:

```bash
./run.sh --full
```

Modo de teste por instituição (executa apenas contratos da instituição informada e envia e-mail normalmente):

```bash
./run.sh --test 12345
```

O modo `--test` também considera `Cod Compartilhado`, força relatório completo para o código filtrado e ativa logs detalhados automaticamente.

Parâmetros podem ser combinados:

```bash
./run.sh --debug --test 2010062401
./run.sh --debug --full
```

Ou diretamente via `uv`:

```bash
uv run src/main.py
```

Com opções:

```bash
uv run src/main.py --debug
uv run src/main.py --full
uv run src/main.py --test 12345
```

## Verificação de Resultados

Para validar alterações de cálculo sem enviar e-mail real, prefira testes automatizados e, quando necessário, execução com SMTP mockado em scripts locais.

Comando padrão de testes:

```bash
uv run pytest
```

Casos já validados nesta base:

| Instituição | Resultado validado |
|---|---|
| `2013032602` | `Individual, API` ilimitado soma `Individual + API`; limite aparece como `∞`; linha `Lote` exibe apenas `Lote`; `Valor Excedente` vazio aparece como `-`. |
| `2010062401` | `Individual + Lote + API = 71.525`; limite `180.000`; consumo `39,74%`. |

## Logs

O projeto usa logging em console e arquivo, com rotação diária e retenção.

Variáveis relevantes no `.env`:

```bash
LOG_DIR=logs
LOG_RETENTION_DAYS=30
```

- Arquivo principal: `logs/monitor.log`
- Rotação: diária
- Retenção: `LOG_RETENTION_DAYS` dias

## Desenvolvimento

Para formatar o código, apenas quando solicitado explicitamente:
```bash
uv run ruff format .
```

Para rodar o linter, apenas quando a dependência estiver disponível no ambiente:
```bash
uv run ruff check .
```
