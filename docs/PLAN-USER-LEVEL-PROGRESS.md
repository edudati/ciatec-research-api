# Plano de implementação: progresso e bests por level (tabela única)

Objetivo: uma **única tabela geral** `user_level_progress` (nome final ajustável) com uma linha por par **(user, level)**, suportando desbloqueio, conclusão e **métricas de melhor marca** variáveis por jogo num campo **`bests` JSONB**, sem tabelas por título.

**Documentação de integração para o *front* (contratos HTTP):** [`LEVEL-AND-PRESET-PAYLOADS.md`](./LEVEL-AND-PRESET-PAYLOADS.md) e, para o fluxo Unity, [`UNITY-GAMEPLAY-SESSIONS.md`](./UNITY-GAMEPLAY-SESSIONS.md) (alinhado após a implementacao).

---

## 1. Modelo de dados (Prisma)

Novo model (ex.: `UserLevelProgress` → mapear para `user_level_progress`).

| Campo | Tipo | Notas |
| --- | --- | --- |
| `id` | `String` @id uuid | opcional: PK composto (user+level) sem id extra, mas uuid simplifica relações no código |
| `userId` | FK → `User` | `onDelete: Cascade` |
| `levelId` | FK → `Level` | `onDelete: Restrict` (ou `Cascade` se apagar level apagar progresso) — alinhar com política de retenção |
| `unlocked` | `Boolean` | default `false` ou `true` consoante regra inicial; seed/criação ajusta |
| `completed` | `Boolean` | fase concluída com sucesso (pelo menos uma vez) |
| `bests` | `Json` | `jsonb` no PG; *shape* variável por jogo (ex. `{ "score", "timeMs", "reactionMs" }`); *merge* no código no `finish` |
| `updatedAt` / `createdAt` | `DateTime` | trilho de auditoria; opcional `lastPlayedAt` |

**Constraint:** `@@unique([userId, levelId])`

**Relações inversas:** adicionar `userLevelProgress` em `User` e `Level` (e opcionalmente em `Game` só via join, **não** em `Game` diretamente, para manter 1 tabela genérica).

**Índices:** o unique já indexa; se houver muita leitura “todos os levels de um `user` num `game`”, o caminho passa por join `level.presetId` → `preset.gameId` (já explicado no plano de leitura).

Não alocar coluna por jogo: **tudo** o que for específico fica em `bests` (e eventualmente regras em `Game`).

**Opcional (fase 2+):** em `Game` um campo `progression` ou `json` de config: `mode: "LINEAR" | "FREE"`, `unlockRule`, etc. — a lógica de *quem* está desbloqueado aplica no serviço.

---

## 2. Migração SQL (Prisma migrate)

- Novo ficheiro `migration` que cria `user_level_progress` com a constraint e FKs.
- **Não** é obrigatório backfill completo no mesmo PR; podes fazer tabela vazia e o primeiro `finish`/`getProgress` a criar linhas em `upsert`.

**Backfill opcional (se quiseres estado inicial coerente):**

- Para pares `user_games` existentes: criar para o `currentLevelId` e levels com `order` &lt; current (no mesmo `preset` que a match progressão linear assumia) linhas `unlocked`/`completed` aproximadas, ou
- deixar backfill a zero e confiar no próximo jogo; ou script SQL one-off a partir de `match_results` + `matches` (níveis com `completed=true`).

Definir política e documentar num comentário da migração/PR.

---

## 3. Módulo de regras (código) — ponto crítico

Criar um ficheiro dedicado, ex.: `src/modules/progress/level-progress.rules.ts` (ou `.../bests.ts`), com:

1. **`mergeBests(gameId, previous: Prisma.JsonValue, incoming: Record<string, unknown> | from extra + matchResult): Prisma.JsonValue`**  
   - Sabe quais chaves de `bests` existem por *jogo* (ou delega a um *registry* `Map<gameId, GameBestsConfig>` lido de env/DB).  
   - “Melhor” = maior *score*, menor *timeMs* — definido no config por jogo, não no JSON cego.

2. **`shouldAdvanceCurrentLevel(...)`** — hoje: só avança se `current === match.level` e `completed` (manter; eventualmente *FREE* pula o avanço automático ou aplica regra de desbloqueio múltipla).

3. **`computeUnlocksAfterComplete(...)`** (opcional na 1.ª fase) — p.ex. desbloquear `order+1` no preset.

Evita espalhar lógica de comparação JSON no `matches.service` bruto: **o serviço chama funções de regra**.

---

## 4. Alterações por fluxo (ordem sugerida de implementação)

### Fase A — Base de dados e escrita no `finish`

- Implementar o model + migração.
- Em **`createMatchesService.finish`** (mesma *transaction* onde já se cria `match_result` e se actualiza `user_games`):
  1. `upsert` em `user_level_progress` para `(userId, match.levelId)`.
  2. Se `input.completed` (e eventualmente regra “conta para bests”):
     - Marcar `completed: true` (não volte a `false`).
  3. Calcular *novo* `bests` a partir de `input.score`, `input.durationMs`, e **fragmentos de `input.extra` ou convenção** (ex. `reactionTimeMs` em `extra`) e `mergeBests` com a linha anterior.
  4. `unlocked: true` para o level em que se jogou (e lógica extra para vizinhos se afinarem desbloqueio).
  5. Manter/ajustar a actualização de `user_games.currentLevelId` existente; eventualmente restringir a jogos *LINEAR* e para *FREE* só `bests` + `completed` + `unlocked` sem forçar cursor (decisão de produto — documentar).

Garantir que tudo acontece no **mesmo** `prisma.$transaction` para coerência.

### Fase B — Leitura: `GET /api/v1/preset` + `GET /api/v1/levels/:level_id`

- **`GET /preset?game_id=`**: para o `user_game` do `(user, game)`, carregar `levels` do `preset` ordenados por `order`, com join a `user_level_progress`; resposta **sem** `config` na trilha (estratégia *slim* fixa).
- **`GET /levels/:level_id`**: devolve o nível completo com `config` se estiver desbloqueado (403 caso contrário).

### Fase C — Validação de `createMatch`

- Após a progressão existir: em **`sessionsService.createMatch`**, antes de criar match (ou depois de carregar o `level`), verificar se o `level` está `unlocked` para o `user` (ou se o jogo está em modo *FREE* e tudo o que pertence ao jogo/preset do `user_games` está acessível — regra a fixar).  
- Se bloqueado: `403` com código claro, ou `400`, conforme convenção da API.

*Ordem Mínima Viable Product:* A → B (só leitura) → C, ou A → C se quiseres forçar desbloqueio cedo; sem `unlocked` preenchido, tudo fica *false* e bloqueia — aí fazer *seed* ou *first unlock* na criação de `user_game` (p.ex. desbloquear `order: 0` do preset).

**Seed de desbloqueio na criação de `user_games`:** ao primeiro `GET /preset` (criação de `user_games`), garantir desbloqueio do primeiro `level` por `order` (como hoje via `ensureFirstLevelUnlockedInPreset`).

### Fase D — Contrato e documentos

- Actualizar `progress.swagger.ts` e `UNITY-GAMEPLAY-SESSIONS.md` + `LEVEL-AND-PRESET-PAYLOADS.md` com os contratos `GET /preset` e `GET /levels/:id`.
- `finish`: opcionalmente resposta a incluir `bests_Updated` / snapshot para o cliente otimisticamente actualizar a UI (nice-to-have).

### Fase E — Testes

- Teste de integração ou serviço: *finish* duas vezes com scores diferentes → `bests` com merge correcto.  
- *createMatch* em level bloqueado → erro esperado.  
- Modo *FREE* (futuro) coberto por regra mockada se já existir `Game` config.

---

## 5. Riscos e decisões pendentes

| Tema | Decisão a tomar |
| --- | --- |
| Quem manda a “reacção” / métricas extra | Vindas de `extra` no `finish` com *schema* por jogo documentada; o servidor *só* aplica regras de *merge* confiáveis, não acredita cegamente nada que não alinhem no contrato. |
| Idempotência de `bests` | Sempre comparar com `mergeBests`; nunca *overwrite* o JSON inteiro sem *merge* consciente. |
| Tamanho do `bests` | Manter chaves e valores pequenos; evitar anexar arrays grandes. |
| Apagar `Level` com progresso | `Restrict` força a pensar; ou `SetNull` / soft-delete de levels. |

---

## 6. Resumo executivo

1. Tabela **única** `user_level_progress` com `@@unique([userId, levelId])` e **`bests Json`**.  
2. **`finish`** a fazer *upsert* + *merge* e a manter a transacção.  
3. **`GET /preset`** a devolver a lista de levels + estados; **`GET /levels/:id`** para `config`.  
4. **`createMatch`** a respeitar `unlocked` quando a fase C estiver activa, com regra inicial a partir de `user_games` + criação do primeiro *unlock*.  
5. Lógica de *merge* e de *modo* de jogo em **código reutilizável** por `gameId`, **não** tabelas por jogo.

Este plano fica alinhado com tudo o que discutiste (tabela geral, custo de leitura/escrita, flexibilidade por título) sem piorar o fluxo *finish* (continua 1 *round-trip* lógica por partida, dentro da mesma transacção que já usam).

---

## 7. Entrada do jogo e clique no level (contrato UX + API)

### 7.1 O que a API devolve **à entrada** (um pedido, preset do `user_games`)

Objectivo: o cliente monta a **trilha** (todos os *nodes* do preset) e sabe o **nivel “actual”** (realce / cursor).

- **`current_level`:** `id`, `name`, `order`, flags e `bests` — **sem** `config` na resposta de `GET /preset`; o cliente chama **`GET /levels/:id`** para o `config`.
- **`preset`:** `id`, `name`, (opcional `description`).
- **`levels`:** **lista ordenada** por `order` com, no mínimo, por item:
  - `id`, `name`, `order`
  - `unlocked`, `completed` (vindos de `user_level_progress` + regras)
  - (opcional) `is_current: boolean` (redundante com `current_level.id`, mas prático no front)

**Peso de payload:** a API fixou estratégia **B** — `GET /preset` é *slim*; `config` vem em **`GET /levels/:level_id`** quando o cliente precisa (nível desbloqueado).

A origem de verdade do preset continua a ser o **`user_games.presetId`**: essa trilha representa **sempre o preset** associado àquele jogador naquele jogo.

### 7.2 Clicar num level vs. clicar em **Play**

O *clique* que interessa é em **um nível específico** na trilha (nó do mapa), **não** em “trocar de preset” (o preset vem do `user_games` e é único nesse ecrã, salvo outro *flow* de produto). **Bests** estão por **nivel** (`level_id`).

Dois momentos; podes afinar o *timing* consoante a UX e o tamanho do *asset* lógico (`config`).

| Momento | O que precisas | Sugestão |
| --- | --- | --- |
| **Clique (selecionar na trilha)** | **Bests**, título, bloqueado, concluído | Vêm em `GET /preset` (`levels[]`). Opcional: `GET /levels/:id` para **`config`** se a UX precisar de pré-visualização (nível desbloqueado). |
| **Play (iniciar partida)** | **Config** imutável para a partida | `POST /api/v1/sessions/matches` devolve **`level_config_snapshot`** — fonte de verdade para essa *match*, mesmo que já tenhas chamado `GET /levels/:id` antes. |

**Resumo:** trilha + bests = `GET /preset`. **Config** por nível = `GET /levels/:id` quando precisares. **Snapshot da partida** = `level_config_snapshot` após `POST /sessions/matches`.
