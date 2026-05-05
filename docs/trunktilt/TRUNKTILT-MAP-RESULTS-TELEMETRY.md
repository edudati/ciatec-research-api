# TrunkTilt: mapa, fases, moedas, resultados e telemetria

Documento de referencia para alinhar o que o TrunkTilt precisa receber da API, como isso vira fase dentro do Unity, e quais pontos de dados do proprio jogo devem alimentar resultados ou telemetria.

Este documento complementa [`API-LEVEL-AND-PRESET-PAYLOADS.md`](../API-LEVEL-AND-PRESET-PAYLOADS.md), que descreve o fluxo de API para `preset`, `level`, `progress/start` e `sessions/matches`.

---

## 1. Conceitos principais

### Game

`game` representa o jogo no catalogo/plataforma. Para o TrunkTilt, ele identifica qual experiencia esta sendo carregada e serve como chave para buscar progresso, presets, levels e iniciar partidas.

Exemplo conceitual:

```json
{
  "id": "game-trunktilt",
  "name": "TrunkTilt",
  "slug": "trunktilt",
  "version": "1.0.0",
  "description": "Jogo de equilibrio com bola, inclinacao de plataforma, moedas e checkpoints."
}
```

No Unity, o `game_id` aparece principalmente nas chamadas de API:

- `GET /api/v1/progress/start?game_id=...`
- `POST /api/v1/sessions/matches`
- `POST /api/v1/sessions/matches/:match_id/finish`

Para o TrunkTilt, os metadados de partida devem ser derivados de `game`, `preset`, `level` e do snapshot usado para jogar a fase.

### Preset

`preset` e a trilha de fases configurada para um jogo. Ele define a sequencia de `levels` que o jogador vai percorrer.

Exemplo conceitual:

```json
{
  "id": "preset-default-trunktilt",
  "game_id": "game-trunktilt",
  "name": "Trilha padrao",
  "description": "Sequencia inicial de fases do TrunkTilt.",
  "isDefault": true,
  "levels": [
    {
      "id": "level-trunktilt-01",
      "order": 0,
      "name": "Fase 01"
    },
    {
      "id": "level-trunktilt-02",
      "order": 1,
      "name": "Fase 02"
    }
  ]
}
```

O jogo nao precisa montar o preset manualmente. A API devolve a trilha no `GET /progress/start`, incluindo `levels[]`, `current_level`, bloqueios/desbloqueios e melhores resultados (`bests`).

### Level

`level` e a fase jogavel. Para o TrunkTilt, o campo mais importante e `config`, porque ele deve conter os dados usados pelo `MapGenerator`.

O `MapGenerator` espera uma estrutura equivalente a `MapGridData`:

```json
{
  "levelName": "Fase 01",
  "cellSize": 10,
  "grid": [
    { "row": [0, 0, 6, 1, 1, 5, 1, 7, 0] }
  ],
  "details": [
    {
      "tileId": 5,
      "x": 5,
      "y": 0,
      "coinValue": 10
    }
  ]
}
```

Na API, esse objeto pode aparecer em dois lugares:

- `current_level.config`, no `GET /progress/start`.
- `level_config_snapshot`, no `POST /sessions/matches`.

Para jogar uma partida, o cliente deve usar `level_config_snapshot`, porque ele e a copia imutavel da configuracao do level no momento em que a partida foi criada.

---

## 2. Configuracao do level no Unity

O formato do level e definido em `Assets/MapGenerator/Scripts/MapGeneration/MapData.cs`.

### Estrutura esperada

```json
{
  "levelName": "Fase 01",
  "cellSize": 10,
  "grid": [
    { "row": [0, 0, 0, 0, 0] },
    { "row": [0, 6, 1, 5, 0] },
    { "row": [0, 0, 0, 7, 0] }
  ],
  "details": [
    {
      "tileId": 5,
      "x": 3,
      "y": 1,
      "coinValue": 10
    }
  ]
}
```

Campos:

| Campo | Uso |
| --- | --- |
| `levelName` | Nome humano da fase. Deve alimentar metadados de partida e telemetria de pacote. |
| `cellSize` | Tamanho de cada celula da grid em unidades Unity. |
| `grid` | Matriz de tiles. Cada `row` representa uma linha no eixo Z; cada numero e um `TileID`. |
| `details` | Parametros extras por tile, identificados por `tileId`, `x` e `y`. |

### Tile IDs

| ID | Nome | Uso |
| --- | --- | --- |
| `0` | `Empty` | Celula vazia. |
| `1` | `Floor` | Piso comum. |
| `2` | `Wall` | Parede. |
| `3` | `MovingObstacle` | Obstaculo movel. |
| `4` | `Checkpoint` | Atualiza ponto de respawn. |
| `5` | `Coin` | Moeda coletavel. |
| `6` | `Start` | Inicio da fase. |
| `7` | `End` | Fim da fase. |
| `8` | `RampUp` | Rampa de subida. |
| `9` | `RampDown` | Rampa de descida. |
| `10` | `DecorativeGround` | Chao decorativo/arena. |
| `11` | `TurnRight` | Curva/direcao para direita, se usado pela fase. |
| `12` | `TurnLeft` | Curva/direcao para esquerda, se usado pela fase. |

### TileDetails

`TileDetails` permite configurar comportamento especifico por celula:

```json
{
  "tileId": 8,
  "x": 4,
  "y": 2,
  "length": 3,
  "rampDirection": "North",
  "elevation": 0,
  "targetElevation": 2
}
```

Campos relevantes:

| Campo | Uso |
| --- | --- |
| `tileId` | ID do tile ao qual os detalhes se aplicam. |
| `x` | Posicao X na grid. |
| `y` | Posicao Y do JSON, usada como Z na Unity. |
| `frequency` / `amplitude` | Parametros previstos para `MovingObstacle`. |
| `coinValue` | Valor da moeda. Hoje esta documentado no modelo, mas o prefab ainda precisa receber esse valor automaticamente na geracao. |
| `elevation` | Elevacao base. |
| `length` | Comprimento da rampa em celulas. |
| `rampDirection` | Direcao da rampa: `North`, `South`, `East`, `West`. |
| `targetElevation` | Altura final da rampa. |

---

## 3. Como o MapGenerator constroi a fase

Script principal: `Assets/MapGenerator/Scripts/MapGeneration/MapGenerator.cs`.

Fluxo atual:

1. `Start()` verifica se existe `mapJson`.
2. `ParseJson(mapJson.text)` converte o JSON para `MapGridData`.
3. `GenerateGrid(mapData)` percorre `grid` linha por linha.
4. Para cada celula nao vazia, `GetDetailsForTile(x, z, id)` busca parametros extras.
5. Se for um piso em canto, `DetectCorner` e `SpawnCurveTile` criam uma curva.
6. Caso contrario, `SpawnTile` cria piso, rampa, arena decorativa ou item via prefab.
7. Rampas ajustam `currentLevelElevation`, para que as proximas partes do mapa possam continuar em outra altura.

Geracao procedural:

| Componente | Script |
| --- | --- |
| Blocos, pisos e rampas volumetricas | `BlockMeshBuilder.cs` |
| Rampas antigas/alternativas | `RampMeshBuilder.cs` |
| Curvas | `CurveMeshBuilder.cs` |
| Instanciacao geral do mapa | `MapGenerator.cs` |

### Itens/prefabs

O `MapGenerator` tem uma lista `itemPrefabs` no Inspector. Quando o `TileID` da celula encontra um `ItemPrefabBinding`, ele:

1. Cria um `Floor` por baixo.
2. Instancia o prefab.
3. Ajusta escala e altura via `globalScale`, `scaleMultiplier` e `yOffset`.

Para moedas, o binding esperado e:

```json
{
  "id": "Coin",
  "prefab": "Coin.prefab",
  "yOffset": 0.5,
  "scaleMultiplier": 1.0
}
```

Observacao importante: o JSON aceita `coinValue`, mas o codigo atual nao copia automaticamente `TileDetails.coinValue` para `TrunkTilt_Coin.coinValue` na instancia. Se a API for controlar valores por moeda, esse ponto precisa ser implementado.

---

## 4. Moedas

Comportamento:

1. O prefab da moeda tem `TrunkTilt_Coin`.
2. Quando o collider entra em trigger com objeto tagueado como `Player`, a moeda emite `COIN_COLLECTED`.
3. O payload do evento leva:
   - `position`: posicao da moeda.
   - `payload`: valor da moeda (`coinValue`).
4. A moeda e destruida depois de `0.1s`.

Fluxo:

```text
Coin prefab
  -> TrunkTilt_Coin.OnTriggerEnter(Player)
  -> TrunkTilt_GameEvents.COIN_COLLECTED(position, coinValue)
  -> TrunkTilt_GameManager.HandleDomainEvent
  -> Score += coinValue
  -> HUD.UpdateScore(score)
  -> registro de evento discreto da partida
```

O score atual fica em `TrunkTilt_GameData.Score`.

---

## 5. Eventos discretos do jogo

Eventos emitidos pelo proprio fluxo de gameplay do TrunkTilt.

| Evento | Origem atual | Dados enviados |
| --- | --- | --- |
| `COIN_COLLECTED` | `TrunkTilt_Coin` | Posicao da moeda + valor no payload. |
| `CHECKPOINT_REACHED` | `TrunkTilt_TileCheckpoint` | Posicao do checkpoint. |
| `FALL_OCCURRED` | `TrunkTilt_KillPlayer` | Posicao da queda. |
| `RESPAWN` | Existe na API de eventos, mas nao esta sendo emitido no fluxo atual. |
| `LEVEL_COMPLETED` | `TrunkTilt_TileEnd`, quando o fim esta habilitado e o player entra no trigger. |
| `LEVEL_STARTED` | Existe, mas hoje nao ha chamada no projeto. |
| `LEVEL_TIMER_STARTED` | Existe, mas hoje nao ha chamada no projeto. |
| `LEVEL_FAILED` | Existe, mas hoje o timeout muda estado para `GameOver` e finaliza sessao sem emitir esse evento. |
| `TRACKING_LOST` / `TRACKING_RESTORED` | Existem, mas dependem de integracao com tracking. |

Todo evento emitido passa pelo gerenciador de gameplay do TrunkTilt e deve gerar um registro com este formato:

```json
{
  "TimestampGlobalMs": 12345,
  "EventType": "COIN_COLLECTED",
  "Position": { "x": 30, "y": 2.5, "z": 10 },
  "Payload": 10
}
```

Este e o payload conceitual do evento discreto de jogo.

---

## 6. Dados continuos do mundo

Enquanto a telemetria de mundo esta ativa, o script gera amostras a cada `Update()`.

Payload especifico do TrunkTilt:

```json
{
  "BallPosition": { "x": 12.4, "y": 1.1, "z": 8.2 },
  "BallVelocity": { "x": 0.8, "y": 0.0, "z": 1.2 },
  "VelocityMagnitude": 1.44,
  "AccelerationMagnitude": 0.21,
  "PlaneTiltX": { "x": 1.0, "y": 0.0, "z": 0.0 },
  "PlaneTiltZ": { "x": 0.0, "y": 0.0, "z": 1.0 },
  "InputVirtualX": 0.15,
  "InputVirtualZ": -0.22
}
```

Esse objeto deve ser enviado como amostra continua do mundo do TrunkTilt:

```json
{
  "TimestampGlobalMs": 12345,
  "FrameId": 350,
  "sample": {
    "BallPosition": { "x": 12.4, "y": 1.1, "z": 8.2 },
    "BallVelocity": { "x": 0.8, "y": 0.0, "z": 1.2 },
    "VelocityMagnitude": 1.44,
    "AccelerationMagnitude": 0.21,
    "PlaneTiltX": { "x": 1.0, "y": 0.0, "z": 0.0 },
    "PlaneTiltZ": { "x": 0.0, "y": 0.0, "z": 1.0 },
    "InputVirtualX": 0.15,
    "InputVirtualZ": -0.22
  }
}
```

Pontos coletados:

| Dado | Origem |
| --- | --- |
| Posicao da bola | `TrunkTilt_PlayerBall.transform.position` |
| Velocidade da bola | `TrunkTilt_PlayerBall.PlayerVelocity` |
| Magnitude da velocidade | `PlayerVelocity.magnitude` |
| Magnitude da aceleracao | `TrunkTilt_PlayerBall.GetAccelerationMagnitude()` |
| Inclinacao do plano | `TrunkTilt_TiltController.TiltAxisX` / `TiltAxisZ` |
| Input virtual | `TargetRoll` / `TargetPitch` |
| Timestamp global | Relogio da partida. |
| Frame | Contador de frames da partida. |

---

## 7. Resultados e resumo da partida

Resumo esperado do TrunkTilt:

```json
{
  "TotalSessionMs": 30000,
  "ActivePlayMs": 30000,
  "InputVariability": 0,
  "TimeInDeadZone": 0,
  "summary": {
    "TotalScore": 20,
    "GoalScore": 20
  }
}
```

Resumo especifico do TrunkTilt:

```json
{
  "TotalScore": 20,
  "GoalScore": 20
}
```

Dados que existem em runtime e podem compor resultado/finish:

| Dado | Onde esta |
| --- | --- |
| Score final | `TrunkTilt_GameData.Score` |
| Score alvo | `TrunkTilt_GameData.TargetScore` |
| Quedas | `TrunkTilt_GameData.Falls` |
| Tempo restante | `TrunkTilt_GameData.CurrentTime` |
| Checkpoint atual | `TrunkTilt_GameData.CurrentCheckpointPosition` |
| Estado final | `GameState.Victory` ou `GameState.GameOver` |

Observacao: no codigo atual, `CurrentTime` representa tempo restante, nao duracao jogada. Para relatorios e `duration_ms`, o ideal e guardar tambem:

- tempo inicial configurado;
- timestamp de inicio da partida;
- timestamp de fim da partida;
- duracao ativa calculada.

---

## 8. Telemetria: canais do TrunkTilt

Canais:

| Canal | Metodo |
| --- | --- |
| Configuracao da fase | `level_config_snapshot` usado para construir o mapa. |
| Eventos do jogo | Moeda, checkpoint, queda, respawn, inicio, fim, falha. |
| Mundo do jogo | Bola, velocidade, aceleracao, inclinacao do plano e input virtual. |
| Resultado final | Score, objetivo, quedas, tempo, vitoria/falha. |

Fluxo desejado apenas do ponto de vista do TrunkTilt:

1. Receber `game`, `preset` e `level` atual.
2. Criar uma partida para o `level_id` selecionado.
3. Receber `level_config_snapshot`.
4. Construir o mapa com esse snapshot.
5. Iniciar relogio e frames da partida.
6. Emitir evento de inicio de fase.
7. Durante a fase, coletar eventos discretos e amostras continuas.
8. Ao terminar, montar resultado/summary do TrunkTilt.
9. Enviar `finish` com `completed`, `score`, `duration_ms` e `extra`.

---

## 9. Payload recomendado para a API

### Exemplo: `game`

```json
{
  "id": "game-trunktilt",
  "name": "TrunkTilt",
  "slug": "trunktilt",
  "version": "1.0.0",
  "defaultPresetId": "preset-default-trunktilt"
}
```

### Exemplo: `preset`

```json
{
  "id": "preset-default-trunktilt",
  "game_id": "game-trunktilt",
  "name": "Trilha padrao",
  "description": "Sequencia inicial de fases.",
  "isDefault": true,
  "levels": [
    {
      "id": "level-trunktilt-01",
      "name": "Fase 01",
      "order": 0,
      "unlocked": true,
      "completed": false,
      "bests": {}
    },
    {
      "id": "level-trunktilt-02",
      "name": "Fase 02",
      "order": 1,
      "unlocked": false,
      "completed": false,
      "bests": {}
    }
  ]
}
```

### Exemplo: `level`

```json
{
  "id": "level-trunktilt-01",
  "game_id": "game-trunktilt",
  "preset_id": "preset-default-trunktilt",
  "name": "Fase 01",
  "order": 0,
  "config": {
    "levelName": "Fase 01",
    "cellSize": 10,
    "grid": [
      { "row": [0, 0, 0, 0, 0, 0] },
      { "row": [0, 6, 1, 5, 1, 0] },
      { "row": [0, 0, 0, 1, 7, 0] }
    ],
    "details": [
      {
        "tileId": 5,
        "x": 3,
        "y": 1,
        "coinValue": 10
      }
    ]
  }
}
```

### Exemplo: resposta de match

```json
{
  "id": "match-001",
  "session_id": "session-001",
  "game_id": "game-trunktilt",
  "level_id": "level-trunktilt-01",
  "level_config_snapshot": {
    "levelName": "Fase 01",
    "cellSize": 10,
    "grid": [
      { "row": [0, 0, 0, 0, 0, 0] },
      { "row": [0, 6, 1, 5, 1, 0] },
      { "row": [0, 0, 0, 1, 7, 0] }
    ],
    "details": [
      {
        "tileId": 5,
        "x": 3,
        "y": 1,
        "coinValue": 10
      }
    ]
  },
  "started_at": "2026-05-04T22:40:00.000Z"
}
```

### Exemplo: finish/resultados

Formato sugerido para finalizar partida:

```json
{
  "completed": true,
  "score": 20,
  "duration_ms": 38650,
  "extra": {
    "goalScore": 20,
    "falls": 1,
    "coinsCollected": 2,
    "remainingTimeMs": 1350,
    "victory": true,
    "levelName": "Fase 01"
  }
}
```

Campos minimos recomendados:

| Campo | Origem |
| --- | --- |
| `completed` | `LEVEL_COMPLETED` ou estado final `Victory`. |
| `score` | `TrunkTilt_GameData.Score`. |
| `duration_ms` | Duracao real da partida, idealmente calculada por timestamps de inicio/fim. |
| `extra.goalScore` | `TrunkTilt_GameData.TargetScore`. |
| `extra.falls` | `TrunkTilt_GameData.Falls`. |
| `extra.remainingTimeMs` | `TrunkTilt_GameData.CurrentTime * 1000`. |
| `extra.levelName` | `MapGridData.levelName` ou metadado da API. |

---

## 10. Lacunas importantes antes da integracao final

1. `TileDetails.coinValue` existe, mas ainda nao e aplicado ao componente `TrunkTilt_Coin` quando a moeda e instanciada.
2. `LEVEL_STARTED` e `LEVEL_TIMER_STARTED` existem, mas nao sao emitidos pelo fluxo atual.
3. `LEVEL_FAILED` existe, mas timeout hoje finaliza a sessao sem emitir evento de falha.
4. Os metadados do level jogado devem vir do `level_config_snapshot`, nao de valores fixos.
5. O resumo usa `CurrentTime` como se fosse duracao, mas `CurrentTime` e tempo restante.
6. O `MapGenerator` hoje le `TextAsset mapJson` no Inspector. Para API, sera necessario alimentar esse JSON dinamicamente a partir de `level_config_snapshot`.

