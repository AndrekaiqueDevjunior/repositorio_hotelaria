#!/usr/bin/env python3
"""
Seed para criar tarifas para todos os tipos de suíte
"""
import asyncio
from datetime import datetime, timedelta
from app.core.database import get_db_connected

DEMO_TARIFAS = [
    {
        "tipo_suite": "DUPLA",
        "valor_diaria": 180.00,
        "valor_fim_semana": 220.00,
        "data_inicio": datetime.now().date() - timedelta(days=30),
        "data_fim": datetime.now().date() + timedelta(days=365),
        "ativo": True
    },
    {
        "tipo_suite": "LUXO",
        "valor_diaria": 250.00,
        "valor_fim_semana": 300.00,
        "data_inicio": datetime.now().date() - timedelta(days=30),
        "data_fim": datetime.now().date() + timedelta(days=365),
        "ativo": True
    },
    {
        "tipo_suite": "LUXO 2º",
        "valor_diaria": 280.00,
        "valor_fim_semana": 330.00,
        "data_inicio": datetime.now().date() - timedelta(days=30),
        "data_fim": datetime.now().date() + timedelta(days=365),
        "ativo": True
    },
    {
        "tipo_suite": "LUXO 3º",
        "valor_diaria": 300.00,
        "valor_fim_semana": 350.00,
        "data_inicio": datetime.now().date() - timedelta(days=30),
        "data_fim": datetime.now().date() + timedelta(days=365),
        "ativo": True
    },
    {
        "tipo_suite": "LUXO 4º EC",
        "valor_diaria": 320.00,
        "valor_fim_semana": 380.00,
        "data_inicio": datetime.now().date() - timedelta(days=30),
        "data_fim": datetime.now().date() + timedelta(days=365),
        "ativo": True
    },
    {
        "tipo_suite": "MASTER",
        "valor_diaria": 450.00,
        "valor_fim_semana": 550.00,
        "data_inicio": datetime.now().date() - timedelta(days=30),
        "data_fim": datetime.now().date() + timedelta(days=365),
        "ativo": True
    },
    {
        "tipo_suite": "REAL",
        "valor_diaria": 600.00,
        "valor_fim_semana": 750.00,
        "data_inicio": datetime.now().date() - timedelta(days=30),
        "data_fim": datetime.now().date() + timedelta(days=365),
        "ativo": True
    }
]

async def seed_tarifas():
    print("=== SEED TARIFAS ===\n")
    
    db = await get_db_connected()
    
    created_count = 0
    updated_count = 0
    
    for tarifa_data in DEMO_TARIFAS:
        try:
            # Verificar se já existe tarifa ativa para este tipo
            existing = await db.tarifasuite.find_first(
                where={
                    "suiteTipo": tarifa_data["tipo_suite"],
                    "ativo": True
                }
            )
            
            if existing:
                print(f"⚠️  Tarifa para '{tarifa_data['tipo_suite']}' já existe (ID: {existing.id})")
                updated_count += 1
            else:
                # Criar nova tarifa
                tarifa = await db.tarifasuite.create({
                    "suiteTipo": tarifa_data["tipo_suite"],
                    "temporada": "ALTA",
                    "dataInicio": str(tarifa_data["data_inicio"]),
                    "dataFim": str(tarifa_data["data_fim"]),
                    "precoDiaria": tarifa_data["valor_diaria"],
                    "ativo": True
                })
                print(f"✅ Tarifa '{tarifa_data['tipo_suite']}' criada (ID: {tarifa.id})")
                print(f"   💰 Diária: R$ {tarifa_data['valor_diaria']:.2f}")
                print(f"   🎉 Fim de semana: R$ {tarifa_data['valor_fim_semana']:.2f}")
                created_count += 1
                
        except Exception as e:
            print(f"❌ Erro ao criar tarifa '{tarifa_data['tipo_suite']}': {e}")
    
    print(f"\n📊 Total de tarifas: {created_count + updated_count}")
    print(f"   🆙 Criadas: {created_count}")
    print(f"   🔄 Já existiam: {updated_count}")

if __name__ == "__main__":
    asyncio.run(seed_tarifas())
