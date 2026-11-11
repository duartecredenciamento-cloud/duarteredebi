# Relatório — correção da fonte dos tipos oficiais

## Alteração
- A distribuição de tipos agora extrai exclusivamente o valor bruto sob o cabeçalho `TIPO`.
- Não há fallback para `ESPECIALIDADE`, `specialty` ou para um campo derivado `specialty_type`.
- A interface principal e a auditoria administrativa só exibem categorias se a resposta da API identificar explicitamente `source_column: TIPO`; se a origem não vier confirmada, os valores são ocultados.
- Vazios e `NÃO INFORMADO` continuam fora da contagem de categorias e são contabilizados separadamente. Não são inventados mapeamentos.

## Teste de regressão
Incluído um caso em que a especialidade contém termos como “Centro de Diagnóstico” e “Hospital”, mas só `TIPO` pode alimentar a distribuição.

## Verificação da planilha disponível
A leitura histórica da aba `BANCO REDE` encontrou 63.035 linhas, 22 categorias e 53.648 linhas classificadas sob o cabeçalho então presente `TIPO ESPECIALIDADE`; 9.387 linhas estavam vazias ou marcadas como `NÃO INFORMADO`. Esses números não validam a coluna atual `TIPO`, pois a planilha fornecida naquele momento ainda usava o cabeçalho anterior, nem confirmam o estado da base publicada no Railway.

## Escopo e limite
A correção é de código e não altera registros já armazenados. Se valores antigos tiverem sido gravados incorretamente dentro da própria chave `TIPO`, será necessária uma revisão controlada da origem dos registros; não é seguro reescrever dados de produção automaticamente. Não foi realizado deploy.
