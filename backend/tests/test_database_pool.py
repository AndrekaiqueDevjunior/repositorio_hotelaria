import asyncio
import os
import sys
import types
from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

import pytest


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://test:test@localhost:5432/test",
)

from app.core import database

try:
    from app.tasks import jornada_tasks
except ModuleNotFoundError as exc:
    if exc.name != "celery":
        raise

    class _CeleryStub:
        def task(self, *args, **kwargs):
            return lambda fn: fn

    celery_stub = types.ModuleType("app.core.celery_app")
    celery_stub.celery_app = _CeleryStub()
    sys.modules["app.core.celery_app"] = celery_stub
    from app.tasks import jornada_tasks
    sys.modules.pop("app.core.celery_app", None)


POOL_ENV_VARS = (
    "PRISMA_CONNECTION_LIMIT",
    "PRISMA_POOL_TIMEOUT_SECONDS",
    "PRISMA_CONNECT_TIMEOUT_SECONDS",
    "PRISMA_DISCONNECT_TIMEOUT_SECONDS",
    "PRISMA_APPLICATION_NAME",
)


def _clear_pool_env(monkeypatch):
    for name in POOL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_configure_prisma_url_applies_safe_defaults(monkeypatch):
    _clear_pool_env(monkeypatch)

    configured = database.configure_prisma_url(
        "postgresql://user:pass@postgres:5432/hotel?schema=public",
        application_name="hotel_backend",
    )
    query = parse_qs(urlsplit(configured).query)

    assert query == {
        "schema": ["public"],
        "connection_limit": ["5"],
        "pool_timeout": ["10"],
        "connect_timeout": ["5"],
        "application_name": ["hotel_backend"],
    }


def test_configure_prisma_url_respects_explicit_settings(monkeypatch):
    _clear_pool_env(monkeypatch)
    original = (
        "postgresql://user:pass@postgres:5432/hotel"
        "?connection_limit=4&pool_timeout=3&connect_timeout=4"
        "&application_name=custom"
    )

    assert database.configure_prisma_url(original) == original


@pytest.mark.parametrize(
    ("unsafe_query", "expected"),
    (
        ("connection_limit=99", "5"),
        ("connection_limit=", "5"),
        ("connection_limit=0", "5"),
        ("pool_timeout=-1", "10"),
        ("connect_timeout=invalid", "5"),
    ),
)
def test_configure_prisma_url_replaces_unsafe_values(
    monkeypatch,
    unsafe_query,
    expected,
):
    _clear_pool_env(monkeypatch)
    configured = database.configure_prisma_url(
        f"postgresql://user:pass@postgres:5432/hotel?{unsafe_query}"
    )
    key = unsafe_query.split("=", 1)[0]

    assert parse_qs(urlsplit(configured).query)[key] == [expected]


def test_invalid_timeout_environment_falls_back_to_safe_default(monkeypatch):
    _clear_pool_env(monkeypatch)
    monkeypatch.setenv("PRISMA_POOL_TIMEOUT_SECONDS", "0")
    monkeypatch.setenv("PRISMA_CONNECT_TIMEOUT_SECONDS", "-2")

    configured = database.configure_prisma_url(
        "postgresql://user:pass@postgres:5432/hotel"
    )
    query = parse_qs(urlsplit(configured).query)

    assert query["pool_timeout"] == ["10"]
    assert query["connect_timeout"] == ["5"]


def test_configure_prisma_url_uses_environment_and_skips_accelerate(monkeypatch):
    _clear_pool_env(monkeypatch)
    monkeypatch.setenv("PRISMA_CONNECTION_LIMIT", "2")
    monkeypatch.setenv("PRISMA_APPLICATION_NAME", "hotel_celery")

    configured = database.configure_prisma_url(
        "postgresql://user:pass@postgres:5432/hotel"
    )
    query = parse_qs(urlsplit(configured).query)

    assert query["connection_limit"] == ["2"]
    assert query["application_name"] == ["hotel_celery"]

    accelerate = "prisma://accelerate.prisma-data.net/?api_key=secret"
    assert database.configure_prisma_url(accelerate) == accelerate


def test_create_prisma_client_routes_through_central_pool_config(monkeypatch):
    _clear_pool_env(monkeypatch)
    monkeypatch.setenv("PRISMA_CONNECTION_LIMIT", "2")
    captured = {}

    def fake_prisma(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(database, "ManagedPrismaClient", fake_prisma)

    database.create_prisma_client(
        "postgresql://user:pass@postgres:5432/hotel",
    )
    query = parse_qs(urlsplit(captured["datasource"]["url"]).query)

    assert query["connection_limit"] == ["2"]
    assert query["pool_timeout"] == ["10"]
    assert query["connect_timeout"] == ["5"]
    assert captured["connect_timeout"] == timedelta(seconds=5)
    assert captured["engine_close_timeout"] == timedelta(seconds=5)


def test_managed_client_bounds_internal_engine_close(monkeypatch):
    close_timeouts = []

    class FakeEngine:
        def close(self, *, timeout=None):
            close_timeouts.append(timeout)

    monkeypatch.setattr(
        database.Prisma,
        "_create_engine",
        lambda self, *args, **kwargs: FakeEngine(),
    )
    client = database.ManagedPrismaClient(
        datasource={"url": "postgresql://user:pass@localhost:5432/hotel"},
        connect_timeout=timedelta(seconds=2),
        engine_close_timeout=timedelta(seconds=2),
    )
    engine = client._create_engine()

    engine.close()
    engine.close(timeout=timedelta(seconds=3))

    assert close_timeouts == [timedelta(seconds=2), timedelta(seconds=3)]


def test_mask_database_url_removes_password_and_query_secrets():
    postgres = database.mask_database_url(
        "postgresql://user:password@postgres:5432/hotel?connection_limit=5"
    )
    accelerate = database.mask_database_url(
        "prisma://accelerate.prisma-data.net/?api_key=super-secret"
    )

    assert postgres == "postgresql://user:****@postgres:5432/hotel"
    assert "password" not in postgres
    assert "super-secret" not in accelerate
    assert "api_key" not in accelerate


@pytest.mark.asyncio
async def test_disconnect_prisma_client_uses_finite_timeout(monkeypatch):
    _clear_pool_env(monkeypatch)
    monkeypatch.setenv("PRISMA_DISCONNECT_TIMEOUT_SECONDS", "3")
    received = {}

    class FakeClient:
        async def disconnect(self, timeout=None):
            received["timeout"] = timeout

    await database.disconnect_prisma_client(FakeClient())

    assert received["timeout"] == timedelta(seconds=3)


@pytest.mark.asyncio
async def test_disconnect_prisma_client_has_outer_wall_clock_timeout(monkeypatch):
    monkeypatch.setattr(database, "_get_int_env", lambda *args, **kwargs: 0.01)

    class HangingClient:
        async def disconnect(self, timeout=None):
            await asyncio.Event().wait()

    with pytest.raises(asyncio.TimeoutError):
        await database.disconnect_prisma_client(HangingClient())


def test_celery_client_uses_own_limit_outside_compose(monkeypatch):
    _clear_pool_env(monkeypatch)
    monkeypatch.delenv("CELERY_PRISMA_CONNECTION_LIMIT", raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:pass@postgres:5432/hotel?connection_limit=5",
    )
    captured = []

    def fake_create(database_url, **kwargs):
        captured.append({"database_url": database_url, **kwargs})
        return object()

    monkeypatch.setattr(database, "create_prisma_client", fake_create)

    database.create_celery_prisma_client()
    monkeypatch.setenv("CELERY_PRISMA_CONNECTION_LIMIT", "2")
    database.create_celery_prisma_client()

    assert captured[0]["connection_limit"] == 1
    assert captured[1]["connection_limit"] == 2
    assert captured[0]["application_name"] == "hotel_celery"


@pytest.mark.asyncio
async def test_celery_task_cleans_up_when_connect_fails(monkeypatch):
    events = []

    class FakeClient:
        async def connect(self):
            events.append("connect")
            raise RuntimeError("database unavailable")

    fake_client = FakeClient()

    async def fake_disconnect(client):
        assert client is fake_client
        events.append("disconnect")

    monkeypatch.setattr(
        database,
        "create_celery_prisma_client",
        lambda: fake_client,
    )
    monkeypatch.setattr(database, "disconnect_prisma_client", fake_disconnect)

    async def should_not_run(_client):
        events.append("callback")

    with pytest.raises(RuntimeError, match="database unavailable"):
        await jornada_tasks._run_with_db(should_not_run)

    assert events == ["connect", "disconnect"]


@pytest.mark.asyncio
async def test_celery_task_preserves_primary_error_when_cleanup_fails(monkeypatch):
    class FakeClient:
        async def connect(self):
            raise RuntimeError("primary failure")

    async def failing_disconnect(_client):
        raise RuntimeError("cleanup failure")

    monkeypatch.setattr(
        database,
        "create_celery_prisma_client",
        lambda: FakeClient(),
    )
    monkeypatch.setattr(database, "disconnect_prisma_client", failing_disconnect)

    with pytest.raises(RuntimeError, match="primary failure"):
        await jornada_tasks._run_with_db(lambda _client: None)


@pytest.mark.asyncio
async def test_celery_task_does_not_retry_successful_work_on_cleanup_error(monkeypatch):
    events = []

    class FakeClient:
        async def connect(self):
            events.append("connect")

    async def successful_callback(_client):
        events.append("callback")
        return "done"

    async def failing_disconnect(_client):
        events.append("disconnect")
        raise RuntimeError("cleanup failure")

    monkeypatch.setattr(
        database,
        "create_celery_prisma_client",
        lambda: FakeClient(),
    )
    monkeypatch.setattr(database, "disconnect_prisma_client", failing_disconnect)

    assert await jornada_tasks._run_with_db(successful_callback) == "done"
    assert events == ["connect", "callback", "disconnect"]


@pytest.mark.asyncio
async def test_get_db_connected_serializes_reconnect(monkeypatch):
    class FakeDatabase:
        connected = False
        connect_calls = 0

        def is_connected(self):
            return self.connected

        async def connect(self):
            self.connect_calls += 1
            await asyncio.sleep(0)
            self.connected = True

    fake_db = FakeDatabase()
    monkeypatch.setattr(database, "db", fake_db)
    monkeypatch.setattr(database, "_db_connect_lock", asyncio.Lock())

    first, second = await asyncio.gather(
        database.get_db_connected(),
        database.get_db_connected(),
    )

    assert first is fake_db
    assert second is fake_db
    assert fake_db.connect_calls == 1
