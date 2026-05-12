# Domínio da API, dados longitudinais e RMS/CRIS

Este documento complementa **[API-ARCHITECTURE-AND-CONVENTIONS.md](./API-ARCHITECTURE-AND-CONVENTIONS.md)**. **Roteamento de leitura:** [`AGENTS.md`](../AGENTS.md) e [`docs/README.md`](./README.md).

- **Convenções** (sempre que implementar na API) → stack, formato HTTP, padrão de módulo (`routes` / `controller` / `service` / `schema` / `swagger`), auth, nomenclatura de API.
- **Este documento** (sob demanda: `Session` / `Match`, telemetria, progresso, catálogo longitudinal, RMS/CRIS) → significado do domínio, entidades Prisma, relacionamentos, eixo longitudinal, telemetria por tabelas próprias, papel de **`timeline_events`**, integração entre módulos e regras ao evoluir para **projetos**, **grupos** e **participantes**.

Fonte de verdade do modelo atual: `prisma/schema.prisma` e registros de rotas em `src/app.ts`.

---

## 1. Visão geral do domínio

A API apoia **pesquisa longitudinal** com tarefas de jogos (cognitivas/motoras, etc.):

- **Organização no tempo** por **`Session`**: uma entrada por **participante** (`User`) e **data de sessão** (`sessionDate`), eixo “dia de coleta”.
- **Execução de tarefa** como **`Match`**: liga sessão, jogo (`Game`), nível (`Level`), snapshot de config (`levelConfigSnapshot`) e instante de início (`startedAt`).
- **Progresso** por participante e nível em **`UserLevelProgress`** (desbloqueio, conclusão, `bests` em Json).
- **Catálogo** de desenho experimental: **`Game` → `Preset` → `Level`**, administrado pelo módulo **`catalog`** (soft delete: `isActive` / `isDeleted`).
- **Telemetria densa** por jogo em **tabelas dedicadas** (ex.: `BubblesEvent`, `TrunktiltWorld`), sempre ancoradas em **`matchId`**.

Dimensões típicas de **RMS/CRIS** — **projeto de pesquisa**, **grupo**, vínculos formais participante–estudo — podem **ainda não** existir como modelos Prisma; quando forem introduzidas, devem ser **entidades próprias com FKs**, não “tudo em um Json” (ver seção 8).

---

## 2. Módulos da aplicação e prefixos

Prefixo global: **`/api/v1`** (`API_PREFIX` em `src/app.ts`).

| Caminho sob `/api/v1` | Pasta do módulo | Responsabilidade |
|----------------------|-----------------|-------------------|
| `/auth` | `auth` | Registro, login, refresh, logout, `me`; JWT com `sub` = `User.id` e `UserRole`. |
| `/matches` | `matches` | Ciclo de vida de `Match`, resultado, ingestão em lote quando aplicável. |
| `/sessions` | `sessions` | `Session` por usuário e data; ancora partidas do dia. |
| `/progress` | `progress` | `UserLevelProgress`, desbloqueio/conclusão/bests. |
| `/catalog` | `catalog` | CRUD de `Game` / `Preset` / `Level` (escrita `ADMIN` / `RESEARCHER`). |
| `/bubbles` | `bubbles` | Telemetria do jogo Bubbles ligada a `Match`. |
| `/bestbeat` | `bestbeat` | Telemetria do jogo Bestbeat ligada a `Match`. |
| `/trunktilt` | `trunktilt` | Telemetria TrunkTilt (world/pose/event) ligada a `Match`. |

Transversais: `src/config`, `src/lib/prisma.ts`, `src/shared` (erros, `authenticate`, `requireRole`).

---

## 3. Entidades principais (Prisma)

### Identidade e acesso

- **`User`**: pessoa no sistema; enum **`UserRole`**: `ADMIN` | `RESEARCHER` | `PLAYER`.
- **`AuthUser`**, **`RefreshToken`**: credenciais e tokens de refresh.

### Catálogo

- **`Game`**, **`Preset`**, **`Level`** (`Level.config` Json).

### Participante no desenho do jogo

- **`UserGame`**: usuário + jogo + preset + `currentLevelId`; único por (`userId`, `gameId`).

### Longitudinalidade operacional

- **`Session`**: `userId`, `sessionDate` (`Date` no PG), `startedAt`; **único** (`userId`, `sessionDate`).
- **`Match`**: `sessionId`, `gameId`, `levelId`, `levelConfigSnapshot`, `startedAt`; agrega resultado e telemetria.

### Resultado

- **`MatchResult`**, **`MatchResultDetail`** (`data` Json).

### Progresso por nível

- **`UserLevelProgress`**: (`userId`, `levelId`) único; `unlocked`, `completed`, `bests` Json.

### Telemetria (tabelas próprias por tipo/jogo)

- Bubbles: `BubblesEvent`, `BubblesPose`, `BubblesWorld`.
- Bestbeat: `BestbeatEvent`, `BestbeatPose`, `BestbeatWorld`.
- Trunktilt: `TrunktiltWorld`, `TrunktiltPose`, `TrunktiltEvent`.

---

## 4. Relacionamentos (integridade e leitura)

- `User` 1—N `Session`, `UserGame`, `UserLevelProgress`.
- `Session` 1—N `Match`.
- `Match` N—1 `Session`, `Game`, `Level`; `Match` 1—0..1 `MatchResult`, `MatchResultDetail`; 1—N linhas nas tabelas de telemetria.
- `Game` → `Preset` → `Level`; `UserGame` referencia preset e nível atual.
- `UserLevelProgress`: unicidade (`userId`, `levelId`).
- Onde o schema usa `onDelete: Restrict` em `Game`/`Level` ligados a `Match`, preserva-se histórico de coleta.

Novas entidades **Project**, **Group**, **Participant** (se separado de `User`): devem relacionar-se com **FKs explícitas** a `User`, `Session`, `Match` ou chaves de negócio estáveis — ver seção 8.

---

## 5. Fluxo de dados (alinhado ao padrão do projeto)

1. Cliente → **`/api/v1/...`** (JSON em **`snake_case`** onde o módulo já padroniza, ex. `catalog`).
2. **`preHandler`**: `authenticate`, `requireRole` quando aplicável.
3. **Controller**: validação **Zod** (`*.schema.ts`).
4. **Service**: **Prisma**, transações para operações multi-linha (ex. soft delete em cascata no catálogo); lança `NotFoundError`, `ForbiddenError`, etc.
5. **Resposta**: corpo direto ou `204`; erros via `setErrorHandler` em `app.ts`.

**Fluxo longitudinal típico hoje:** garantir ou obter **`Session`** do dia → criar/usar **`Match`** → ingerir telemetria nas tabelas do jogo → finalizar **`Match`** → atualizar **`MatchResult`** / **`UserLevelProgress`** conforme regras do módulo `progress` / `matches`.

---

## 6. Responsabilidades por módulo (integração)

- **`auth`**: identidade; JWT com `sub` e `role`.
- **`sessions`**: fronteira “dia de estudo”; fornece `sessionId` coerente com `userId` + data.
- **`matches`**: unidade primária de coleta de uma corrida; orquestra sessão, jogo, nível.
- **`progress`**: estado longitudinal de níveis (`UserLevelProgress`) alinhado a preset/ordem de níveis.
- **`catalog`**: governança de `Game`/`Preset`/`Level`; `Match.levelConfigSnapshot` preserva contexto no momento da coleta.
- **Módulos por jogo**: apenas persistência/consulta de séries ligadas a **`matchId`**; não substituir o papel de `Session` nem duplicar fatos de resultado em Json genérico sem necessidade.

Ao adicionar **Project** / **Group**, os serviços que criam `Session` ou `Match` passam a validar **pertencimento** (participante inscrito no projeto, etc.) — sem colocar essa lógica só no cliente.

---

## 7. Modelagem Prisma / PostgreSQL (regras)

- IDs `String` UUID na maioria dos modelos; `createdAt` / `updatedAt`; `@@map("snake_case")` nas tabelas.
- **Índices** compostos em telemetria: padrão `(matchId, timestamp)` ou equivalente (`timestampMs`, `frameId`) conforme o jogo.
- **Json**: para config evolutiva (`Level.config`), detalhe opaco (`MatchResultDetail.data`), eventos `type` + `data` — **não** para substituir entidades de relatório estáveis (**projeto**, **grupo**, **inscrição**).
- **Soft delete** no catálogo: `isDeleted` / `isActive`; consultas “visíveis” filtram registros ativos e não deletados (padrão do `catalog.service.ts`).

---

## 8. Participantes, pesquisadores, projetos e grupos (RMS/CRIS)

### Mapeamento com o modelo atual

- **Participante** (sujeito do estudo): na API atual, corresponde tipicamente a **`User`** com **`UserRole.PLAYER`** (evoluir para tabela **`Participant`** só se houver separação clínica vs. conta de login; manter **FK** `participantId` → `User` ou modelo dedicado).
- **Pesquisador**: **`UserRole.RESEARCHER`** ou **`ADMIN`** para operações de catálogo e, no futuro, gestão de projeto/grupo.
- **Projeto** / **Grupo**: **não** modelados no `schema.prisma` atual como tabelas próprias; são **extensões planejadas** para RMS/CRIS.

### Regra ao implementar

- Cada um: **modelo Prisma próprio** (`Project`, `ResearchGroup`, `ProjectEnrollment`, etc.) com **FKs** e índices para consultas por projeto/participante/data.
- Não armazenar árvore de estudo inteira em um único Json sem chaves normalizadas quando o relatório longitudinal depende disso.

---

## 9. Eventos longitudinais e `timeline_events`

### O que é fonte de verdade hoje

- **Dia**: `Session.sessionDate` + `Session.userId`.
- **Corrida**: `Match.startedAt`, `Match` ligação a `sessionId`, `gameId`, `levelId`.
- **Alta densidade**: linhas em `*Event`, `*World`, `*Pose` indexadas por `matchId` (e tempo).

### Papel de `timeline_events` (camada unificadora)

**`timeline_events` não existe ainda no schema;** quando for adicionado, deve obedecer:

1. **Somente camada de visualização / agregação longitudinal** (UI, export CRIS, dashboards), **não** substituto das tabelas de telemetria nem do `MatchResult` detalhado.
2. Campos típicos: `occurred_at`, tipo de evento estável (`event_type` enum ou string versionada), `participant_id` (ex. `User.id` do papel participante), referências opcionais `session_id`, `match_id`, `project_id`, `group_id`, e **ponteiro para a fonte** (FK polimórfica disciplinada ou colunas `source_table` + `source_id` com convenção de escrita única no service).
3. **Não** duplicar payload de séries grandes (ex. todas as linhas de `TrunktiltPose`); apontar para `Match` ou para agregados já calculados.
4. **Materialização**: escrita no fechamento de `Match`, em transições de `UserLevelProgress`, ou em jobs assíncronos — mantendo handlers HTTP enxutos e padrão **controller → service**.

---

## 10. Autenticação e autorização (domínio)

- JWT Bearer; `authenticate` + `requireRole` conforme rota.
- Payload: `sub` = id de `User`, `role` = `UserRole`.
- Operações de participante vs. pesquisador devem permanecer **explícitas** nas rotas (`requireRole`), alinhado a `API-ARCHITECTURE-AND-CONVENTIONS.md`.

---

## 11. Convenções de nomenclatura (domínio e API)

- Propriedades JSON na API: **`snake_case`** (`session_date`, `game_id`, `is_active`, `created_at`) onde o módulo segue esse padrão.
- Banco: `@map` para colunas snake_case quando o campo Prisma é camelCase.
- Novos recursos longitudinais: nomes de tabela em **snake_case** no PostgreSQL; modelos Prisma em **PascalCase**.

---

## 12. Estratégia de escalabilidade

- API **stateless**; JWT para sessão de cliente.
- PostgreSQL com índices alinhados a consultas por `matchId` e tempo.
- Crescimento de telemetria: considerar **particionamento**, **retenção** por política, **réplica de leitura** ou export analítico — sem abandonar o padrão modular (service + Prisma).
- **`timeline_events`** mantém consultas de linha do tempo **sem** varrer todas as tabelas de alta frequência.

---

## 13. Integração entre módulos (obrigatório ao desenhar features)

- `sessions` → fornece `sessionId` usado por `matches`.
- `matches` → fornece `matchId` para `bubbles` / `bestbeat` / `trunktilt`.
- `progress` → consistente com `UserGame` e ordem de `Level`.
- `catalog` → altera definição de níveis; `Match.levelConfigSnapshot` congela o contexto da coleta.
- `auth` → `sub` identifica o `User` nas rotas do participante.

Com **Project/Group**, novas FKs em `Session` ou `Match` (ou apenas em `timeline_events` + tabelas de inscrição) devem ser definidas de forma que **consultas por participante e intervalo de datas** permaneçam indexáveis.

---

## 14. Regras arquiteturais obrigatórias (checklist para agentes)

1. Seguir **API-ARCHITECTURE-AND-CONVENTIONS.md** para código (módulo, Zod, Swagger, `.js` nos imports, erros).
2. **Entidades de negócio complexas** → **tabelas próprias** + **FKs**; Json só onde o conteúdo é evolutivo ou opaco por natureza.
3. **Telemetria densa** → tabelas dedicadas por formato/jogo; **não** empurrar séries inteiras para `timeline_events`.
4. **`timeline_events`** (quando existir) → **somente** camada unificadora de **visualização longitudinal**, com referência à fonte, não fonte única de verdade científica.
5. Eixo longitudinal operacional: **`User` → `Session` (data) → `Match` → tabelas de jogo**; novas soluções devem **respeitar** esse eixo ou estendê-lo com migrações explícitas (não quebrar unicidade `userId`+`sessionDate` sem decisão documentada).
6. **Soft delete** no catálogo: manter padrão `isActive`/`isDeleted` e filtros nos services de leitura.

---

*Documento de domínio longitudinal. Manter alinhado a `prisma/schema.prisma`; ao mudar o modelo de dados, atualizar este arquivo na mesma PR sempre que a mudança alterar significado para RMS/CRIS ou para integração entre módulos.*
