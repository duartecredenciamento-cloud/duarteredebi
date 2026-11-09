# BI Rede Duarte

Aplicação web para consulta, análise e administração da base de prestadores da Rede Duarte. A interface foi desenhada a partir das cores e dos padrões do sistema enviado: azul institucional, laranja, acentos azuis, navegação lateral e painéis responsivos.

## Incluído

- Login individual por CPF e senha; senhas com hash PBKDF2, sessões no banco e tentativas de acesso limitadas.
- Perfis **Administrador Master**, **Consulta** e **Operador**. O cadastro público fica desativado.
- Pesquisa combinada, paginação no servidor (até 100 linhas por resposta), ficha de prestador e indicadores com gráficos.
- Importação XLSX em duas etapas (prévia e confirmação), com preservação de todas as linhas preenchidas, inclusive semelhantes.
- Exportação de backup CSV e Excel somente para o Administrador Master.
- Exclusão lógica, gestão básica de usuários, registro de ações administrativas e interface adaptável a celular.
- Campos originais mantidos como dados da linha, acrescidos de ID interno próprio; nenhum CNPJ/CPF é usado como chave de deduplicação.

## Requisitos e execução local

Requer Python 3.11 ou mais recente e PostgreSQL para uma implantação persistente. Para uma avaliação local sem PostgreSQL, o sistema usa um SQLite de desenvolvimento, criado em `data/`; não use esse modo como banco de produção.

### Windows (PowerShell)

1. Instale Python e PostgreSQL e crie um banco e usuário para a aplicação.
2. Abra o PowerShell nesta pasta e prepare o ambiente:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

3. Edite `.env`: informe `DATABASE_URL`, `SESSION_SECRET`, `ADMIN_BOOTSTRAP_CPF`, `ADMIN_BOOTSTRAP_PASSWORD` e `COOKIE_SECURE=0` apenas no acesso local por HTTP.
4. Inicie:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

5. Acesse `http://127.0.0.1:8080`. O primeiro Administrador Master é criado no primeiro início de um banco vazio, desde que CPF e senha estejam configurados.

### Linux/macOS

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edite .env e configure PostgreSQL e credenciais privadas
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Para desenvolvimento local com SQLite, deixe `DATABASE_URL` vazio/ausente e configure `COOKIE_SECURE=0`. O modo SQLite é apenas para teste local.

## Importar a planilha fornecida

1. Entre como Administrador Master.
2. Abra **Administração → Importar planilha Excel** e selecione a planilha original `.xlsx`.
3. Confira a aba detectada, a contagem de linhas e as informações de validação; marque a autorização explícita e confirme.
4. A aplicação pula linhas totalmente vazias, registra todas as demais como linhas distintas e recusa uma segunda importação do mesmo arquivo.

A aplicação não deduplica ou consolida organizações, unidades, especialidades ou CNPJs. A conversão de células Excel para a base grava texto para valores e datas ISO, mantendo os nomes originais das colunas. A importação precisa ser testada primeiro em homologação, comparando a contagem com a origem e verificando uma exportação de backup.

## Deploy (Railway ou equivalente)

- Use PostgreSQL persistente e configure `DATABASE_URL` fornecida pelo serviço.
- Configure `SESSION_SECRET` aleatória e persistente, `COOKIE_SECURE=1`, credenciais iniciais privadas e um limite adequado para `MAX_IMPORT_MB`.
- Monte volume persistente para `DATA_DIR` (arquivos temporários da prévia de importação). Banco de produção e arquivos do usuário não devem depender do disco efêmero do contêiner.
- Aplique HTTPS, restrinja acesso administrativo, faça backup automático do PostgreSQL e teste a restauração.
- Revise o domínio, as origens confiáveis, as políticas de acesso e a conformidade LGPD com a equipe responsável antes de publicar.

O arquivo `railway.json` traz o comando de inicialização e o health check. O pacote é o código-fonte e não publica a aplicação, não acessa a instância atual do Duarte Repay e não migra dados automaticamente.

## Segurança e limites conhecidos

- Usuários de consulta não veem observações internas, CPF/CNPJ integral, certos contatos pessoais, nem recebem a exportação da base.
- O Administrador Master pode exportar todos os registros ativos; ações relevantes entram na trilha de auditoria.
- A consulta é limitada e paginada no servidor. Não foi incluída recuperação pública de senha: ela deve ser feita por processo administrativo seguro, sem revelar se um CPF existe.
- A conta inicial exige CPF válido e senha definida por ambiente. Não há senha padrão no pacote.
- A tela de consulta não substitui revisão de qualidade; dados da origem com formatos inconsistentes permanecem como enviados.
- Antes de produção, solicite revisão independente de segurança, teste a importação/backup com cópia da base e configure retenção de logs e backups.

## Testes

```bash
python tests/smoke_test.py
```

## Estrutura

- `app/main.py` — API, banco, autenticação, pesquisa, importação, exportação e auditoria.
- `static/` — interface web responsiva e marca Duarte em SVG.
- `requirements.txt` — dependências Python.
- `.env.example` — variáveis de configuração.
- `railway.json` — configuração inicial de deploy.
- `tests/smoke_test.py` — verificação básica das funções principais.
