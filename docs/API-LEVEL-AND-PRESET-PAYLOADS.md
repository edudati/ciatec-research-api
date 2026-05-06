# O que a API devolve: preset e level (jogo)

Documento curto para o time do jogo e **agentes** que implementam o cliente: **que dados** a API envia sobre **preset** e **level**, e **em que momentos**.

**Fluxo HTTP completo** (sessão, match, telemetria, finish): [`API-GAMEPLAY-SESSIONS.md`](./API-GAMEPLAY-SESSIONS.md). **UUIDs `game_id` do seed:** `src/constants/game-ids.ts`.

**Não** existe hoje um endpoint do tipo `GET /presets/:id` ou `GET /levels/:id` no catálogo. O jogo combina:

1. **`GET /api/v1/progress/start?...`** — trilha completa do preset do jogador, *current level*, e **bests** por nível (ver abaixo).
2. **`POST /api/v1/sessions/matches`** com `level_id` — só se o nível estiver **desbloqueado**; devolve a **config da fase** fixada num *snapshot* para a partida.

Detalhe de implementação no servidor: [`PLAN-USER-LEVEL-PROGRESS.md`](./PLAN-USER-LEVEL-PROGRESS.md) (secção 7, UX).

Todas as rotas de gameplay requerem `Authorization: Bearer <accessToken>`.

---

## 1) Progresso: `GET /api/v1/progress/start?game_id=...&levels_detail=...`

Usado para criar ou recuperar o `user_game` do utilizador nesse jogo e devolver a **trilha** (todos os *levels* do *preset* actual no `user_games`).

### Query

| Parâmetro | Obrigatório | Notas |
| --- | --- | --- |
| `game_id` | sim | UUID do jogo |
| `levels_detail` | não (default: `summary`) | `summary` — a lista `levels[]` **não** inclui `config` em cada ponto (menos *payload*). `full` — cada item em `levels[]` inclui `config`. O **`current_level` inclui sempre `config`**, em ambos os modos. |

### O que o servidor escolhe na primeira vez

- **Preset:** o **preset *default* do jogo** (`presets.isDefault = true`); se nenhum estiver marcado, cai no primeiro `preset` por `id` ascendente. Só um *default* por jogo (índice único parcial no PostgreSQL). Não é escolha do cliente.
- **Level** inicial no `user_games`: o `level` com `order` mais baixo nesse preset. O **primeiro nível** fica com desbloqueio gravado; os restantes vêm com `unlocked: false` até a lógica de *finish* o permitir (progressão linear *default*).

Se já existir `user_game`, o preset não muda; devolve o estado actual, com trilha do preset em que o jogador está.

### Corpo de resposta (200)

| Campo | Conteúdo |
| --- | --- |
| `user_game_id` | UUID do registo de progresso (user + game) |
| `game` | `{ "id", "name" }` |
| `preset` | `{ "id", "name", "description" }` (description pode ser `null`) |
| **`levels`** | Array de **todos** os *levels* desse preset, ordenado por `order`, para a trilha. Por item, no mínimo: `id`, `name`, `order`, **`unlocked`**, **`completed`**, **`is_current`**, **`bests`** (object; métricas por jogo, ex. `score`, `timeMs`). Com `levels_detail=full`, cada item pode incluir ainda `config`. |
| **`current_level`** | Nível “em foco”: `id`, `name`, `order`, **`config`**, **`unlocked`**, **`completed`**, `is_current` (sempre `true`), **`bests`**. Trata o `config` como a fase actual; para consistência, o **Play** deve ainda depender do *snapshot* da *match* (ponto 2). |

A configuração jogável da fase *actual* no ecrã é principalmente **`current_level.config`**, mas a partida usa o *snapshot* da criação da *match*.

**Exemplo** (repartido, campos *essenciais* — `bests` reais vêm vazios ou com chaves de melhor desempenho):

```json
{
  "user_game_id": "…",
  "game": { "id": "…", "name": "…" },
  "preset": { "id": "…", "name": "…", "description": null },
  "current_level": {
    "id": "…",
    "name": "…",
    "order": 0,
    "config": { },
    "unlocked": true,
    "completed": false,
    "is_current": true,
    "bests": { }
  },
  "levels": [
    {
      "id": "…",
      "name": "…",
      "order": 0,
      "unlocked": true,
      "completed": false,
      "is_current": true,
      "bests": { }
    }
  ]
}
```

O `config` vazio `{}` em *seed* é possível; cada jogo define a estrutura. O **`POST .../matches/:id/finish`** *merge* `score`, `duration_ms` e chaves numéricas do `extra` nesses `bests` (regras no serviço).

---

## 2) Partida: `POST /api/v1/sessions/matches` — “pedir” um level específico

O jogo indica **explicitamente** qual fase vai jogar com `level_id` (e `game_id`).

**Corpo:**

```json
{
  "game_id": "<uuid>",
  "level_id": "<uuid>"
}
```

A API confirma que o level existe e que pertence ao `game_id` indicado. Caso contrário responde **404**. Se o nível **não** estiver **desbloqueado** para o utilizador, responde **403** (código de erro padrão da API, p.ex. `FORBIDDEN`).

### O que a API devolve (`201 Created`)

A API responde sempre **`201`** com o corpo do **registo de match** (não o mesmo objecto de `current_level`):

| Campo | Conteúdo |
| --- | --- |
| `id` | UUID da partida |
| `session_id` | Sessão diária |
| `game_id` | Igual ao pedido |
| `level_id` | Igual ao pedido |
| **`level_config_snapshot`** | **Cópia do `config` desse level** no momento em que a match foi criada. É o que o cliente deve tratar como config **imutável** para essa partida, mesmo que o level seja editado no futuro. |
| `started_at` | `Date` ISO |

Isto é o “envio para o jogo” quando o cliente **requisita jogar** um `level_id` concreto: a config joga-se a partir de **`level_config_snapshot`**, não (só) do último `GET /progress/start`.

Exemplo mínimo:

```json
{
  "id": "…",
  "session_id": "…",
  "game_id": "…",
  "level_id": "…",
  "level_config_snapshot": { },
  "started_at": "2026-04-14T18:45:02.008Z"
}
```

---

## 3) Resumo

| Pergunta | Onde responde a API |
| --- | --- |
| Trilha do *preset* + *current* + *bests* por nível? | `GET /progress/start` (campos `levels[]`, `current_level`, e `?levels_detail=...`) |
| Melhores resultados (por nível)? | Campo `bests` em cada nó; actualizado em cada `POST .../matches/:match_id/finish` |
| Qual a **config da fase** que esta **partida** usa? | `level_config_snapshot` em `POST /sessions/matches` para o `level_id` escolhido |
| Trocar de *preset* via API? | Não exposto hoje; o preset vem de `user_games` (na primeira ida: o *default* do jogo + primeiro *level* por `order`) |
| Progresso linear? | *Finish* com `completed: true` no *level* *actual* desbloqueia o seguinte e (quando aplica) avança o *cursor* em `user_games` |

Mais pormenores de sessão, eventos, telemetria e finish: [`API-GAMEPLAY-SESSIONS.md`](./API-GAMEPLAY-SESSIONS.md). Modelo de dados: [`GAME-OVERVIEW.md`](./GAME-OVERVIEW.md).
