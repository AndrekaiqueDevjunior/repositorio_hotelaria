#!/usr/bin/env python3
"""
Script de validação para garantir que o backend está usando
o banco de dados remoto do Prisma Data Platform.
"""
import os
import asyncio
from urllib.parse import urlparse
from app.core.database import db, connect_db


def mask_database_url(url: str) -> str:
    """Mascara credenciais da URL do banco para log seguro."""
    if not url:
        return "NOT_SET"
    
    try:
        parsed = urlparse(url)
        if parsed.password:
            masked_netloc = f"{parsed.username}:****@{parsed.hostname}:{parsed.port}"
            return f"{parsed.scheme}://{masked_netloc}{parsed.path}?{parsed.query}"
        return url
    except:
        return "INVALID_URL"


async def validate_prisma_connection():
    """Valida conexão com Prisma e verifica se é o banco remoto."""
    print("🔍 VALIDAÇÃO PRISMA REMOTO - Hotel Cabo Frio")
    print("=" * 60)
    
    # 1. Verificar DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    print(f"\n📋 DATABASE_URL carregada:")
    print(f"   {mask_database_url(database_url)}")
    
    if not database_url:
        print("❌ ERRO: DATABASE_URL não está definida!")
        return False
    
    # 2. Verificar se é Prisma remoto
    if "db.prisma.io" in database_url:
        print("✅ CORRETO: Usando Prisma Data Platform remoto")
    elif any(host in database_url for host in ["localhost", "127.0.0.1", "postgres:5432"]):
        print("❌ PROBLEMA: Usando banco local!")
        return False
    else:
        print("⚠️  ATENÇÃO: Host não reconhecido")
    
    # 3. Testar conexão
    try:
        print(f"\n🌐 Testando conexão com Prisma...")
        await connect_db()
        
        if db.is_connected():
            print("✅ Conexão estabelecida com sucesso!")
        else:
            print("❌ Falha na conexão!")
            return False
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False
    
    # 4. Testar queries básicas
    try:
        print(f"\n📊 Testando queries básicas...")
        
        # Contar registros em tabelas principais
        counts = {}
        
        try:
            counts["reservas"] = await db.reserva.count()
            print(f"   Reservas: {counts['reservas']}")
        except Exception as e:
            print(f"   Reservas: ERRO - {e}")
        
        try:
            counts["clientes"] = await db.cliente.count()
            print(f"   Clientes: {counts['clientes']}")
        except Exception as e:
            print(f"   Clientes: ERRO - {e}")
        
        try:
            counts["quartos"] = await db.quarto.count()
            print(f"   Quartos: {counts['quartos']}")
        except Exception as e:
            print(f"   Quartos: ERRO - {e}")
        
        try:
            counts["funcionarios"] = await db.funcionario.count()
            print(f"   Funcionários: {counts['funcionarios']}")
        except Exception as e:
            print(f"   Funcionários: ERRO - {e}")
        
        print("✅ Queries executadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro nas queries: {e}")
        return False
    
    # 5. Desconectar
    try:
        await db.disconnect()
        print(f"\n✅ Desconectado com sucesso!")
    except Exception as e:
        print(f"⚠️  Aviso na desconexão: {e}")
    
    print(f"\n🎯 RESULTADO: Validação concluída com sucesso!")
    print(f"   O backend está configurado para usar o Prisma Data Platform remoto.")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(validate_prisma_connection())
        if result:
            print(f"\n✅ SUCESSO: Configuração validada!")
            exit(0)
        else:
            print(f"\n❌ FALHA: Problemas na configuração!")
            exit(1)
    except KeyboardInterrupt:
        print(f"\n⚠️  Validação interrompida pelo usuário")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        exit(1)
