# Documentação (`docs/`)

Índice da pasta. Para agentes, o ponto de entrada na raiz do repo é **[`../AGENTS.md`](../AGENTS.md)**.

## Camadas

| Camada | Ficheiros |
|--------|-----------|
| **Entrada / roteamento** | [`AGENTS.md`](../AGENTS.md) (raiz) · este `README.md` |
| **Normativo backend** | [`API-ARCHITECTURE-AND-CONVENTIONS.md`](./API-ARCHITECTURE-AND-CONVENTIONS.md) · [`API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md`](./API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md) |
| **Integração (frontend / cliente)** | [`FRONTEND-API-OVERVIEW.md`](./FRONTEND-API-OVERVIEW.md) · [`FRONTEND-AUTH.md`](./FRONTEND-AUTH.md) · [`API-GAMEPLAY-SESSIONS.md`](./API-GAMEPLAY-SESSIONS.md) · [`API-LEVEL-AND-PRESET-PAYLOADS.md`](./API-LEVEL-AND-PRESET-PAYLOADS.md) |
| **Operações** | [`PR-PRODUCTION-READINESS.md`](./PR-PRODUCTION-READINESS.md) · [`DEPLOY-E-ATUALIZACOES.md`](./DEPLOY-E-ATUALIZACOES.md) · [`runbook-prisma-migracoes-producao.md`](./runbook-prisma-migracoes-producao.md) · [`COMO-RODAR-LOCAL.md`](./COMO-RODAR-LOCAL.md) |
| **Planos / histórico (não normativos)** | [`CRIS-IMPLEMENTATION-PLAN.md`](./CRIS-IMPLEMENTATION-PLAN.md) · [`PLAN-USER-LEVEL-PROGRESS.md`](./PLAN-USER-LEVEL-PROGRESS.md) · [`GAME-OVERVIEW.md`](./GAME-OVERVIEW.md) |

## Fontes de verdade (evitar duplicar em Markdown)

| Assunto | Fonte |
|---------|--------|
| Contrato HTTP, códigos, schemas | **Swagger** `GET /docs` e `*.swagger.ts` |
| Env obrigatório em runtime | `src/config/env.ts` |
| Modelo relacional | `prisma/schema.prisma` |
| Prefixos e plugins | `src/app.ts` |

## Variáveis e segredos

Descrição das chaves do `.env`: [`DOT-ENV-GUIDE.md`](./DOT-ENV-GUIDE.md). Modelo: `.env.example` na raiz.
