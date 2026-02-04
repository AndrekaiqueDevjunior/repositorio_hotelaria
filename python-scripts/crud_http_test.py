import datetime as dt
import json
import uuid

import requests


BASE = "http://127.0.0.1:8080/api/v1"
ADMIN = {"email": "admin@hotelreal.com.br", "password": "admin123"}


def _short(body) -> str:
    if isinstance(body, (dict, list)):
        return json.dumps(body, ensure_ascii=False)[:300]
    return str(body)[:300]


def _req(session: requests.Session, method: str, path: str, **kwargs):
    r = session.request(method, BASE + path, timeout=30, **kwargs)
    ct = r.headers.get("content-type", "")
    if "application/json" in ct.lower():
        try:
            return r.status_code, r.json()
        except Exception:
            return r.status_code, r.text
    return r.status_code, r.text


def main() -> int:
    s = requests.Session()

    st, body = _req(s, "POST", "/login", json=ADMIN)
    print("login", st, _short(body))
    if st != 200:
        return 1

    # =====================
    # QUARTOS
    # =====================
    quarto_num = f"T{uuid.uuid4().hex[:3]}"

    st, body = _req(
        s,
        "POST",
        "/quartos",
        json={"numero": quarto_num, "tipo_suite": "MASTER", "status": "LIVRE"},
    )
    print("create quarto", st, _short(body))
    if st not in (200, 201):
        return 2

    st, body = _req(s, "GET", "/quartos", params={"search": quarto_num})
    print("list quartos(search)", st, _short(body))

    st, body = _req(s, "PUT", f"/quartos/{quarto_num}", json={"status": "MANUTENCAO"})
    print("update quarto", st, _short(body))

    st, body = _req(s, "DELETE", f"/quartos/{quarto_num}")
    print("delete quarto", st, _short(body))

    # =====================
    # FUNCIONARIOS
    # =====================
    func_email = f"teste.{uuid.uuid4().hex[:6]}@hotelreal.com.br"

    st, body = _req(
        s,
        "POST",
        "/funcionarios",
        json={
            "nome": "Teste CRUD",
            "email": func_email,
            "perfil": "FUNCIONARIO",
            "status": "ATIVO",
            "senha": "123456",
        },
    )
    print("create func", st, _short(body))
    if st not in (200, 201):
        return 3

    func_id = body.get("id") if isinstance(body, dict) else None
    if not func_id:
        print("func_id ausente")
        return 31

    st, body = _req(s, "GET", f"/funcionarios/{func_id}")
    print("get func", st, _short(body))

    st, body = _req(s, "PUT", f"/funcionarios/{func_id}", json={"nome": "Teste CRUD 2", "status": "INATIVO"})
    print("update func", st, _short(body))

    st, body = _req(s, "DELETE", f"/funcionarios/{func_id}")
    print("delete func", st, _short(body))

    # =====================
    # RESERVAS
    # =====================
    st, body = _req(s, "GET", "/clientes")
    print("list clientes", st)
    if st != 200:
        print(_short(body))
        return 4

    clientes = body
    if isinstance(clientes, dict) and "clientes" in clientes:
        clientes = clientes["clientes"]
    if not isinstance(clientes, list) or not clientes:
        print("SEM CLIENTES para testar reserva")
        return 5

    cliente_id = clientes[0]["id"]

    st, body = _req(s, "GET", "/quartos", params={"limit": 10, "offset": 0})
    print("list quartos", st)
    if st != 200:
        print(_short(body))
        return 6

    quartos_resp = body
    if isinstance(quartos_resp, dict) and "quartos" in quartos_resp:
        quartos = quartos_resp["quartos"]
    else:
        quartos = quartos_resp

    if not isinstance(quartos, list) or not quartos:
        print("SEM QUARTOS para testar reserva")
        return 7

    quarto_numero = quartos[0]["numero"]
    tipo_suite = quartos[0].get("tipo_suite") or quartos[0].get("tipoSuite") or "MASTER"

    checkin = (dt.datetime.utcnow() + dt.timedelta(days=10)).replace(hour=0, minute=0, second=0, microsecond=0)
    checkout = checkin + dt.timedelta(days=2)

    payload = {
        "cliente_id": cliente_id,
        "quarto_numero": quarto_numero,
        "tipo_suite": tipo_suite,
        "checkin_previsto": checkin.isoformat() + "Z",
        "checkout_previsto": checkout.isoformat() + "Z",
        "valor_diaria": 100.0,
        "num_diarias": 2,
    }

    idem = str(uuid.uuid4())
    st, body = _req(s, "POST", "/reservas", json=payload, headers={"Idempotency-Key": idem})
    print("create reserva", st, _short(body))
    if st != 201:
        return 8

    reserva_id = body.get("data", {}).get("id") if isinstance(body, dict) else None
    if not reserva_id:
        print("reserva_id ausente")
        return 81

    st, body = _req(s, "GET", f"/reservas/{reserva_id}")
    print("get reserva", st, _short(body))

    st, body = _req(s, "PATCH", f"/reservas/{reserva_id}", json={"status": "CONFIRMADO"})
    print("confirm reserva", st, _short(body))

    st, body = _req(s, "PATCH", f"/reservas/{reserva_id}", json={"status": "CANCELADO"})
    print("cancel reserva", st, _short(body))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
