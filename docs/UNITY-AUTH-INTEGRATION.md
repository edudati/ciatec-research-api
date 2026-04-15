# Unity Auth Integration (Login/Password)

Guia curto para integrar autenticacao da API no cliente Unity.

Base URL local (exemplo): `http://localhost:3333`  
Base path auth: `/api/v1/auth`

## Endpoints usados no app

- `POST /api/v1/auth/register`
  - body: `{ "email": "...", "password": "...", "name": "..." }`
  - retorno: `{ user, accessToken, refreshToken }`
- `POST /api/v1/auth/login`
  - body: `{ "email": "...", "password": "..." }`
  - retorno: `{ user, accessToken, refreshToken }`
- `POST /api/v1/auth/refresh`
  - body: `{ "refreshToken": "..." }`
  - retorno: `{ accessToken, refreshToken }`
- `POST /api/v1/auth/logout`
  - header: `Authorization: Bearer <accessToken>`
  - body opcional: `{ "refreshToken": "..." }`
- `GET /api/v1/auth/me`
  - header: `Authorization: Bearer <accessToken>`
  - retorno: `{ id, email, name, role, createdAt }`

## Regras importantes para Unity

- Salve `accessToken` e `refreshToken` localmente.
- Sempre envie `Authorization: Bearer <accessToken>` nas rotas protegidas.
- Se receber `401`, tente **uma vez** o `refresh`:
  - se der certo, troque os 2 tokens e repita a request original.
  - se falhar, limpe sessao e volte para tela de login.
- `register` sempre cria usuario com role `PLAYER`.
- `sub` do JWT representa o `user.id` (id da plataforma).

## Fluxo recomendado de telas

1. **LoginScreen**
   - email + password
   - chama `POST /auth/login`
2. **RegisterScreen**
   - name + email + password
   - chama `POST /auth/register`
3. **Bootstrap/AuthGate**
   - se existir token salvo, chama endpoint protegido ou `GET /auth/me`
   - se `401`, tenta refresh e repete
4. **Logout**
   - chama `POST /auth/logout`
   - limpa tokens locais
   - volta para login

## Estrutura minima sugerida (Unity)

- `AuthApiClient`
  - metodos: `Login`, `Register`, `Refresh`, `Logout`, `Me`
- `TokenStore`
  - `GetAccessToken`, `GetRefreshToken`, `SaveTokens`, `Clear`
- `AuthService`
  - orquestra login/logout/refresh
- `AuthHttp`
  - wrapper para requests autenticadas com retry unico no refresh

## Modelos C# (exemplo)

```csharp
[Serializable]
public class AuthUserDto
{
    public string id;
    public string email;
    public string name;
    public string role;
}

[Serializable]
public class LoginResponseDto
{
    public AuthUserDto user;
    public string accessToken;
    public string refreshToken;
}

[Serializable]
public class RefreshResponseDto
{
    public string accessToken;
    public string refreshToken;
}
```

## Exemplo de login (pseudo-fluxo)

```csharp
var result = await authApi.Login(email, password);
tokenStore.SaveTokens(result.accessToken, result.refreshToken);
currentUser = result.user;
```

## Exemplo de request autenticada com refresh

```csharp
var response = await api.CallWithBearer(accessToken);
if (response.StatusCode == 401)
{
    var refreshed = await authApi.Refresh(tokenStore.GetRefreshToken());
    tokenStore.SaveTokens(refreshed.accessToken, refreshed.refreshToken);
    response = await api.CallWithBearer(refreshed.accessToken);
}
```

## Erros esperados na UI

- Login invalido: mensagem generica (`Invalid credentials`).
- Refresh invalido/expirado: forcar relogin.
- Erro de rede: mostrar mensagem e opcao de tentar novamente.

## Checklist rapido

- [ ] Login retorna tokens e entra no app
- [ ] App reabre com sessao valida (tokens salvos)
- [ ] Access expirado faz refresh automatico
- [ ] Refresh expirado volta para login
- [ ] Logout limpa sessao local e remota

---

Referencia de contrato da API: `docs/AUTH-FLOW.md`  
Fluxo de gameplay (sessoes, progresso, matches): `docs/UNITY-GAMEPLAY-SESSIONS.md`
