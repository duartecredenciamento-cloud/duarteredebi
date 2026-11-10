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


## 2.0.0 — Executive Intelligence Duarte

- Reformulação do panorama, navegação lateral recolhível, cabeçalho executivo e layout responsivo.
- Mapa vetorial interativo por UF com seleção de estado, usando agregados centralizados de prestadores únicos e geometrias públicas do IBGE carregadas sob demanda.
- Rankings TOP 10/BOTTOM 10, distribuição por região e tipos oficiais com percentuais, estados sem registros identificados como tais e feedback de atualização/erro.
- API do dashboard passa a informar `by_state` e a data/hora mais recente de atualização da base.
- Mantidos autenticação, perfis, permissões, importação, auditoria, exportações, filtros e esquema do banco.

## Complemento — remoção de cartão e exportação filtrada

- Removido do panorama o cartão “Atenção prioritária” marcado na captura; os demais quatro indicadores foram preservados e reequilibrados.
- Adicionado botão XLSX após pesquisas com resultados, com os filtros atuais e exportação de todas as páginas.
- Consulta e exportação usam o mesmo construtor de filtros no backend.
- A rota continua restrita ao Administrador Master e registra o evento no histórico administrativo.
- Testes ampliados para classificação oficial por registro e consistência das contagens estaduais.


## Correção — fonte exclusiva para tipos de especialidade

- A agregação lê os tipos somente do cabeçalho oficial `TIPO ESPECIALIDADE` no dado bruto; removeu-se qualquer caminho de fallback para `ESPECIALIDADE`, `specialty` ou `specialty_type` derivados.
- A interface e a auditoria ocultam a distribuição quando a API não confirma explicitamente `source_column: TIPO ESPECIALIDADE`.
- A normalização não remove mais diferenças de acento ou pontuação entre categorias oficiais; apenas caixa e espaços são consolidados.
- Incluído teste de regressão com valores de especialidade que não podem aparecer na distribuição de tipos.
