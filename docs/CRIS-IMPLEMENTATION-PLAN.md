# RMS/CRIS Longitudinal Architecture — Incremental Implementation

> **Plano de roadmap / implementação.** Não substitui o contrato em **Swagger** (`/docs`), `prisma/schema.prisma` nem [`API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md`](./API-DOMAIN-AND-LONGITUDINAL-ARCHITECTURE.md) como descrição do estado actual.

## Objetivo

Evoluir a arquitetura atual do `ciatec-research-api` para um modelo RMS/CRIS longitudinal sem quebrar:

* sessões
* matches
* telemetria
* catálogo
* módulos existentes

A implementação deve ocorrer incrementalmente em fases pequenas e independentes.

---

# Princípios arquiteturais

## 1. Match NÃO é o eixo longitudinal

`Match` representa apenas:

* uma partida
* execução de jogo
* coleta de telemetria

Ele não define o RMS.

No futuro:

* `Match` poderá gerar um `timeline_event`
* mas continua sendo domínio de gameplay/coleta

---

## 2. Timeline é projeção longitudinal

`timeline_events`:

* NÃO armazena telemetria densa
* NÃO substitui tabelas de domínio
* NÃO substitui `Match`

Serve apenas para:

* timeline do participante
* auditoria longitudinal
* visualização unificada
* histórico de touchpoints

---

## 3. Entidades complexas possuem tabelas próprias

Nunca usar JSON para:

* projects
* groups
* enrollments
* assessments
* questionnaires
* interventions

JSON apenas para:

* metadados flexíveis
* snapshots
* payloads auxiliares

---

# Arquitetura alvo

```txt
User
├── AuthUser
├── roles
│   ├── ADMIN
│   ├── RESEARCHER
│   └── PARTICIPANT

ParticipantProfile
└── user_id

Project
├── researchers
├── groups
└── participants

Group
└── project_id

ParticipantEnrollment
├── participant_id
├── project_id
└── group_id

TimelineEvent
├── participant_id
├── project_id
├── event_type
├── source_type
├── source_id
└── occurred_at
```

---

# FASE 1 — PARTICIPANT role

## Objetivo

Separar semanticamente:

* pesquisador
* participante

## Implementação

Adicionar:

```prisma
enum UserRole {
  ADMIN
  RESEARCHER
  PLAYER
  PARTICIPANT
}
```

## Regras

* `PLAYER` continua existindo temporariamente
* novos fluxos usam `PARTICIPANT`
* evitar migração destrutiva

## Resultado esperado

Sistema preparado para RMS sem quebrar jogos atuais.

---

# FASE 2 — ParticipantProfile

## Objetivo

Separar:

* autenticação
* identidade longitudinal

## Implementação

```prisma
model ParticipantProfile {
  id        String @id @default(uuid())
  userId    String @unique
  user      User   @relation(...)
  
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

## Regras

* dados clínicos NÃO ficam em `User`
* `User` continua sendo identidade/login

## Resultado esperado

Participante passa a existir como entidade RMS.

---

# FASE 3 — Projects

## Objetivo

Introduzir organização longitudinal.

## Implementação

```prisma
model Project {
  id
  name
  code
  description
}
```

Criar módulo:

```txt
src/modules/projects/
```

## Regras

* CRUD básico
* soft delete
* pesquisadores vinculados ao projeto

## Resultado esperado

Estrutura mínima RMS funcional.

---

# FASE 4 — Groups

## Objetivo

Permitir segmentação experimental.

## Implementação

```prisma
model Group {
  id
  projectId
  name
}
```

## Exemplos

* controle
* intervenção
* piloto
* coorte A

## Resultado esperado

Projetos passam a suportar braços/grupos.

---

# FASE 5 — ParticipantEnrollment

## Objetivo

Vincular participante ao estudo.

## Implementação

```prisma
model ParticipantEnrollment {
  id
  participantId
  projectId
  groupId
  
  enrolledAt
  status
}
```

## Regras

* participant pode participar de múltiplos projetos
* group opcional inicialmente

## Resultado esperado

Participante entra formalmente no RMS.

---

# FASE 6 — TimelineEvent

## Objetivo

Criar camada longitudinal unificada.

## Implementação

```prisma
model TimelineEvent {
  id
  
  participantId
  projectId
  
  eventType
  sourceType
  sourceId
  
  occurredAt
  
  metadata Json?
}
```

## NÃO armazenar

* pose
* frames
* landmarks
* world telemetry

## Apenas referências

Exemplo:

```txt
event_type: MATCH_COMPLETED
source_type: Match
source_id: xxx
```

## Resultado esperado

Timeline longitudinal funcional.

---

# FASE 7 — Assessments

## Objetivo

Adicionar avaliações estruturadas.

## Implementação

```prisma
model Assessment {
  id
  participantId
  projectId
  
  type
  performedAt
}
```

## Regra

Toda avaliação gera:

```txt
TimelineEvent
```

## Resultado esperado

Primeiro touchpoint clínico formal.

---

# FASE 8 — Questionnaires

## Objetivo

Estruturar instrumentos.

## Implementação

```prisma
Questionnaire
QuestionnaireResponse
QuestionnaireAnswer
```

## Regra

Resposta concluída gera:

```txt
TimelineEvent
```

---

# FASE 9 — Integrar Match à timeline

## Objetivo

Conectar gameplay ao RMS.

## Implementação

Ao finalizar:

```txt
Match
```

Criar:

```txt
TimelineEvent
```

## Exemplo

```txt
MATCH_COMPLETED
GAME_SESSION
LEVEL_FINISHED
```

## Importante

`Match` continua independente.

---

# FASE 10 — Camada analítica

## Objetivo

Preparar escalabilidade.

## Adicionar

* Redis
* filas
* jobs assíncronos
* materialized views
* agregações

## Resultado esperado

Escala para grande volume longitudinal.

---

# Regras obrigatórias

## Sempre

* routes/controller/service
* Prisma
* Zod
* Swagger
* tabelas próprias para domínios complexos

## Nunca

* JSON gigante para entidades centrais
* timeline como storage principal
* lógica longitudinal dentro de Match

---

# Resultado final

O sistema passa a ter:

## Camada operacional

* games
* matches
* telemetria

## Camada RMS/CRIS

* projects
* groups
* participants
* enrollments
* assessments
* questionnaires
* timeline longitudinal

## Camada longitudinal

* timeline_events como projeção unificada
