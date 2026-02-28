#!/usr/bin/env python3
"""
Testes do Sistema de Validação Anti-Fraude de Clientes
Valida duplicação de CPF e nome para prevenir fraudes
"""

import asyncio
from app.core.database import get_db
from app.repositories.cliente_repo import ClienteRepository
from app.services.validacao_cliente_service import ValidacaoClienteService

class TestValidacaoCliente:
    """Suite de testes para validação anti-fraude"""
    
    def __init__(self):
        self.db = None
        self.cliente_repo = None
        self.validacao_service = None
        
    async def setup(self):
        """Configurar ambiente de teste"""
        self.db = get_db()
        await self.db.connect()
        self.cliente_repo = ClienteRepository(self.db)
        self.validacao_service = ValidacaoClienteService(self.cliente_repo)
        print("✅ Ambiente de teste configurado")
        
    async def cleanup(self):
        """Limpar ambiente de teste"""
        if self.db:
            await self.db.disconnect()
        print("✅ Ambiente de teste limpo")

    # ========================================
    # TESTES DE VALIDAÇÃO DE CPF
    # ========================================
    
    async def test_validacao_cpf(self):
        """Testar validação de CPF"""
        print("\n🧪 Testando validação de CPF...")
        
        # Teste 1: CPF válido (usando CPF aleatório)
        cpf_teste = "999.888.777-66"
        resultado = await self.validacao_service.verificar_duplicacao_cpf(cpf_teste)
        assert resultado[0] == False, f"CPF válido {cpf_teste} não deve ter duplicação"
        print("   ✅ CPF válido: OK")
        
        # Teste 2: CPF inválido (formato)
        resultado = await self.validacao_service.verificar_duplicacao_cpf("123.456.789")
        assert resultado[0] == False, "CPF inválido deve retornar False"
        assert "CPF inválido" in resultado[1], "Deve retornar erro de formato"
        print("   ✅ CPF inválido: OK")
        
        # Teste 3: CPF com dígitos iguais
        resultado = await self.validacao_service.verificar_duplicacao_cpf("111.111.111-11")
        assert resultado[0] == False, "CPF com dígitos iguais deve ser inválido"
        print("   ✅ CPF com dígitos iguais: OK")
        
        print("   ✅ Validação de CPF: Todos os testes passaram")

    # ========================================
    # TESTES DE VALIDAÇÃO DE NOME
    # ========================================
    
    async def test_validacao_nome(self):
        """Testar validação de nome"""
        print("\n🧪 Testando validação de nome...")
        
        # Teste 1: Nome válido
        resultado = await self.validacao_service.verificar_duplicacao_nome("João Silva")
        assert resultado[0] == False, "Nome válido não deve ter duplicação"
        print("   ✅ Nome válido: OK")
        
        # Teste 2: Nome normalização
        nome_normalizado = self.validacao_service.normalizar_nome("  joão  da  silva  ")
        assert nome_normalizado == "JOÃO DA SILVA", "Nome deve ser normalizado"
        print("   ✅ Normalização de nome: OK")
        
        print("   ✅ Validação de nome: Todos os testes passaram")

    # ========================================
    # TESTES DE VALIDAÇÃO COMBINADA
    # ========================================
    
    async def test_validacao_combinada(self):
        """Testar validação combinada de CPF e nome"""
        print("\n🧪 Testando validação combinada...")
        
        # Teste 1: Cliente válido
        resultado = await self.validacao_service.verificar_duplicacao_combinada(
            "Maria Teste Santos", "777.666.555-44"
        )
        assert resultado["valido"] == True, "Cliente válido deve passar"
        assert len(resultado["erros"]) == 0, "Não deve ter erros"
        print("   ✅ Cliente válido: OK")
        
        # Teste 2: CPF inválido
        resultado = await self.validacao_service.verificar_duplicacao_combinada(
            "Maria Santos", "123.456.789"
        )
        assert resultado["valido"] == False, "CPF inválido deve falhar"
        assert len(resultado["erros"]) > 0, "Deve ter erros"
        print("   ✅ CPF inválido: OK")
        
        print("   ✅ Validação combinada: Todos os testes passaram")

    # ========================================
    # TESTES DE CRIAÇÃO E ATUALIZAÇÃO
    # ========================================
    
    async def test_criacao_cliente_valido(self):
        """Testar criação de cliente válido"""
        print("\n🧪 Testando criação de cliente válido...")
        
        try:
            # Criar cliente válido
            cliente_data = {
                "nome_completo": "Pedro Teste Oliveira",
                "documento": "888.777.666-55",
                "telefone": "(11) 99999-9999",
                "email": "pedro.teste@email.com"
            }
            
            resultado = await self.validacao_service.validar_cliente_create(cliente_data)
            assert resultado["valido"] == True, "Cliente válido deve passar"
            assert len(resultado["erros"]) == 0, "Não deve ter erros"
            
            # Limpar cliente criado
            await self.db.cliente.delete_many(
                where={"documento": "88877766655"}
            )
            
            print("   ✅ Criação de cliente válido: OK")
            
        except Exception as e:
            print(f"   ❌ Erro na criação: {e}")
            raise

    async def test_criacao_cliente_duplicado(self):
        """Testar criação de cliente duplicado"""
        print("\n🧪 Testando criação de cliente duplicado...")
        
        try:
            # Testar com CPF que já existe no banco
            cliente_data = {
                "nome_completo": "Roberto Almeida",
                "documento": "123.456.789-01",  # CPF que já existe
                "telefone": "(11) 88888-8888",
                "email": "roberto@email.com"
            }
            
            # Tentar criar cliente duplicado
            resultado = await self.validacao_service.validar_cliente_create(cliente_data)
            assert resultado["valido"] == False, "Cliente duplicado deve falhar"
            assert len(resultado["erros"]) > 0, "Deve ter erros de duplicação"
            
            # Verificar se o erro menciona CPF duplicado
            erros_texto = " ".join(resultado["erros"])
            assert "já está cadastrado" in erros_texto, "Erro deve mencionar que já está cadastrado"
            
            print("   ✅ Criação de cliente duplicado: OK")
            
        except Exception as e:
            print(f"   ❌ Erro no teste de duplicação: {e}")
            raise

    # ========================================
    # TESTES DE DETECÇÃO DE FRAUDES
    # ========================================
    
    async def test_deteccao_fraudes(self):
        """Testar detecção de fraudes"""
        print("\n🧪 Testando detecção de fraudes...")
        
        try:
            # Testar detecção de fraudes (sem criar dados)
            fraudes = await self.validacao_service.detectar_potenciais_fraudes(limite_similaridade=2)
            
            # Verificar se o método funciona (não precisa encontrar fraudes)
            assert isinstance(fraudes, list), "Deve retornar lista de fraudes"
            
            print("   ✅ Detecção de fraudes: OK")
            print(f"   📊 Fraudes potenciais encontradas: {len(fraudes)}")
            
        except Exception as e:
            print(f"   ❌ Erro na detecção de fraudes: {e}")
            raise

    # ========================================
    # MÉTODO PRINCIPAL
    # ========================================
    
    async def executar_todos_os_testes(self):
        """Executar todos os testes de validação"""
        print("🧪 INICIANDO TESTES DE VALIDAÇÃO ANTI-FRAUDE")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Testes de validação
            await self.test_validacao_cpf()
            await self.test_validacao_nome()
            await self.test_validacao_combinada()
            
            # Testes de criação
            await self.test_criacao_cliente_valido()
            await self.test_criacao_cliente_duplicado()
            
            # Testes de fraude
            await self.test_deteccao_fraudes()
            
            print("\n" + "=" * 60)
            print("🎉 TODOS OS TESTES DE VALIDAÇÃO PASSARAM!")
            print("✅ Sistema anti-fraude está funcionando corretamente")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
            raise
            
        finally:
            await self.cleanup()

# ========================================
# FUNÇÃO PRINCIPAL
# ========================================

async def executar_testes_validacao():
    """Executar testes de validação"""
    teste = TestValidacaoCliente()
    await teste.executar_todos_os_testes()

if __name__ == "__main__":
    print("🚀 Executando Testes de Validação Anti-Fraude...")
    asyncio.run(executar_testes_validacao())
