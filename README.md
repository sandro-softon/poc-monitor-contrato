# Monitor de Contratos

Ferramenta de automação para monitoramento de vencimento e consumo de contratos, com interface web para CRUD e notificações via e-mail.

## Instalação Rápida (Docker)

### Pré-requisitos

- Git
- Docker + Docker Compose
- Acesso a um banco MySQL com as tabelas `TB_INSTITUICAO`, `TB_CONTRATO`, `TB_USUARIOS`

### Passos

```bash
# 1. Clonar
git clone <url-do-repositorio> monitor-contratos
cd monitor-contratos

# 2. Configurar ambiente
cp .env.example .env
# Editar .env com as credenciais do MySQL:
#   DB_HOST, DB_USER, DB_PASS, DB_DATABASE
#   SMTP_HOST, SMTP_USER, SMTP_PASS (para envio de e-mail)

# 3. Subir
docker compose up --build -d

# 4. Acessar
# Frontend: http://localhost:5173
# API:      http://localhost:8000/api/health
# Login:    usuário e senha da tabela TB_USUARIOS
#           (COD_INSTITUICAO = 2007011801, STATUS = 1)
```

## Instalação Manual (sem Docker)

### Pré-requisitos

- Python >= 3.12
- Node.js >= 24
- MySQL acessível

### Backend

```bash
# 1. Clonar
git clone <url-do-repositorio> monitor-contratos
cd monitor-contratos

# 2. Ambiente Python
pip install uv
uv sync

# 3. Configurar
cp .env.example .env
# Editar .env com credenciais MySQL e SMTP

# 4. Iniciar API
uv run uvicorn src.web_api.app:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
# Em outro terminal
cd web
npm install
npm run dev
```

### CLI (processamento batch)

```bash
uv run python src/main.py --src db
uv run python src/main.py --src db --test 2007020905
```

## Primeiro Acesso

1. Acessar `http://localhost:5173`
2. Logar com credenciais da `TB_USUARIOS` (ex: `admin` / `dtfasof02`)
3. Navegar entre **Contratos** e **Instituições** no menu lateral
4. Usar o seletor de temas no canto superior direito para alternar visual

## Docker: Comandos Úteis

```bash
docker compose logs -f api    # Logs da API
docker compose logs -f web    # Logs do frontend
docker compose restart api    # Reiniciar API
docker compose down           # Parar tudo
```

## Variáveis de Ambiente (.env)

| Variável | Padrão | Descrição |
|---|---|---|
| `DB_HOST` | `localhost` | Host do MySQL |
| `DB_USER` | `root` | Usuário MySQL |
| `DB_PASS` | `""` | Senha MySQL |
| `DB_DATABASE` | `meubanco` | Nome do banco |
| `SMTP_HOST` | `127.0.0.1` | Servidor SMTP |
| `SMTP_PORT` | `25` | Porta SMTP |
| `SMTP_USER` | `""` | Usuário SMTP |
| `EMAIL_FROM` | `monitor@localhost` | Remetente |
| `EMAIL_TO` | `admin@localhost` | Destinatários (vírgula) |
| `CONTRACT_SOURCE` | `db` | Fonte (`excel` ou `db`) |
| `DEBUG` | `False` | Modo debug |

## Estrutura do Projeto

- `src/main.py`: Ponto de entrada da aplicação.
- `src/core/analyzer.py`: Lógica central de comparação entre limites e uso real.
- `src/readers/`: Módulos para leitura de dados (Excel e MySQL).
- `src/notifications/`: Gerenciamento de alertas e envio de e-mails.
- `src/config.py`: Centralização de variáveis de ambiente e configurações.
- `docs/`: Documentação adicional e arquivos de suporte.
- `hints/`: orientações versionadas para agentes de IA e manutenção assistida.

## Orientações Para Agentes

Agentes de IA devem considerar os arquivos em `hints/` antes de alterar regras de cálculo, relatórios, consultas SQL ou testes.

O arquivo principal é `hints/PROJECT_CONTEXT.md`, que registra regras funcionais, comandos seguros e casos já validados.

O diretório `.agent/` permanece ignorado por poder conter arquivos locais do toolkit, configurações ou dados sensíveis.

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
- Frequências suportadas para ciclo de corte: mensal, trimestral, semestral e anual.
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

## POC Headroom

Se quiser testar compressão de contexto em um fluxo parecido com o deste projeto, rode a POC local:

```bash
uv run --with headroom-ai python scripts/headroom_poc.py
```

O script monta um payload representativo com logs, SQL e rascunho de e-mail, e imprime:

- caracteres brutos vs comprimidos
- tokens antes vs depois
- tokens salvos e taxa de compressão
- uma prévia do payload resultante


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
