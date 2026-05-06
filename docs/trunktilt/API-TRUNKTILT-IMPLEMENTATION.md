# API TrunkTilt — O que precisa ser criado

Documento de implementação para o time de backend (Node.js + PostgreSQL).  
Complementa [`API-GAMEPLAY-SESSIONS.md`](../API-GAMEPLAY-SESSIONS.md) e [`API-LEVEL-AND-PRESET-PAYLOADS.md`](../API-LEVEL-AND-PRESET-PAYLOADS.md).

---

## 1. Tabelas novas

### 1.1 `trunktilt_telemetry`

Armazena as amostras contínuas do mundo do jogo: posição da bola, velocidade, inclinação do plano e input virtual.

```sql
CREATE TABLE trunktilt_telemetry (
  id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id       UUID        NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  timestamp_ms   BIGINT      NOT NULL,  -- epoch ms vindo do cliente
  frame_id       INTEGER     NOT NULL,  -- contador de frames da partida
  ball_pos_x     FLOAT       NOT NULL,
  ball_pos_y     FLOAT       NOT NULL,
  ball_pos_z     FLOAT       NOT NULL,
  ball_vel_x     FLOAT       NOT NULL,
  ball_vel_y     FLOAT       NOT NULL,
  ball_vel_z     FLOAT       NOT NULL,
  velocity_mag   FLOAT       NOT NULL,
  accel_mag      FLOAT       NOT NULL,
  tilt_x_x       FLOAT       NOT NULL,
  tilt_x_y       FLOAT       NOT NULL,
  tilt_x_z       FLOAT       NOT NULL,
  tilt_z_x       FLOAT       NOT NULL,
  tilt_z_y       FLOAT       NOT NULL,
  tilt_z_z       FLOAT       NOT NULL,
  input_virt_x   FLOAT       NOT NULL,
  input_virt_z   FLOAT       NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_trunktilt_telemetry_match
  ON trunktilt_telemetry (match_id, timestamp_ms);
```

**Notas:**
- Colunas tipadas (não JSON) para permitir queries analíticas diretas sem deserialização.
- Índice em `(match_id, timestamp_ms)` cobre o acesso mais comum: "toda a telemetria de uma partida em ordem cronológica".

---

### 1.2 `trunktilt_pose`

Armazena as coordenadas espaciais dos **landmarks** MediaPipe Pose. Uma linha por landmark por frame.

```sql
CREATE TABLE trunktilt_pose (
  id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id       UUID        NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  timestamp_ms   BIGINT      NOT NULL,
  frame_id       INTEGER     NOT NULL,
  landmark_id    SMALLINT    NOT NULL,  -- 0–32 (índice MediaPipe Pose)
  x              FLOAT       NOT NULL,
  y              FLOAT       NOT NULL,
  z              FLOAT       NOT NULL,
  visibility     FLOAT,                 -- 0.0–1.0, pode ser null se não enviado
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_trunktilt_pose_match_landmark
  ON trunktilt_pose (match_id, landmark_id, timestamp_ms);

CREATE INDEX idx_trunktilt_pose_match_frame
  ON trunktilt_pose (match_id, frame_id);
```

**Notas:**
- 33 landmarks × N frames = volume alto. Dois índices cobrem trajetória por landmark e todos os landmarks de um frame.
- `landmark_id` segue a enumeração MediaPipe Pose (0 = nose, 15 = left wrist, 16 = right wrist, etc.).
- `visibility` é opcional — enviar quando disponível.

---

## 2. Validação de `level.config` (MapGridData)

O campo `config` já existe na tabela genérica de `levels`. O que precisa ser adicionado é **validação no momento do cadastro** para garantir que o JSON segue o schema esperado pelo `MapGenerator`.

Schema Zod recomendado:

```typescript
import { z } from 'zod';

const TileDetailsSchema = z.object({
  tileId:         z.number().int(),
  x:              z.number().int(),
  y:              z.number().int(),
  coinValue:      z.number().optional(),
  elevation:      z.number().optional(),
  targetElevation:z.number().optional(),
  length:         z.number().int().optional(),
  rampDirection:  z.enum(['North', 'South', 'East', 'West']).optional(),
  frequency:      z.number().optional(),
  amplitude:      z.number().optional(),
});

const MapGridDataSchema = z.object({
  levelName: z.string().min(1),
  cellSize:  z.number().positive(),
  grid:      z.array(z.object({ row: z.array(z.number().int().min(0).max(12)) })).min(1),
  details:   z.array(TileDetailsSchema).optional().default([]),
});
```

Aplicar essa validação no endpoint de criação/edição de levels **antes** de persistir. Retornar `400` com mensagem descritiva se o schema falhar.

---

## 3. Endpoints novos

### 3.1 Telemetria do mundo do jogo

```
POST /api/v1/trunktilt/matches/:match_id/telemetry/world
```

Recebe chunks de amostras contínuas do TrunkTilt.

**Regras:**
- Limite: 200 frames por request.
- Requer match ativa (não finalizada). Retornar `409` se a match já foi finalizada.
- Validar schema de cada frame antes de qualquer insert.
- Insert em batch único (um `INSERT ... VALUES` com todos os frames).
- Responder `202 Accepted` — não aguardar processamento adicional.

**Body:**

```json
{
  "frames": [
    {
      "timestampMs": 1760001131033,
      "frameId": 350,
      "ballPosition":         { "x": 12.4, "y": 1.1, "z": 8.2 },
      "ballVelocity":         { "x": 0.8,  "y": 0.0, "z": 1.2 },
      "velocityMagnitude":    1.44,
      "accelerationMagnitude":0.21,
      "planeTiltX":           { "x": 1.0, "y": 0.0, "z": 0.0 },
      "planeTiltZ":           { "x": 0.0, "y": 0.0, "z": 1.0 },
      "inputVirtualX":        0.15,
      "inputVirtualZ":       -0.22
    }
  ]
}
```

**Resposta (202):**

```json
{ "accepted": 200 }
```

---

### 3.2 Telemetria de landmarks (MediaPipe Pose)

```
POST /api/v1/trunktilt/matches/:match_id/telemetry/pose
```

Recebe chunks de frames; cada frame inclui o array **`landmarks`** (33 entradas, ids 0–32).

**Regras:**
- Limite: 200 frames por request.
- Cada frame contém exatamente 33 landmarks (índices 0–32).
- Rejeitar o batch inteiro se qualquer frame estiver malformado (`400`).
- Insert em batch único — 200 frames × 33 landmarks = 6.600 linhas por insert.
- Responder `202 Accepted`.

**Body:**

```json
{
  "frames": [
    {
      "timestampMs": 1760001131033,
      "frameId": 350,
      "landmarks": [
        { "id": 0,  "x": 0.51, "y": 0.23, "z": -0.02, "visibility": 0.99 },
        { "id": 1,  "x": 0.52, "y": 0.21, "z": -0.01, "visibility": 0.98 },
        { "id": 15, "x": 0.38, "y": 0.61, "z":  0.10, "visibility": 0.95 }
      ]
    }
  ]
}
```

**Resposta (202):**

```json
{ "accepted": 200, "rows_inserted": 6600 }
```

---

## 4. Deduplicação e idempotência

O cliente Unity pode reenviar um chunk em caso de falha de rede. Estratégia recomendada:

Para `trunktilt_world` e `trunktilt_pose`, usar `ON CONFLICT DO NOTHING` com constraint única em `(match_id, frame_id, landmark_id)` para pose e `(match_id, frame_id)` para telemetria world:

```sql
-- Adicionar às tabelas:
ALTER TABLE trunktilt_world
  ADD CONSTRAINT uq_trunktilt_world_match_frame UNIQUE (match_id, frame_id);

ALTER TABLE trunktilt_pose
  ADD CONSTRAINT uq_pose_match_frame_landmark UNIQUE (match_id, frame_id, landmark_id);
```

Insert com deduplicação automática:

```sql
INSERT INTO trunktilt_world (...) VALUES (...)
ON CONFLICT (match_id, frame_id) DO NOTHING;
```

Dessa forma reenvios são silenciosamente ignorados sem erro.

---

## 5. Eventos de gameplay (sem tabela nova)

Os eventos discretos do TrunkTilt (`COIN_COLLECTED`, `CHECKPOINT_REACHED`, `FALL_OCCURRED`, `LEVEL_COMPLETED`, etc.) usam o endpoint dedicado:

```
POST /api/v1/trunktilt/matches/:match_id/events
```

O campo `type` recebe o nome do evento e `data` recebe o payload específico. Nenhuma tabela nova é necessária.

Exemplos de payload:

```json
{ "type": "COIN_COLLECTED",   "timestamp": 1760001131000, "data": { "x": 30, "y": 2.5, "z": 10, "value": 10 } }
{ "type": "CHECKPOINT_REACHED","timestamp": 1760001132000, "data": { "x": 40, "y": 0.0, "z": 20 } }
{ "type": "FALL_OCCURRED",    "timestamp": 1760001133000, "data": { "x": 15, "y": -5.0, "z": 8 } }
{ "type": "LEVEL_COMPLETED",  "timestamp": 1760001160000, "data": {} }
```

---

## 6. Resultado da partida (sem tabela nova)

O finish usa o endpoint genérico já existente:

```
POST /api/v1/matches/:match_id/finish
```

Os campos específicos do TrunkTilt vão no `extra`:

```json
{
  "score":       20,
  "duration_ms": 38650,
  "completed":   true,
  "extra": {
    "goalScore":        20,
    "falls":             1,
    "coinsCollected":    2,
    "remainingTimeMs":  1350,
    "victory":          true,
    "levelName":        "Fase 01"
  }
}
```

Se precisar de queries analíticas sobre `extra` no futuro, adicionar índices funcionais:

```sql
CREATE INDEX idx_match_results_falls
  ON match_results (((extra->>'falls')::int));
```

---

## 7. Resumo do que criar

| Item | Ação |
|---|---|
| `trunktilt_world` | Tabela + índice + constraint única |
| `trunktilt_pose` | Tabela + índices + constraint única (`landmark_id`) |
| Validação `level.config` | Adicionar schema Zod no endpoint de levels |
| `POST /api/v1/trunktilt/.../telemetry/world` | Implementado |
| `POST /api/v1/trunktilt/.../telemetry/pose` | Body: array `landmarks` por frame |
| Eventos discretos | `POST /api/v1/trunktilt/.../events` (`trunktilt_events`) |
| Resultado/finish | Usar endpoint genérico existente |

---

## 8. O que não está pronto no cliente Unity (lacunas conhecidas)

Itens documentados em [`TRUNKTILT-MAP-RESULTS-TELEMETRY.md`](./TRUNKTILT-MAP-RESULTS-TELEMETRY.md) que precisam ser resolvidos antes da integração final:

| Lacuna | Impacto na API |
|---|---|
| `TileDetails.coinValue` não é aplicado ao prefab na instanciação | O `extra.coinsCollected` pode não refletir o valor correto por moeda |
| `LEVEL_STARTED` e `LEVEL_TIMER_STARTED` não são emitidos | Eventos de início não chegam ao endpoint de events |
| `LEVEL_FAILED` não é emitido no timeout | `completed: false` chega sem evento de falha registrado |
| `MapGenerator` lê `TextAsset` no Inspector, não JSON dinâmico | Sem ajuste, `level_config_snapshot` não alimenta o mapa |
| `CurrentTime` é tempo restante, não duração | `duration_ms` no finish pode ser calculado incorretamente |
