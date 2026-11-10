# Atualização do BI Rede Duarte — tipos de especialidade

Este pacote contém os arquivos alterados para habilitar o indicador com a classificação já existente na coluna oficial `TIPO ESPECIALIDADE`. Não cria um mapa novo nem altera os registros de origem.

## Arquivos incluídos

- `app/analytics.py` — calcula categorias distintas e frequência por valor oficial.
- `app/main.py` — ajusta a mensagem da auditoria administrativa.
- `app/static/index.html`, `app/static/app.js`, `app/static/app.css` — apresenta o indicador e a distribuição.
- `tests/test_analytics.py` — cobre valores oficiais, ausências e filtros; mantém os testes de ranking.
- `CHANGELOG.md` — registra a alteração.

## Aplicação

Copie os arquivos mantendo os caminhos relativos para a raiz do projeto existente. O pacote é uma atualização parcial, não substitui o restante do projeto. Preserve a configuração, as credenciais e os demais módulos existentes.

Execute os testes no ambiente do projeto (`python -m pytest -q`). Faça primeiro deploy de homologação e confira a auditoria e o painel. A importação da planilha e o deploy no Railway não são realizados por este pacote.

## Regra de contagem

Contam-se valores distintos de `TIPO ESPECIALIDADE`, ignorando diferenças apenas de maiúsculas/minúsculas e espaços repetidos nas comparações. A grafia exibida mantém o valor da planilha. Campos vazios e `NÃO INFORMADO` não entram na contagem de categorias válidas; são informados separadamente como linhas sem classificação. Frequências representam linhas, não prestadores únicos.
