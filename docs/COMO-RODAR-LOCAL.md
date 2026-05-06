# Como rodar localmente

Este projeto usa **Node** + **PostgreSQL**. O Docker Compose local sobe **PostgreSQL 18** (e opcionalmente o pgAdmin). A **API** pode rodar no host (`npm run dev`) ou **em container** — veja a seção [Rodar a API em Docker (local)](#rodar-a-api-em-docker-local).

Variáveis de ambiente: veja `docs/DOT-ENV-GUIDE.md` e o modelo `.env.example` na raiz do repositório (principalmente `DATABASE_URL`, `PORT` e `APP_URL` na mesma porta).

**Atualização de major do Postgres no Compose:** se você já tinha dados em volume criado com Postgres 16 e trocou para 18, o container pode falhar ao subir. Nesse caso, ou faça dump/restore, ou — **só se puder perder dados locais** — `docker compose down -v` e suba de novo (`db:deploy` + `db:seed` depois).

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

## Rodar a API em Docker (local)

Útil para validar a mesma imagem que será usada no servidor (Node 22 na imagem; não precisa de Node instalado só para rodar o container).

1. `docker compose up -d` e, no **host**, `npm run db:deploy` (e seed se precisar), com `.env` apontando para `localhost:5432`.
2. Build: `docker build -t ciatec-research-api:local .`
3. Crie um arquivo **local** (não commitado), por exemplo `.env.docker`, copiando `.env.example` e altere só o banco para alcançar o Postgres no host:

   ```text
   DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/ciatec_research
   ```

   No **Linux**, use `docker run` com `--add-host=host.docker.internal:host-gateway` (Docker não resolve `host.docker.internal` por padrão).

4. Suba o container:

   ```bash
   docker run --rm -p 3333:3333 --env-file .env.docker ciatec-research-api:local
   ```

5. Teste [http://localhost:3333/health](http://localhost:3333/health).

Fluxo completo de deploy e atualizações: `docs/DEPLOY-E-ATUALIZACOES.md`.

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
