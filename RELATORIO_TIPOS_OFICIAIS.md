# Relatório — correção da fonte dos tipos oficiais

## Alteração
- A distribuição de tipos agora extrai exclusivamente o valor bruto sob o cabeçalho `TIPO ESPECIALIDADE`.
- Não há fallback para `ESPECIALIDADE`, `specialty` ou para um campo derivado `specialty_type`.
- A interface principal e a auditoria administrativa só exibem categorias se a resposta da API identificar explicitamente `source_column: TIPO ESPECIALIDADE`; se a origem não vier confirmada, os valores são ocultados.
- Vazios e `NÃO INFORMADO` continuam fora da contagem de categorias e são contabilizados separadamente. Não são inventados mapeamentos.

## Teste de regressão
Incluído um caso em que a especialidade contém termos como “Centro de Diagnóstico” e “Hospital”, mas só `TIPO ESPECIALIDADE` pode alimentar a distribuição.

## Verificação da planilha disponível
Na aba `BANCO REDE` da planilha de referência disponível, a leitura direta do cabeçalho oficial encontrou 63.035 linhas de dados, 22 categorias distintas válidas, 53.648 linhas classificadas e 9.387 vazias ou equivalentes a `NÃO INFORMADO` após normalização de espaços/acentos para detectar esse marcador. Esses números descrevem somente essa planilha; não confirmam o estado atual do banco publicado no Railway.

## Escopo e limite
A correção é de código e não altera registros já armazenados. Se valores antigos tiverem sido gravados incorretamente dentro da própria chave `TIPO ESPECIALIDADE`, será necessária uma revisão controlada da origem dos registros; não é seguro reescrever dados de produção automaticamente. Não foi realizado deploy.
