# TrunkTilt — Integração com a API (lado do jogo)

Documento de referência para o dev Unity: quais chamadas fazer, em que ordem, e qual estrutura de dados esperar ou enviar.

O jogo roda embarcado numa página web. O MediaPipe processa os **landmarks** no JS da página e envia o array **`landmarks`** por frame para a API separadamente. O Unity é responsável pelo fluxo de gameplay e telemetria do mundo do jogo.

Complementa [`API-GAMEPLAY-SESSIONS.md`](./API-GAMEPLAY-SESSIONS.md) e [`API-TRUNKTILT-IMPLEMENTATION.md`](./API-TRUNKTILT-IMPLEMENTATION.md).

---

## 1. Fluxo completo (ordem obrigatória)

```
1. POST /api/v1/sessions/start
2. GET  /api/v1/progress/start?game_id=<uuid>
3. POST /api/v1/sessions/matches
4. [durante a partida]
   POST /api/v1/trunktilt/matches/:match_id/events          (eventos discretos)
   POST /api/v1/trunktilt/matches/:match_id/telemetry/world (amostras contínuas — Unity)
   POST /api/v1/trunktilt/matches/:match_id/telemetry/pose (MediaPipe landmarks — JS da página)
5. POST /api/v1/matches/:match_id/finish
```

O `match_id` retornado no passo 3 é usado em todas as chamadas subsequentes.

---

## 2. Abrir sessão

```
POST /api/v1/sessions/start
Body: {}
```

**Resposta:**

```json
{
  "id": "7f30f09f-...",
  "user_id": "c2a2d2e5-...",
  "started_at": "2026-05-04T18:40:21.153Z"
}
```

Guardar o `id` como `session_id`. Retorna `201` se sessão criada hoje, `200` se já existia — tratar os dois da mesma forma.

---

## 3. Obter progresso e level atual

```
GET /api/v1/progress/start?game_id=<uuid>
```

**Resposta relevante para o TrunkTilt:**

```json
{
  "user_game_id": "...",
  "game":   { "id": "...", "name": "TrunkTilt" },
  "preset": { "id": "...", "name": "Trilha padrão", "description": null },
  "current_level": {
    "id":        "...",
    "name":      "Fase 01",
    "order":     0,
    "unlocked":  true,
    "completed": false,
    "is_current":true,
    "bests":     {},
    "config": {
      "levelName": "Fase 01",
      "cellSize":  10,
      "grid": [
        { "row": [0, 0, 0, 0, 0, 0] },
        { "row": [0, 6, 1, 5, 1, 0] },
        { "row": [0, 0, 0, 1, 7, 0] }
      ],
      "details": [
        { "tileId": 5, "x": 3, "y": 1, "coinValue": 10 }
      ]
    }
  },
  "levels": [
    { "id": "...", "name": "Fase 01", "order": 0, "unlocked": true,  "completed": false, "is_current": true,  "bests": {} },
    { "id": "...", "name": "Fase 02", "order": 1, "unlocked": false, "completed": false, "is_current": false, "bests": {} }
  ]
}
```

**O que usar:**

| Campo | Uso no jogo |
|---|---|
| `levels[]` | Montar a tela de seleção de fases / trilha do preset |
| `levels[].unlocked` | Exibir fase bloqueada ou disponível |
| `levels[].completed` | Exibir fase já concluída |
| `levels[].bests` | Exibir melhor pontuação por fase (se houver) |
| `current_level.id` | `level_id` para criar a match |
| `current_level.config` | Referência visual da fase — **não usar para construir o mapa** |

> ⚠️ O `current_level.config` serve para exibir informações da fase antes de jogar. O mapa deve ser construído a partir do `level_config_snapshot` retornado na criação da match (passo 4).

---

## 4. Criar match

```
POST /api/v1/sessions/matches
```

**Body:**

```json
{
  "game_id":  "<uuid do jogo>",
  "level_id": "<uuid do level selecionado>"
}
```

**Resposta:**

```json
{
  "id":         "0a01f0a8-...",
  "session_id": "7f30f09f-...",
  "game_id":    "...",
  "level_id":   "...",
  "started_at": "2026-05-04T18:45:02.008Z",
  "level_config_snapshot": {
    "levelName": "Fase 01",
    "cellSize":  10,
    "grid": [
      { "row": [0, 0, 0, 0, 0, 0] },
      { "row": [0, 6, 1, 5, 1, 0] },
      { "row": [0, 0, 0, 1, 7, 0] }
    ],
    "details": [
      { "tileId": 5, "x": 3, "y": 1, "coinValue": 10 }
    ]
  }
}
```

Guardar `id` como `match_id`.

**O `level_config_snapshot` é o JSON que alimenta o `MapGenerator`.** É uma cópia imutável da configuração do level no momento em que a match foi criada — usar este e não o `current_level.config`.

**Erros possíveis:**

| Status | Motivo |
|---|---|
| `403` | Level bloqueado para o jogador |
| `404` | `level_id` ou `game_id` inválido |

---

## 5. Eventos discretos de gameplay

```
POST /api/v1/trunktilt/matches/:match_id/events
Limite: até 500 eventos por request
```

**Body:**

```json
{
  "events": [
    { "type": "COIN_COLLECTED",    "timestamp": 1760001131000, "data": { "x": 30.0, "y": 2.5, "z": 10.0, "value": 10 } },
    { "type": "CHECKPOINT_REACHED","timestamp": 1760001132000, "data": { "x": 40.0, "y": 0.0, "z": 20.0 } },
    { "type": "FALL_OCCURRED",     "timestamp": 1760001133000, "data": { "x": 15.0, "y": -5.0,"z": 8.0  } },
    { "type": "LEVEL_COMPLETED",   "timestamp": 1760001160000, "data": {} },
    { "type": "LEVEL_FAILED",      "timestamp": 1760001160000, "data": { "reason": "timeout" } }
  ]
}
```

**Tipos de evento do TrunkTilt:**

| Tipo | Quando emitir | Campos em `data` |
|---|---|---|
| `LEVEL_STARTED` | Ao iniciar a partida | `{}` |
| `COIN_COLLECTED` | Colisão com moeda | `x`, `y`, `z`, `value` |
| `CHECKPOINT_REACHED` | Colisão com checkpoint | `x`, `y`, `z` |
| `FALL_OCCURRED` | Colisão com kill zone | `x`, `y`, `z` |
| `RESPAWN` | Após queda, ao reaparecer | `x`, `y`, `z` |
| `LEVEL_COMPLETED` | Player entra no tile End | `{}` |
| `LEVEL_FAILED` | Timeout ou game over | `reason: "timeout"` |

**Regras:**
- `timestamp` sempre em epoch milissegundos.
- Enviar em lote — não fazer uma chamada por evento.
- Em caso de falha de rede, manter fila local e reenviar na ordem dos `timestamp`.

---

## 6. Telemetria contínua do mundo do jogo

```
POST /api/v1/trunktilt/matches/:match_id/telemetry/world
Limite: até 200 frames por request
```

**Body:**

```json
{
  "frames": [
    {
      "timestampMs":           1760001131033,
      "frameId":               350,
      "ballPosition":          { "x": 12.4, "y": 1.1, "z": 8.2 },
      "ballVelocity":          { "x": 0.8,  "y": 0.0, "z": 1.2 },
      "velocityMagnitude":     1.44,
      "accelerationMagnitude": 0.21,
      "planeTiltX":            { "x": 1.0, "y": 0.0, "z": 0.0 },
      "planeTiltZ":            { "x": 0.0, "y": 0.0, "z": 1.0 },
      "inputVirtualX":         0.15,
      "inputVirtualZ":        -0.22
    }
  ]
}
```

**Origem de cada campo no Unity:**

| Campo | Origem |
|---|---|
| `timestampMs` | Relógio da partida em epoch ms |
| `frameId` | Contador de frames da partida |
| `ballPosition` | `TrunkTilt_PlayerBall.transform.position` |
| `ballVelocity` | `TrunkTilt_PlayerBall.PlayerVelocity` |
| `velocityMagnitude` | `PlayerVelocity.magnitude` |
| `accelerationMagnitude` | `TrunkTilt_PlayerBall.GetAccelerationMagnitude()` |
| `planeTiltX` | `TrunkTilt_TiltController.TiltAxisX` |
| `planeTiltZ` | `TrunkTilt_TiltController.TiltAxisZ` |
| `inputVirtualX` | `TargetRoll` |
| `inputVirtualZ` | `TargetPitch` |

**Resposta (202):**

```json
{ "accepted": 200 }
```

**Regras:**
- Acumular frames e enviar em chunks de 200.
- Não bloquear o loop de jogo para aguardar resposta — enviar de forma assíncrona.
- Em falha de rede, reenviar o chunk — a API descarta duplicatas por `(match_id, frameId)`.

---

## 7. Telemetria de pose (MediaPipe — lado JS da página)

```
POST /api/v1/trunktilt/matches/:match_id/telemetry/pose
Limite: até 200 frames por request
```

Esta chamada é feita pelo JS da página, não pelo Unity. O Unity deve expor o `match_id` para o contexto JS assim que a match for criada.

**Body:**

```json
{
  "frames": [
    {
      "timestampMs": 1760001131033,
      "frameId":     350,
      "landmarks": [
        { "id": 0,  "x": 0.51, "y": 0.23, "z": -0.02, "visibility": 0.99 },
        { "id": 1,  "x": 0.52, "y": 0.21, "z": -0.01, "visibility": 0.98 },
        { "id": 15, "x": 0.38, "y": 0.61, "z":  0.10, "visibility": 0.95 },
        { "id": 16, "x": 0.63, "y": 0.60, "z":  0.08, "visibility": 0.94 }
      ]
    }
  ]
}
```

**Referência de landmarks MediaPipe Pose (principais):**

| ID | Landmark |
|---|---|
| 0 | Nose |
| 11 | Left shoulder |
| 12 | Right shoulder |
| 13 | Left elbow |
| 14 | Right elbow |
| 15 | Left wrist |
| 16 | Right wrist |
| 23 | Left hip |
| 24 | Right hip |
| 25 | Left knee |
| 26 | Right knee |
| 27 | Left ankle |
| 28 | Right ankle |

**Resposta (202):**

```json
{ "accepted": 200, "rows_inserted": 6600 }
```

---

## 8. Finalizar partida

```
POST /api/v1/matches/:match_id/finish
```

**Body:**

```json
{
  "score":       20,
  "duration_ms": 38650,
  "completed":   true,
  "extra": {
    "goalScore":       20,
    "falls":            1,
    "coinsCollected":   2,
    "remainingTimeMs": 1350,
    "victory":         true,
    "levelName":       "Fase 01"
  }
}
```

**Origem de cada campo no Unity:**

| Campo | Origem |
|---|---|
| `score` | `TrunkTilt_GameData.Score` |
| `duration_ms` | Timestamp de fim − timestamp de início da partida |
| `completed` | `GameState == Victory` |
| `extra.goalScore` | `TrunkTilt_GameData.TargetScore` |
| `extra.falls` | `TrunkTilt_GameData.Falls` |
| `extra.remainingTimeMs` | `TrunkTilt_GameData.CurrentTime * 1000` |
| `extra.victory` | `GameState == Victory` |
| `extra.levelName` | `MapGridData.levelName` do snapshot |

**Antes de chamar `/finish`:** tentar flush da fila de eventos e telemetria pendentes.

**Erros possíveis:**

| Status | Motivo |
|---|---|
| `409` | Match já finalizada — não reenviar |

**Resposta:**

```json
{
  "id":          "f9bb51e4-...",
  "match_id":    "0a01f0a8-...",
  "score":       20,
  "duration_ms": 38650,
  "completed":   true,
  "extra":       { ... },
  "created_at":  "2026-05-04T10:10:00.000Z"
}
```

---

## 9. Requisito de adaptação identificado

O `MapGenerator` atualmente lê a configuração do mapa a partir de um `TextAsset` arrastado no Inspector. Para integrar com a API, ele precisa aceitar a string JSON do `level_config_snapshot` via código. Essa adaptação deve ser planejada separadamente.
