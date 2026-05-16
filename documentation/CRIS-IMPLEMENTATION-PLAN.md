# CRIS/RMS — Plano de Implementação Longitudinal
> **CIATec Research API** · Revisão 4 (API Python v2)  
> Roadmap **conceptual** do domínio CRIS (organização longitudinal + prontuário). **Priorização e Definition of Done por cartão:** [`BACKLOG.md`](BACKLOG.md). **Stack, camadas e qualidade:** [`STACK-AND-ARCHITECTURE.md`](STACK-AND-ARCHITECTURE.md). **Schema aplicado no código:** `src/models/` + `alembic/versions/`. **Contratos HTTP:** Pydantic + OpenAPI (documentação servida pela app, ex. `/branding/docs`).

---

## Implementação na API Python (repositório atual)

| Camada | Local |
|--------|--------|
| Rotas HTTP | `src/modules/<domínio>/router.py` |
| Negócio e transação | `src/modules/<domínio>/service.py` |
| Consultas SQL / ORM | `src/modules/<domínio>/repository.py` |
| Entrada/saída JSON | `src/modules/<domínio>/schemas.py` (Pydantic v2) |
| Modelo relacional | `src/models/*.py` (SQLAlchemy 2, `Mapped` / `mapped_column`) |
| Evolução de schema | Alembic em `alembic/versions/` |
| Erros de domínio | `src/core/exceptions.py` → handlers em `src/core/middleware.py` |
| Vocabulário controlado | `vocabulary_schemes` / `vocabulary_terms` + `src/modules/vocabulary/` |

Não existe `prisma/schema.prisma` neste repositório; qualquer referência legada a Prisma/Zod/controllers refere-se à **API Node antiga** e foi substituída pelo fluxo acima.

---

## Contexto e princípios

### O que o CRIS não é
- Não substitui `Match`, `Session` nem telemetria
- Não armazena frames, poses ou landmarks
- Não é uma camada paralela — é a camada organizacional que dá contexto científico ao que já existe

### O que o CRIS é
Uma camada longitudinal que responde perguntas como:
- Quem participou de qual estudo, em qual papel, entre quais datas?
- Quais avaliações ocorreram antes de determinada intervenção?
- Qual a evolução clínica de um participante ao longo do tempo?
- Quais eventos um pesquisador executou em um projeto?

### Princípios obrigatórios
- **Entidades complexas têm tabelas próprias** — nunca JSON para projects, enrollments, assessments, questionnaires
- **JSON apenas para** metadados flexíveis, snapshots e payloads auxiliares
- **Timeline é projeção**, não storage — referencia via `source_type + source_id`
- **Player e Participant coexistem** — Player é acesso livre ao jogo; Participant existe quando alocado em um projeto
- **Toda atividade clínica tem executor** — `researcher_id` obrigatório em registros de avaliação e intervenção
- **Vocabulário controlado** — papéis, tipos de evento e status nunca são texto livre

### Stack obrigatória por módulo (API v2)
Toda fase entrega: **Router FastAPI** (fino) → **Service** (regras, `commit`) → **Repository** (SQLAlchemy async) → **schemas Pydantic**; **Alembic** para migrations; **OpenAPI** gerado automaticamente. Não há camada “controller” separada, nem Prisma nem Zod.

### Notação dos diagramas de dados
Os blocos `text` nas secções por fase usam **sintaxe inspirada em Prisma** só como **diagrama legível** (campos e relações em camelCase lógico). O mapeamento real para PostgreSQL é `snake_case` nas tabelas e colunas em Alembic/models — não trate esses blocos como ficheiros geráveis; alinhe sempre ao código em `src/models/` e às migrations.

---

## Arquitetura alvo

```
IDENTIDADE
  User (existe) ──→ ParticipantProfile (novo)
                         └──→ ParticipantCondition ──→ HealthCondition

ORGANIZAÇÃO
  Project ──→ Group
     ├──→ ProjectMember   (pesquisador × projeto × papel)
     └──→ Enrollment      (participante × projeto × grupo × papel × datas)

INSTRUMENTOS (repositório reutilizável)
  AssessmentTemplate      (BERG, MMSE, FIM, Barthel…)
  QuestionnaireTemplate   (SF-36, PHQ-9, WHOQOL… · self_report flag)
    └──→ QuestionItem
  InterventionTemplate    (protocolo de jogo, exercício, consulta)
  InstrumentIndication    (template × condição × tipo de indicação — gerenciado por ADMIN)
  Vocabulary              (papéis, tipos, status — vocabulário controlado)

EXECUÇÃO (instâncias)
  AssessmentRecord        ──→ TimelineEvent
  QuestionnaireResponse   ──→ TimelineEvent
    └──→ QuestionAnswer
  InterventionRecord      ──→ TimelineEvent
  Session / Match (existe) → TimelineEvent

TIMELINE UNIFICADA (prontuário)
  TimelineEvent
    participant_id · project_id · executor_id
    event_type · source_type · source_id
    occurred_at · context Json?

VISÕES (filtros sobre TimelineEvent)
  → pessoal     (participant_id = X)
  → projeto     (project_id = Y)
  → global      (ADMIN/PI — sem filtro de escopo)

TELEMETRIA ESPECIALIZADA (independente)
  TrunktiltWorld/Pose/Event
  BubblesEvent/Pose/World
  BestbeatEvent/Pose/World
```

---

## Fases de implementação

---

### FASE 1 — ParticipantProfile + HealthCondition

**Objetivo:** separar identidade de autenticação da identidade longitudinal; criar repositório de condições de saúde.

**Por que primeiro:** todas as fases seguintes precisam de `ParticipantProfile` como âncora do participante no sistema de pesquisa.

**Schema:**

```text
model ParticipantProfile {
  id           String   @id @default(uuid())
  userId       String   @unique
  user         User     @relation(fields: [userId], references: [id], onDelete: Cascade)

  // dados demográficos e clínicos — nunca em User
  birthDate    DateTime? @map("birth_date") @db.Date
  biologicalSex String?  @map("biological_sex")   // M | F | outro — via Vocabulary
  phone        String?
  notes        String?   // observações livres do pesquisador

  conditions   ParticipantCondition[]
  enrollments  ParticipantEnrollment[]

  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  @@map("participant_profiles")
}

model HealthCondition {
  id          String   @id @default(uuid())
  code        String   @unique   // CID-10 ou código interno
  name        String
  description String?
  category    String?            // ex: neurológico, musculoesquelético
  isActive    Boolean  @default(true)

  participants ParticipantCondition[]

  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@map("health_conditions")
}

model ParticipantCondition {
  id                    String              @id @default(uuid())
  participantProfileId  String              @map("participant_profile_id")
  participantProfile    ParticipantProfile  @relation(fields: [participantProfileId], references: [id], onDelete: Cascade)
  healthConditionId     String              @map("health_condition_id")
  healthCondition       HealthCondition     @relation(fields: [healthConditionId], references: [id], onDelete: Restrict)

  diagnosedAt  DateTime? @map("diagnosed_at") @db.Date
  resolvedAt   DateTime? @map("resolved_at") @db.Date
  severity     String?                          // via Vocabulary
  notes        String?

  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  @@index([participantProfileId])
  @@index([healthConditionId])
  @@map("participant_conditions")
}
```

**Regras:**
- `User` continua sendo identidade de autenticação — dados clínicos nunca entram em `User`
- `ParticipantProfile` é criado automaticamente quando um `User` recebe papel `PARTICIPANT` ou recebe um `Enrollment`
- `HealthCondition` é um repositório global gerenciado por ADMIN — não por projeto
- `ParticipantCondition` é o vínculo temporal (CERIF-style): participante × condição × datas

**Módulos a criar:**
```
src/modules/participants/
src/modules/health-conditions/
```

**Entrega mínima:** CRUD de `HealthCondition` (admin), criação de `ParticipantProfile` ao enrollar, leitura de condições do participante.

---

### FASE 2 — Vocabulary (vocabulário controlado)

**Objetivo:** eliminar texto livre em campos semânticos críticos.

**Por que antes dos projetos:** `Project`, `Enrollment`, `AssessmentTemplate` e `TimelineEvent` todos dependem de tipos controlados.

**Schema:**

```text
model VocabularyScheme {
  id          String          @id @default(uuid())
  code        String          @unique   // ex: ENROLLMENT_ROLE, EVENT_TYPE, CONDITION_SEVERITY
  name        String
  description String?
  terms       VocabularyTerm[]

  createdAt   DateTime @default(now())

  @@map("vocabulary_schemes")
}

model VocabularyTerm {
  id          String           @id @default(uuid())
  schemeId    String           @map("scheme_id")
  scheme      VocabularyScheme @relation(fields: [schemeId], references: [id], onDelete: Cascade)
  code        String                              // ex: COORDINATOR, RESEARCHER, ASSISTANT
  label       String
  description String?
  isActive    Boolean          @default(true)
  order       Int              @default(0)

  createdAt   DateTime @default(now())

  @@unique([schemeId, code])
  @@index([schemeId])
  @@map("vocabulary_terms")
}
```

**Schemes iniciais a sedar:**

| scheme code | exemplos de terms |
|---|---|
| `PROJECT_MEMBER_ROLE` | PI, RESEARCHER, ASSISTANT, COLLABORATOR |
| `ENROLLMENT_ROLE` | PARTICIPANT, CONTROL, PILOT |
| `ENROLLMENT_STATUS` | ACTIVE, COMPLETED, WITHDRAWN, SCREENING |
| `TIMELINE_EVENT_TYPE` | ASSESSMENT, QUESTIONNAIRE, INTERVENTION, GAME_SESSION, ENROLLMENT, CONDITION_CHANGE, NOTE |
| `CONDITION_SEVERITY` | MILD, MODERATE, SEVERE |
| `BIOLOGICAL_SEX` | M, F, OTHER |
| `ASSESSMENT_TYPE` | FUNCTIONAL, COGNITIVE, MOTOR, PSYCHOLOGICAL |
| `INTERVENTION_TYPE` | GAME, EXERCISE, INTERVIEW, CLINICAL_EXAM, CONSULTATION |

**Regra:** campos que hoje seriam `String` livre (severity, type, role) passam a referenciar `VocabularyTerm.code`. Validação no service, não no banco — permite flexibilidade sem perder controle.

---

### FASE 3 — Project + Group + ProjectMember

**Objetivo:** estrutura organizacional do estudo.

**Schema:**

```text
model Project {
  id          String   @id @default(uuid())
  code        String   @unique           // ex: CIATEC-2025-001
  name        String
  description String?
  status      String   @default("DRAFT") // DRAFT | ACTIVE | COMPLETED | ARCHIVED
  startDate   DateTime? @map("start_date") @db.Date
  endDate     DateTime? @map("end_date")   @db.Date
  metadata    Json?                       // campos livres: financiador, CAAE, etc.

  groups      Group[]
  members     ProjectMember[]
  enrollments ParticipantEnrollment[]
  timeline    TimelineEvent[]

  isDeleted   Boolean  @default(false)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@index([status])
  @@map("projects")
}

model Group {
  id          String   @id @default(uuid())
  projectId   String   @map("project_id")
  project     Project  @relation(fields: [projectId], references: [id], onDelete: Cascade)
  name        String                        // ex: controle, intervenção, coorte A
  description String?
  isActive    Boolean  @default(true)

  enrollments ParticipantEnrollment[]

  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@index([projectId])
  @@map("groups")
}

// Entidade de ligação CERIF: pesquisador × projeto × papel × datas
model ProjectMember {
  id          String   @id @default(uuid())
  projectId   String   @map("project_id")
  project     Project  @relation(fields: [projectId], references: [id], onDelete: Cascade)
  userId      String   @map("user_id")
  user        User     @relation(fields: [userId], references: [id], onDelete: Restrict)

  role        String   // VocabularyTerm.code de PROJECT_MEMBER_ROLE
  startDate   DateTime @map("start_date") @db.Date
  endDate     DateTime? @map("end_date")  @db.Date

  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@unique([projectId, userId, role])
  @@index([projectId])
  @@index([userId])
  @@map("project_members")
}
```

**Regras:**
- Um pesquisador pode ter múltiplos papéis em projetos diferentes
- `status` do projeto segue vocabulário controlado mas armazenado como String (simplificação intencional)
- `metadata` aceita campos livres para atender variação entre projetos (ex: número CAAE, financiador, CEP)

---

### FASE 4 — ParticipantEnrollment

**Objetivo:** vínculo formal entre participante e estudo — coração do modelo CERIF.

**Schema:**

```text
// Entidade de ligação CERIF: participante × projeto × grupo × papel × datas
model ParticipantEnrollment {
  id                   String             @id @default(uuid())
  participantProfileId String             @map("participant_profile_id")
  participantProfile   ParticipantProfile @relation(fields: [participantProfileId], references: [id], onDelete: Restrict)
  projectId            String             @map("project_id")
  project              Project            @relation(fields: [projectId], references: [id], onDelete: Restrict)
  groupId              String?            @map("group_id")
  group                Group?             @relation(fields: [groupId], references: [id], onDelete: SetNull)

  role        String   // VocabularyTerm.code de ENROLLMENT_ROLE
  status      String   @default("ACTIVE") // VocabularyTerm.code de ENROLLMENT_STATUS
  enrolledAt  DateTime @default(now()) @map("enrolled_at")
  exitedAt    DateTime? @map("exited_at")
  exitReason  String?   @map("exit_reason")

  // executor que realizou o enrollment
  enrolledBy  String   @map("enrolled_by")
  enrolledByUser User  @relation("EnrolledBy", fields: [enrolledBy], references: [id], onDelete: Restrict)

  sessions    Session[]        // sessions dentro deste enrollment
  timeline    TimelineEvent[]

  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@unique([participantProfileId, projectId])  // um participante por projeto
  @@index([projectId])
  @@index([participantProfileId])
  @@index([status])
  @@map("participant_enrollments")
}
```

**Regras:**
- Um participante pode ter enrollments em múltiplos projetos
- `groupId` é opcional no momento do enrollment — pode ser atribuído depois
- Ao criar um Enrollment, gerar automaticamente um `TimelineEvent` com `event_type: ENROLLMENT`
- `Session` ganha campo `enrollmentId` opcional — quando presente, a sessão pertence ao contexto de pesquisa

---

### FASE 5 — Repositório de instrumentos

**Objetivo:** templates reutilizáveis de avaliações, questionários e intervenções — desacoplados de projetos específicos.

**Schema:**

```text
// Template de avaliação clínica (aplicada por pesquisador)
model AssessmentTemplate {
  id          String   @id @default(uuid())
  code        String   @unique          // ex: BERG, MMSE, FIM, BARTHEL
  name        String
  description String?
  type        String                    // VocabularyTerm.code de ASSESSMENT_TYPE
  version     String   @default("1.0")
  isActive    Boolean  @default(true)
  metadata    Json?                     // instruções, referências, domínios

  records     AssessmentRecord[]

  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@map("assessment_templates")
}

// Template de questionário (pode ser autoaplicável)
model QuestionnaireTemplate {
  id          String   @id @default(uuid())
  code        String   @unique          // ex: SF36, PHQ9, WHOQOL
  name        String
  description String?
  selfReport  Boolean  @default(false) @map("self_report")  // true = formulário para o participante
  type        String
  version     String   @default("1.0")
  isActive    Boolean  @default(true)
  metadata    Json?

  items       QuestionItem[]
  responses   QuestionnaireResponse[]

  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@map("questionnaire_templates")
}

model QuestionItem {
  id             String                @id @default(uuid())
  templateId     String                @map("template_id")
  template       QuestionnaireTemplate @relation(fields: [templateId], references: [id], onDelete: Cascade)
  code           String                // identificador do item dentro do template
  label          String
  type           String                // SCALE | MULTIPLE_CHOICE | TEXT | BOOLEAN | NUMBER
  order          Int
  options        Json?                 // para SCALE e MULTIPLE_CHOICE
  isRequired     Boolean  @default(true) @map("is_required")

  answers        QuestionAnswer[]

  @@unique([templateId, code])
  @@index([templateId])
  @@map("question_items")
}

// Template de intervenção (jogo, exercício, consulta, entrevista)
model InterventionTemplate {
  id          String   @id @default(uuid())
  code        String   @unique
  name        String
  description String?
  type        String                    // VocabularyTerm.code de INTERVENTION_TYPE
  isActive    Boolean  @default(true)
  metadata    Json?                     // protocolo, duração esperada, materiais

  // ligação opcional ao catálogo de jogos
  gameId      String?  @map("game_id")
  game        Game?    @relation(fields: [gameId], references: [id], onDelete: SetNull)

  records     InterventionRecord[]

  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@map("intervention_templates")
}
```

```text
// Indicação clínica global — gerenciada por ADMIN
model InstrumentIndication {
  id                String          @id @default(uuid())

  // polimórfico: aponta para AssessmentTemplate ou QuestionnaireTemplate
  instrumentType    String          @map("instrument_type") // ASSESSMENT | QUESTIONNAIRE
  instrumentId      String          @map("instrument_id")

  healthConditionId String          @map("health_condition_id")
  healthCondition   HealthCondition @relation(fields: [healthConditionId], references: [id], onDelete: Restrict)

  // via Vocabulary scheme INSTRUMENT_INDICATION_TYPE
  indicationType    String          @map("indication_type") // INDICATED | COMMONLY_USED | GOLD_STANDARD
  notes             String?         // justificativa clínica opcional

  createdAt         DateTime        @default(now())

  @@unique([instrumentType, instrumentId, healthConditionId])
  @@index([instrumentType, instrumentId])
  @@index([healthConditionId])
  @@map("instrument_indications")
}
```

**Regras:**
- Templates são globais (não pertencem a projetos) — um projeto os referencia via registros de execução
- `selfReport: true` em `QuestionnaireTemplate` indica que o formulário é enviado ao participante para preenchimento próprio
- `InterventionTemplate` pode ou não estar ligado a um `Game` — intervenções não-jogo (entrevistas, exames) também são modeladas aqui
- `InstrumentIndication` é gerenciada exclusivamente por ADMIN — pesquisadores não alteram indicações globais
- O sistema não bloqueia uso de instrumentos não indicados — exibe aviso, mas a decisão clínica final é do pesquisador
- O Vocabulary scheme `INSTRUMENT_INDICATION_TYPE` deve ser seedado com: `INDICATED`, `COMMONLY_USED`, `GOLD_STANDARD`

**Fluxo de uso no frontend:**
```
Pesquisador abre painel de avaliação do participante
  └── sistema carrega condições do ParticipantProfile
        └── filtra templates com InstrumentIndication matching
              └── exibe "recomendados" primeiro, demais disponíveis abaixo com aviso
```

---

### FASE 6 — Registros de execução (instâncias)

**Objetivo:** instanciar templates em eventos reais vinculados a participante + projeto + executor.

**Schema:**

```text
model AssessmentRecord {
  id                   String             @id @default(uuid())
  templateId           String             @map("template_id")
  template             AssessmentTemplate @relation(fields: [templateId], references: [id], onDelete: Restrict)
  participantProfileId String             @map("participant_profile_id")
  participantProfile   ParticipantProfile @relation(fields: [participantProfileId], references: [id], onDelete: Restrict)
  projectId            String             @map("project_id")
  project              Project            @relation(fields: [projectId], references: [id], onDelete: Restrict)
  executorId           String             @map("executor_id")    // pesquisador que aplicou
  executor             User               @relation("AssessmentExecutor", fields: [executorId], references: [id], onDelete: Restrict)

  performedAt          DateTime           @map("performed_at")
  score                Float?
  data                 Json               // respostas/scores por domínio
  notes                String?

  timelineEvent        TimelineEvent?

  createdAt            DateTime @default(now())
  updatedAt            DateTime @updatedAt

  @@index([participantProfileId])
  @@index([projectId])
  @@index([templateId])
  @@map("assessment_records")
}

model QuestionnaireResponse {
  id                   String                @id @default(uuid())
  templateId           String                @map("template_id")
  template             QuestionnaireTemplate @relation(fields: [templateId], references: [id], onDelete: Restrict)
  participantProfileId String                @map("participant_profile_id")
  participantProfile   ParticipantProfile    @relation(fields: [participantProfileId], references: [id], onDelete: Restrict)
  projectId            String                @map("project_id")
  project              Project               @relation(fields: [projectId], references: [id], onDelete: Restrict)

  // executor é opcional: null = autoaplicável (self_report)
  executorId           String?               @map("executor_id")
  executor             User?                 @relation("QuestionnaireExecutor", fields: [executorId], references: [id], onDelete: SetNull)

  respondedAt          DateTime              @map("responded_at")
  status               String               @default("COMPLETED")  // PENDING | IN_PROGRESS | COMPLETED
  answers              QuestionAnswer[]

  timelineEvent        TimelineEvent?

  createdAt            DateTime @default(now())
  updatedAt            DateTime @updatedAt

  @@index([participantProfileId])
  @@index([projectId])
  @@index([templateId])
  @@map("questionnaire_responses")
}

model QuestionAnswer {
  id           String                @id @default(uuid())
  responseId   String                @map("response_id")
  response     QuestionnaireResponse @relation(fields: [responseId], references: [id], onDelete: Cascade)
  itemId       String                @map("item_id")
  item         QuestionItem          @relation(fields: [itemId], references: [id], onDelete: Restrict)
  value        Json                  // resposta normalizada — String, Number, Boolean ou array

  @@unique([responseId, itemId])
  @@index([responseId])
  @@map("question_answers")
}

model InterventionRecord {
  id                   String               @id @default(uuid())
  templateId           String               @map("template_id")
  template             InterventionTemplate @relation(fields: [templateId], references: [id], onDelete: Restrict)
  participantProfileId String               @map("participant_profile_id")
  participantProfile   ParticipantProfile   @relation(fields: [participantProfileId], references: [id], onDelete: Restrict)
  projectId            String               @map("project_id")
  project              Project              @relation(fields: [projectId], references: [id], onDelete: Restrict)
  executorId           String               @map("executor_id")
  executor             User                 @relation("InterventionExecutor", fields: [executorId], references: [id], onDelete: Restrict)

  // ligação opcional ao Match quando a intervenção é um jogo
  matchId              String?              @unique @map("match_id")
  match                Match?               @relation(fields: [matchId], references: [id], onDelete: SetNull)

  performedAt          DateTime             @map("performed_at")
  durationMinutes      Int?                 @map("duration_minutes")
  notes                String?
  data                 Json?                // dados específicos do tipo de intervenção

  timelineEvent        TimelineEvent?

  createdAt            DateTime @default(now())
  updatedAt            DateTime @updatedAt

  @@index([participantProfileId])
  @@index([projectId])
  @@map("intervention_records")
}
```

**Regras:**
- Todo registro de execução cria automaticamente um `TimelineEvent` (via service, não trigger de banco)
- `executorId` é obrigatório em `AssessmentRecord` e `InterventionRecord` — sempre há um responsável
- `executorId` é nulo em `QuestionnaireResponse` quando `template.selfReport = true`
- `InterventionRecord.matchId` conecta o domínio de gameplay ao CRIS quando a intervenção é um jogo

---

### FASE 7 — TimelineEvent (hub longitudinal)

**Objetivo:** camada unificada de todos os eventos — o prontuário.

**Schema:**

```text
enum TimelineEventType {
  ENROLLMENT
  CONDITION_CHANGE
  ASSESSMENT
  QUESTIONNAIRE
  INTERVENTION
  GAME_SESSION
  NOTE
  STATUS_CHANGE
}

model TimelineEvent {
  id                   String              @id @default(uuid())

  // contexto longitudinal obrigatório
  participantProfileId String              @map("participant_profile_id")
  participantProfile   ParticipantProfile  @relation(fields: [participantProfileId], references: [id], onDelete: Restrict)
  projectId            String              @map("project_id")
  project              Project             @relation(fields: [projectId], references: [id], onDelete: Restrict)
  enrollmentId         String?             @map("enrollment_id")
  enrollment           ParticipantEnrollment? @relation(fields: [enrollmentId], references: [id], onDelete: SetNull)

  // executor responsável pelo evento (null apenas para eventos automáticos do sistema)
  executorId           String?             @map("executor_id")
  executor             User?               @relation("TimelineExecutor", fields: [executorId], references: [id], onDelete: SetNull)

  // referência polimórfica à entidade de origem
  eventType            TimelineEventType
  sourceType           String              @map("source_type")  // ex: AssessmentRecord, Match, ParticipantEnrollment
  sourceId             String              @map("source_id")

  occurredAt           DateTime            @map("occurred_at")
  context              Json?               // metadados livres por tipo de evento

  // back-relations para consulta direta
  assessmentRecord     AssessmentRecord?   @relation(fields: [sourceId], references: [id])
  questionnaireResponse QuestionnaireResponse? @relation(fields: [sourceId], references: [id])
  interventionRecord   InterventionRecord? @relation(fields: [sourceId], references: [id])

  createdAt            DateTime @default(now())

  @@index([participantProfileId, occurredAt])
  @@index([projectId, occurredAt])
  @@index([enrollmentId])
  @@index([eventType])
  @@index([sourceType, sourceId])
  @@map("timeline_events")
}
```

**Regras:**
- `TimelineEvent` é sempre criado pelo service da entidade de origem — nunca inserido diretamente
- `occurredAt` é a data real do evento clínico, não `createdAt` (que é a data de inserção no sistema)
- Os índices compostos `(participantProfileId, occurredAt)` e `(projectId, occurredAt)` são obrigatórios para performance das visões

**Visões implementadas como queries filtradas (não views de banco):**

```
Timeline pessoal:   WHERE participant_profile_id = :id ORDER BY occurred_at DESC
Timeline do projeto: WHERE project_id = :id ORDER BY occurred_at DESC
Timeline global:    sem filtro de escopo (ADMIN/PI only) ORDER BY occurred_at DESC
```

---

### FASE 8 — Integração Match → Timeline

**Objetivo:** conectar sessões de jogo existentes ao prontuário.

**Mudanças no schema existente:**

```text
// Adicionar ao model Session:
enrollmentId String? @map("enrollment_id")
enrollment   ParticipantEnrollment? @relation(...)

// Adicionar ao model Match:
timelineEvent TimelineEvent?
```

**Regra:** ao finalizar um `Match` (`POST /matches/:id/finish`), se `session.enrollmentId` estiver preenchido, criar automaticamente um `TimelineEvent` com:
```
eventType:  GAME_SESSION
sourceType: Match
sourceId:   match.id
executorId: null  (evento gerado pelo sistema)
occurredAt: match.startedAt
```

**Importante:** `Match` continua independente. A lógica de timeline é adicionada ao service de finish como efeito colateral opcional — não bloqueia o flow do jogo.

---

### FASE 9 — Formulários autoaplicáveis (self-report)

**Objetivo:** permitir que questionários com `selfReport: true` sejam enviados ao participante para preenchimento.

**Fluxo:**

```
Pesquisador cria QuestionnaireResponse com status: PENDING
  └──→ sistema gera link/token de acesso para o participante
         └──→ participante preenche via frontend público
                └──→ status muda para COMPLETED
                       └──→ TimelineEvent criado automaticamente
```

**Schema adicional:**

```text
model SelfReportToken {
  id           String                @id @default(uuid())
  responseId   String                @unique @map("response_id")
  response     QuestionnaireResponse @relation(fields: [responseId], references: [id], onDelete: Cascade)
  token        String                @unique @default(uuid())
  expiresAt    DateTime              @map("expires_at")
  usedAt       DateTime?             @map("used_at")
  createdAt    DateTime              @default(now())

  @@map("self_report_tokens")
}
```

**Rotas necessárias:**
```
POST   /api/v1/questionnaires/:responseId/send-link   (pesquisador envia link)
GET    /api/v1/self-report/:token                     (participante acessa, público)
POST   /api/v1/self-report/:token/submit              (participante submete, público)
```

---

### FASE 10 — Camada analítica e escalabilidade

**Objetivo:** preparar para volume longitudinal e exportação científica.

**Itens:**
- Redis para cache de timelines frequentemente acessadas
- Filas assíncronas para criação de `TimelineEvent` (desacoplar do request)
- Materialized views para agregações por projeto (contagem de eventos, progresso de participantes)
- Export OSF-compatible (JSON-LD ou CSV por projeto)
- Audit log de alterações em `ParticipantProfile` e `ParticipantCondition`

---

## Resumo das fases

| Fase | Entrega | Depende de |
|------|---------|------------|
| 1 | ParticipantProfile + HealthCondition | — |
| 2 | Vocabulary (vocabulário controlado) | — |
| 3 | Project + Group + ProjectMember | 1, 2 |
| 4 | ParticipantEnrollment | 1, 2, 3 |
| 5 | Repositório de instrumentos (templates + InstrumentIndication) | 1, 2 |
| 6 | Registros de execução (Assessment, Questionnaire, Intervention) | 1, 3, 4, 5 |
| 7 | TimelineEvent + visões | 1, 3, 4, 6 |
| 8 | Integração Match → Timeline | 4, 7 |
| 9 | Self-report / formulários autoaplicáveis | 5, 6 |
| 10 | Camada analítica | 7, 8 |

**Fases 1 e 2 são paralelas** — podem ser desenvolvidas simultaneamente.  
**Fases 3 e 5 são paralelas** após 1 e 2.

---

## O que nunca fazer

- JSON para entidades centrais (projects, enrollments, assessments)
- `TimelineEvent` como storage principal — é sempre referência
- Lógica longitudinal dentro de `Match`
- Campos de papel/tipo como texto livre sem vocabulário
- `executorId` nulo em registros clínicos obrigatórios
- Migração destrutiva que quebre o fluxo de jogo livre (Player sem projeto)
