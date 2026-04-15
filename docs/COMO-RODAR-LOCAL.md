# Como rodar localmente

Este projeto usa **Node** + **PostgreSQL**. O Docker aqui serve só para **subir o Postgres** (e opcionalmente o pgAdmin); não é preciso saber Docker além dos comandos abaixo.

Variáveis de ambiente: veja `docs/DOT-ENV-GUIDE.md` (principalmente `DATABASE_URL`, `PORT` e `APP_URL` na mesma porta).

---

## Primeira vez no repositório

1. Instale o [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows) e deixe-o **rodando** (ícone na bandeja).
2. Na **raiz do projeto**, suba o banco:

   ```bash
   docker compose up -d
   ```

   O Postgres fica em `localhost:5432`. O compose cria o banco **`ciatec_research`**, usuário **`postgres`**, senha **`postgres`**. Ajuste o `DATABASE_URL` do `.env` para bater com isso (ou use outro Postgres e aponte o `DATABASE_URL` para ele).

3. Instale dependências:

   ```bash
   npm install
   ```

4. Aplique as migrações no banco:

   ```bash
   npm run db:deploy
   ```

5. Rode o seed inicial (cria o jogo Bubli com ID fixo):

   ```bash
   npm run db:seed
   ```

6. Suba a API:

   ```bash
   npm run dev
   ```

7. Teste no navegador (use a porta do seu `.env`, exemplo `3333`):

   - [http://localhost:3333/health](http://localhost:3333/health) — deve responder `status: ok`
   - [http://localhost:3333/docs](http://localhost:3333/docs) — documentação Swagger

---

## Toda vez que for testar (banco já existe)

1. Docker Desktop ligado (se o Postgres for o do `docker compose`).
2. Se o container não estiver no ar:

   ```bash
   docker compose up -d
   ```

3. Depois de **atualizar o código** (novas migrações no repositório):

   ```bash
   npm run db:deploy
   ```

4. Suba a API:

   ```bash
   npm run dev
   ```

Não precisa `npm install` nem `db:generate` em todo teste — só quando mudar dependências ou o `schema.prisma`. Se aparecer erro de client Prisma desatualizado: `npm run db:generate`.

---

## Se você alterar o banco (mudou `prisma/schema.prisma`)

Use o Prisma em modo desenvolvimento (cria migração com nome que você escolhe):

```bash
npx prisma migrate dev --name descreva_a_mudanca
```

Evite usar `npm run db:migrate` para isso: o script fixa `--name init` e atrapalha o histórico.

---

## Parar

- API: no terminal do `npm run dev`, **Ctrl+C**.
- Postgres do compose: na raiz, `docker compose stop` (dados ficam no volume). `docker compose down` remove os containers; **não** use `down -v` se quiser manter os dados do banco.
