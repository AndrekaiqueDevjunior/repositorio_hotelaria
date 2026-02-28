import json
import httpx
from datetime import datetime, timedelta, timezone

BASE = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@hotelreal.com.br"
ADMIN_PASSWORD = "rKKv0FibuygVioryw0GJD87C2n"

PNG_1X1_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/axpF8kAAAAASUVORK5CYII="


def _pp(title: str, obj) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    if isinstance(obj, (dict, list)):
        print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))
    else:
        print(obj)


def main() -> None:
    with httpx.Client(timeout=60.0) as client:
        # 1) login -> refresh
        login = client.post(
            f"{BASE}/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        _pp("LOGIN", {"status": login.status_code, "body": login.json() if login.headers.get('content-type','').startswith('application/json') else login.text})
        login.raise_for_status()
        refresh_token = login.json().get("refresh_token")
        if not refresh_token:
            raise RuntimeError("login não retornou refresh_token")

        refresh = client.post(f"{BASE}/refresh", json={"refresh_token": refresh_token})
        _pp("REFRESH", {"status": refresh.status_code, "body": refresh.json()})
        refresh.raise_for_status()
        access_token = refresh.json().get("access_token")
        if not access_token:
            raise RuntimeError("refresh não retornou access_token")

        headers = {"Authorization": f"Bearer {access_token}"}

        me = client.get(f"{BASE}/me", headers=headers)
        _pp("ME", {"status": me.status_code, "body": me.json()})
        me.raise_for_status()
        admin_id = me.json().get("id")

        # 2) create cliente
        now = datetime.now(timezone.utc)
        suffix = now.strftime("%Y%m%d%H%M%S")
        cliente_body = {
            "nome_completo": f"Cliente E2E {suffix}",
            "documento": f"CPF{suffix}",
            "telefone": "21999999999",
            "email": f"cliente{suffix}@teste.local",
        }
        cliente = client.post(f"{BASE}/clientes", json=cliente_body, headers=headers)
        _pp("CRIAR CLIENTE", {"status": cliente.status_code, "body": cliente.json() if cliente.content else None})
        cliente.raise_for_status()
        cliente_id = cliente.json().get("id")

        # 3) create funcionario
        func_body = {
            "nome": f"Func E2E {suffix}",
            "email": f"func{suffix}@teste.local",
            "perfil": "RECEPCAO",
            "status": "ATIVO",
            "senha": "123456",
        }
        func = client.post(f"{BASE}/funcionarios", json=func_body, headers=headers)
        _pp("CRIAR FUNCIONARIO", {"status": func.status_code, "body": func.json() if func.content else None})
        func.raise_for_status()
        funcionario_id = func.json().get("id")

        # 4) pick quarto livre
        quartos = client.get(f"{BASE}/quartos", params={"status": "LIVRE", "limit": 5}, headers=headers)
        _pp("LISTAR QUARTOS LIVRE", {"status": quartos.status_code, "body": quartos.json() if quartos.content else None})
        quartos.raise_for_status()
        quartos_list = quartos.json().get("quartos") or []
        if not quartos_list:
            raise RuntimeError("Nenhum quarto LIVRE encontrado")
        quarto = quartos_list[0]
        quarto_numero = quarto.get("numero")
        tipo_suite = quarto.get("tipo_suite")
        if not quarto_numero or not tipo_suite:
            raise RuntimeError(f"Resposta de quarto inesperada: {quarto}")

        # 5) criar reserva (datas futuras)
        checkin = (now + timedelta(days=10)).replace(hour=15, minute=0, second=0, microsecond=0)
        checkout = (now + timedelta(days=12)).replace(hour=12, minute=0, second=0, microsecond=0)
        reserva_body = {
            "cliente_id": int(cliente_id),
            "quarto_numero": str(quarto_numero),
            "tipo_suite": str(tipo_suite),
            "checkin_previsto": checkin.isoformat(),
            "checkout_previsto": checkout.isoformat(),
            "num_diarias": 2,
            # valor_diaria é opcional; backend usa tarifa cadastrada
        }
        reserva = client.post(f"{BASE}/reservas", json=reserva_body, headers=headers)
        _pp("CRIAR RESERVA", {"status": reserva.status_code, "body": reserva.json() if reserva.content else None})
        reserva.raise_for_status()
        reserva_data = reserva.json().get("data") or reserva.json().get("reserva") or reserva.json()
        reserva_id = reserva_data.get("id")

        # 6) upload comprovante balcão
        comp_body = {
            "arquivo_base64": PNG_1X1_BASE64,
            "nome_arquivo": f"comprovante_{suffix}.png",
            "metodo_pagamento": "DINHEIRO",
            "observacao": "Pagamento balcão E2E",
        }
        comp = client.post(f"{BASE}/reservas/{reserva_id}/comprovante", json=comp_body, headers=headers)
        _pp("UPLOAD COMPROVANTE", {"status": comp.status_code, "body": comp.json() if comp.content else None})
        comp.raise_for_status()
        pagamento_id = comp.json().get("pagamento_id")

        # 7) aprovar comprovante
        validar_body = {
            "pagamento_id": int(pagamento_id),
            "status": "APROVADO",
            "motivo": "E2E",
            "usuario_validador_id": int(admin_id),
            "observacoes_internas": "E2E",
        }
        validar = client.post(f"{BASE}/comprovantes/validar", json=validar_body, headers=headers)
        _pp("APROVAR COMPROVANTE", {"status": validar.status_code, "body": validar.json() if validar.content else None})
        validar.raise_for_status()

        # 8) status reserva
        r1 = client.get(f"{BASE}/reservas/{reserva_id}", headers=headers)
        _pp("RESERVA APOS APROVACAO", {"status": r1.status_code, "body": r1.json() if r1.content else None})
        r1.raise_for_status()

        # 9) realizar check-in
        checkin_body = {
            "hospede_titular_nome": f"Hospede E2E {suffix}",
            "hospede_titular_documento": f"DOC{suffix}",
            "hospede_titular_documento_tipo": "CPF",
            "num_hospedes_real": 2,
            "num_criancas": 0,
            "veiculo_placa": "ABC1D23",
            "observacoes_checkin": "E2E",
            "caucao_cobrada": 0,
            "caucao_forma_pagamento": "DINHEIRO",
            "pagamento_validado": True,
            "documentos_conferidos": True,
            "termos_aceitos": True,
            "assinatura_digital": None,
            "hospedes": [],
        }
        do_checkin = client.post(f"{BASE}/checkin/{reserva_id}/realizar", json=checkin_body, headers=headers)
        _pp("REALIZAR CHECKIN", {"status": do_checkin.status_code, "body": do_checkin.json() if do_checkin.content else None})
        do_checkin.raise_for_status()

        r2 = client.get(f"{BASE}/reservas/{reserva_id}", headers=headers)
        _pp("RESERVA APOS CHECKIN", {"status": r2.status_code, "body": r2.json() if r2.content else None})
        r2.raise_for_status()

        # 10) realizar checkout
        checkout_body = {
            "vistoria_ok": True,
            "danos_encontrados": None,
            "valor_danos": 0,
            "consumo_frigobar": 0,
            "servicos_extras": 0,
            "taxa_late_checkout": 0,
            "caucao_devolvida": 0,
            "caucao_retida": 0,
            "motivo_retencao": None,
            "avaliacao_hospede": 5,
            "comentario_hospede": "E2E",
            "forma_acerto": "DINHEIRO",
            "observacoes_checkout": "E2E",
            "consumos_adicionais": [],
        }
        do_checkout = client.post(f"{BASE}/checkin/{reserva_id}/checkout/realizar", json=checkout_body, headers=headers)
        _pp("REALIZAR CHECKOUT", {"status": do_checkout.status_code, "body": do_checkout.json() if do_checkout.content else None})
        do_checkout.raise_for_status()

        r3 = client.get(f"{BASE}/reservas/{reserva_id}", headers=headers)
        _pp("RESERVA APOS CHECKOUT", {"status": r3.status_code, "body": r3.json() if r3.content else None})
        r3.raise_for_status()

        print("\n✅ FLUXO E2E CONCLUÍDO")
        print(f"Cliente ID: {cliente_id}")
        print(f"Funcionario ID: {funcionario_id}")
        print(f"Reserva ID: {reserva_id}")
        print(f"Pagamento ID: {pagamento_id}")


if __name__ == "__main__":
    main()
