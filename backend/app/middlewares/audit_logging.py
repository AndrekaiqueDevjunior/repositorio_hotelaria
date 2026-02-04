import time
from fastapi import Request


async def audit_logging(request: Request, call_next):
    start = time.time()
    client_ip = request.client.host
    method = request.method
    path = request.url.path
    ua = request.headers.get("user-agent", "Unknown")[:80]

    print(f"[SECURITY] {method} {path} from {client_ip} - {ua}")

    response = await call_next(request)
    elapsed = time.time() - start

    if response.status_code >= 400:
        print(f"[SECURITY ALERT] {method} {path} - {response.status_code} - IP {client_ip}")

    if elapsed > 5.0:
        print(f"[SECURITY] Slow request: {method} {path} - {elapsed:.2f}s")

    return response