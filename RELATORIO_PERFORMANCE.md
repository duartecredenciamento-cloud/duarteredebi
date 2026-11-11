# Atualização pontual — BI Rede Duarte

## Escopo aplicado

As mudanças ficaram concentradas em `app/main.py`, `app/static/app.js`, `app/static/app.css` e `app/static/index.html`, sem alteração de banco, arquitetura, autenticação, permissões, filtros de negócio ou regras de deduplicação.

- **API do painel:** cache temporário das agregações por combinação de filtros, limitado a 24 combinações e invalidado em cadastros, alterações, desativações e importações. Os resultados são copiados ao sair do cache para impedir que a auditoria administrativa altere dados compartilhados.
- **Memória do painel:** o cache mantém os campos analíticos necessários e o valor oficial de `TIPO ESPECIALIDADE`, em vez de reter cada JSON completo da planilha durante os 45 segundos de cache. O banco ainda precisa ler o JSON para extrair esse campo; não foi aplicada extração específica de banco para evitar dependência de dialeto.
- **Consultas e navegação:** requisições antigas do painel e da pesquisa de prestadores são canceladas no navegador; a resposta obsoleta não substitui a mais recente. A geometria do mapa também não é redesenhada com dados de um filtro antigo.
- **Administração:** usuários, histórico e auditoria são carregados na primeira visita; os botões de atualização continuam forçando uma consulta. Após importação, a auditoria é marcada para recarga.
- **Especialidades:** o painel agora usa a série completa `normalized_specialties`, em ordem decrescente de prestadores únicos. As categorias são inseridas em lotes conforme a rolagem; os nomes completos ficam legíveis, sem animação de largura em centenas de barras.
- **Acabamento:** feedback discreto durante consultas, fonte carregada por uma única referência no HTML, barras longas com rolagem interna e respeito a `prefers-reduced-motion`.

## Arquivos alterados

- `app/main.py`
- `app/static/app.js`
- `app/static/app.css`
- `app/static/index.html`
- `tests/test_performance_scope.py` (novos testes focados)

## Validação e limites

Foram acrescentados testes para garantir que a série analítica não seja truncada, permaneça ordenada e que cache/cancelamento estejam conectados ao fluxo da aplicação. A validação local não mede o tempo do Railway nem do banco ativo; não foi possível comparar tempos reais antes/depois ou navegar na instância implantada. Nenhuma base foi alterada e nenhum deploy foi realizado.

O pacote foi montado a partir da última cópia completa do projeto disponível nesta conversa. Os três anexos mais recentes do usuário e a referência visual Duarte Repay não apareceram como arquivos legíveis no ambiente desta execução; por isso, confira a integração com a versão atualmente implantada antes de publicar. As decisões de refinamento visual foram baseadas nos estilos existentes do BI, não em uma captura do Repay.

## Testes

- Executar a suíte: `python -m unittest discover -s tests -v`
- Verificar sintaxe Python: `python -m compileall -q app`
- Verificar sintaxe JavaScript: `node --check app/static/app.js`
