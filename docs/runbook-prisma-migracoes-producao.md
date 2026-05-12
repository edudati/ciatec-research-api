# Runbook: migrações Prisma, drift e produção

**Índice:** [docs/README.md](./README.md) · [AGENTS.md](../AGENTS.md)

Este documento orienta **agentes** (ou humanos) a **diagnosticar** problemas de migração, **comparar** o estado da base com a **versão do código** que vai para produção e **corrigir** o ambiente alvo quando houver inconsistência.

Antes de abrir PR para `main`, cumprir primeiro o checklist fixo em **[PR-PRODUCTION-READINESS.md](./PR-PRODUCTION-READINESS.md)**; este runbook entra quando há falha ou ambiguidade após esse fluxo.

---

## 1. Contexto rápido

- O **schema canónico** da aplicação está em `prisma/schema.prisma`.
- As alterações versionadas estão em `prisma/migrations/<timestamp>_<nome>/migration.sql`.
- O Prisma regista o que já foi aplicado na tabela **`_prisma_migrations`** (PostgreSQL).
- **Drift** = o que está na BD (tabelas/colunas) ou em `_prisma_migrations` **não bate certo** com o histórico de ficheiros no Git da versão que vais deployar.

Sintomas típicos:

- `npx prisma migrate deploy` falha (ex.: objeto já existe, migração fantasma).
- `npx prisma migrate status` reporta migrações “na BD mas não no repo” ou muitas “por aplicar” apesar da BD já ter o schema.

---

## 2. O que a versão “vamos atualizar na produção” significa

Antes de qualquer comparação, fixar:

1. **Branch/commit** que será deployado (ex.: `main` após merge, ou tag de release).
2. **Árvore de migrações** nesse commit: listar pastas em `prisma/migrations/` (ordenadas por nome/timestamp).
3. **Última migração esperada** = a pasta com maior timestamp nesse commit (ex.: `20260506123000_match_result_server_duration_ms`).

O agente deve usar **sempre** o mesmo commit que o pipeline de produção vai usar, não um checkout local desatualizado.

---

## 3. Como recolher informação (diagnóstico)

### 3.1 No repositório (código alvo de produção)

```bash
git fetch origin && git checkout <branch-ou-tag-de-release>
```

- Ler `prisma/schema.prisma` (modelos, `@@map`, `@map`).
- Listar migrações: `ls prisma/migrations` (ou equivalente no SO).
- Opcional: `npx prisma migrate diff --from-migrations prisma/migrations --to-schema-datamodel prisma/schema.prisma --script`  
  (deve ser vazio ou só comentários se pastas e schema estão alinhados.)

### 3.2 Na base de dados do ambiente (local/staging/produção)

**Variável:** `DATABASE_URL` apontando para **esse** ambiente (nunca misturar URLs).

1. **Estado segundo o Prisma**

   ```bash
   npx prisma migrate status
   ```

   Interpretar:

   - **“Migrations have not yet been applied”** — lista o que o Prisma acha que falta aplicar.
   - **“Migrations from the database are not found locally”** — há linhas em `_prisma_migrations` com `migration_name` que **não existe** em `prisma/migrations` no checkout atual → histórico **quebrado** ou repo **diferente** do que criou a BD.

2. **Tentativa controlada de aplicar (staging primeiro; produção só com janela e backup)**

   ```bash
   npx prisma migrate deploy
   ```

   Guardar mensagem de erro completa (código PostgreSQL, nome da migração).

3. **Inspeção direta (quando `migrate status` for ambíguo)**

   Executar SQL read-only (psql, cliente GUI, ou `prisma db execute` com ficheiro só de `SELECT`):

   ```sql
   SELECT migration_name, finished_at, applied_steps_count
   FROM _prisma_migrations
   ORDER BY finished_at, migration_name;
   ```

   Comparar nomes com as pastas em `prisma/migrations/` do commit de release.

   Para tabelas críticas (ex.: `match_results`):

   ```sql
   SELECT column_name, data_type
   FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'match_results'
   ORDER BY ordinal_position;
   ```

   Cruzar com `MatchResult` em `schema.prisma` (`@map` → nome real na BD).

---

## 4. Como comparar “BD atual” vs “versão que vamos deployar”

| Pergunta | Onde verificar |
|----------|----------------|
| O código de release inclui quais migrações? | Pastas em `prisma/migrations` no commit de release. |
| A BD já tem essas alterações físicas? | `information_schema` / `\d tabela` / `migrate diff` (ver abaixo). |
| O Prisma “sabe” que as migrações foram aplicadas? | `_prisma_migrations.migration_name` vs nomes das pastas. |

**Comando útil (gera SQL entre schema da BD e o datamodel do repo):**

```bash
npx prisma migrate diff \
  --from-url "$DATABASE_URL" \
  --to-schema-datamodel prisma/schema.prisma \
  --script
```

- Se sair **vazio** (ou só transações vazias): schema da BD **compatível** com `schema.prisma` desse commit.
- Se sair **ALTER/CREATE**: há **drift**; o script mostra o que falta (ou o que sobra) relativamente ao schema declarado.

**Atenção:** isto não substitui validar `_prisma_migrations`; podes ter schema “certo” à mão mas histórico errado (ou o contrário).

---

## 5. Caminhos de correção (por cenário)

Ordem recomendada: **sempre staging primeiro**; produção só com backup, janela e rollback plano.

### Cenário A — Histórico limpo; só faltam migrações do repo

- `migrate status` lista migrações por aplicar **e não** há “migrations from the database not found locally”.
- `migrate deploy` **completa sem erro**.

**Ação:** em produção, no deploy: executar `npx prisma migrate deploy` (ou o passo equivalente no CI/CD) **antes** ou **conforme** o processo atual de arranque da API.

### Cenário B — Schema já reflete o `schema.prisma`, mas `_prisma_migrations` está incompleto

Às vezes alguém aplicou SQL manualmente e não registou no Prisma.

1. Confirmar com `migrate diff --from-url --to-schema-datamodel` que não há alterações pendentes (ou só triviais).
2. Para **cada** migração já refletida na BD mas não listada como aplicada, usar **marcação explícita** (evitar reexecutar SQL destrutivo):

   ```bash
   npx prisma migrate resolve --applied "20260506123000_nome_da_pasta"
   ```

   Repetir só para migrações **já** refletidas na BD. Validar de novo com `migrate status`.

**Risco:** marcar como aplicada uma migração cujo SQL **nunca** correu na BD deixa o schema errado. Por isso o passo 1 (`migrate diff`) é obrigatório.

### Cenário C — Entradas fantasma em `_prisma_migrations` (nome no BD, pasta não existe no repo)

Ex.: `migration_name = '20260505120000_init'` no PostgreSQL, mas **não** existe `prisma/migrations/20260505120000_init/` no Git da release.

**Não** apagar linhas em produção sem análise.

1. Identificar **quem** criou essa migração (outro branch, fork, deploy antigo).
2. Se for erro evidente e a BD já está alinhada com o repo **e** há consenso da equipa:
   - Opção conservadora: **baseline** documentado (ticket + SQL + revisão).
   - Remover só a linha fantasma **se** `migrate status` e `migrate diff` confirmarem que o resto do histórico local pode continuar; depois `migrate deploy`.

Se não houver consenso, tratar como **incidente**: copiar estado de `_prisma_migrations` e schema para análise offline.

### Cenário D — `migrate deploy` falha a meio (ex.: “tipo já existe”)

Indica migração a correr **contra** um estado parcial ou duplicado.

1. Ler a migração que falhou e o erro PostgreSQL.
2. Comparar com `migrate diff --from-url --to-schema-datamodel`.
3. Corrigir **manualmente** só o delta necessário (ex.: `IF NOT EXISTS` em ambiente de dev; em produção, script revisto por humano).
4. Usar `migrate resolve` (`--applied` ou `--rolled-back` conforme [documentação Prisma](https://www.prisma.io/docs/orm/prisma-migrate/workflows/troubleshooting-development)) para destravar o histórico **após** o schema estar correto.

### Cenário E — Ambiente de desenvolvimento apenas (nunca produção)

- `npx prisma migrate reset` — **apaga dados** e reaplica migrações do zero.

Útil para developer local; **proibido** como solução padrão em produção.

---

## 6. Checklist mínimo antes de produção

- [ ] Deploy usa o **mesmo commit** que foi validado em staging.
- [ ] Em staging: `migrate deploy` OK **ou** drift documentado e resolvido com `migrate resolve` + SQL auditado.
- [ ] `migrate diff --from-url production_readonly_url --to-schema-datamodel prisma/schema.prisma` revisto (ou equivalente em staging espelho).
- [ ] Backup/snapshot da BD de produção antes de primeira migração “arriscada”.
- [ ] Plano de rollback (reverter deploy de aplicação **e** saber se migrações são reversíveis — muitas não são).

---

## 7. O que o agente **não** deve fazer

- Não assumir que a BD local e produção partilham o mesmo `_prisma_migrations`.
- Não correr `migrate reset` em produção.
- Não apagar linhas de `_prisma_migrations` sem cruzar com `schema.prisma`, pastas de migração e `migrate diff`.
- Não usar `db push` em produção se o projeto adota **migrações versionadas** (só exceções documentadas pela equipa).

---

## 8. Referências internas do projeto

- Schema: `prisma/schema.prisma`
- Migrações: `prisma/migrations/`
- Comandos úteis no `package.json`: `db:deploy` → `prisma migrate deploy`

Para detalhes oficiais de recuperação: [Prisma — Troubleshooting migrations](https://www.prisma.io/docs/orm/prisma-migrate/workflows/troubleshooting-development).
