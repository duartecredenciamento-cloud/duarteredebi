# Atualização de performance — BI Rede Duarte

**Escopo:** otimização pontual, apresentação integral das especialidades e acabamento visual. A estrutura FastAPI/SQLAlchemy, os dados, autenticação, permissões, filtros, exportações, mapa e análises regionais foram preservados.

## Alterações realizadas

- **API e agregações:** cache de resultados por combinação de filtros, com validade de 45 segundos, limite de 24 combinações e invalidação após importação, criação, edição e desativação de registros. Resultados armazenados são copiados antes de serem devolvidos, evitando alterações cruzadas entre respostas.
- **Cálculos:** filtros vazios não normalizam campos por registro; a cobertura de UFs passou a usar uma passagem única. A busca do cabeçalho oficial `TIPO` é resolvida uma vez por esquema de colunas e nunca usa `ESPECIALIDADE` como alternativa.
- **Navegação:** ao retornar ao Panorama Executivo, a interface reutiliza a resposta por até 30 segundos; chamadas idênticas em andamento são compartilhadas e uma consulta anterior é cancelada quando filtros novos são enviados.
- **Gráficos:** o painel mostra a lista completa de `ESPECIALIDADE`, por prestadores únicos e em ordem decrescente. A rolagem virtual limita as linhas montadas simultaneamente, sem limitar as categorias; as geometrias e o desenho dos estados são reutilizados depois do primeiro carregamento.
- **Visual:** mantidos fundo claro, azul-marinho e laranja. Do Duarte Repay foram usados como referência a hierarquia, o espaçamento, a organização da navegação e as transições discretas — sem copiar o fundo escuro nem redesenhar as demais páginas.
- **Dependências e dados:** nenhuma dependência foi acrescentada; não houve migração, alteração destrutiva, importação ou publicação.

## Medição local

Na aba `BANCO REDE` da planilha de referência disponível, foram processadas **63.035 linhas**. A agregação anterior levou **2,311 s**; a versão otimizada levou **1,123 s** na mesma rotina local — redução de aproximadamente **51%** no tempo de cálculo observado. A resposta manteve **33.792 prestadores únicos**, **1.026 especialidades distintas** e entregou as **1.026** na lista integral.

Essa comparação mede apenas a função de agregação local sobre a planilha, não inclui consulta a banco remoto, rede, serialização HTTP ou o ambiente Railway. Os tempos podem variar conforme a máquina.

## Validações e limites

- **15 testes analíticos e estruturais** passaram por execução direta, incluindo ordenação, contagem única, cobertura regional, fonte exclusiva `TIPO` e apresentação sem limite de dez categorias.
- A sintaxe do JavaScript passou; a análise sintática dos 9 módulos Python passou; o HTML estrutural passou com 74 IDs únicos e os destinos principais presentes.
- Este ambiente não dispõe de `pytest`, FastAPI, SQLAlchemy ou Starlette. Portanto, não foi possível iniciar a API, testar consultas contra o banco nem executar um teste ponta a ponta dos filtros e navegação.
- Não foi possível renderizar o painel autenticado em diferentes navegadores/resoluções nem conferir console/API em execução. A responsividade foi revisada no código, mas ainda deve ser validada em homologação.
- Nenhuma alteração foi publicada no Railway; a base de produção não foi acessada ou modificada.
