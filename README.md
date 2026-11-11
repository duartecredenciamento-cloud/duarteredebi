# BI Rede Duarte — atualização de performance

Projeto completo FastAPI/SQLAlchemy do BI, com a identidade visual Duarte, login protegido, indicadores, análises territoriais e pesquisa de prestadores.

## Alterações desta versão
- Cache limitado por tempo e quantidade para resultados agregados do dashboard, invalidado após importações e mutações cadastrais.
- Cache da interface por 30 segundos ao retornar ao panorama, com deduplicação de requisições idênticas em andamento e cancelamento de consultas antigas ao trocar filtros.
- Menos normalizações repetidas durante agregações; contagens e identidade dos prestadores permanecem centralizadas na camada analítica.
- Lista de especialidades completa e ordenada por prestadores únicos, com rolagem virtual para manter poucas linhas no DOM ao mesmo tempo.
- Mapa reutiliza as geometrias e o desenho vetorial após o primeiro carregamento.
- Removido o carregamento redundante da folha de fontes; sem dependências novas.
- A distribuição de tipos continua lendo exclusivamente a coluna `TIPO`.

## Estrutura
- `app/` — API, autenticação, modelos, análises e recursos estáticos.
- `tests/` — testes analíticos e verificações estruturais.
- `requirements.txt` — dependências já utilizadas pelo projeto.
- `railway.json` — configuração existente do serviço.

## Execução local
Instale as dependências de `requirements.txt`, configure as variáveis de ambiente exigidas pelo projeto (incluindo a URL do banco e segredo da sessão) e inicie com `uvicorn app.main:app`. Não configure credenciais reais em código-fonte.

## Testes
Execute `pytest -q` no diretório do projeto. Antes da implantação, valide também a API e o banco de homologação; esta entrega não altera nem publica dados de produção.

## Cache
Os agregados permanecem em memória por até 45 segundos, com limite de 24 combinações de filtros. O cache é local a cada processo e é invalidado após gravações feitas pela própria aplicação; mudanças externas são refletidas ao expirar o prazo.
