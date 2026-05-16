# Stack Técnica — CIATec Research API
> **Python Migration** · Revisão 1  
> Define as ferramentas, padrões arquiteturais e convenções obrigatórias para a reescrita e evolução da API.

---

## Visão geral

A API cobre dois domínios em um único serviço:

**Domínio de gameplay** — autenticação, usuários, jogos, presets, levels, sessões, matches, progresso e telemetria especializada por jogo. Endpoints de alta frequência, escrita em bulk, latência crítica.

**Domínio CRIS** — projetos, grupos, enrollments, participantes, instrumentos clínicos, registros de execução e timeline longitudinal. Endpoints de menor frequência, lógica de negócio complexa, integridade de dados crítica.

Ambos os domínios compartilham a mesma stack e o mesmo padrão arquitetural.

### Python

Versão de referência em desenvolvimento e CI: **3.14.2**. O `pyproject.toml` fixa `requires-python = ">=3.14.2,<3.15"` (linha 3.14.x). Use o mesmo patch em produção quando possível, para alinhar com `mypy` (`python_version = "3.14"`) e com o comportamento de asyncio no Windows (ProactorEventLoop).

**Ruff:** com `ruff<0.9`, o `target-version` aceito no config vai até **py313**; mantemos `py313` no `pyproject.toml` até uma versão do Ruff suportar `py314` — o interpretador continua sendo 3.14.2.

---

## Stack principal

### FastAPI
Framework web assíncrono. Escolhido pela combinação de async nativo (fundamental para receber telemetria de jogo sem bloquear outros requests), geração automática de OpenAPI/Swagger a partir dos tipos Pydantic, e alinhamento com as boas práticas da documentação oficial.

Versão: `>=0.111`  
Referência: https://fastapi.tiangolo.com

**Convenções:**
- Todo endpoint declara explicitamente `response_model` com o schema Pydantic de saída
- Routers organizados por módulo em `src/modules/<modulo>/router.py`
- Dependências de autenticação e autorização via `Depends()` — nunca inline no handler
- Handlers são finos — recebem o request, chamam o service, retornam a resposta. Sem lógica de negócio no router

```python
# correto
@router.post("/projects", response_model=ProjectOut, status_code=201)
async def create_project(
    body: ProjectCreate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectOut:
    return await service.create(body, current_user)

# errado — lógica de negócio no handler
@router.post("/projects")
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(**body.dict())
    db.add(project)
    await db.commit()
    ...
```

---

### SQLAlchemy 2 + Alembic
ORM principal e sistema de migrations. SQLAlchemy 2 com async engine via `asyncpg`. Alembic gerencia todas as migrations — nenhuma alteração de schema é feita diretamente no banco.

Versões: `sqlalchemy>=2.0`, `alembic>=1.13`, `asyncpg>=0.29`  
Referência: https://docs.sqlalchemy.org/en/20/

**Convenções — models:**
- Todos os models herdam de `Base` declarativo com `mapped_column` e `Mapped` (API 2.0)
- Tipos explícitos em todos os campos — nunca `Column(String)` sem tamanho quando aplicável
- Relacionamentos declarados com `relationship()` e `lazy="raise"` por padrão — carregamento explícito obrigatório
- Nomes de tabela em snake_case via `__tablename__`
- Timestamps `created_at` e `updated_at` em todas as tabelas, com `server_default` e `onupdate`
- PKs com `default=uuid.uuid4`: o valor **não** fica disponível em `instance.id` antes do flush; ao criar linhas dependentes na mesma transação (FK para o mesmo UUID), **atribua o UUID explicitamente** no service e passe o mesmo valor ao `User` e às tabelas filhas.

```python
# correto — SQLAlchemy 2 style
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project", lazy="raise"
    )
```

**Convenções — sessions:**
- Session async via `AsyncSession` com `expire_on_commit=False`
- Uma session por request via `Depends(get_db)` — nunca session global
- Commits e rollbacks gerenciados no service, nunca no repository

```python
# src/core/database.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

**Convenções — Alembic:**
- Toda migration tem `upgrade()` e `downgrade()` implementados
- Migrations geradas com `alembic revision --autogenerate` e revisadas manualmente antes de aplicar
- Nunca editar uma migration já aplicada em produção — sempre criar uma nova

---

### PostgreSQL
Banco de dados principal. Versão mínima: `16`.

**Convenções:**
- UUIDs como primary keys em todas as tabelas (`uuid_generate_v4()`)
- Soft delete via `deleted_at: DateTime | None` — nunca `DELETE` físico em entidades de domínio
- Índices declarados no model SQLAlchemy via `Index()` — nunca criados manualmente fora de migration
- JSON/JSONB apenas para metadados flexíveis, snapshots e payloads auxiliares — nunca para entidades centrais
- Constraints de unicidade declaradas no model e refletidas na migration

---

### Pydantic v2
Validação de entrada, serialização de saída e definição de contratos. Substitui Zod do projeto Node.

Versão: `pydantic>=2.6`  
Referência: https://docs.pydantic.dev/latest/

**Convenções:**
- Schemas separados por intenção: `<Entidade>Create`, `<Entidade>Update`, `<Entidade>Out`
- `model_config = ConfigDict(from_attributes=True)` em todos os schemas de saída
- Validadores customizados via `@field_validator` e `@model_validator` — nunca lógica de validação no service
- Nunca expor o model SQLAlchemy diretamente — sempre serializar via schema Pydantic

```python
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)
    description: str | None = None

class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    status: str
    created_at: datetime
```

---

### asyncpg
Driver PostgreSQL assíncrono nativo. Usado pelo SQLAlchemy como backend de conexão.

Versão: `asyncpg>=0.29`

---

### Alembic
Migrations de banco. Toda alteração de schema passa por migration versionada.

**Fluxo obrigatório:**
```bash
# gerar migration a partir dos models
alembic revision --autogenerate -m "descricao_clara"

# revisar o arquivo gerado em alembic/versions/

# aplicar em desenvolvimento
alembic upgrade head

# rollback se necessário
alembic downgrade -1
```

---

## Autenticação e segurança

### JWT + bcrypt
Autenticação via Bearer token. Access token de vida curta + refresh token com rotação. Mesmo modelo do projeto Node atual.

Bibliotecas: `python-jose[cryptography]>=3.3`, `bcrypt>=4.1` (pacote `bcrypt` direto — evita incompatibilidade do `passlib` com bcrypt/Python 3.14 na detecção do backend).

**Convenções:**
- Access token: 15 minutos
- Refresh token: 7 dias com rotação obrigatória
- Refresh tokens armazenados no banco com `revoked_at` para invalidação
- Senha: bcrypt com custo 12 (`bcrypt.gensalt(rounds=12)`)

### Autorização — dois eixos
Verificação sempre em dois passos via `Depends()`:

1. `get_current_user` — valida o JWT e retorna o usuário
2. `require_project_role(roles)` — verifica o `ProjectMember.role` no projeto do request

```python
# dependências de autorização
async def get_current_user(token: str = Depends(oauth2_scheme), ...) -> User: ...
async def require_admin(user: User = Depends(get_current_user)) -> User: ...
async def require_project_role(*roles: str): ...  # retorna Depends configurável
```

---

## Testes

### pytest + httpx + pytest-asyncio
Testes assíncronos com cliente HTTP real contra a aplicação em memória.

Versões: `pytest>=8`, `httpx>=0.27`, `pytest-asyncio>=0.23`

**Convenções:**
- Banco de testes isolado — banco separado, limpo a cada sessão de teste
- Fixtures em `conftest.py` por módulo
- Cada teste cobre: happy path + pelo menos 2 casos de erro
- Testes de integração cobrem o fluxo completo: request → banco → response
- Cobertura mínima de 80% por módulo — medida com `pytest-cov`

```python
# exemplo de teste de integração
@pytest.mark.asyncio
async def test_create_project_success(client: AsyncClient, admin_token: str):
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Estudo A", "code": "CIATEC-2025-001"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["code"] == "CIATEC-2025-001"

@pytest.mark.asyncio
async def test_create_project_duplicate_code(client: AsyncClient, admin_token: str):
    # setup
    await client.post("/api/v1/projects", json={...}, headers=...)
    # duplicate
    response = await client.post("/api/v1/projects", json={...}, headers=...)
    assert response.status_code == 409
```

---

## Painel administrativo

### sqladmin
Painel de administração para FastAPI + SQLAlchemy. Cobre o gerenciamento de vocabulários, condições de saúde, templates de instrumentos e usuários — operações exclusivas do role ADMIN.

Versão: `sqladmin>=0.16`  
Referência: https://aminalaee.dev/sqladmin/

**Convenções:**
- ModelView declarado para cada entidade administrativa
- Autenticação do painel via `AuthenticationBackend` customizado — reutiliza o JWT da API
- Acesso restrito a `UserRole.ADMIN`

---

## Estrutura de pastas

```
src/
├── core/
│   ├── config.py          # settings via pydantic-settings
│   ├── database.py        # engine, session factory, get_db
│   ├── security.py        # JWT, bcrypt, dependências de auth
│   ├── exceptions.py      # exceções de domínio customizadas
│   └── middleware.py      # CORS, logging, error handling
│
├── modules/
│   ├── auth/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   │
│   ├── users/
│   ├── catalog/           # jogos, presets, levels (público + admin)
│   ├── sessions/          # sessões diárias
│   ├── matches/           # partidas, resultados, progresso
│   ├── progress/
│   │
│   ├── telemetry/
│   │   ├── trunktilt/     # world, pose, events
│   │   ├── bubbles/
│   │   └── bestbeat/
│   │
│   ├── participants/      # CRIS — ParticipantProfile
│   ├── participant_conditions/
│   ├── health_conditions/
│   ├── vocabulary/        # CRIS — VocabularyScheme, VocabularyTerm
│   ├── projects/          # CRIS — Project, ProjectMember
│   ├── project_enrollments/  # CRIS — ParticipantEnrollment
│   ├── project_groups/    # CRIS — ProjectGroup (tabela groups)
│   ├── project_members/   # CRIS — ProjectMember (equipe)
│   ├── enrollments/       # (futuro) rotas; modelo em participant_enrollment.py
│   ├── instruments/       # CRIS — assessments + questionnaires (/instruments/…)
│   ├── records/           # (futuro) registros de execução
│   ├── timeline/          # (futuro) TimelineEvent + visões
│   └── self_report/       # (futuro) formulários autoaplicáveis
│
├── models/                # models SQLAlchemy (importados pelos módulos)
│   ├── base.py
│   ├── user.py
│   ├── game.py
│   ├── session.py
│   ├── match.py
│   ├── telemetry.py
│   ├── participant.py
│   ├── project.py
│   ├── enrollment.py
│   ├── instrument.py
│   ├── record.py
│   └── timeline.py
│
└── main.py                # criação da app, registro de routers, lifespan

alembic/
├── versions/
├── env.py
└── alembic.ini

tests/
├── conftest.py
└── modules/
    ├── test_auth.py
    ├── test_games.py
    ├── test_projects.py
    └── ...
```

---

## Padrão arquitetural — Repository + Service + Router

### Responsabilidades por camada

**Router** — recebe o request HTTP, valida entrada via Pydantic, chama o service, retorna a resposta. Sem lógica de negócio. Sem acesso direto ao banco.

**Service** — contém toda a lógica de negócio. Orquestra chamadas ao repository, aplica regras de domínio, lança exceções de negócio, gerencia transações. Sem conhecimento de HTTP.

**Repository** — único ponto de acesso ao banco. Queries SQLAlchemy, sem lógica de negócio. Recebe e retorna models ou tipos primitivos.

```
request → Router → Service → Repository → PostgreSQL
                ↓
           Pydantic (validação entrada / serialização saída)
```

### Injeção de dependências
Services e repositories injetados via `Depends()` do FastAPI — nunca instanciados diretamente no handler.

```python
# repository
class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID) -> Project | None:
        result = await self.db.execute(
            select(Project).where(Project.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> Project:
        project = Project(**data)
        self.db.add(project)
        await self.db.flush()
        return project

# service
class ProjectService:
    def __init__(self, repo: ProjectRepository):
        self.repo = repo

    async def create(self, body: ProjectCreate, actor: User) -> Project:
        existing = await self.repo.get_by_code(body.code)
        if existing:
            raise ConflictError("Código de projeto já existe")
        return await self.repo.create(body.model_dump())

# dependências
def get_project_repository(db: AsyncSession = Depends(get_db)) -> ProjectRepository:
    return ProjectRepository(db)

def get_project_service(
    repo: ProjectRepository = Depends(get_project_repository),
) -> ProjectService:
    return ProjectService(repo)
```

### Tratamento de erros
Exceções de domínio customizadas mapeadas para HTTP via exception handlers globais em `main.py`. Nunca levantar `HTTPException` dentro do service.

```python
# core/exceptions.py
class NotFoundError(Exception): ...
class ConflictError(Exception): ...
class ForbiddenError(Exception): ...
class ValidationError(Exception): ...

# core/middleware.py — handlers globais
@app.exception_handler(NotFoundError)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"code": "NOT_FOUND", "message": str(exc)})
```

---

## Convenções gerais

### Nomenclatura
- Arquivos e pastas: `snake_case`
- Classes: `PascalCase`
- Funções e variáveis: `snake_case`
- Constantes: `UPPER_SNAKE_CASE`
- Endpoints: `kebab-case` nas URLs, substantivos no plural (`/projects`, `/health-conditions`)

### Versionamento de API
Todas as rotas sob `/api/v1/`. Prefixo aplicado no registro do router em `main.py`.

### Respostas de erro
Formato padronizado em todos os erros:
```json
{
  "success": false,
  "code": "NOT_FOUND",
  "message": "Projeto não encontrado",
  "details": []
}
```

### Variáveis de ambiente
Gerenciadas via `pydantic-settings` com validação na inicialização. Nunca `os.getenv()` direto no código.

```python
# core/config.py
class Settings(BaseSettings):
    database_url: PostgresDsn
    secret_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    model_config = ConfigDict(env_file=".env")

settings = Settings()
```

### Logging
Logging estruturado via `structlog`. Nível `INFO` em produção, `DEBUG` em desenvolvimento. Todo request logado com `method`, `path`, `status_code` e `duration_ms`.

---

## Dependências — resumo

```toml
# pyproject.toml (resumo; o repo usa setuptools, não Poetry)
[project]
requires-python = ">=3.14.2,<3.15"
dependencies = [
  "fastapi>=0.111,<0.116",
  "uvicorn[standard]>=0.30,<0.32",
  "sqlalchemy[asyncio]>=2.0,<2.1",
  "alembic>=1.13,<1.16",
  "asyncpg>=0.29,<0.32",
  "pydantic>=2.11,<3",
  "pydantic-settings>=2.2,<3",
  "python-jose[cryptography]>=3.3,<3.4",
  "bcrypt>=4.1,<5",
  "email-validator>=2.0,<3",
  "httpx>=0.27,<0.29",
]

[project.optional-dependencies]
dev = [
  "pytest>=8,<9",
  "pytest-asyncio>=0.23,<0.26",
  "python-dotenv>=1.0,<2",
  "ruff>=0.6,<0.9",
  "mypy>=1.10,<1.14",
]
```

---

## Fase 0 — Baseline da API (paridade funcional)

A API **Python v2** neste repositório é o produto ativo. A “Fase 0” descreve o conjunto de capacidades de gameplay/auth/catalog/sessões/telemetria que devem estar estáveis **antes** de expandir o CRIS além do que o [`BACKLOG.md`](BACKLOG.md) já marcou como concluído. Não é necessário manter paridade linha-a-linha com um monólito Node legado — use testes de integração e OpenAPI como critério.

**Escopo típico da Fase 0 (já refletido no backlog inicial):**

| Módulo | Endpoints |
|--------|-----------|
| Auth | register, login, refresh, logout, me |
| Users | CRUD completo + listagem paginada |
| Catalog | games, presets, levels (público + admin) |
| Sessions | start, current, create match |
| Matches | preset, level, finish (com idempotência) |
| Progress | start |
| Telemetria TrunkTilt | world, pose, events |
| Telemetria Bubbles | world, pose, events |
| Telemetria Bestbeat | world, pose, events |

**Critério de aprovação da Fase 0 (Python v2):**
- Endpoints críticos documentados no OpenAPI e alinhados aos contratos acordados com o frontend
- Testes de integração cobrindo happy path + casos de erro principais
- Telemetria recebendo batches em async sem degradar outros endpoints
- Migração Alembic limpa aplicável do zero

---

## O que nunca fazer

- Lógica de negócio no router
- Acesso direto ao banco fora do repository
- `os.getenv()` fora do `Settings`
- Migrations manuais no banco sem Alembic
- JSON para entidades centrais do CRIS
- `HTTPException` dentro do service
- Commits de banco no repository — somente no service
- Expor models SQLAlchemy diretamente nas respostas
- Testes sem banco isolado — nunca testar contra o banco de desenvolvimento