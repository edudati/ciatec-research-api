# Authentication (API contract)

Base path: `/api/v1/auth`

## Tokens

| Token | Secret | TTL | Storage |
| --- | --- | --- | --- |
| **Access** | `JWT_SECRET` | `JWT_EXPIRES_IN` (e.g. `30m`) | Client only |
| **Refresh** | `JWT_REFRESH_SECRET` | `JWT_REFRESH_EXPIRES_IN` (e.g. `7d`) | Client + server stores **SHA-256 hash** only |

Both tokens are JWTs with registered claims `iss` (`JWT_ISSUER`) and `aud` (`JWT_AUDIENCE`). Payload includes `sub` (user id) and `role` (`ADMIN` \| `RESEARCHER` \| `PLAYER`). **Name and email are not in the JWT**; use `GET /auth/me` with the access token.

## Endpoints

### `POST /register`

Body: `{ "email": string, "password": string, "name": string }`

- Password: min 8 chars, ≥1 uppercase letter, ≥1 digit.
- Creates user with role `PLAYER`.
- Returns `201` with `{ user, accessToken, refreshToken }`.

### `POST /login`

Body: `{ "email": string, "password": string }`

- Returns `200` with `{ user, accessToken, refreshToken }`.
- Invalid email/password both respond with **the same** message: `Invalid credentials` (do not branch in the UI).

### `POST /refresh`

Body: `{ "refreshToken": string }`

- Verifies refresh JWT, checks DB row (not revoked, not expired), **revokes the used refresh row**, issues a **new** access + refresh pair.
- Returns `200` with `{ accessToken, refreshToken }`.
- **Rotation:** every successful refresh invalidates the previous refresh token. Persist the new refresh; old one will fail.

### `POST /logout`

Headers: `Authorization: Bearer <accessToken>`

Body (optional JSON): `{ "refreshToken"?: string }`

- If `refreshToken` is sent: revoke that refresh session (when it matches the authenticated user).
- If omitted: revoke **all** refresh sessions for the user.
- Returns `204` with no body.

### `GET /me`

Headers: `Authorization: Bearer <accessToken>`

- Returns `200` with `{ id, email, name, role, createdAt }`.

## Client flow (recommended)

1. Store `accessToken` and `refreshToken` securely (memory + secure storage tradeoffs are your choice).
2. Call protected routes with `Authorization: Bearer <accessToken>`.
3. On `401` from expired access: call `POST /refresh` **once** with the current refresh token; replace both tokens; retry the original request.
4. If refresh fails (`401`): clear tokens and send the user through login/register again.
5. On explicit sign-out: call `POST /logout` with the access token; optionally send `refreshToken` to revoke a single device session.

## Security notes for frontend

- Treat refresh tokens like credentials; prefer HTTP-only cookies if you move to cookie-based refresh (not required by this API today).
- Never log raw refresh tokens.
- Do not infer identity from JWT beyond `sub` and `role`; load profile via `/me` when you need email/name.
