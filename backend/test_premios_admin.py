#!/usr/bin/env python3
"""Teste rapido dos endpoints de premios (CRUD)."""
import requests


def main():
    base_url = "http://backend:8000"

    login_data = {"email": "admin@hotelreal.com.br", "password": "admin123"}
    login_resp = requests.post(f"{base_url}/api/v1/login", json=login_data)
    refresh_token = login_resp.json().get("refresh_token")
    refresh_resp = requests.post(f"{base_url}/api/v1/refresh", json={"refresh_token": refresh_token})
    token = refresh_resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    print("LISTAR PREMIOS")
    list_resp = requests.get(f"{base_url}/api/v1/premios", headers=headers)
    print("Status:", list_resp.status_code)

    print("CRIAR PREMIO")
    create_payload = {
        "nome": "Premio Temporada Teste",
        "descricao": "Premio criado para teste do CRUD",
        "preco_em_pontos": 15,
        "preco_em_rp": 15,
        "categoria": "TESTE",
        "ativo": True
    }
    create_resp = requests.post(f"{base_url}/api/v1/premios", json=create_payload, headers=headers)
    print("Status:", create_resp.status_code)
    premio = create_resp.json()
    premio_id = premio.get("id")
    print("Premio ID:", premio_id)

    print("ATUALIZAR PRECO")
    update_resp = requests.put(
        f"{base_url}/api/v1/premios/{premio_id}",
        json={"preco_em_pontos": 18, "preco_em_rp": 18},
        headers=headers
    )
    print("Status:", update_resp.status_code)

    print("DESATIVAR PREMIO")
    delete_resp = requests.delete(f"{base_url}/api/v1/premios/{premio_id}", headers=headers)
    print("Status:", delete_resp.status_code)


if __name__ == "__main__":
    main()
