# Autenticação — URLs de produção

**Host da API:** `https://api.ciatec.org`

**Prefixo da API:** `/api/v1`

**Base de autenticação:** `https://api.ciatec.org/api/v1/auth`

O contrato (corpos de pedido, respostas, cabeçalhos, rotação de refresh, notas de segurança) está descrito em [`AUTH-FLOW.md`](./AUTH-FLOW.md). Este documento apenas lista os **caminhos completos em produção**.

---

## Endpoints de autenticação

| Método | Caminho relativo | URL absoluta (produção) |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | `https://api.ciatec.org/api/v1/auth/register` |
| `POST` | `/api/v1/auth/login` | `https://api.ciatec.org/api/v1/auth/login` |
| `POST` | `/api/v1/auth/refresh` | `https://api.ciatec.org/api/v1/auth/refresh` |
| `POST` | `/api/v1/auth/logout` | `https://api.ciatec.org/api/v1/auth/logout` |
| `GET` | `/api/v1/auth/me` | `https://api.ciatec.org/api/v1/auth/me` |

- **`POST /logout` e `GET /me`:** enviar `Authorization: Bearer <accessToken>`.

---

## Outros caminhos úteis (mesmo host)

| Finalidade | URL absoluta |
| --- | --- |
| Health check | `https://api.ciatec.org/health` |
| Documentação OpenAPI (Swagger UI) | `https://api.ciatec.org/docs` |

---

## Exemplo rápido (cliente)

- Registo: `POST https://api.ciatec.org/api/v1/auth/register`
- Login: `POST https://api.ciatec.org/api/v1/auth/login`
- Perfil: `GET https://api.ciatec.org/api/v1/auth/me` com o access token no header.

Para detalhes de payloads e fluxo recomendado, ver [`AUTH-FLOW.md`](./AUTH-FLOW.md).
