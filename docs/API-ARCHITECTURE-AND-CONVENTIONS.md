# Arquitetura da API e convenções para novos módulos

Este documento descreve a stack, o desenho da API e os padrões de código usados no **ciatec-research-api**. O objetivo é qualquer agente ou desenvolvedor replicar a mesma estrutura ao criar endpoints, serviços e mudanças de dados.

### Documentação relacionada (uso por agentes)

Ao criar **novas soluções** que envolvam sessões, partidas, telemetria, progresso, catálogo ou organização longitudinal (RMS/CRIS), usar **também**:

- **[API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md](./API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md)** — domínio de negócio, entidades Prisma, relacionamentos, fluxo `Session` → `Match`, integração entre módulos, regras para **`timeline_events`** (camada de linha do tempo), participantes/pesquisadores/projetos/grupos e checklist de modelagem.

**Este arquivo** cobre *como* implementar (stack e padrão de módulo); o documento de domínio cobre *o quê* existe no modelo e *como* estender sem violar o eixo longitudinal.

---

## 1. Stack

| Camada | Tecnologia |
|--------|------------|
| Runtime | Node.js (ES modules: `"type": "module"` no `package.json`) |
| Linguagem | TypeScript (`strict`, `module`/`moduleResolution`: `NodeNext`) |
| HTTP | Fastify 5 |
| ORM / banco | Prisma 7 + adapter `@prisma/adapter-pg`, driver `pg` |
| Banco de dados | PostgreSQL (`DATABASE_URL`) |
| Validação | Zod 4 |
| Auth | `@fastify/jwt` (access token Bearer), refresh tokens no modelo Prisma |
| Documentação OpenAPI | `@fastify/swagger` + `@fastify/swagger-ui` (`/docs`) |
| Segurança / CORS | `@fastify/helmet`, `@fastify/cors` |
| Config | `dotenv` + validação de env com Zod em `src/config/env.ts` |

Scripts úteis: `npm run dev`, `npm run build`, `npm run db:migrate`, `npm run db:generate`, `npm run db:deploy`.

---

## 2. Estrutura de pastas (visão geral)

- `src/server.ts` — bootstrap: sobe o app na `PORT` do env.
- `src/app.ts` — monta plugins (CORS, Helmet, Swagger, JWT), prefixo da API, rotas, health, error handler, hooks de log.
- `src/config/` — `env.ts` (Zod), `swagger.ts` (OpenAPI base).
- `src/lib/prisma.ts` — instância singleton do `PrismaClient` com adapter PG; em dev reutiliza `globalThis.prisma`.
- `src/modules/<domínio>/` — um módulo de negócio por pasta (ver seção 4).
- `src/shared/` — erros, middlewares (`authenticate`, `requireRole`), tipos compartilhados.

Imports internos usam **sufixo `.js`** nos caminhos (ex.: `from './catalog.service.js'`), por causa do `NodeNext`.

---

## 3. API HTTP

### Prefixo e versão

Todas as rotas de negócio ficam sob **`/api/v1`** (constante `API_PREFIX` em `src/app.ts`).

Ex.: módulo registrado com `prefix: ${API_PREFIX}/catalog` → URLs como `/api/v1/catalog/games`.

### Health e documentação

- `GET /health` — liveness, sem prefixo de versão.
- `GET /docs` — Swagger UI (OpenAPI 3.0.3).

### Formato de erro (padrão global)

O `setErrorHandler` em `src/app.ts` padroniza respostas de erro:

1. **Zod** (`ZodError`) → `400`, corpo com `success: false`, `code: 'VALIDATION_ERROR'`, `message`, `details` e `issues` (issues do Zod).
2. **`AppError` e subclasses** → status e `code` definidos na classe; corpo `{ success: false, code, message }`.
3. **Demais erros** → `500`, `code: 'INTERNAL_ERROR'`.

Respostas de **sucesso** neste projeto costumam ser **JSON direto** do recurso (ex.: objeto ou `{ games: [...] }`), **sem** envelope obrigatório `{ success: true, data }` — o tipo `ApiResponse<T>` em `src/shared/types/api-response.ts` existe como utilitário, mas não é aplicado em todos os handlers.

### Logging

Hooks registram entrada (`request_in`) e saída (`request_out`) com duração. Campos sensíveis (`password`, `token`, `refreshToken`, `authorization`) são mascarados em logs de query/params/body.

---

## 4. Padrão de módulo (`src/modules/<nome>/`)

Cada domínio segue a separação **rotas → controller → service**, com validação e documentação explícitas.

| Arquivo | Responsabilidade |
|---------|------------------|
| `<nome>.routes.ts` | Registra rotas no `FastifyInstance`; injeta `prisma` (ou deps); cria `create<Nome>Service` e `create<Nome>Controller`; associa `preHandler` (auth/roles) e `schema` Swagger a cada rota. |
| `<nome>.controller.ts` | Exporta **`create<Nome>Controller(service)`** que devolve objeto com handlers. Cada handler: faz `schema.parse` (Zod) em `params`/`body`/`query`, chama o service, envia resposta com `reply.send` ou `reply.status(201|204).send(...)`. |
| `<nome>.service.ts` | Exporta **`create<Nome>Service(deps)`** (ex.: `{ prisma }`). Contém Prisma, regras de negócio, transações. Lança erros de domínio (`NotFoundError`, etc.), não conhece HTTP. |
| `<nome>.schema.ts` | Schemas Zod: params, query, body (`.strict()` em bodies quando aplicável). Nomes de campos alinhados ao **JSON da API** (ex.: `game_id`, `is_active`). |
| `<nome>.swagger.ts` | Objetos `FastifySchema` (OpenAPI) por operação: `tags`, `summary`, `security`, `body`, `response` (incluir `401`, `403`, `404`, validação quando fizer sentido). Reutilizar blocos como `appError` / `zodValidationError` como no `catalog.swagger.ts`. |

**Referência canônica recente:** `src/modules/catalog/` (CRUD com leitura autenticada e escrita com `requireRole('ADMIN', 'RESEARCHER')`).

### Factories em vez de classes

Preferir **`createXService`** / **`createXController`** que retornam objetos com métodos, para injeção de dependências e testes, em linha com o restante do repositório.

---

## 5. Autenticação e autorização

- **JWT access:** header `Authorization: Bearer <token>`. Verificação com `request.jwtVerify()` no middleware `authenticate` (`src/shared/middlewares/authenticate.ts`). Falha → `UnauthorizedError` (401).
- **Payload:** tipado em `src/shared/types/jwt.d.ts` (`sub`, `role`, `iss`, `aud`).
- **Papéis:** enum Prisma `UserRole` (`ADMIN`, `RESEARCHER`, `PLAYER`). Restrição por rota com `requireRole('ADMIN', 'RESEARCHER')` etc.
- Rotas públicas (ex.: login/register) não usam `authenticate`; rotas protegidas listam `preHandler: [authenticate]` e, se necessário, `requireRole`.

Em schemas Swagger, rotas protegidas devem incluir `security: [{ bearerAuth: [] }]` (esquema definido em `src/config/swagger.ts`).

---

## 6. Dados (Prisma e convenções)

### Modelagem

- IDs: `String @id @default(uuid())` na maioria dos modelos.
- Timestamps: `createdAt`, `updatedAt` com `@default(now())` e `@updatedAt`.
- Relações com `onDelete` explícito onde importa (Cascade vs Restrict).
- Nomes de tabela: `@@map("snake_case")` quando o modelo é PascalCase.

### Soft delete e “ativo”

Entidades como `Game`, `Preset`, `Level` usam **`isDeleted`** e **`isActive`**. Consultas “visíveis” no catálogo filtram algo equivalente a `{ isActive: true, isDeleted: false }` (constante no service, ex.: `ACTIVE_NOT_DELETED` em `catalog.service.ts`). Exclusões são **soft delete** (e, quando necessário, cascata em transação atualizando filhos).

Novos recursos que precisem do mesmo comportamento devem seguir esse padrão em vez de `delete` físico, salvo decisão explícita em contrário.

### JSON no banco

Campos `Json` no Prisma (ex.: `Level.config`) devem ser gravados com cast apropriado (`Prisma.InputJsonValue`) quando o valor vem de `Record<string, unknown>` validado pelo Zod.

### Migrações

Alterações de schema: editar `prisma/schema.prisma`, gerar migração com `prisma migrate dev` (ou fluxo da equipe), commitar SQL em `prisma/migrations/`. Produção: `prisma migrate deploy`.

---

## 7. Contrato JSON da API (nomenclatura)

- **Preferir `snake_case`** nos nomes de propriedades expostas na API (`game_id`, `is_active`, `created_at`), como no módulo Catalog.
- Parâmetros de rota podem usar `snake_case` com segmentos alinhados (ex.: `:game_id`), coerentes com os schemas Zod de `params`.

No **código TypeScript interno** (services), é aceitável usar **camelCase** nos objetos de entrada do service (`gameId`, `isActive`) desde que o **controller** faça o mapeamento explícito a partir do body/params validados em snake_case — como em `catalog.controller.ts`.

---

## 8. Swagger / OpenAPI

- Configuração global: `buildSwaggerOptions()` em `src/config/swagger.ts` (título, servidor a partir de `APP_URL`, `bearerAuth`, lista inicial de `tags`).
- Ao criar um **novo domínio**, adicionar a tag em `openapi.tags` em `swagger.ts` para agrupamento limpo na UI (o módulo Catalog usa tag `Catalog`; inclua entrada equivalente ao adotar novas tags).
- Cada rota: `schema` apontando para objeto em `<nome>.swagger.ts`.
- Manter descrições de respostas alinhadas ao error handler (`VALIDATION_ERROR`, códigos de `AppError`).

---

## 9. Erros de domínio

Hierarquia em `src/shared/errors/`:

- `AppError` — base (`statusCode`, `code`).
- `NotFoundError` → 404, `NOT_FOUND`.
- `UnauthorizedError`, `ForbiddenError`, `ConflictError`, `ValidationError`, etc.

Serviços lançam essas classes; **não** enviam `reply` diretamente. O error handler traduz para JSON.

---

## 10. Checklist — novo recurso / novo módulo

1. **Domínio longitudinal / RMS:** revisar **[API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md](./API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md)** se a mudança tocar `Session`, `Match`, telemetria, progresso, catálogo ou linha do tempo.
2. **Prisma:** atualizar `schema.prisma`, migrar, `prisma generate`.
3. **Módulo:** criar pasta `src/modules/<nome>/` com `routes`, `controller`, `service`, `schema`, `swagger` (e helpers se preciso).
4. **Rotas:** registrar plugin em `src/app.ts` com prefixo `/api/v1/<nome>`.
5. **Swagger:** tag e schemas; garantir `security` nas rotas protegidas.
6. **Auth:** definir quais rotas são públicas vs `authenticate` vs `requireRole`.
7. **Validação:** Zod no controller; bodies `.strict()` quando não se quiser propriedades extras.
8. **Respostas:** 201 para criação, 204 para delete sem corpo, erros consistentes com o handler global.
9. **Imports:** sempre com extensão `.js` nos paths relativos.
10. **Testar:** manualmente via `/docs` ou cliente HTTP; verificar logs e códigos de erro.

---

## 11. Módulos existentes (referência)

Incluem, entre outros: `auth`, `matches`, `progress`, `sessions`, `bubbles`, `bestbeat`, `trunktilt`, `catalog`. Use o mais próximo do domínio novo como modelo (ex.: ingestão de partidas → `matches`; catálogo → `catalog`).

---

*Última revisão alinhada ao código em maio/2026. Ao divergir deste guia, prefira alinhar o código ao padrão descrito ou atualizar este documento explicitamente.*
