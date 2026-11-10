# BI Rede Duarte

Aplicação web para consulta e gestão da rede de prestadores, evoluída sobre o código recebido. Backend FastAPI/SQLAlchemy, PostgreSQL em produção e SQLite local; interface estática responsiva servida pelo próprio FastAPI.

## Estrutura

- `app/main.py`: rotas, autenticação, CRUD, importação e exportação XLSX/CSV.
- `app/analytics.py`: identidade única e normalização analítica, mapeamento UF/região e agregações.
- `app/models.py`, `app/database.py`, `app/config.py`, `app/security.py`: persistência, configuração e sessão/autenticação.
- `app/static/`: HTML, CSS, JavaScript e logo Duarte recebida.
- `tests/`: testes de regras e checagem estrutural.

## Regras analíticas

- Os dados originais de cada linha continuam preservados; normalização ocorre somente em memória, na análise.
- Prestador único: documento normalizado para dígitos se tiver 11 ou 14 dígitos e não for uma sequência de um único dígito. Os dígitos verificadores não são recalculados para não rejeitar registros históricos por um erro de DV. Documento vazio/inválido usa razão social normalizada (acentos, pontuação, caixa e espaços ignorados). Sem documento válido e sem razão social, a linha permanece identificada individualmente pelo ID interno.
- Um mesmo documento não se divide por diferenças de razão social. Documento e razão social são namespaces distintos e não são misturados.
- Especialidades são agrupadas por texto sem acentos, pontuação, diferenças de caixa ou espaços. Um mesmo prestador pode aparecer em várias especialidades distintas, mas só uma vez dentro de cada especialidade.
- A região é classificada pela UF: siglas e nomes de estados brasileiros são aceitos. Município, sigla desconhecida ou UF vazia não são inferidos e caem em `NÃO INFORMADO`. Se um prestador tiver várias linhas, a região usa sua primeira UF válida por ID; se nenhuma for válida, entra em `NÃO INFORMADO`. Isso mantém a partição regional igual ao total único.
- A métrica “Tipos de especialidade” está intencionalmente pendente. O anexo oficial de mapeamento não foi enviado; o sistema não cria categorias. O endpoint de auditoria sinaliza o estado e lista valores normalizados enquanto o mapeamento oficial não estiver disponível.

## Execução local

Requer Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Para rodar os testes automatizados, instale também as dependências de desenvolvimento:
pip install -r requirements-dev.txt
```

Sem `DATABASE_URL`, o sistema usa SQLite em `data/bi_rede_duarte.sqlite3`. Para criar o primeiro usuário administrador, configure variáveis de ambiente privadas antes de iniciar:

```text
ADMIN_BOOTSTRAP_CPF=<CPF válido do administrador>
ADMIN_BOOTSTRAP_PASSWORD=<senha privada com no mínimo 12 caracteres>
ADMIN_BOOTSTRAP_NAME=<nome do administrador, opcional>
SESSION_SECRET=<segredo aleatório longo>
```

Não grave segredos neste repositório. Após criar a conta master, remova a senha de bootstrap do ambiente. Inicie a aplicação:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Acesse `http://127.0.0.1:8000`; saúde em `/api/health`.

## Painel, filtros e auditoria

O endpoint autenticado `/api/dashboard` alimenta os cartões e os gráficos. Os filtros de região, UF, município e especialidade são aplicados antes da deduplicação e todos os totais/agregações da resposta usam a mesma função central. O painel exibe prestadores únicos, quantidade de especialidades normalizadas, prioridade, municípios, participação regional, estados presentes e os rankings TOP 10/10 menores sem especialidades com zero registros.

O indicador antigo de status ativo e o gráfico de status foram retirados da análise e da interface; a coluna original continua preservada para consulta e exportação. A interface usa barras HTML/CSS nativas, sem biblioteca externa de gráficos; valores e tooltips vêm da API, sem dados simulados. Não foi introduzido novo CDN de visualização.

O endpoint `GET /api/admin/data-audit` é restrito ao Administrador Master e informa linhas ativas, prestadores únicos por critério, duplicidades não contadas, registros e prestadores sem UF válida, valores normalizados de especialidade, pendência dos tipos oficiais e conciliação da soma regional.

Uma cópia em cache local por processo dura até 45 segundos e é invalidada após importação, inclusão, edição e desativação. Em implantação com múltiplas réplicas, cada processo mantém seu próprio cache; haverá até 45 segundos de diferença entre réplicas após uma gravação.

## Importação e preservação

Como antes, a importação aceita XLSX de até 25 MB, procura a aba `BANCO REDE` (ou usa a última aba), mostra uma prévia e requer confirmação administrativa. Bloqueia o mesmo arquivo por hash exato, mas não apaga nem deduplica as linhas importadas: a deduplicação é apenas da camada analítica. Exporte/ faça backup e valide a prévia antes de importar a planilha real.

## Testes

```bash
pip install -r requirements-dev.txt
pytest -q
python tests/smoke_test.py
node --check app/static/app.js
```

Os testes usam amostras artificiais anonimizadas da regra, não a base real da Rede Duarte. Nesta entrega, 11 funções de teste foram executadas diretamente e passaram; o runner `pytest` não pôde ser executado porque `pytest` não estava disponível e a instalação no ambiente foi bloqueada. O smoke test, a análise sintática Python, `node --check` e a validação estrutural do HTML passaram. A verificação responsiva automatizada checa breakpoints e a regra de ocultação do login, mas não substitui inspeção visual em navegadores/dispositivos. O ambiente também não tinha FastAPI/SQLAlchemy instalados, portanto as rotas e a integração com o banco não foram inicializadas. Um ensaio sintético de 63.007 linhas (50.000 identidades simuladas) concluiu a agregação em 1,075 s neste ambiente; não representa a planilha nem a infraestrutura de produção. Não foi fornecida planilha real; não foi possível conferir valores reais nem executar importação integral.

## Publicação no Railway — passo a passo

Nada foi publicado por esta entrega. Para publicar manualmente:

1. Faça backup do serviço atual e valide esta versão em homologação.
2. Conecte o repositório ao Railway e mantenha o comando de início de `railway.json`: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Configure um serviço PostgreSQL e `DATABASE_URL`; configure `SESSION_SECRET`, `COOKIE_SECURE=1`, `ENVIRONMENT=production` e, se necessário, `DATA_DIR` em volume persistente.
4. Configure temporariamente `ADMIN_BOOTSTRAP_CPF`, `ADMIN_BOOTSTRAP_PASSWORD` e `ADMIN_BOOTSTRAP_NAME` para a primeira inicialização, usando segredos próprios. Depois de criado o master, remova a senha de bootstrap.
5. Faça o deploy e confira `/api/health`.
6. No navegador, use `Ctrl+Shift+R`, autentique-se, valide permissões e tela de auditoria, carregue primeiro uma planilha de teste, confira a prévia e depois importe a planilha real. Confira os indicadores, filtros e regiões; compare a auditoria com os totais esperados.
7. Confirme os backups do PostgreSQL e a política de retenção; não use SQLite local como banco principal em produção.

## Segurança

Preservadas as rotas/perfis atuais: Administrador Master, Consulta e Operador; sessão com cookie protegido, hashing PBKDF2 e limitação de tentativas. O administrador vê documentos e campos restritos, então mantenha acesso, rede, backups e exportações limitados e considere a governança LGPD. O projeto não inclui `.env`, credenciais, banco real ou ambiente virtual.
