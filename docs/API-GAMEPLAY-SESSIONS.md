# Unity Gameplay Sessions, Match e Telemetria

Guia pratico para dev Unity (e **agentes** que geram integração) seguirem o fluxo completo de gameplay.

**Leitura em par:** [`API-LEVEL-AND-PRESET-PAYLOADS.md`](./API-LEVEL-AND-PRESET-PAYLOADS.md) (preset, níveis, `progress/start`, snapshot da match).

**UUIDs fixos dos jogos no seed** (fonte no código: `src/constants/game-ids.ts`):

| Jogo     | `game_id` (exemplo seed) |
| -------- | ------------------------ |
| Bubbles  | `d601b66e-2f7d-42bd-b7e2-11baa208faf3` |
| Bestbeat | `e802c4a6-1b2d-4e3f-8a9b-0c1d2e3f4a5b` |
| TrunkTilt | `a1b2c3d4-e5f6-4789-a8b0-c1d2e3f4a5b6` |

## Objetivo deste documento

Ao final da implementacao no cliente, o jogo deve conseguir:

1. Abrir/retomar sessao diaria.
2. Obter progresso e level atual.
3. Criar match.
4. Enviar eventos e telemetria durante a partida.
5. Finalizar match com resultado.

## Regras obrigatorias de integracao

- Enviar `Authorization: Bearer <accessToken>` em todos os endpoints de gameplay.
- Nunca enviar `user_id` no payload.
- A API usa o `sub` do JWT como identidade do jogador.
- `timestamp` de eventos/telemetria sempre em **epoch milissegundos** (exemplo: `1760001130120`).
- `data` em eventos e telemetria e JSON livre.
- Limites de batch (**bubbles** e **bestbeat** — JSON genérico):
  - eventos: ate 500 por request;
  - landmarks (telemetria JSON): ate 100 frames por request;
  - world (telemetria JSON): ate 100 frames por request.
- **TrunkTilt** usa payloads tipados e limites diferentes (ex.: world e pose ate **200** frames por request, eventos ate **500**); contrato em **Swagger** (tag TrunkTilt em `/docs`) e código em `src/modules/trunktilt/`.

## Fluxo recomendado no cliente (ordem)

1. `POST /api/v1/sessions/start`
2. `GET /api/v1/progress/start?game_id=<uuid>`
3. `POST /api/v1/sessions/matches`
4. Durante a partida (prefixo por jogo — exemplos **bubbles** e **bestbeat**):
   - `POST /api/v1/bubbles/matches/:match_id/events` ou `POST /api/v1/bestbeat/matches/:match_id/events`
   - `POST /api/v1/bubbles/matches/:match_id/telemetry/pose` ou `.../bestbeat/.../telemetry/pose`
   - `POST /api/v1/bubbles/matches/:match_id/telemetry/world` ou `.../bestbeat/.../telemetry/world`
5. Ao encerrar:
   - `POST /api/v1/matches/:match_id/finish`

TrunkTilt: `POST /api/v1/trunktilt/matches/:match_id/...` (world, pose, eventos com tipos fixos). Detalhes no **Swagger** e em `src/modules/trunktilt/`.

## Contratos de endpoint

### 1) Iniciar/obter sessao diaria

- `POST /api/v1/sessions/start`
- Body: `{}` (vazio)
- Status:
  - `201`: sessao criada hoje
  - `200`: sessao do dia ja existia

Resposta:

```json
{
  "id": "7f30f09f-5f7a-4f74-9357-6b617ca4be31",
  "user_id": "c2a2d2e5-8f2f-4d05-a90a-4efbeaf4e447",
  "started_at": "2026-04-14T18:40:21.153Z"
}
```

### 2) Consultar sessao atual sem criar

- `GET /api/v1/sessions/current`
- Body: vazio

Resposta com sessao:

```json
{
  "session": {
    "id": "7f30f09f-5f7a-4f74-9357-6b617ca4be31",
    "user_id": "c2a2d2e5-8f2f-4d05-a90a-4efbeaf4e447",
    "started_at": "2026-04-14T18:40:21.153Z"
  }
}
```

Resposta sem sessao:

```json
{
  "session": null
}
```

### 3) Iniciar/obter progresso do jogo

- `GET /api/v1/progress/start?game_id=<uuid>&levels_detail=summary|full` (o segundo query param e opcional; *default* `summary`)
- Body: vazio
- Retorna `user_game_id`, `game`, `preset` (com `description` opcional), `current_level` (sempre com `config`, mais `unlocked`, `completed`, `is_current`, `bests`) e **`levels`**: a trilha completa do *preset* actual, com `id`, `name`, `order`, `unlocked`, `completed`, `is_current`, `bests` e, com `levels_detail=full`, `config` em cada ponto. Em `summary` nao manda o `config` de cada ponto da trilha (menor payload), mas o `current_level` continua com `config` completo.
- Guia alinhado a preset/níveis: [`API-LEVEL-AND-PRESET-PAYLOADS.md`](./API-LEVEL-AND-PRESET-PAYLOADS.md).
- `game_id` do **bubbles** na tabela no topo; usar o UUID correcto para **bestbeat** ou **trunktilt** quando aplicável.

### 4) Criar match

- `POST /api/v1/sessions/matches`
- O **level** precisa estar **desbloqueado**; caso contrario a API responde **403**.
- Status: `201` em match criada (cada pedido cria uma partida nova; dedupe por janela de tempo está desactivado até termos regra no `finish`).

Body:

```json
{
  "game_id": "d601b66e-2f7d-42bd-b7e2-11baa208faf3",
  "level_id": "c7476ec4-2bc5-4fee-afde-648e82fef278"
}
```

Resposta:

```json
{
  "id": "0a01f0a8-7a63-45f5-bf84-a45a9f8f2307",
  "session_id": "7f30f09f-5f7a-4f74-9357-6b617ca4be31",
  "game_id": "d601b66e-2f7d-42bd-b7e2-11baa208faf3",
  "level_id": "c7476ec4-2bc5-4fee-afde-648e82fef278",
  "level_config_snapshot": {},
  "started_at": "2026-04-14T18:45:02.008Z"
}
```

### 5) Enviar eventos de gameplay (batch)

- `POST /api/v1/bubbles/matches/:match_id/events` ou `POST /api/v1/bestbeat/matches/:match_id/events` (conforme o `game_id` da match)
- Limite: ate 500 eventos por request

Body:

```json
{
  "events": [
    { "type": "jump", "timestamp": 1760001131000, "data": { "height": 1.2 } },
    { "type": "hit", "timestamp": 1760001131250, "data": { "target": "wall" } }
  ]
}
```

### 6) Enviar telemetria landmarks (batch, JSON generico)

- `POST /api/v1/bubbles/matches/:match_id/telemetry/pose` ou `POST /api/v1/bestbeat/matches/:match_id/telemetry/pose`
- Limite: ate 100 frames por request

Body:

```json
{
  "frames": [
    {
      "timestamp": 1760001131033,
      "data": {
        "joints": {
          "left_knee": { "x": 0.1, "y": 0.5, "z": 0.0 }
        }
      }
    }
  ]
}
```

### 7) Enviar telemetria world (batch, JSON generico)

- `POST /api/v1/bubbles/matches/:match_id/telemetry/world` ou `POST /api/v1/bestbeat/matches/:match_id/telemetry/world`
- Limite: ate 100 frames por request

Body:

```json
{
  "frames": [
    {
      "timestamp": 1760001131010,
      "device": "mouse",
      "data": { "x": 120, "y": 340, "drag_ms": 200 }
    },
    {
      "timestamp": 1760001131200,
      "device": "keyboard",
      "data": { "key": "space", "pressure": 0.8 }
    }
  ]
}
```

### 8) Finalizar match

- `POST /api/v1/matches/:match_id/finish`

Body:

```json
{
  "score": 1500,
  "duration_ms": 45000,
  "completed": true,
  "extra": { "errors": 2, "bonus_collected": 5 }
}
```

Resposta:

```json
{
  "id": "f9bb51e4-0eb2-4a8f-90d4-5de4472e5108",
  "match_id": "0a01f0a8-7a63-45f5-bf84-a45a9f8f2307",
  "score": 1500,
  "duration_ms": 45000,
  "completed": true,
  "extra": { "errors": 2, "bonus_collected": 5 },
  "created_at": "2026-04-15T10:10:00.000Z"
}
```

Importante:
- segunda tentativa de finalizar a mesma match retorna `409 Conflict`.

## Estrategia de envio no cliente

- Eventos e telemetria devem ser enviados em lotes pequenos e frequentes.
- Em caso de falha de rede:
  - manter fila local;
  - reenviar na ordem dos `timestamp`;
  - evitar duplicacao desnecessaria.
- Ao finalizar match, tentar flush da fila antes de chamar `/finish`.

## Erros esperados

- `400`: payload invalido (schema).
- `401`: token ausente/invalido.
- `403`: nivel bloqueado (ex.: criar match sem desbloquear).
- `404`: recurso inexistente ou nao autorizado ao utilizador (user, jogo, level, match, etc., conforme o endpoint).
- `409`: match ja finalizada (somente no `/finish`).
