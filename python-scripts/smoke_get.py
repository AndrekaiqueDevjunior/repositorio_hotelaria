import json
import sys
from typing import Any, Tuple

import requests


BASE = "http://127.0.0.1:8080/api/v1"
ADMIN = {"email": "admin@hotelreal.com.br", "password": "admin123"}
ENDPOINTS = [
    "/me",
    "/clientes",
    "/quartos",
    "/reservas",
    "/funcionarios",
    "/premios",
    "/tarifas",
    "/pontos",
    "/antifraude",
]


def _format_body(body: Any) -> str:
    if isinstance(body, (dict, list)):
        try:
            return json.dumps(body, ensure_ascii=False)[:300]
        except Exception:
            return str(body)[:300]
    return str(body)[:300]


def call(session: requests.Session, method: str, path: str, **kwargs) -> Tuple[int, Any]:
    r = session.request(method, BASE + path, timeout=20, **kwargs)
    ct = r.headers.get("content-type", "")
    if "application/json" in ct.lower():
        try:
            return r.status_code, r.json()
        except Exception:
            return r.status_code, r.text
    return r.status_code, r.text


def main() -> int:
    session = requests.Session()
    results = []

    st, body = call(session, "POST", "/login", json=ADMIN)
    results.append(("POST /login", st, body))

    if st == 200:
        for ep in ENDPOINTS:
            st2, body2 = call(session, "GET", ep)
            results.append((f"GET {ep}", st2, body2))

    ok = [x for x in results if x[1] == 200]
    fail = [x for x in results if x[1] != 200]

    print(f"OK {len(ok)}")
    for name, status, _ in ok:
        print(f"[OK] {name} ({status})")

    print(f"FAIL {len(fail)}")
    for name, status, b in fail:
        print(f"[FAIL] {name} ({status}) -> {_format_body(b)}")

    return 0 if len(fail) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
