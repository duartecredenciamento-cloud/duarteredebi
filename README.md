# BI Rede Duarte — tela de acesso

Pacote visual para substituir a tela de login do BI Rede Duarte. Mantém o endpoint existente `/api/login`, os campos `cpf` e `password`, a sessão por cookie e a aplicação principal após autenticação.

## Conteúdo
- `index.html` — tela de login e estrutura atual do BI.
- `static/app.css` — estilos da aplicação e novo visual da tela de acesso.
- `static/app.js` — lógica original com animação leve de partículas, alternância da visibilidade da senha e estado de envio.
- `static/logo.png` — logo enviado.

## Instalação
Substitua os arquivos equivalentes no projeto, preservando as rotas estáticas `/static/app.css`, `/static/app.js` e `/static/logo.png`. Faça commit e push para acionar o deploy do Railway.

O pacote mantém o backend e os fluxos já existentes. Após a instalação, valide o login e as funções no ambiente de homologação antes do deploy no Railway.

## Complemento de pesquisa
O cartão “Atenção prioritária” foi removido do Panorama Executivo. Na página Prestadores, o Administrador Master pode exportar em Excel todos os registros da busca atual, com os mesmos filtros, independentemente da paginação exibida. A exportação usa uma rota autenticada, preserva as colunas da origem e é registrada no histórico administrativo.
