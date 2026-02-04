"""
Testes de Segurança - Sistema de Pontos
Validação de vulnerabilidades identificadas na auditoria
"""
import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime


class TestRaceConditions:
    """Testes de Race Condition"""
    
    @pytest.mark.asyncio
    async def test_race_condition_resgate_premio(self, async_client: AsyncClient, auth_headers):
        """
        VULNERABILIDADE CRÍTICA: Race Condition em Resgate de Prêmios
        
        Cenário:
        1. Cliente tem 100 pontos
        2. Prêmio custa 100 pontos
        3. Fazer 10 requisições simultâneas
        4. Apenas 1 deve ter sucesso
        """
        # Setup: Criar cliente com saldo conhecido
        cliente_id = 1
        premio_id = 1
        
        # Garantir saldo inicial
        await async_client.post(
            "/api/v1/pontos/ajustes",
            json={"cliente_id": cliente_id, "pontos": 100, "motivo": "Setup teste"},
            headers=auth_headers
        )
        
        # Ataque: Requisições simultâneas
        tasks = [
            async_client.post(
                "/api/v1/premios/resgatar",
                json={"cliente_id": cliente_id, "premio_id": premio_id},
                headers=auth_headers
            )
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Validação
        sucessos = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        
        assert sucessos <= 1, (
            f"🔴 VULNERABILIDADE CONFIRMADA: {sucessos} resgates simultâneos permitidos! "
            f"Deveria permitir apenas 1."
        )
        
        # Verificar saldo final
        saldo_response = await async_client.get(
            f"/api/v1/pontos/saldo/{cliente_id}",
            headers=auth_headers
        )
        saldo_final = saldo_response.json().get("saldo", 0)
        
        # Saldo não pode ficar negativo
        assert saldo_final >= 0, f"🔴 Saldo negativo detectado: {saldo_final}"
    
    @pytest.mark.asyncio
    async def test_race_condition_ajuste_pontos(self, async_client: AsyncClient, auth_headers):
        """
        VULNERABILIDADE CRÍTICA: Race Condition em Ajuste de Pontos
        
        Cenário:
        1. Saldo inicial: 50 pontos
        2. Fazer 10 ajustes simultâneos de +4 pontos
        3. Saldo final deve ser 50 + (10 * 4) = 90 pontos
        """
        cliente_id = 1
        
        # Setup: Zerar saldo
        saldo_response = await async_client.get(
            f"/api/v1/pontos/saldo/{cliente_id}",
            headers=auth_headers
        )
        saldo_inicial = saldo_response.json().get("saldo", 0)
        
        # Ataque: Ajustes simultâneos
        tasks = [
            async_client.post(
                "/api/v1/pontos/ajustes",
                json={"cliente_id": cliente_id, "pontos": 4, "motivo": f"Teste {i}"},
                headers=auth_headers
            )
            for i in range(10)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        sucessos = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        
        # Verificar saldo final
        saldo_response = await async_client.get(
            f"/api/v1/pontos/saldo/{cliente_id}",
            headers=auth_headers
        )
        saldo_final = saldo_response.json().get("saldo", 0)
        
        saldo_esperado = saldo_inicial + (sucessos * 4)
        
        assert saldo_final == saldo_esperado, (
            f"🔴 VULNERABILIDADE CONFIRMADA: Race condition detectada! "
            f"Esperado: {saldo_esperado}, Obtido: {saldo_final}, "
            f"Diferença: {saldo_esperado - saldo_final} pontos perdidos"
        )


class TestValidacaoValores:
    """Testes de Validação de Valores"""
    
    @pytest.mark.asyncio
    async def test_valores_negativos_extremos(self, async_client: AsyncClient, auth_headers):
        """
        VULNERABILIDADE ALTA: Aceita valores negativos extremos
        """
        cliente_id = 1
        
        test_cases = [
            (-999999, "Valor extremamente negativo"),
            (-10000, "Valor muito negativo"),
            (-100, "Valor negativo moderado"),
        ]
        
        for pontos, descricao in test_cases:
            response = await async_client.post(
                "/api/v1/pontos/ajustes",
                json={"cliente_id": cliente_id, "pontos": pontos, "motivo": descricao},
                headers=auth_headers
            )
            
            # Deve bloquear valores extremos
            assert response.status_code in [400, 422], (
                f"🔴 VULNERABILIDADE: Aceita {pontos} pontos ({descricao})"
            )
    
    @pytest.mark.asyncio
    async def test_valores_positivos_extremos(self, async_client: AsyncClient, auth_headers):
        """
        VULNERABILIDADE ALTA: Aceita valores positivos extremos
        """
        cliente_id = 1
        
        test_cases = [
            (999999, "Valor extremamente positivo"),
            (10000, "Valor muito positivo"),
            (100, "Valor positivo moderado"),
        ]
        
        for pontos, descricao in test_cases:
            response = await async_client.post(
                "/api/v1/pontos/ajustes",
                json={"cliente_id": cliente_id, "pontos": pontos, "motivo": descricao},
                headers=auth_headers
            )
            
            # Valores acima do limite devem ser bloqueados
            if abs(pontos) > 4:
                assert response.status_code in [400, 422], (
                    f"🔴 VULNERABILIDADE: Aceita {pontos} pontos ({descricao})"
                )
    
    @pytest.mark.asyncio
    async def test_valor_zero(self, async_client: AsyncClient, auth_headers):
        """Validar que transações de 0 pontos são bloqueadas"""
        response = await async_client.post(
            "/api/v1/pontos/ajustes",
            json={"cliente_id": 1, "pontos": 0, "motivo": "Teste zero"},
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422], (
            "🔴 VULNERABILIDADE: Aceita transações de 0 pontos"
        )


class TestLimitesOperacionais:
    """Testes de Limites Operacionais"""
    
    @pytest.mark.asyncio
    async def test_multiplos_ajustes_pequenos(self, async_client: AsyncClient, auth_headers):
        """
        VULNERABILIDADE MÉDIA: Múltiplos ajustes pequenos para burlar limite
        
        Cenário:
        1. Limite individual: ±4 pontos
        2. Fazer 100 ajustes de +4 pontos
        3. Total: 400 pontos acumulados fraudulentamente
        """
        cliente_id = 1
        saldo_inicial_response = await async_client.get(
            f"/api/v1/pontos/saldo/{cliente_id}",
            headers=auth_headers
        )
        saldo_inicial = saldo_inicial_response.json().get("saldo", 0)
        
        sucessos = 0
        bloqueios = 0
        
        for i in range(100):
            response = await async_client.post(
                "/api/v1/pontos/ajustes",
                json={"cliente_id": cliente_id, "pontos": 4, "motivo": f"Ajuste {i}"},
                headers=auth_headers
            )
            
            if response.status_code == 200:
                sucessos += 1
            elif response.status_code == 429:  # Rate limit
                bloqueios += 1
                break
        
        saldo_final_response = await async_client.get(
            f"/api/v1/pontos/saldo/{cliente_id}",
            headers=auth_headers
        )
        saldo_final = saldo_final_response.json().get("saldo", 0)
        
        pontos_acumulados = saldo_final - saldo_inicial
        
        # Deve ter limite diário ou rate limit efetivo
        assert pontos_acumulados < 200, (
            f"🟠 VULNERABILIDADE: Acumulou {pontos_acumulados} pontos "
            f"através de {sucessos} ajustes pequenos"
        )
    
    @pytest.mark.asyncio
    async def test_rate_limit_ajustes(self, async_client: AsyncClient, auth_headers):
        """Validar que rate limit está funcionando"""
        cliente_id = 1
        
        # Fazer requisições rápidas até atingir rate limit
        for i in range(30):
            response = await async_client.post(
                "/api/v1/pontos/ajustes",
                json={"cliente_id": cliente_id, "pontos": 1, "motivo": f"Rate test {i}"},
                headers=auth_headers
            )
            
            if response.status_code == 429:
                # Rate limit funcionando
                return
        
        pytest.fail("🔴 VULNERABILIDADE: Rate limit não está funcionando")


class TestResgatePublico:
    """Testes de Segurança em Resgate Público"""
    
    @pytest.mark.asyncio
    async def test_resgate_publico_sem_autenticacao(self, async_client: AsyncClient):
        """
        VULNERABILIDADE ALTA: Resgate público sem autenticação adequada
        """
        # Tentar resgatar prêmio apenas com CPF
        response = await async_client.post(
            "/api/v1/premios/resgatar-publico",
            json={
                "premio_id": 1,
                "cliente_documento": "12345678901",
                "observacoes": "Teste de segurança"
            }
        )
        
        # Idealmente deveria exigir 2FA ou autenticação forte
        if response.status_code == 200:
            pytest.fail(
                "🔴 VULNERABILIDADE CRÍTICA: Resgate público permitido sem 2FA! "
                "Qualquer pessoa com CPF pode resgatar prêmios."
            )
    
    @pytest.mark.asyncio
    async def test_consulta_publica_expoe_dados(self, async_client: AsyncClient):
        """
        VULNERABILIDADE MÉDIA: Consulta pública expõe dados sensíveis
        """
        # Consultar pontos sem autenticação
        response = await async_client.get("/api/v1/pontos/consultar/12345678901")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar se expõe dados sensíveis
            assert "historico" not in data or len(data.get("historico", [])) == 0, (
                "🟠 VULNERABILIDADE: Consulta pública expõe histórico completo de transações"
            )
            
            assert "saldo" not in data, (
                "🟠 VULNERABILIDADE: Consulta pública expõe saldo de pontos"
            )


class TestEstoque:
    """Testes de Controle de Estoque"""
    
    @pytest.mark.asyncio
    async def test_estoque_negativo(self, async_client: AsyncClient, auth_headers):
        """
        VULNERABILIDADE MÉDIA: Estoque pode ficar negativo
        """
        # Criar prêmio com estoque limitado
        premio_response = await async_client.post(
            "/api/v1/premios",
            json={
                "nome": "Prêmio Teste Estoque",
                "preco_em_pontos": 10,
                "estoque": 1,
                "ativo": True
            },
            headers=auth_headers
        )
        
        if premio_response.status_code != 201:
            pytest.skip("Não foi possível criar prêmio de teste")
        
        premio_id = premio_response.json()["id"]
        
        # Tentar resgatar múltiplas vezes
        tasks = [
            async_client.post(
                "/api/v1/premios/resgatar",
                json={"cliente_id": 1, "premio_id": premio_id},
                headers=auth_headers
            )
            for _ in range(5)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        sucessos = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        
        # Apenas 1 resgate deve ter sucesso (estoque = 1)
        assert sucessos <= 1, (
            f"🔴 VULNERABILIDADE: {sucessos} resgates permitidos com estoque de 1"
        )


class TestAuditoria:
    """Testes de Auditoria e Rastreabilidade"""
    
    @pytest.mark.asyncio
    async def test_rastreabilidade_ajustes(self, async_client: AsyncClient, auth_headers):
        """Validar que ajustes são rastreáveis"""
        cliente_id = 1
        
        # Fazer ajuste
        response = await async_client.post(
            "/api/v1/pontos/ajustes",
            json={"cliente_id": cliente_id, "pontos": 4, "motivo": "Teste auditoria"},
            headers=auth_headers
        )
        
        if response.status_code != 200:
            pytest.skip("Ajuste falhou")
        
        # Verificar histórico
        historico_response = await async_client.get(
            f"/api/v1/pontos/historico/{cliente_id}",
            headers=auth_headers
        )
        
        assert historico_response.status_code == 200
        historico = historico_response.json().get("transacoes", [])
        
        # Última transação deve ter informações completas
        if historico:
            ultima = historico[0]
            assert "funcionario_id" in ultima or "funcionario_nome" in ultima, (
                "🟠 VULNERABILIDADE: Ajuste sem rastreabilidade de funcionário"
            )
            assert "motivo" in ultima, (
                "🟠 VULNERABILIDADE: Ajuste sem motivo registrado"
            )


# Fixtures
@pytest.fixture
async def async_client():
    """Cliente HTTP assíncrono para testes"""
    async with AsyncClient(base_url="http://localhost:8000/api/v1") as client:
        yield client


@pytest.fixture
async def auth_headers(async_client):
    """Headers de autenticação para testes"""
    # Login como admin
    response = await async_client.post(
        "/auth/login",
        json={"email": "admin@hotelreal.com.br", "senha": "admin123"}
    )
    
    if response.status_code != 200:
        pytest.skip("Não foi possível autenticar")
    
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
