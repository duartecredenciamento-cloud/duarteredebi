# BI Rede Duarte

Aplicação web para consulta e gestão da base de prestadores, preparada para PostgreSQL e implantação em Railway ou ambiente equivalente. Cada linha importada recebe um identificador próprio; registros repetidos não são consolidados nem apagados automaticamente.

## O que está incluído

- Login individual por CPF e senha, bloqueio temporário após tentativas falhas, alteração de senha do próprio usuário e redefinição administrativa; perfis `admin`, `consulta` e `operador`.
- Dashboard com contagens e gráficos agregados, sem carregar a planilha inteira no navegador.
- Pesquisa com paginação no servidor; os usuários de consulta não recebem observações internas nem alguns campos pessoais/restritos.
- Manutenção administrativa dos registros, desativação lógica, importação XLSX com prévia e confirmação e exportação XLSX/CSV restrita ao administrador.
- Histórico administrativo de logins, consultas, visualizações, alterações, importações e exportações.
- Interface responsiva com paleta azul e laranja inspirada nos materiais enviados. A imagem de logo não chegou entre os arquivos disponíveis; o pacote usa um monograma tipográfico provisório “D”.

## Execução local

Requer Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Para um teste local, o sistema usa SQLite persistente em `data/bi_rede_duarte.sqlite3` se `DATABASE_URL` não estiver definido. Crie variáveis de ambiente para o primeiro administrador antes de iniciar. O CPF de bootstrap precisa passar na validação, e a senha deve ter pelo menos 12 caracteres.

```bash
# Windows PowerShell (substitua os valores por segredos próprios)
$env:ADMIN_BOOTSTRAP_CPF="CPF_VALIDO"
$env:ADMIN_BOOTSTRAP_PASSWORD="SENHA_LONGA_PRIVADA"
$env:ADMIN_BOOTSTRAP_NAME="Administrador Master"
$env:SESSION_SECRET="CHAVE_ALEATORIA_LONGA"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Acesse `http://127.0.0.1:8000`. A conta master é criada uma única vez, quando ainda não existe administrador e as três variáveis de bootstrap estão configuradas. Depois da criação, remova `ADMIN_BOOTSTRAP_PASSWORD` das configurações do serviço. Não use os exemplos em produção.

## Configuração de produção

1. Crie PostgreSQL gerenciado e configure `DATABASE_URL` com usuário de privilégio mínimo.
2. Configure `SESSION_SECRET` com valor aleatório, `COOKIE_SECURE=1`, `ENVIRONMENT=production` e `DATA_DIR` em volume persistente.
3. Configure as variáveis de bootstrap do primeiro administrador; remova a senha de bootstrap depois do primeiro início.
4. Implante o serviço web e confira `/api/health`. Ative HTTPS, backups do banco e uma rotina de teste de restauração.
5. Faça a primeira importação em homologação e compare a prévia e o total importado antes da produção.

O arquivo `railway.json` inclui comando de inicialização e endpoint de saúde. O volume persistente deve ser montado em `DATA_DIR`, pois as prévias de importação ficam em área privada temporária. Em produção, não use o SQLite local como banco principal e não exponha o diretório de dados.

## Importação da base Excel

Acesse como Administrador Master → Administração → Importar planilha. O limite configurado atualmente é de **25 MB por arquivo XLSX**. Envie a planilha, confira a prévia e confirme. O importador procura a aba `BANCO REDE`, preserva os nomes originais dos campos, converte datas para texto ISO, ignora somente linhas completamente vazias, mantém as linhas repetidas e cria um ID interno. Um arquivo idêntico já importado é bloqueado por impressão digital; arquivos diferentes não sobrescrevem os dados existentes.

A prévia atualmente informa a quantidade de linhas preenchidas e mostra amostras; não representa validação semântica de CNPJ, CEP, UF ou duplicidade. Dados inconsistentes permanecem como recebidos e devem ser revisados por uma pessoa autorizada. Faça backup antes da migração.

## Segurança e limites

- Senhas armazenadas com PBKDF2-HMAC-SHA256; sessão aleatória assinada, cookie `HttpOnly`, `SameSite=Strict`, expiração configurável e hash do token no banco.
- Bloqueio temporário depois de 8 tentativas falhas no intervalo de 15 minutos, com chave derivada do CPF digitado e endereço de origem.
- Rotas de edição, usuários, exportação e importação protegidas no backend por perfil; a interface não é a barreira de segurança.
- As exportações Excel e CSV incluem os campos da base ativa e são exclusivas de administrador; o perfil de consulta não vê observações internas, documentos de identificação nem campos de contato pessoal/comercial definidos como restritos.
- O operador pode editar registros, mas não administrar usuários, desativar registros ou exportar.
- Como parte dos dados é sensível, restrinja rede, contas administrativas, backups e logs; defina base legal, retenção e governança LGPD antes da operação.

Este pacote é o código-fonte e a configuração inicial: não cria uma conta de produção, não provisiona banco/volume, não publica o serviço e não migra automaticamente a planilha. Faça homologação e revisão de segurança antes de disponibilizar a usuários.

## Testes

```bash
python tests/smoke_test.py
node --check app/static/app.js
```

O teste leve verifica a estrutura e sintaxe, mas não substitui teste integrado com PostgreSQL, fluxos de senha, permissões, importação da planilha inteira, exportação, carga ou revisão de segurança. O bloqueio de tentativas é aplicado pelo serviço; em implantação com múltiplas réplicas, complemente com limite compartilhado no proxy ou no provedor de identidade.
