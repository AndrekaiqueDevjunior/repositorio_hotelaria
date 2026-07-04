import os
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

from app.core import security

AUTH_ROUTES_PATH = Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "auth_routes.py"
AUTH_SPEC = importlib.util.spec_from_file_location("auth_routes_under_test", AUTH_ROUTES_PATH)
auth_routes = importlib.util.module_from_spec(AUTH_SPEC)
AUTH_SPEC.loader.exec_module(auth_routes)


class FakeCache:
    def __init__(self, initial=None):
        self.store = dict(initial or {})
        self.deleted = []
        self.set_calls = []

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ttl=300):
        self.store[key] = value
        self.set_calls.append({"key": key, "value": value, "ttl": ttl})

    async def delete(self, key):
        self.deleted.append(key)
        self.store.pop(key, None)

    async def incr(self, key):
        self.store[key] = int(self.store.get(key, 0)) + 1
        return self.store[key]

    async def expire(self, key, seconds):
        self.store[f"{key}:ttl"] = seconds

    async def ttl(self, key):
        return self.store.get(f"{key}:ttl", 900)


def make_request(cookie_header: str = "", authorization: str = "") -> Request:
    headers = [(b"host", b"localhost")]
    if cookie_header:
        headers.append((b"cookie", cookie_header.encode("latin-1")))
    if authorization:
        headers.append((b"authorization", authorization.encode("latin-1")))

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/test",
            "scheme": "http",
            "headers": headers,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }
    )


def test_validate_new_password_rejects_common_and_personal_values():
    funcionario = SimpleNamespace(email="ana.silva@example.com", nome="Ana Silva")

    with pytest.raises(HTTPException):
        auth_routes._validate_new_password("hotel123", funcionario)

    with pytest.raises(HTTPException):
        auth_routes._validate_new_password("AnaSilva2026!", funcionario)


def test_validate_new_password_accepts_strong_password_and_passphrase():
    funcionario = SimpleNamespace(email="ana.silva@example.com", nome="Ana Silva")

    auth_routes._validate_new_password("ReservaForte2026!", funcionario)
    auth_routes._validate_new_password("frase longa para acesso seguro", funcionario)


def test_access_token_prefers_bearer_and_falls_back_to_cookie():
    bearer_request = make_request(
        cookie_header=f"{auth_routes.settings.COOKIE_NAME}=cookie-token",
        authorization="Bearer header-token",
    )
    cookie_request = make_request(cookie_header=f"{auth_routes.settings.COOKIE_NAME}=cookie-token")

    assert auth_routes._get_access_token_from_request(bearer_request) == "header-token"
    assert auth_routes._get_access_token_from_request(cookie_request) == "cookie-token"


@pytest.mark.asyncio
async def test_blacklist_access_token_stores_jti_until_expiration(monkeypatch):
    fake_cache = FakeCache()
    monkeypatch.setattr(auth_routes, "cache", fake_cache)

    token = security.create_access_token({"sub": "1", "email": "admin@example.com", "perfil": "ADMIN"})
    await auth_routes._blacklist_access_token(token)

    assert fake_cache.set_calls
    assert fake_cache.set_calls[0]["key"].startswith("blacklist:jti:")
    assert fake_cache.set_calls[0]["ttl"] > 0


@pytest.mark.asyncio
async def test_refresh_rotates_refresh_token_and_keeps_tokens_out_of_body(monkeypatch):
    fake_cache = FakeCache({"refresh_token:10": "old-refresh"})
    monkeypatch.setattr(auth_routes, "cache", fake_cache)
    monkeypatch.setattr(
        auth_routes,
        "verify_token",
        lambda token, token_type="refresh": {
            "sub": "10",
            "email": "admin@example.com",
            "perfil": "ADMIN",
        },
    )
    monkeypatch.setattr(auth_routes, "create_access_token", lambda data: "new-access")
    monkeypatch.setattr(auth_routes, "create_refresh_token", lambda data: "new-refresh")

    request = make_request(cookie_header=f"{auth_routes.settings.COOKIE_NAME}_refresh=old-refresh")
    response = Response()

    result = await auth_routes.refresh_access_token(request=request, response=response)

    assert result == {
        "success": True,
        "token_type": "cookie",
        "expires_in": auth_routes.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    assert fake_cache.store["refresh_token:10"] == "new-refresh"
    assert "access_token" not in result
    assert "refresh_token" not in result
    set_cookie_headers = [value.decode("latin-1") for key, value in response.raw_headers if key == b"set-cookie"]
    assert any("new-access" in header for header in set_cookie_headers)
    assert any("new-refresh" in header for header in set_cookie_headers)


@pytest.mark.asyncio
async def test_refresh_reuse_revokes_stored_refresh_token(monkeypatch):
    fake_cache = FakeCache({"refresh_token:10": "newer-refresh"})
    monkeypatch.setattr(auth_routes, "cache", fake_cache)
    monkeypatch.setattr(
        auth_routes,
        "verify_token",
        lambda token, token_type="refresh": {
            "sub": "10",
            "email": "admin@example.com",
            "perfil": "ADMIN",
        },
    )

    request = make_request(cookie_header=f"{auth_routes.settings.COOKIE_NAME}_refresh=old-refresh")
    response = Response()

    with pytest.raises(HTTPException) as exc:
        await auth_routes.refresh_access_token(request=request, response=response)

    assert exc.value.status_code == 401
    assert "refresh_token:10" in fake_cache.deleted
