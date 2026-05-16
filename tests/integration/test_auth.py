"""Auth integration tests."""

from httpx import AsyncClient

_VALID_PASSWORD = "ValidPass1"


async def test_register_login_me(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "player1@example.com",
            "password": _VALID_PASSWORD,
            "name": "Player One",
        },
    )
    assert reg.status_code == 201
    data = reg.json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert data["user"]["email"] == "player1@example.com"
    assert data["user"]["role"] == "PLAYER"
    assert data["user"]["emailVerified"] is True
    assert "totpEnabled" in data["user"]

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {data['accessToken']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "player1@example.com"


async def test_register_duplicate_email_409(client: AsyncClient) -> None:
    body = {
        "email": "dup@example.com",
        "password": _VALID_PASSWORD,
        "name": "A",
    }
    assert (await client.post("/api/v1/auth/register", json=body)).status_code == 201
    dup = await client.post("/api/v1/auth/register", json=body)
    assert dup.status_code == 409
    err = dup.json()
    assert err["success"] is False
    assert err["code"] == "EMAIL_IN_USE"


async def test_login_wrong_password_401(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": _VALID_PASSWORD,
            "name": "L",
        },
    )
    bad = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "WrongPass1"},
    )
    assert bad.status_code == 401
    assert bad.json()["success"] is False


async def test_refresh_rotates_old_token_invalid(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rot@example.com",
            "password": _VALID_PASSWORD,
            "name": "R",
        },
    )
    rt1 = reg.json()["refreshToken"]
    ref1 = await client.post("/api/v1/auth/refresh", json={"refreshToken": rt1})
    assert ref1.status_code == 200
    rt2 = ref1.json()["refreshToken"]
    old_again = await client.post("/api/v1/auth/refresh", json={"refreshToken": rt1})
    assert old_again.status_code == 401
    new_ok = await client.post("/api/v1/auth/refresh", json={"refreshToken": rt2})
    assert new_ok.status_code == 200


async def test_change_password_any_role_clears_first_access(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "chpwd@example.com",
            "password": _VALID_PASSWORD,
            "name": "Change Pwd",
        },
    )
    assert reg.status_code == 201
    assert reg.json()["user"]["isFirstAccess"] is True
    access = reg.json()["accessToken"]

    new_password = "NewValid1Pass"
    ch = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {access}"},
        json={"password": new_password},
    )
    assert ch.status_code == 200
    assert ch.json()["user"]["isFirstAccess"] is False

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert me.status_code == 200
    assert me.json()["isFirstAccess"] is False

    login_new = await client.post(
        "/api/v1/auth/login",
        json={"email": "chpwd@example.com", "password": new_password},
    )
    assert login_new.status_code == 200


async def test_logout_partial_revokes_one_session(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "multi@example.com",
            "password": _VALID_PASSWORD,
            "name": "M",
        },
    )
    access_a = reg.json()["accessToken"]
    rt_a = reg.json()["refreshToken"]

    login_b = await client.post(
        "/api/v1/auth/login",
        json={"email": "multi@example.com", "password": _VALID_PASSWORD},
    )
    rt_b = login_b.json()["refreshToken"]
    access_b = login_b.json()["accessToken"]

    lo = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_a}"},
        json={"refreshToken": rt_a},
    )
    assert lo.status_code == 204

    assert (
        await client.post("/api/v1/auth/refresh", json={"refreshToken": rt_a})
    ).status_code == 401
    assert (
        await client.post("/api/v1/auth/refresh", json={"refreshToken": rt_b})
    ).status_code == 200

    lo_all = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_b}"},
        json={},
    )
    assert lo_all.status_code == 204
    assert (
        await client.post("/api/v1/auth/refresh", json={"refreshToken": rt_b})
    ).status_code == 401
