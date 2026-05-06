# TrunkTilt — Eventos, telemetria World e telemetria Landmarks (Pose)

---

## 1. Contratos mínimos

| Item | Valor |
|------|--------|
| Prefixo | `/api/v1` |
| Formato | `Content-Type: application/json` |
| Autenticação | `Authorization: Bearer <accessToken>` |
| Parâmetro de rota | `match_id` — UUID da partida (string) |
| Swagger | `GET /docs` |

**Erros (corpo JSON típico):**

| HTTP | Situação |
|------|-----------|
| `401` | Token ausente ou inválido |
| `400` | Validação Zod — `code: "VALIDATION_ERROR"`, `details` / `issues` |
| `404` | Partida inexistente ou não pertence ao utilizador do JWT |
| `403` | Partida não é do jogo TrunkTilt (`match.gameId` ≠ UUID TrunkTilt no servidor) |
| `409` | Partida já finalizada — estas rotas deixam de aceitar dados |

UUID TrunkTilt no backend (para interpretar `403`): `a1b2c3d4-e5f6-4789-a8b0-c1d2e3f4a5b6` — ver `src/constants/game-ids.ts`.

---

## 2. Prefixo das três rotas

```text
/api/v1/trunktilt/matches/:match_id/...
```

**Pré-condições (serviço TrunkTilt):** a match existe, pertence ao utilizador autenticado, é uma partida associada ao game_id do TrunkTilt e **ainda não** tem resultado final.

---

## 3. Telemetria World

### `POST /api/v1/trunktilt/matches/:match_id/telemetry/world`

**Sucesso:** `202 Accepted`

**Corpo:** objeto com propriedade `frames` — array com **1** a **200** elementos.

**Campos por frame:**

| Campo | Tipo |
|-------|------|
| `timestampMs` | int ≥ 0 |
| `frameId` | int ≥ 0 |
| `ballPosition` | `{ "x", "y", "z" }` number |
| `ballVelocity` | `{ "x", "y", "z" }` number |
| `velocityMagnitude` | number |
| `accelerationMagnitude` | number |
| `planeTiltX` | `{ "x", "y", "z" }` number |
| `planeTiltZ` | `{ "x", "y", "z" }` number |
| `inputVirtualX` | number |
| `inputVirtualZ` | number |

**Exemplo (1 frame):**

```json
{
  "frames": [
    {
      "timestampMs": 1000,
      "frameId": 0,
      "ballPosition": { "x": 0, "y": 0.1, "z": 0 },
      "ballVelocity": { "x": 0, "y": 0, "z": 0 },
      "velocityMagnitude": 0,
      "accelerationMagnitude": 0,
      "planeTiltX": { "x": 1, "y": 0, "z": 0 },
      "planeTiltZ": { "x": 0, "y": 0, "z": 1 },
      "inputVirtualX": 0,
      "inputVirtualZ": 0
    }
  ]
}
```

**Resposta `202`:**

```json
{
  "match_id": "<uuid>",
  "frames_received": 1,
  "rows_inserted": 1
}
```

**Idempotência:** unicidade `(match_id, frame_id)` em `trunktilt_world`; reenvio do mesmo `frameId` pode fazer `rows_inserted` menor que `frames_received` (`skipDuplicates`).

**Batch:** até **200** frames por pedido.

---

## 4. Telemetria Landmarks (endpoint `telemetry/pose`)

### `POST /api/v1/trunktilt/matches/:match_id/telemetry/pose`

Na API o recurso chama-se **pose**; o payload são **landmarks** (MediaPipe Pose). **Sucesso:** `202 Accepted`.

**Corpo:** `{ "frames": [ ... ] }` com **1** a **200** frames.

**Por frame:**

| Campo | Tipo |
|-------|------|
| `timestampMs` | int ≥ 0 |
| `frameId` | int ≥ 0 |
| `landmarks` | array de comprimento **33** |

**Por landmark:**

| Campo | Tipo |
|-------|------|
| `id` | int entre **0** e **32** (índice MediaPipe) |
| `x`, `y`, `z` | number |
| `visibility` | opcional: number entre 0 e 1, ou `null` / omitido |

**Validação:** os 33 elementos devem ter exatamente os ids **0..32**, cada um **uma vez** (caso não tenha sido capturado, o id não precisa existir, caso contrário, qualquer valor capturado deve estar presente).

Exemplo de **um** landmark (o cliente deve enviar os 33):

```json
{ "id": 11, "x": 0.52, "y": 0.48, "z": -0.02, "visibility": 0.95 }
```

**Resposta `202`:** igual à world — `match_id`, `frames_received`, `rows_inserted`.

**Idempotência:** unicidade `(match_id, frame_id, landmark_id)` em `trunktilt_pose`.

**Batch:** até **200** frames por pedido (cada frame persiste 33 linhas na BD).

---

## 5. Eventos discretos

### `POST /api/v1/trunktilt/matches/:match_id/events`

**Sucesso:** `201 Created`

**Corpo:** `{ "events": [ ... ] }` com **1** a **500** eventos.

**Por evento:**

| Campo | Tipo |
|-------|------|
| `type` | literal discriminado (tabela abaixo) |
| `timestamp` | int ≥ 0 (recomenda-se ms, alinhado à telemetria) |
| `data` | objeto — forma fixa por `type` |

| `type` | `data` |
|--------|--------|
| `COIN_COLLECTED` | `{ "x", "y", "z", "value" }` number |
| `CHECKPOINT_REACHED` | `{ "x", "y", "z" }` number |
| `FALL_OCCURRED` | `{ "x", "y", "z" }` number |
| `LEVEL_COMPLETED` | objeto JSON livre (pode ser `{}`) |
| `LEVEL_FAILED` | idem |
| `LEVEL_STARTED` | idem |
| `LEVEL_TIMER_STARTED` | idem |

**Exemplo:**

```json
{
  "events": [
    { "type": "LEVEL_STARTED", "timestamp": 0, "data": { "source": "unity" } },
    {
      "type": "COIN_COLLECTED",
      "timestamp": 5000,
      "data": { "x": 1, "y": 0, "z": 2, "value": 10 }
    },
    { "type": "LEVEL_COMPLETED", "timestamp": 120000, "data": { "stars": 3 } }
  ]
}
```

**Resposta `201`:**

```json
{
  "match_id": "<uuid>",
  "events_received": 3,
  "events_created": 3
}
```

**Idempotência:** **não** há deduplicação — reenvios criam linhas duplicadas; evitar retries cegos ou deduplicar no cliente.

---

## 6. Resumo das rotas (este documento)

| Recurso | Método | Caminho |
|---------|--------|---------|
| World | POST | `/api/v1/trunktilt/matches/:match_id/telemetry/world` |
| Landmarks (pose) | POST | `/api/v1/trunktilt/matches/:match_id/telemetry/pose` |
| Events | POST | `/api/v1/trunktilt/matches/:match_id/events` |

---

## 7. Checklist para agentes (apenas estas rotas)

1. Substituir `:match_id` pelo UUID da partida TrunkTilt em curso.
2. Enviar sempre `Authorization: Bearer ...`.
3. World / pose: no máximo **200** frames por POST; eventos: no máximo **500** por POST.
4. Pose: **33** landmarks, ids **0–32** todos presentes e únicos.
5. Tratar `409` como partida já terminada (parar envios ou ignorar conforme política do cliente).

---