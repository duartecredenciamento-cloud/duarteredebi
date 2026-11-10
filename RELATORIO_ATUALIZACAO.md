# Relatório de atualização — BI Rede Duarte 2.0

## Resultado

Reformulação visual para a direção **Executive Intelligence — Duarte**, com fundo claro, navegação azul-marinho, acentos laranja, hierarquia tipográfica executiva e layout responsivo. A atualização trabalha sobre o projeto recebido e mantém o fluxo da aplicação existente; não inclui nem substitui a base real de prestadores.

## Arquivos modificados

- `app/static/index.html` — cabeçalho executivo, menu lateral recolhível, panorama, mapa, filtros, rankings e distribuição por tipo.
- `app/static/app.css` — identidade visual, estados de interação, responsividade e suporte a redução de movimento.
- `app/static/app.js` — ligação dos componentes à API atual, atualização manual, filtros, contadores, mapa SVG interativo, tooltips e mensagens de erro/carregamento.
- `app/analytics.py` — agregação estadual usando a mesma deduplicação central de prestadores; classificação por registro lida de `TIPO ESPECIALIDADE`, excluindo vazios e `NÃO INFORMADO` das categorias.
- `app/main.py` — a API `/api/dashboard` informa as agregações por estado e a data/hora mais recente de atualização da base ativa.
- `tests/test_analytics.py` e `tests/smoke_test.py` — cobertura de classificação oficial, reconciliação das contagens estaduais e elementos da interface.
- `CHANGELOG.md` — registro das mudanças da versão 2.0.

`requirements.txt`, modelos do banco e módulos de segurança/autenticação foram mantidos; nenhuma dependência adicional foi introduzida. As rotas administrativas, permissões, importação, consultas, exportações e auditoria existentes foram preservadas.

## Regra de dados e mapa

- Cartões, regiões, rankings e mapa usam a rotina central de prestadores únicos já existente.
- A distribuição estadual associa cada prestador à primeira UF válida encontrada em seus registros; sem UF válida, ele permanece na parcela “Não informado”, não em um estado inventado.
- Tipos são lidos diretamente da coluna oficial `TIPO ESPECIALIDADE` por registro, sem inferi-los de `ESPECIALIDADE`.
- As geometrias estaduais são solicitadas sob demanda ao serviço público de malhas do IBGE. O mapa apresenta estados sem correspondência de dados como “Sem registros”, em cor neutra; selecionar um estado aplica o filtro de UF ao panorama.

## Verificações e limites

- **12 testes analíticos** executados: aprovados.
- Teste estrutural do projeto: aprovado.
- Sintaxe do JavaScript: aprovada.
- A tentativa de teste ponta a ponta da API foi bloqueada porque FastAPI não está instalado no ambiente de execução desta conversa. Por isso, não afirmo que a aplicação foi iniciada neste ambiente.
- A rota cartográfica do IBGE respondeu com uma FeatureCollection GeoJSON durante a revisão. O carregamento a partir do navegador no ambiente publicado/Railway e a publicação da aplicação não foram testados; se a rede do usuário bloquear o serviço, o painel apresenta aviso e mantém os demais agregados disponíveis.
- Nenhuma publicação, migração ou alteração em dados de produção foi feita.

## Referência cartográfica

A geometria é solicitada à [API de malhas geográficas do IBGE](https://servicodados.ibge.gov.br/api/docs/malhas?versao=3), no endpoint público de malhas do Brasil com subdivisão por UF.

## Aplicação

O pacote preserva a estrutura esperada (`app/`, `app/static/` e `tests/`). Use-o como código do projeto, mantendo as variáveis de ambiente e o banco configurados no Railway; valide primeiro em ambiente de teste antes de substituir a versão publicada.
