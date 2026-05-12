# Guia de implementação: login e cadastro (API)

Este documento descreve como o cliente web ou mobile deve integrar **cadastro (signup)** e **login** com a Ciatec Research API, além do fluxo mínimo de tokens. Serve como referência para o time de frontend implementar autenticação de ponta a ponta.

---

## Onde está a documentação

| O quê | URL |
| --- | --- |
| **API e documentação interativa (produção)** | [`https://api.ciatec.org`](https://api.ciatec.org) — Swagger UI em **`/docs`** |
| **OpenAPI / Swagger em produção** | [`https://api.ciatec.org/docs`](https://api.ciatec.org/docs) |
| **Visão geral da API (frontend)** | [`FRONTEND-API-OVERVIEW.md`](./FRONTEND-API-OVERVIEW.md) |

Em **desenvolvimento local**, com o servidor a correr, a mesma UI fica em `http://localhost:<PORT>/docs` (porta habitual no projeto: **3333**; confira `PORT` / `APP_URL` no `.env`).

---

## 1. Base da URL e cabeçalhos

### Ambientes

| Ambiente | Base URL da API | Swagger (`/docs`) |
| --- | --- | --- |
| **Produção** | `https://api.ciatec.org` | [`https://api.ciatec.org/docs`](https://api.ciatec.org/docs) |
| **Local** | `http://localhost:<PORT>` (ex.: `http://localhost:3333`) | `http://localhost:<PORT>/docs` |

### Convenções

| Item | Valor |
| --- | --- |
| Prefixo da API | `/api/v1` |
| Rotas de autenticação | `/api/v1/auth/...` |
| Corpo | JSON: `Content-Type: application/json` |
| CORS | A API usa `cors` com `origin: true` (o navegador pode fazer requisições a partir do origin do app em desenvolvimento) |

### URLs completas (produção)

- Registo: `POST https://api.ciatec.org/api/v1/auth/register`
- Login: `POST https://api.ciatec.org/api/v1/auth/login`

Em **local**, substitua o host por `http://localhost:<PORT>` mantendo o mesmo path (`/api/v1/auth/...`).

---

## 2. Cadastro (signup): `POST /api/v1/auth/register`

Cria um utilizador com papel **PLAYER** e devolve pares de tokens.

### Corpo (JSON)

| Campo | Tipo | Regras |
| --- | --- | --- |
| `email` | string | E-mail válido |
| `password` | string | Mínimo **8** caracteres, **pelo menos 1 letra maiúscula** e **pelo menos 1 dígito** (0–9) |
| `name` | string | Não vazio (mínimo 1 caractere) |

Exemplo:

```json
{
  "email": "jogador@exemplo.com",
  "password": "Senha1234",
  "name": "Nome do Jogador"
}
```

### Respostas de sucesso

- **201 Created**  
  Corpo (campos principais):

```json
{
  "user": {
    "id": "<uuid>",
    "email": "jogador@exemplo.com",
    "name": "Nome do Jogador",
    "role": "PLAYER"
  },
  "accessToken": "<JWT>",
  "refreshToken": "<JWT>"
}
```

### Erros comuns

| HTTP | Uso |
| --- | --- |
| **400** | Validação (formato de corpo, password que não cumpre regras, etc.) |
| **409** | E-mail já registado (`Email already in use`) |

Formato de erro de validação (Zod) — **400:**

```json
{
  "success": false,
  "code": "VALIDATION_ERROR",
  "message": "Validation error",
  "details": [ /* issues Zod */ ],
  "issues": [ /* igual a details */ ]
}
```

Formato de erro de aplicação (ex.: conflito) — **409:**

```json
{
  "success": false,
  "code": "CONFLICT",
  "message": "Email already in use"
}
```

**Implementação sugerida:** após 201, guardar `accessToken` e `refreshToken` (ver secção 5) e redirecionar para a área autenticada.

---

## 3. Login: `POST /api/v1/auth/login`

### Corpo (JSON)

| Campo | Tipo | Regras |
| --- | --- | --- |
| `email` | string | E-mail válido |
| `password` | string | Mínimo 1 caractere (sem as regras extras do registo) |

Exemplo:

```json
{
  "email": "jogador@exemplo.com",
  "password": "Senha1234"
}
```

### Respostas

- **200 OK** — mesmo formato de sucesso que o registo: `{ user, accessToken, refreshToken }`.
- **400** — corpo inválido (ex.: e-mail mal formatado).
- **401** — credenciais erradas.

Para **401**, a mensagem é propositadamente **genérica**:

```json
{
  "success": false,
  "code": "UNAUTHORIZED",
  "message": "Invalid credentials"
}
```

**Importante para UI/UX:** não tente distinguir “e-mail desconhecido” vs “password errada” com base na resposta — a API **não** o permite. Mostre um único erro neutro, por exemplo: “E-mail ou palavra-passe incorretos”.

---

## 4. O que fazer com os tokens (resumo)

- **Access token (JWT):** enviar em pedidos autenticados:  
  `Authorization: Bearer <accessToken>`
- **Refresh token (JWT):** enviar no corpo de `POST /api/v1/auth/refresh` para obter um **novo par** quando o access expirar.
- **Rotação:** cada refresh **invalida** o refresh anterior. Sempre **substitua e persista o novo** `refreshToken` devolvido.
- Nome, e-mail e detalhes completos de perfil: o JWT de access contém sobretudo `sub` (id) e `role`. Para e-mail/nome actualizados use **`GET /api/v1/auth/me`** com o access token.
- Prazo de expiração dos tokens depende do ambiente (variáveis do servidor, ex. `JWT_EXPIRES_IN`). Não hardcodeie “30 minutos” no front sem alinhar com a API.

Rotas auxiliares usam o mesmo prefixo (`/api/v1/auth`): `POST /refresh`, `POST /logout` e `GET /me`. Os pedidos em produção usam o mesmo prefixo completo: `https://api.ciatec.org/api/v1/auth/...`.

---

## 5. Fluxo recomendado no cliente (checklist)

1. **Ecrã de registo** → `POST /register` → 201 → guardar tokens; opcionalmente chamar `GET /me` se precisar de `createdAt` ou dados extra.
2. **Ecrã de login** → `POST /login` → 200 → guardar tokens.
3. **Chamadas à API protegida** → header `Authorization: Bearer ...`.
4. Se uma chamada devolver **401** por access expirado → **um** `POST /refresh` com o refresh actual → substituir ambos os tokens → repetir o pedido original; se o refresh falhar (401) → apagar tokens e ir para o login.
5. **Terminar sessão** → `POST /auth/logout` com access no header; opcionalmente enviar o `refreshToken` no corpo para revogar só essa sessão.

Onde guardar os tokens (memória, `sessionStorage`, cookies HttpOnly, etc.) é uma decisão do front e do modelo de ameaças; **não** coloque refresh tokens em logs.

---

## 6. Referência rápida de tipos (TypeScript)

Ajuste se o backend evoluir; útil para alinhar o cliente:

```ts
// Pedidos
type RegisterBody = { email: string; password: string; name: string };
type LoginBody = { email: string; password: string };

// Sucesso (register 201, login 200)
type UserPublic = {
  id: string;
  email: string;
  name: string;
  role: 'PLAYER' | 'RESEARCHER' | 'ADMIN';
};
type AuthSuccess = { user: UserPublic; accessToken: string; refreshToken: string };

// Erro de aplicação
type AppErrorBody = { success: false; code: string; message: string };
```

---

## 7. Documentação OpenAPI

A especificação interactiva (contratos, schemas de `Auth`, exemplos alinhados ao código) está na **documentação hospedada na API**:

- **Produção:** [`https://api.ciatec.org/docs`](https://api.ciatec.org/docs)
- **Local:** `http://localhost:<PORT>/docs` quando o servidor estiver a correr

Para detalhes de contrato, schemas e exemplos atualizados, use a tag **Auth** no Swagger.
