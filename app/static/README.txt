BI Rede Duarte — atualização da interface

Conteúdo: index.html, app.css, app.js e logo.png.

Aplicação: substitua os quatro arquivos correspondentes na pasta de arquivos estáticos do BI (normalmente app/static/) e publique a versão atualizada. Preserve os endereços /static/app.css, /static/app.js e /static/logo.png usados pela aplicação.

A tela de login usa os mesmos endpoints de autenticação já existentes. O cadastro de prestador envia os campos ao endpoint atual /api/admin/records no formato {"data": {...}}. Esta entrega atualiza somente a interface; não inclui o backend e não publica alterações no Railway.
