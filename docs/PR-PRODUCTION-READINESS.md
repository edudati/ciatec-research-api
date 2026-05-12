# PR para `main` / produção — checklist obrigatório

**Índice:** [AGENTS.md](../AGENTS.md) · [docs/README.md](./README.md)

Este fluxo é **fixo**: cada PR que vá para `main` (e deploy para produção, ex. `api.ciatec.org`) deve cumprir os mesmos passos. Objetivo: não reinventar revisão de deploy, Docker ou migrações a cada merge.

Documentação relacionada: [DEPLOY-E-ATUALIZACOES.md](./DEPLOY-E-ATUALIZACOES.md), [runbook-prisma-migracoes-producao.md](./runbook-prisma-migracoes-producao.md), [API-ARCHITECTURE-AND-CONVENTIONS.md](./API-ARCHITECTURE-AND-CONVENTIONS.md).

---

## 1. Código e contrato

| # | Regra | Comando / critério |
|---|--------|-------------------|
| 1.1 | TypeScript compila | `npm run build` |
| 1.2 | Lint passa | `npm run lint` |
| 1.3 | Alterou `package.json` | `npm install` e **commit** do `package-lock.json` junto |
| 1.4 | Novos endpoints ou mudança de contrato | OpenAPI nos `*.swagger.ts` + smoke em `/docs` quando fizer sentido |
| 1.5 | Breaking change de API | Descrição na PR + aviso a consumidores (front); atualizar docs de API em `docs/` se o contrato público mudou |

---

## 2. Prisma e base de dados

| # | Regra | Comando / critério |
|---|--------|-------------------|
| 2.1 | Toda alteração de `schema.prisma` tem migração versionada | Pasta nova em `prisma/migrations/<timestamp>_<nome>/migration.sql` no **mesmo** PR |
| 2.2 | Não editar SQL de migração **já aplicada** em ambientes partilhados | Nova migração em vez de reescrever histórico; exceções só com runbook |
| 2.3 | Migrações aplicam sem erro no alvo esperado | `npm run db:deploy` contra uma BD com o estado **anterior** ao PR (local ou clone de staging) |
| 2.4 | Após `db:deploy`, app sobe | `npm run dev` ou teste mínimo dos fluxos tocados |
| 2.5 | Dúvida de drift / falha de migrate | Seguir [runbook-prisma-migracoes-producao.md](./runbook-prisma-migracoes-producao.md) antes de forçar `resolve` em produção |

---

## 3. Docker (imagem de produção)

| # | Regra | Comando / critério |
|---|--------|-------------------|
| 3.1 | Imagem builda na raiz do repo | `docker build -t ciatec-research-api:pr .` (Docker Desktop ou CI) |
| 3.2 | Falha de build = PR bloqueada | Corrigir Dockerfile / contexto antes de pedir review de deploy |
| 3.3 | Comportamento esperado da imagem | `CMD` executa `prisma migrate deploy` e só depois `node dist/server.js` (ver [Dockerfile](../Dockerfile)); healthcheck usa `GET /health` |
| 3.4 | Teste opcional mas recomendado | Subir container com env válido (incl. `DATABASE_URL` alcançável) e confirmar `GET /health` — ver [DEPLOY-E-ATUALIZACOES.md](./DEPLOY-E-ATUALIZACOES.md) secção 3 |

Variáveis obrigatórias em runtime: lista canónica em `src/config/env.ts` (não duplicar aqui; manter um só sítio).

---

## 4. Descrição da PR (obrigatório para reviewers)

Incluir sempre, ainda que curto:

1. **O quê** mudou (domínio / endpoints / modelo).
2. **Migrações:** nomes das pastas novas ou “nenhuma”.
3. **Risco:** nenhum / médio (ex. rename de tabela) / alto — e mitigação se aplicável.
4. **Pós-merge:** algo a correr na produção além do deploy normal (ex. seed one-off) — se não houver, escrever “nenhum”.

---

## 5. Após merge em `main` (deploy)

Seguir a ordem de [DEPLOY-E-ATUALIZACOES.md](./DEPLOY-E-ATUALIZACOES.md): build da imagem, `migrate deploy` antes ou no arranque do container (a imagem já corre `migrate deploy` no boot), substituir container, validar `/health`.

---

## 6. Agentes (Cursor / automação)

Ao preparar uma PR para `main`, **executar** os passos das secções 1–3 (comandos reais), não apenas listar intenções. Se algo falhar, corrigir antes de marcar a PR como pronta.

Quem atualizar o [Dockerfile](../Dockerfile) ou o fluxo de deploy deve **atualizar também** este ficheiro ou o [DEPLOY-E-ATUALIZACOES.md](./DEPLOY-E-ATUALIZACOES.md) para o checklist continuar a bater certo com a realidade.
