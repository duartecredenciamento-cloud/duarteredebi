# Changelog — BI Rede Duarte

## Evolução analítica

- Criada `app/analytics.py` como camada central para identidade/deduplicação e agregações por prestador único.
- Documento é comparado somente pelos dígitos e aceito analiticamente com 11/14 dígitos não repetidos; o DV não é recalculado. Documento vazio/inválido recorre à razão social normalizada. Se ambos faltarem, mantém-se o ID interno da linha.
- Adicionados normalização de especialidades, TOP 10 e 10 menores, contagens distintas, filtros do dashboard e classificação de UF por região para siglas e nomes de estados.
- UF não reconhecida ou municipalidade no campo UF não é inferida: resulta em `NÃO INFORMADO`. A soma regional é conciliável com a contagem única.
- `/api/dashboard` agora reporta prestadores únicos e omite a antiga métrica de status ativo. A interface substituiu esse cartão por especialidades e removeu a distribuição por status.
- Incluído `/api/admin/data-audit`, restrito a administrador, com reconciliação de linhas, identidade, duplicidades, localidades e especialidades.
- Criados estados visuais distintos para maiores/menores especialidades, percentuais e estados regionais, filtros por região/UF/município/especialidade, contadores animados e layout responsivo.
- Implementado cache analítico local de 45 segundos, invalidado após importação e alterações de registros.
- Criados testes automatizados unitários anonimizados e ampliada a checagem estrutural.

## Preservado

- Framework, stack, autenticação, perfis, senha/sessões, limites de acesso, histórico administrativo, cadastro/edição/desativação lógica, importação com prévia, exportações, start command e healthcheck Railway.
- Campos e linhas brutos importados continuam armazenados sem alteração; deduplicação afeta somente as métricas.
- Identidade visual recebida, logo institucional e tela de login aprovada, incluindo `[hidden]{display:none!important}`.

## Pendências conhecidas

- O anexo oficial de mapeamento de especialidades/tipos não foi enviado. O indicador de tipo fica marcado como pendente e não apresenta contagem presumida.
- Não recebemos a planilha real de prestadores nesta etapa; não há reconciliação ou teste de carga da base de aproximadamente 63 mil linhas.
- 11 funções de teste foram executadas diretamente e passaram; o runner pytest e a integração com FastAPI/SQLAlchemy não puderam ser executados neste ambiente por indisponibilidade/bloqueio de instalação das dependências. A verificação visual em navegadores ainda deve ser feita após deploy/homologação.
- A cache é local a cada processo (não compartilhada entre réplicas).
- Não houve deploy, conexão a serviço Railway, migração de banco ou importação real.
