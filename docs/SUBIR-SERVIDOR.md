# Subir o servidor (resumo)

## Pré-requisitos

- **Node.js** (versão compatível com o projeto) e **npm**
- **PostgreSQL** acessível (URL no `DATABASE_URL`)

## Uma vez

1. `npm install`
2. Criar `.env` na raiz do repositório com (valores reais / segredos fortes em produção):

   - `NODE_ENV=development`
   - `APP_URL` — URL base da app (ex.: `http://localhost:3000`)
   - `PORT` — porta HTTP (ex.: `3000`)
   - `DATABASE_URL` — connection string PostgreSQL
   - `JWT_SECRET`, `JWT_REFRESH_SECRET` — strings não vazias
   - `JWT_EXPIRES_IN`, `JWT_REFRESH_EXPIRES_IN` — ex.: `7d` / `30d`
   - `JWT_ISSUER`, `JWT_AUDIENCE` — identificadores do token (ex.: `ciatec-research-api`)

3. Banco: `npx prisma generate` e, se ainda não existir esquema aplicado, `npx prisma migrate dev` (ou `db:deploy` em produção).

## Sempre (desenvolvimento)

```powershell
Set-Location <pasta-do-repo>; npm run dev
```

http://localhost:3333/



A API escuta em `0.0.0.0` na porta de `PORT`.

**Produção sem Docker:** `npm run build` e `npm start` (usa `dist/server.js`).

**Produção com Docker (EC2 etc.):** build da imagem, variáveis via ambiente do host, migrações com `npx prisma migrate deploy`. Passo a passo e checklist em `docs/DEPLOY-E-ATUALIZACOES.md`.
