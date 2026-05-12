# Deploy e atualizações da API

**Índice da documentação:** [docs/README.md](./README.md) · **setup local:** [COMO-RODAR-LOCAL.md](./COMO-RODAR-LOCAL.md)

Este guia resume o fluxo sempre que houver **nova versão do código** (local, EC2 ou outro servidor com Docker). A API roda em **Node 22** dentro da imagem; o PostgreSQL de desenvolvimento local usa **Docker Compose** (Postgres 18). Em produção, o banco costuma ser **RDS** (ou outro Postgres gerenciado).

**Antes de cada PR para `main`:** checklist fixo em **[PR-PRODUCTION-READINESS.md](./PR-PRODUCTION-READINESS.md)** (build, lint, Prisma, `docker build`, texto da PR). O deploy em produção assume que esse checklist já foi cumprido no merge.

---

## Convenções

| Artefato | Função |
|----------|--------|
| [Dockerfile](../Dockerfile) | Imagem da API (build multi-stage) |
| [docker-compose.yml](../docker-compose.yml) | Postgres + pgAdmin **só para desenvolvimento local** |
| [.env.example](../.env.example) | Modelo de variáveis (copiar para `.env` no host; não commitar segredos) |
| [src/config/env.ts](../src/config/env.ts) | Lista canônica de variáveis obrigatórias |

**Produção:** `NODE_ENV=production`, `DATABASE_URL` do RDS, `APP_URL` com URL pública (ex.: `https://api.exemplo.org`), segredos JWT fortes.

---

## 1. Desenvolvimento local (primeira vez ou após mudar dependências)

1. Subir o banco: na raiz do repo, `docker compose up -d`.
2. Criar `.env` a partir de `.env.example` e ajustar `DATABASE_URL` (localhost + porta 5432 do compose).
3. Na máquina host: `npm install`, `npm run db:deploy`, `npm run db:seed` (seed conforme necessidade).
4. API no host: `npm run dev` **ou** API em Docker (ver seção 3 abaixo).

Se o Postgres do compose foi atualizado de major version e o volume antigo der erro, veja [COMO-RODAR-LOCAL.md](./COMO-RODAR-LOCAL.md) (nota sobre volume).

---

## 2. Build da imagem (qualquer ambiente)

O daemon do Docker precisa estar em execução no host (ex.: Docker Desktop no Windows).

Na raiz do repositório:

```bash
docker build -t ciatec-research-api:latest .
```

Tagueie por versão ou commit quando for rastrear releases:

```bash
docker build -t ciatec-research-api:$(git rev-parse --short HEAD) .
```

---

## 3. Testar a imagem localmente contra o Postgres do Compose

O container da API precisa alcançar o Postgres que está escutando na **máquina host** (porta publicada `5432`).

- **Windows / macOS (Docker Desktop):** use o host `host.docker.internal` na `DATABASE_URL`.
- **Linux:** ao rodar o container, adicione `--add-host=host.docker.internal:host-gateway`.

Exemplo de `DATABASE_URL` dentro do container:

```text
postgresql://postgres:postgres@host.docker.internal:5432/ciatec_research
```

**Antes** de subir a API, o esquema do banco deve existir. No host (com Postgres de pé):

```bash
npm run db:deploy
```

Subir o container (ajuste caminho do env ou use `-e`):

```bash
docker run --rm -p 3333:3333 --env-file .env.docker ciatec-research-api:latest
```

Crie `.env.docker` localmente (gitignored) copiando de `.env.example` e trocando só o host do Postgres para `host.docker.internal`. Não commite esse arquivo.

Verificação: `GET http://localhost:3333/health` deve retornar `status: ok`.

**Migrações a partir do container** (útil em servidores):

```bash
docker run --rm --env-file .env.production ciatec-research-api:latest npx prisma migrate deploy
```

(Exige `DATABASE_URL` apontando para um Postgres acessível a partir do container.)

---

## 4. Atualização em servidor (EC2 ou similar, sem ECR)

Fluxo típico **a cada release**:

1. **Backup** do banco (política da equipe / snapshots RDS).
2. No servidor, entrar na pasta do repositório e atualizar código: `git pull` (ou extrair artefato).
3. **Build:** `docker build -t ciatec-research-api:latest .` (ou tag com SHA do commit).
4. **Migrações:** rodar `migrate deploy` (no host com `DATABASE_URL` do RDS **ou** com o comando `docker run` da seção 3, usando env de produção).
5. **Substituir o container** em execução: parar o container antigo e subir o novo com as mesmas variáveis de ambiente (`-e` / `--env-file` no disco do servidor, **não** no Git).
6. **Verificar:** `GET /health` e um fluxo crítico da API.

Se usar **docker compose** só para a API no servidor (sem serviço Postgres no YAML), mantenha um `compose` ou script que passe `env_file` e `ports` coerentes com o **Nginx** na frente.

---

## 5. Nginx no EC2 (TLS e proxy)

Sem ALB: o Nginx escuta **443** (Let’s Encrypt ou certificado próprio) e faz `proxy_pass` para `http://127.0.0.1:<PORT>`, onde `<PORT>` é a mesma definida no `.env` da API (`PORT`). `APP_URL` deve ser a URL **https** que o cliente usa.

Detalhes de configuração do Nginx ficam fora deste repositório; apenas alinhe `APP_URL`, `PORT` e o `proxy_pass`.

---

## 6. Checklist rápido pós-deploy

- [ ] `NODE_ENV=production` no ambiente do container.
- [ ] `DATABASE_URL` correto e testado; RDS aceita conexão do security group do EC2.
- [ ] `JWT_*` e demais segredos não versionados.
- [ ] Migrações aplicadas antes ou durante o deploy (`migrate deploy`).
- [ ] `/health` OK e logs sem erros de boot.

---

## 7. Rollback

- **Aplicação:** subir de novo a imagem anterior (tag/SHA guardado) e reiniciar o container.
- **Banco:** rollback de migração é delicado; prefira restore de backup + imagem antiga alinhada ao esquema esperado.

---

## Referências no repo

- [COMO-RODAR-LOCAL.md](./COMO-RODAR-LOCAL.md) — fluxo dev, Compose, Postgres 18.
- [DOT-ENV-GUIDE.md](./DOT-ENV-GUIDE.md) — descrição das variáveis do `.env`.
