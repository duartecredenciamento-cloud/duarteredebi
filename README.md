# BI Rede Duarte — tela de acesso

Pacote visual para substituir a tela de login do BI Rede Duarte. Mantém o endpoint existente `/api/login`, os campos `cpf` e `password`, a sessão por cookie e a aplicação principal após autenticação.

## Conteúdo
- `index.html` — tela de login e estrutura atual do BI.
- `static/app.css` — estilos da aplicação e novo visual da tela de acesso.
- `static/app.js` — lógica original com animação leve de partículas, alternância da visibilidade da senha e estado de envio.
- `static/logo.png` — logo enviado.

## Instalação
Substitua os arquivos equivalentes no projeto, preservando as rotas estáticas `/static/app.css`, `/static/app.js` e `/static/logo.png`. Faça commit e push para acionar o deploy do Railway.

O login deve ser validado no Railway após o deploy; este pacote não contém nem altera o backend. Os efeitos são locais, adaptáveis a celular e respeitam `prefers-reduced-motion`.
