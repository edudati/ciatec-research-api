# Unity Gameplay Sessions, Match e Telemetria

Guia pratico para dev Unity integrar o fluxo completo de gameplay.

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
- Limites de batch:
  - eventos: ate 500 por request;
  - landmarks: ate 100 frames por request;
  - inputs: ate 100 itens por request.

## Fluxo recomendado no cliente (ordem)

1. `POST /api/v1/sessions/start`
2. `GET /api/v1/progress/start?game_id=<uuid>`
3. `POST /api/v1/sessions/matches`
4. Durante a partida:
   - `POST /api/v1/matches/:match_id/events`
   - `POST /api/v1/matches/:match_id/telemetry/landmarks`
   - `POST /api/v1/matches/:match_id/telemetry/input`
5. Ao encerrar:
   - `POST /api/v1/matches/:match_id/finish`

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
- Guia alinhado ao *front* / payload: [`LEVEL-AND-PRESET-PAYLOADS.md`](./LEVEL-AND-PRESET-PAYLOADS.md).
- ID fixo do Bubli (seed): `d601b66e-2f7d-42bd-b7e2-11baa208faf3`.

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

- `POST /api/v1/matches/:match_id/events`
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

### 6) Enviar telemetria landmarks (batch)

- `POST /api/v1/matches/:match_id/telemetry/landmarks`
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

### 7) Enviar telemetria input (batch)

- `POST /api/v1/matches/:match_id/telemetry/input`
- Limite: ate 100 inputs por request

Body:

```json
{
  "inputs": [
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
- `404`: match nao encontrada ou sem permissao.
- `409`: match ja finalizada (somente no `/finish`).
