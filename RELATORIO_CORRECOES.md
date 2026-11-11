# Relatório — ajustes da pesquisa no BI Rede Duarte

## Implementado
- Removido do panorama o cartão “Atenção prioritária”, apontado na captura.
- Mantidos prestadores únicos, especialidades, cobertura municipal e cobertura de UF; a grade se reorganiza em desktop, tablet e celular.
- Adicionado o botão “Exportar resultados (.xlsx)” à tela Prestadores após uma pesquisa com resultados.
- O Excel exporta todos os resultados, não apenas a página atual, com os filtros usados na pesquisa: texto, especialidade, município, UF, status, serviço e prioridade.
- A consulta e a exportação compartilham a mesma montagem dos filtros no backend. São preservados os campos de origem, com uma coluna `ID INTERNO` adicional.
- A exportação permanece exclusiva ao Administrador Master e é registrada no histórico de auditoria.

## Validação e limites
A checagem estrutural passou; os 13 testes analíticos foram executados diretamente com sucesso; a sintaxe do JavaScript e a análise sintática dos módulos Python passaram. Este ambiente não dispõe de FastAPI, SQLAlchemy, pytest ou httpx; assim, a API não pôde ser iniciada nem a rota validada com banco de dados. Não foram alterados dados reais nem realizado deploy no Railway.
