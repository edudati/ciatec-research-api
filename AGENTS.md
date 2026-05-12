# Instruções para agentes (Cursor / automação)

**Leia primeiro este ficheiro.** Evita abrir vários docs longos sem necessidade.

## Roteamento por tarefa

| Tarefa | Onde ir |
|--------|---------|
| Qualquer alteração de código | [docs/API-ARCHITECTURE-AND-CONVENTIONS.md](docs/API-ARCHITECTURE-AND-CONVENTIONS.md) + módulo de referência em `src/modules/catalog/` |
| PR para `main` / produção | [docs/PR-PRODUCTION-READINESS.md](docs/PR-PRODUCTION-READINESS.md) |
| `Session`, `Match`, telemetria, progresso, RMS/CRIS, modelo longitudinal | [docs/API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md](docs/API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md) + `prisma/schema.prisma` |
| Deploy, Docker, migrações em produção, drift | [docs/DEPLOY-E-ATUALIZACOES.md](docs/DEPLOY-E-ATUALIZACOES.md) · [docs/runbook-prisma-migracoes-producao.md](docs/runbook-prisma-migracoes-producao.md) |
| Setup local (Postgres, seed, primeira vez) | [docs/COMO-RODAR-LOCAL.md](docs/COMO-RODAR-LOCAL.md) |
| Consumo da API no **frontend** / cliente | [docs/FRONTEND-API-OVERVIEW.md](docs/FRONTEND-API-OVERVIEW.md) |
| Índice completo da pasta `docs/` | [docs/README.md](docs/README.md) |

## Fontes técnicas canónicas (código)

- Contrato HTTP e erros: **OpenAPI** em `GET /docs` + `src/modules/*/*.swagger.ts`
- Variáveis de ambiente: `src/config/env.ts`
- Rotas registadas: `src/app.ts`
- Modelo de dados: `prisma/schema.prisma`

## Regras curtas do repo

Ver [.cursor.rules/PROJECT-STANDARDS.md](.cursor.rules/PROJECT-STANDARDS.md) — não duplicar aqui listas longas.

## Não usar como contrato atual

Planos e estratégia antiga: `docs/CRIS-IMPLEMENTATION-PLAN.md`, `docs/PLAN-USER-LEVEL-PROGRESS.md`, `docs/GAME-OVERVIEW.md` — só quando a tarefa for explicitamente roadmap ou histórico.
