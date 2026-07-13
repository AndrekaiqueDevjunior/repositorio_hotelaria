import os

from fastapi import Request

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://test:test@localhost:5432/test",
)
os.environ.setdefault("CIELO_MERCHANT_ID", "waf-test-merchant")
os.environ.setdefault("CIELO_MERCHANT_KEY", "waf-test-key")


from app.api.v1.customer_auth_routes import _request_meta
from app.middleware.rate_limit import get_client_identifier
from app.utils.validation_errors import sanitize_validation_errors


def _request(*, client_ip="203.0.113.10", headers=None):
    raw_headers = [
        (name.lower().encode("ascii"), value.encode("utf-8"))
        for name, value in (headers or {}).items()
    ]
    return Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": "https",
            "path": "/api/v1/login",
            "raw_path": b"/api/v1/login",
            "query_string": b"",
            "headers": raw_headers,
            "client": (client_ip, 12345),
            "server": ("hotelrealcabofrio.com", 443),
        }
    )


def test_rate_limit_ignores_spoofed_x_forwarded_for():
    request = _request(headers={"X-Forwarded-For": "198.51.100.77"})

    assert get_client_identifier(request) == "203.0.113.10"


def test_customer_auth_metadata_uses_normalized_client_ip():
    request = _request(
        headers={
            "X-Forwarded-For": "198.51.100.77",
            "User-Agent": "browser-test",
        }
    )

    assert _request_meta(request) == ("203.0.113.10", "browser-test")


def test_validation_error_sanitizer_removes_sensitive_input_and_context():
    secret = "Senha-Super-Secreta-123"
    sanitized = sanitize_validation_errors(
        [
            {
                "type": "string_too_short",
                "loc": ("body", "password"),
                "msg": "String should have at least 12 characters",
                "input": secret,
                "ctx": {"min_length": 12},
            }
        ]
    )

    assert secret not in repr(sanitized)
    assert "input" not in sanitized[0]
    assert "ctx" not in sanitized[0]
    assert sanitized[0]["loc"] == ("body", "password")
