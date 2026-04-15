# 📄 Descrição do `.env`

Este arquivo `.env` define as variáveis de ambiente da API, controlando configuração de execução, conexão com banco de dados e autenticação via JWT.

## Ambiente e banco de dados

* `NODE_ENV`: Define o ambiente da aplicação (`development` neste caso), influenciando logs, validações e comportamento geral.
* `PORT`: Porta em que o servidor HTTP escuta. Deve ser definida explicitamente no `.env` (o código não usa valor padrão); alinhe com a porta usada em `APP_URL` quando for `localhost` (por exemplo, `3333` nos dois).
* `APP_URL`: URL base da aplicação, usada para geração de links e callbacks.
* `DATABASE_URL`: String de conexão com o PostgreSQL, incluindo credenciais, host, porta, nome do banco e schema.

## Autenticação (JWT)

A autenticação utiliza dois tipos de token:

* **Access Token (curta duração)**:

  * `JWT_SECRET`: chave usada para assinar o token de acesso.
  * `JWT_EXPIRES_IN`: tempo de expiração (30 minutos).

* **Refresh Token (longa duração)**:

  * `JWT_REFRESH_SECRET`: chave separada para maior segurança.
  * `JWT_REFRESH_EXPIRES_IN`: tempo de expiração (7 dias).

## Metadados do Token

* `JWT_ISSUER`: identifica quem emitiu o token (a própria API).
* `JWT_AUDIENCE`: define quem pode utilizar o token (clientes autorizados).

