# Visão geral da API para frontend / agente cliente

Trilho **curto**. Contrato fino: **sempre** [`GET /docs`](https://api.ciatec.org/docs) (produção) ou `http://localhost:<PORT>/docs` (local).

## Base e formato

| Item | Valor |
|------|--------|
| Produção (exemplo) | `https://api.ciatec.org` |
| Prefixo API | `/api/v1` |
| JSON | `Content-Type: application/json` |
| Auth | `Authorization: Bearer <accessToken>` |

## O que ler neste repo

1. Este ficheiro (orientação).
2. [`FRONTEND-AUTH.md`](./FRONTEND-AUTH.md) — login, tokens, `/refresh`, `/logout`, `/me`.
3. Fluxo de jogo: [`API-GAMEPLAY-SESSIONS.md`](./API-GAMEPLAY-SESSIONS.md) e [`API-LEVEL-AND-PRESET-PAYLOADS.md`](./API-LEVEL-AND-PRESET-PAYLOADS.md).
4. **Catálogo de jogos** (lista e detalhe): `GET /api/v1/catalog/games` e `GET /api/v1/catalog/games/:game_id` — ver Swagger tag Catalog.
5. **Utilizadores** (admin / tooling): `GET|POST|PATCH|DELETE /api/v1/users` — Swagger tag Users; política de papéis pode evoluir.

## UUIDs de jogos (seed)

`src/constants/game-ids.ts` — usar os IDs correctos por jogo nas chamadas.

## Telemetria por jogo

- **Bubbles / Bestbeat:** `POST /api/v1/{bubbles|bestbeat}/matches/:match_id/telemetry/world`, `.../telemetry/pose`, `.../events` — limites e corpos no Swagger.
- **TrunkTilt:** payloads tipados; mesma ideia de paths sob `/api/v1/trunktilt/matches/...` — **detalhe só no Swagger** (tag TrunkTilt) e em `src/modules/trunktilt/`.

## Erros

Respostas de sucesso são JSON directo (muitas vezes sem envelope `{ success, data }`). Erros: ver secção de formato em [`API-ARCHITECTURE-AND-CONVENTIONS.md`](./API-ARCHITECTURE-AND-CONVENTIONS.md).

## O que **não** precisas para consumir a API

- [`API-ARCHITECTURE-AND-CONVENTIONS.md`](./API-ARCHITECTURE-AND-CONVENTIONS.md) e [`API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md`](./API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md) — são para quem **implementa** a API.
- Planos em `docs/*PLAN*.md` e [`GAME-OVERVIEW.md`](./GAME-OVERVIEW.md) — roadmap / histórico, não contrato HTTP.

## Índice geral

[`docs/README.md`](./README.md) · agentes: [`AGENTS.md`](../AGENTS.md)
