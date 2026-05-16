# Roles e Permissões
> **CIATec Research API** · Revisão 1  
> Define a hierarquia de acesso, as regras de autorização e o comportamento esperado por contexto.

---

## Dois eixos de autorização

O sistema opera com dois eixos independentes que sempre são verificados em sequência. Um usuário só executa uma ação se passar nos dois.

**Eixo 1 — `UserRole`:** papel fixo no cadastro do usuário. Define o que ele pode fazer no sistema como um todo.

**Eixo 2 — `ProjectMember.role`:** papel contextual dentro de um projeto específico. Define o que ele pode fazer dentro daquele projeto.

Regra de ouro: o `UserRole` abre a porta do sistema; o `ProjectMember.role` abre a porta do projeto. Se qualquer um falhar, a ação é negada.

---

## UserRole — escopo sistema

### ADMIN
Acesso absoluto a todas as operações do sistema. Gerencia usuários, vocabulários controlados, repositório de instrumentos, condições de saúde e configurações globais. Pode visualizar a timeline global de todos os projetos e participantes sem restrição de escopo.

Quando um ADMIN participa de um projeto como PI ou RESEARCHER, ele age com as permissões do papel do projeto — não com privilégios de ADMIN. O acesso absoluto é restrito a operações de sistema.

### PI (Primary Investigator)
Responsável científico de projetos. Pode criar e gerenciar seus próprios projetos, definir grupos, enrollar participantes, adicionar membros à equipe e visualizar a timeline completa de todos os projetos que coordena. Não gerencia o sistema — só seus projetos.

Um usuário pode ser PI em múltiplos projetos simultaneamente.

### RESEARCHER
Executa atividades clínicas dentro dos projetos em que está alocado. Não cria projetos nem enrolla participantes — só opera dentro do que o PI configurou. Acesso à timeline limitado aos participantes que atendeu diretamente, salvo configuração diferente pelo PI.

Um usuário pode ser RESEARCHER em múltiplos projetos simultaneamente, com papéis diferentes em cada um.

### PARTICIPANT
Usuário alocado formalmente em um ou mais projetos de pesquisa. Possui área pessoal onde visualiza seus próprios eventos na timeline, responde formulários autoaplicáveis (self-report) e, dependendo da configuração do projeto, pode enviar feedback. Não acessa dados de outros participantes nem a estrutura do projeto.

`PARTICIPANT` coexiste com `PLAYER` — um participante continua tendo acesso ao jogo livremente.

### PLAYER
Estado padrão de qualquer usuário que se cadastra na plataforma. Acesso livre aos jogos sem vínculo com projeto ou prontuário. Não possui `ParticipantProfile` nem aparece em nenhuma timeline de pesquisa.

Torna-se `PARTICIPANT` implicitamente quando recebe um `Enrollment` ativo — o `ParticipantProfile` é criado automaticamente nesse momento.

---

## ProjectMember.role — escopo projeto

Cada projeto tem uma equipe definida via `ProjectMember`. Um mesmo usuário pode ter papéis diferentes em projetos diferentes. O papel no projeto é independente do `UserRole` — um RESEARCHER do sistema pode ser PI de um projeto específico se assim for configurado.

### PI (no projeto)
Autoridade máxima dentro do projeto. Cria e edita grupos, enrolla e desvincula participantes, adiciona e remove membros da equipe, aplica qualquer instrumento e visualiza a timeline completa de todos os participantes do projeto.

Cada projeto deve ter exatamente um PI ativo. Projetos sem PI não podem iniciar coleta.

### RESEARCHER (no projeto)
Executa a coleta clínica. Aplica avaliações (`AssessmentRecord`), registra intervenções (`InterventionRecord`), inicia questionários mediados (`QuestionnaireResponse` com executor). Visualiza a timeline dos participantes que atendeu diretamente.

### ASSISTANT (no projeto)
Papel de suporte. Aplica questionários e registra notas livres. Acesso somente leitura à timeline — não cria avaliações nem intervenções formais. Útil para estagiários e colaboradores com acesso limitado.

### COLLABORATOR (no projeto)
Acesso somente leitura. Pode visualizar dados agregados e timelines conforme configurado pelo PI. Não executa nenhuma ação clínica. Útil para co-autores, consultores externos e auditores.

---

## Regras de autorização

### Verificação em dois passos
Toda requisição autenticada verifica primeiro o `UserRole` (permissão de sistema) e depois o `ProjectMember.role` (permissão de projeto). Ambos precisam autorizar a ação.

### Isolamento de projeto
Um RESEARCHER alocado no Projeto A não enxerga dados do Projeto B, mesmo que ambos usem os mesmos instrumentos. O escopo de projeto é sempre verificado.

### Herança de ADMIN
ADMIN herda todas as permissões de todos os roles, mas quando atua dentro de um projeto age pelo papel do projeto. Isso garante rastreabilidade — toda ação clínica tem um executor com papel explícito, nunca "foi o admin".

### executor_id obrigatório
Todo registro clínico (`AssessmentRecord`, `InterventionRecord`) exige `executor_id`. Formulários autoaplicáveis (`QuestionnaireResponse` com `selfReport: true`) são a única exceção — `executor_id` é nulo porque o próprio participante é o respondente.

### Timeline — regras de visibilidade

| Visão | Quem acessa | Filtro aplicado |
|-------|-------------|-----------------|
| Pessoal | PARTICIPANT | `participant_profile_id = próprio` |
| Do projeto | PI, RESEARCHER (parcial) | `project_id = projeto autorizado` |
| Global | ADMIN, PI (seus projetos) | sem filtro / `PI nos projetos` |

RESEARCHER vê na timeline do projeto apenas os participantes que atendeu diretamente. PI pode ampliar esse acesso por configuração do projeto.

---

## Multipapéis — exemplos válidos

Um mesmo usuário pode acumular os seguintes papéis sem conflito:

- `UserRole: RESEARCHER` + PI no Projeto A + RESEARCHER no Projeto B
- `UserRole: PI` + PI no Projeto A + COLLABORATOR no Projeto C
- `UserRole: ADMIN` + PI no Projeto B + ASSISTANT no Projeto D
- `UserRole: PARTICIPANT` + PARTICIPANT enrollado em dois projetos distintos

O que não é permitido: um usuário ter dois papéis ativos no mesmo projeto ao mesmo tempo (ex: PI e RESEARCHER no Projeto A simultaneamente). Um projeto, um papel por usuário.

---

## Vocabulário controlado de papéis

Os papéis de projeto são gerenciados via `Vocabulary` (scheme `PROJECT_MEMBER_ROLE`) e não são texto livre. Os valores iniciais do seed são:

| code | label | descrição |
|------|-------|-----------|
| `PI` | Primary Investigator | responsável científico do projeto |
| `RESEARCHER` | Pesquisador | executa coleta clínica |
| `ASSISTANT` | Assistente | suporte à coleta, acesso limitado |
| `COLLABORATOR` | Colaborador | somente leitura, sem ação clínica |

Novos papéis podem ser adicionados via ADMIN sem migração de banco — o sistema valida contra o vocabulary no service.

---

## O que nunca fazer

- Usar `UserRole: ADMIN` como executor de registros clínicos — toda ação clínica precisa de papel de projeto explícito
- Verificar só o `UserRole` sem checar `ProjectMember.role` — abre acesso cross-project
- Verificar só o `ProjectMember.role` sem checar `UserRole` — um PLAYER poderia ser adicionado como membro de projeto
- Armazenar papéis de projeto como texto livre — sempre via Vocabulary
- Criar projetos sem PI definido — projetos em estado `DRAFT` podem existir sem PI, mas não podem transitar para `ACTIVE`