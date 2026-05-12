# ciatec-research-api — Project Standards

**Leitura primeiro:** [AGENTS.md](../AGENTS.md) e [docs/README.md](../docs/README.md). Aqui ficam só **invariantes**; convenções longas estão nos Markdown ligados.

## Stack
Node.js ESM · TypeScript (strict, NodeNext) · Fastify 5 · Prisma 7 + pg · Zod 4 · @fastify/jwt

## Módulo (sempre 5 arquivos em `src/modules/<nome>/`)
- **routes** → registra rotas, instancia service/controller, define `preHandler` e `schema`
- **controller** → `create<Nome>Controller(service)`: Zod parse → chama service → `reply.send`
- **service** → `create<Nome>Service({ prisma })`: lógica + Prisma + erros de domínio; nunca toca HTTP
- **schema** → Zod de params/query/body (`snake_case`; bodies com `.strict()`)
- **swagger** → `FastifySchema` por operação com `tags`, `summary`, `security`, respostas 400/401/403/404

Registrar em `app.ts`: `app.register(routes, { prefix: \`${API_PREFIX}/<nome>\` })`  
Adicionar tag em `src/config/swagger.ts`.

## Regras obrigatórias
- **Imports:** sempre com extensão `.js` em paths relativos
- **Factories, nunca classes:** `createXService` / `createXController`
- **JSON da API:** `snake_case` (`game_id`, `is_active`, `created_at`)
- **Controller** mapeia `snake_case` → `camelCase` antes de chamar o service
- **Status:** `201` criação · `204` delete sem corpo
- **Soft delete:** `isActive`/`isDeleted`; nunca `prisma.x.delete()` em recursos com esses campos
- **Erros:** lançar `NotFoundError`, `ForbiddenError`, `ConflictError` etc. de `src/shared/errors/`; nunca `reply` no service
- **Auth:** rotas protegidas com `preHandler: [authenticate]`; com role: `requireRole('ADMIN', 'RESEARCHER')`; Swagger com `security: [{ bearerAuth: [] }]`
- **Env:** nunca `process.env` fora de `src/config/env.ts`
- **Json no Prisma:** cast para `Prisma.InputJsonValue` ao gravar `Record<string, unknown>`

## Eixo longitudinal (inviolável)
`User → Session (userId + sessionDate único) → Match → tabelas de telemetria por jogo`

- Nunca quebrar unicidade `(userId, sessionDate)` sem decisão documentada
- `Match.levelConfigSnapshot` congela contexto da coleta — não alterar retroativamente
- Telemetria densa → tabelas dedicadas com índice `(matchId, timestamp)`; nunca em Json genérico
- Project/Group/Participant → modelos Prisma com FKs explícitas; nunca em Json de `Session`/`Match`

## Anti-patterns
```ts
// ❌ import sem .js
import { x } from './service'
// ❌ classe em vez de factory
export class MyService {}
// ❌ reply/request no service
const svc = { get: async (reply) => reply.send(...) }
// ❌ delete físico com soft delete
await prisma.game.delete({ where: { id } })
// ❌ telemetria em Json genérico
await prisma.match.update({ data: { telemetry: JSON.stringify(arr) } })
// ❌ process.env direto
const port = process.env.PORT
```

## Referências canônicas
- Módulo CRUD: `src/modules/catalog/`
- Telemetria: `src/modules/trunktilt/`
- Convenções: `docs/API-ARCHITECTURE-AND-CONVENTIONS.md`
- Domínio (sob demanda): `docs/API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md`
