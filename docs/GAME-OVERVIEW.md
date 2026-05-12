# GAME API
## Arquitetura de Dados e APIs para Serious Games
*Documento de Estratégia Técnica — v1.0 — Abril 2025*

> **Histórico / estratégia (Abril 2025).** Não é fonte normativa do contrato HTTP ou do modelo Prisma actual. Para integração use **Swagger** (`/docs`), [`FRONTEND-API-OVERVIEW.md`](./FRONTEND-API-OVERVIEW.md) e `prisma/schema.prisma`.

---

## 1. Visão Geral

Este documento define a estratégia de banco de dados e APIs para um package de jogos sérios (serious games). Os jogos são independentes entre si, mas compartilham a mesma infraestrutura: API, banco de dados, sessões, resultados e telemetria.

**Princípios adotados:**
- Tabela única de jogos com configuração flexível via JSONB
- Sessions diárias agrupando todas as partidas do jogador no dia
- Snapshot imutável da configuração do level no momento da partida
- Resultados com base comum mais extensão específica por jogo
- Telemetria separada por natureza: **landmarks** (articulações / MediaPipe em JSON) e **world** (interface / estado do mundo em JSON genérico)
- Eventos de jogo globais com tipo e dados livres por jogo

---

## 2. Estrutura de Dados

### 2.1 Jogos, Presets e Levels

Cada jogo possui presets (conjuntos de levels). Cada preset pertence a um único game. Cada level pertence a um único preset. A configuração da fase fica no campo `config` em JSONB, que pode variar livremente entre jogos diferentes.

| Tabela | Descrição | Campos principais |
|---|---|---|
| `games` | Catálogo de jogos | id, name, description, created_at |
| `presets` | Conjunto de levels de um game | id, game_id, name, description |
| `levels` | Fase com configuração livre | id, preset_id, name, order, config (JSONB) |
| `user_games` | Progresso do jogador no jogo | id, user_id, game_id, preset_id, current_level_id |

**Exemplo de `config` JSONB em um level:**
```json
{
  "time_limit": 60,
  "lives": 3,
  "enemies": ["goblin", "troll"],
  "background": "forest"
}
```

ISSO VAI MUDAR POR JOGO, NÃO ALTERAR NADA SOBRE O EXEMPLO AGORA

---

### 2.2 Usuários

A arquitetura separa identidade de dominio e credenciais de autenticacao:

| Tabela | Descricao | Campos principais |
|---|---|---|
| `users` | Entidade de dominio (jogador/perfil) | id, name, role, created_at |
| `auth_users` | Credenciais de login | id, user_id (unique), email (unique), password_hash |
| `refresh_tokens` | Sessao de autenticacao | id, auth_user_id, token_hash, expires_at, revoked_at |

**Regra de isolamento:**
- `AuthUser` existe apenas para autenticar (login, refresh, logout).
- Apos autenticar, os modulos de negocio usam apenas `User`.
- O `sub` do access token representa `user.id`.
- Endpoints de gameplay nao recebem `user_id` no payload; usam o `sub` do JWT.

**Consequencias praticas:**
- `sessions`, `progress`, matches e telemetria trabalham com `users.id`.
- Mudancas de credencial (email/senha/tokens) nao afetam o modelo de negocio.
- Regras de autorizacao por papel (`role`) ficam no contexto de dominio do usuario.

---

### 2.3 Sessions e Matches

Uma session representa um dia de jogo. Todas as partidas realizadas no mesmo dia pertencem à mesma session. Ao mudar o dia calendário, uma nova session é criada automaticamente no próximo login.

| Tabela | Descrição | Campos principais |
|---|---|---|
| `sessions` | 1 por jogador por dia | id, user_id, session_date, started_at |
| `matches` | Cada partida iniciada | id, session_id, game_id, level_id, level_config_snapshot (JSONB), started_at |
| `match_results` | Resultado base da partida | id, match_id, score, duration_ms, completed (bool) |
| `match_result_details` | Resultado específico por jogo (1:1 por match) | id, match_id (unique), data (JSONB), created_at |
| `match_events` | Eventos de gameplay em batch | id, match_id, type, timestamp, data (JSONB) |
| `telemetry_world` | Telemetria de mundo/interface em batch | id, match_id, timestamp, device, data (JSONB) |
| `telemetry_landmarks` | Telemetria de landmarks / articulações em batch | id, match_id, timestamp, data (JSONB) |


**Sobre o `level_config_snapshot`:**
O campo guarda uma cópia completa do config do level no momento em que a partida foi iniciada. Mesmo que o level seja alterado no futuro, o histórico da partida preserva exatamente o que o jogador jogou.

**Sobre `match_result_details`:**
Os campos comuns (score, duration, completed) ficam em `match_results` para permitir comparações e analytics entre jogos. Dados exclusivos de cada jogo ficam em `match_result_details` no campo `data` JSONB.

---

### 2.4 Eventos de Jogo

Registro global de eventos em tempo real durante a partida. O campo `type` identifica o evento e o campo `data` é livre por jogo.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador único |
| `match_id` | FK | Partida associada |
| `type` | VARCHAR | Tipo do evento: cair, pular, colidir, etc. |
| `timestamp` | BIGINT | Momento exato do evento durante a partida em epoch milissegundos |
| `data` | JSONB | Dados livres específicos do evento e do jogo |

---

### 2.5 Telemetria

A telemetria é dividida em duas tabelas separadas pois possuem natureza completamente diferente em volume, frequência e estrutura de dados.

#### Landmarks — Articulações em séries temporais (`telemetry_landmarks`)

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador único |
| `match_id` | FK | Partida associada |
| `timestamp` | BIGINT | Momento da captura em epoch milissegundos |
| `data` | JSONB | Ex: `{joints: {left_knee: {x,y,z}, right_elbow: {x,y,z}}}` |

**⚠️ Atenção ao volume de dados:**
- Captura a 30fps gera 30 registros por segundo por partida
- Definir frequência de captura antes de implementar: 30fps, 10fps ou por evento
- Para volumes grandes em produção avaliar TimescaleDB ou armazenamento em S3

#### World — Interface / estado do jogo (`telemetry_world`)

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador único |
| `match_id` | FK | Partida associada |
| `timestamp` | BIGINT | Momento da amostra em epoch milissegundos |
| `device` | VARCHAR | keyboard, mouse, touch ou joystick |
| `data` | JSONB | Ex: `{key: "space", pressure: 0.8}` ou `{x: 120, y: 340, drag_ms: 200}` |

---

## 3. APIs de Jogo

### 3.1 Início de Sessão

Chamada realizada quando o jogador faz login. A API verifica se já existe uma session para o dia atual. Se sim, retorna a existente. Se não, cria uma nova.

```
POST /api/v1/sessions/start
```

**Body:**
```json
{}
```

**Resposta:**
```json
{ "id": "uuid", "user_id": "uuid", "started_at": "2025-04-15T10:00:00.000Z" }
```

**Status esperados:**
- `201` quando cria a sessao do dia
- `200` quando a sessao do dia ja existe

---

### 3.2 Início de Partida

Chamada realizada quando o jogador inicia uma partida. A API valida o game e o level informado, garante a session diaria e salva o snapshot da configuracao do level na match.

```
POST /api/v1/sessions/matches
```

**Body:**
```json
{ "game_id": "uuid", "level_id": "uuid" }
```

**Resposta:**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "game_id": "uuid",
  "level_id": "uuid",
  "level_config_snapshot": { "time_limit": 60, "lives": 3, "background": "forest" },
  "started_at": "2025-04-15T10:00:00.000Z"
}
```

---

### 3.3 Fim de Partida

Chamada ao encerrar a partida. Salva o resultado base e o detalhe específico do jogo. Atualiza o `current_level` do jogador se a fase foi concluída.

```
POST /api/v1/matches/:match_id/finish
```

**Body:**
```json
{
  "score": 1500,
  "duration_ms": 45000,
  "completed": true,
  "extra": { "errors": 2, "bonus_collected": 5 }
}
```

**Status esperados:**
- `201` quando finaliza com sucesso
- `409` quando a match ja foi finalizada anteriormente

---

### 3.4 Registro de Eventos

Endpoint para envio de eventos durante a partida (prefixo por jogo, ex.: bubbles ou bestbeat).

```
POST /api/v1/bubbles/matches/:match_id/events
```

**Body:**
```json
{
  "events": [
    { "type": "pular", "timestamp": "2025-04-15T10:00:01Z", "data": { "height": 1.2 } },
    { "type": "colidir", "timestamp": "2025-04-15T10:00:03Z", "data": { "object": "wall" } }
  ]
}
```

---

### 3.5 Telemetria — Landmarks (por jogo)

Exemplo para o jogo **bubbles** (análogo em `/api/v1/bestbeat/...`):

```
POST /api/v1/bubbles/matches/:match_id/telemetry/pose
```

**Body:**
```json
{
  "frames": [
    {
      "timestamp": "2025-04-15T10:00:01.033Z",
      "data": { "joints": { "left_knee": { "x": 0.1, "y": 0.5, "z": 0.0 } } }
    }
  ]
}
```

**Regra de batch:**
- Maximo de `100` frames por request

---

### 3.6 Telemetria — World (por jogo)

```
POST /api/v1/bubbles/matches/:match_id/telemetry/world
```

**Body:**
```json
{
  "frames": [
    { "timestamp": "2025-04-15T10:00:01.010Z", "device": "mouse", "data": { "x": 120, "y": 340, "drag_ms": 200 } },
    { "timestamp": "2025-04-15T10:00:01.200Z", "device": "keyboard", "data": { "key": "space", "pressure": 0.8 } }
  ]
}
```

**Regra de batch:**
- Maximo de `100` frames por request

---

## 4. Status de Implementação (Temporário)

Status rapido do que ja foi implementado na API para manter este documento aderente ao codigo atual.

---

### 4.1 Implementado

- Estrutura base de dominio: `users`, `games`, `presets`, `levels`, `user_games`
- Auth separado de dominio: `auth_users`, `refresh_tokens`
- Session diaria por usuario: `POST /api/v1/sessions/start`, `GET /api/v1/sessions/current`
- Criacao de match com snapshot: `POST /api/v1/sessions/matches`
- Finalizacao de match: `POST /api/v1/matches/:match_id/finish`
  - cria `match_results` + `match_result_details` (1:1)
  - segunda finalizacao retorna `409`
- Eventos de gameplay em batch (por jogo): `POST /api/v1/bubbles/matches/:match_id/events`, `POST /api/v1/bestbeat/matches/:match_id/events`
- Telemetria JSON em batch (por jogo):
  - `POST /api/v1/{bubbles|bestbeat}/matches/:match_id/telemetry/pose` (max 100 frames)
  - `POST /api/v1/{bubbles|bestbeat}/matches/:match_id/telemetry/world` (max 100 frames)
- TrunkTilt: telemetria tipada e eventos em `/api/v1/trunktilt/matches/...`

---

### 4.2 Regras de integracao para cliente de jogo

- Cliente nunca envia `user_id` em gameplay; API usa `sub` do JWT
- `timestamp` deve ser epoch em milissegundos e consistente em todos os eventos/telemetria
- `data` dos eventos/telemetria e livre em JSON
- Em caso de perda de rede, reenviar lote mantendo ordem temporal local