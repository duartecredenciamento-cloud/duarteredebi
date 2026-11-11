# Relatório histórico — BI Rede Duarte 2.0

> Este documento registra a atualização visual anterior. Para as otimizações, medição de desempenho, lista completa de especialidades e validações desta entrega, consulte `RELATORIO_PERFORMANCE.md`.

## Resultado

Reformulação visual para a direção **Executive Intelligence — Duarte**, com fundo claro, navegação azul-marinho, acentos laranja, hierarquia tipográfica executiva e layout responsivo. A atualização trabalha sobre o projeto recebido e mantém o fluxo da aplicação existente; não inclui nem substitui a base real de prestadores.

## Arquivos modificados

- `app/static/index.html` — cabeçalho executivo, menu lateral recolhível, panorama, mapa, filtros, TOP 10 e gráfico de distribuição de prestadores únicos por UF.
- `app/static/app.css` — identidade visual, estados de interação, responsividade, refinamento de alinhamento do cabeçalho e suporte a redução de movimento.
- `app/static/app.js` — ligação dos componentes à API atual, filtros, contadores, mapa, barras estaduais com tooltips e estados de carregamento/erro.
- `app/analytics.py` — agregação estadual usando a mesma deduplicação central de prestadores; classificação por registro lida de `TIPO ESPECIALIDADE`, excluindo vazios e `NÃO INFORMADO` das categorias.
- `app/main.py` — a API `/api/dashboard` informa as agregações por estado e a data/hora mais recente de atualização da base ativa.
- `tests/test_analytics.py` e `tests/smoke_test.py` — cobertura de classificação oficial, reconciliação das contagens estaduais e elementos da interface.
- `CHANGELOG.md` — registro das mudanças da versão 2.0.

`requirements.txt`, modelos do banco e módulos de segurança/autenticação foram mantidos; nenhuma dependência adicional foi introduzida. As rotas administrativas, permissões, importação, consultas, exportações e auditoria existentes foram preservadas.

## Regra de dados e mapa

- Cartões, regiões, rankings e mapa usam a rotina central de prestadores únicos já existente.
- O gráfico estadual usa exclusivamente `UF` e conta cada identidade única uma vez em cada estado válido onde aparece. Se uma identidade aparece em duas UFs, ela conta uma vez em cada UF; UFs ausentes ou inválidas ficam numa linha separada “UF não informada”. Estados sem prestadores não são listados como se tivessem volume.
- A cobertura de UFs é uma métrica distinta: conta as siglas brasileiras distintas identificadas nos registros filtrados, em relação ao total de 27. Ela não representa o total de prestadores.
- Tipos são lidos diretamente da coluna oficial `TIPO ESPECIALIDADE` por registro, sem inferi-los de `ESPECIALIDADE`.
- As geometrias estaduais são solicitadas sob demanda ao serviço público de malhas do IBGE. O mapa apresenta estados sem correspondência de dados como “Sem registros”, em cor neutra; selecionar um estado aplica o filtro de UF ao panorama.

## Verificações e limites

- Os testes da versão 2.0 haviam passado anteriormente. Para este complemento foram incluídos casos de UF filtrada, nome oficial do estado, identidade presente em mais de uma UF e cobertura territorial; a execução destes testes complementares não foi concluída neste ambiente.
- A checagem do pacote e a execução ponta a ponta da API também não foram concluídas nesta rodada por falha do ambiente de validação. Não afirmo que os números da planilha anexada foram recalculados ou reconciliados com o Railway neste complemento.
- A rota cartográfica do IBGE respondeu com uma FeatureCollection GeoJSON durante a revisão. O carregamento a partir do navegador no ambiente publicado/Railway e a publicação da aplicação não foram testados; se a rede do usuário bloquear o serviço, o painel apresenta aviso e mantém os demais agregados disponíveis.
- Nenhuma publicação, migração ou alteração em dados de produção foi feita.

## Referência cartográfica

A geometria é solicitada à [API de malhas geográficas do IBGE](https://servicodados.ibge.gov.br/api/docs/malhas?versao=3), no endpoint público de malhas do Brasil com subdivisão por UF.

## Aplicação

O pacote preserva a estrutura esperada (`app/`, `app/static/` e `tests/`). Esta atualização visual não altera nem publica dados de produção. Antes de substituir a versão publicada, valide a integração com a base ativa em ambiente de homologação, incluindo os totais por UF e a atualização dos filtros.
