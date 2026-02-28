#!/usr/bin/env python3
"""
Seed para criar prêmios no sistema de pontos
"""
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seeds.bootstrap import bootstrap_seed_environment

bootstrap_seed_environment()

from app.core.database import get_db_connected

DEMO_PREMIOS = [
    {
        "nome": "Café da manhã para 2 pessoas",
        "descricao": "Café da manhã completo no restaurante do hotel para 2 pessoas",
        "pontos_necessarios": 500,
        "categoria": "ALIMENTACAO",
        "quantidade_disponivel": 50,
        "ativo": True,
        "imagem_url": "/media/premios/cafe_manha.jpg"
    },
    {
        "nome": "Late checkout (14:00)",
        "descricao": "Extend stay até as 14:00 sem custo adicional",
        "pontos_necessarios": 300,
        "categoria": "HOSPEDAGEM",
        "quantidade_disponivel": 100,
        "ativo": True,
        "imagem_url": "/media/premios/late_checkout.jpg"
    },
    {
        "nome": "Upgrade de suíte",
        "descricao": "Upgrade automático para categoria superior (sujeito à disponibilidade)",
        "pontos_necessarios": 800,
        "categoria": "HOSPEDAGEM",
        "quantidade_disponivel": 20,
        "ativo": True,
        "imagem_url": "/media/premios/upgrade_suite.jpg"
    },
    {
        "nome": "Garrafa de vinho selecionada",
        "descricao": "Garrafa de vinho tinto ou branco selecionado pelo sommelier",
        "pontos_necessarios": 400,
        "categoria": "ALIMENTACAO",
        "quantidade_disponivel": 30,
        "ativo": True,
        "imagem_url": "/media/premios/vinho.jpg"
    },
    {
        "nome": "Spa Day - 50% de desconto",
        "descricao": "50% de desconto em qualquer tratamento de spa (até 2 horas)",
        "pontos_necessarios": 600,
        "categoria": "BEM_ESTAR",
        "quantidade_disponivel": 25,
        "ativo": True,
        "imagem_url": "/media/premios/spa_day.jpg"
    },
    {
        "nome": "Noite gratuita (suíte padrão)",
        "descricao": "Diária gratuita em suíte padrão (sujeito à disponibilidade)",
        "pontos_necessarios": 1500,
        "categoria": "HOSPEDAGEM",
        "quantidade_disponivel": 10,
        "ativo": True,
        "imagem_url": "/media/premios/noite_gratuita.jpg"
    },
    {
        "nome": "Transfer aeroporto",
        "descricao": "Transfer ida/volta entre aeroporto e hotel",
        "pontos_necessarios": 700,
        "categoria": "TRANSPORTE",
        "quantidade_disponivel": 40,
        "ativo": True,
        "imagem_url": "/media/premios/transfer.jpg"
    },
    {
        "nome": "Jantar romântico",
        "descricao": "Jantar especial para 2 pessoas com vinho no restaurante",
        "pontos_necessarios": 900,
        "categoria": "ALIMENTACAO",
        "quantidade_disponivel": 15,
        "ativo": True,
        "imagem_url": "/media/premios/jantar_romantico.jpg"
    },
    {
        "nome": "Early check-in (10:00)",
        "descricao": "Check-in antecipado às 10:00 sem custo adicional",
        "pontos_necessarios": 250,
        "categoria": "HOSPEDAGEM",
        "quantidade_disponivel": 100,
        "ativo": True,
        "imagem_url": "/media/premios/early_checkin.jpg"
    },
    {
        "nome": "Kit bem-estar",
        "descricao": "Kit com produtos de spa para uso no quarto",
        "pontos_necessarios": 350,
        "categoria": "BEM_ESTAR",
        "quantidade_disponivel": 60,
        "ativo": True,
        "imagem_url": "/media/premios/kit_bem_estar.jpg"
    }
]

async def seed_premios():
    print("=== SEED PRÊMIOS REAL POINTS ===\n")
    
    db = await get_db_connected()
    
    created_count = 0
    updated_count = 0
    
    for premio_data in DEMO_PREMIOS:
        try:
            # Verificar se já existe
            existing = await db.premio.find_first(
                where={"nome": premio_data["nome"]}
            )
            
            if existing:
                print(f"⚠️  Prêmio '{premio_data['nome']}' já existe (ID: {existing.id})")
                updated_count += 1
            else:
                # Criar novo prêmio
                premio = await db.premio.create({
                    "nome": premio_data["nome"],
                    "descricao": premio_data["descricao"],
                    "precoEmPontos": premio_data["pontos_necessarios"],
                    "categoria": premio_data["categoria"],
                    "estoque": premio_data["quantidade_disponivel"],
                    "ativo": premio_data["ativo"],
                    "imagemUrl": premio_data["imagem_url"]
                })
                print(f"✅ Prêmio '{premio_data['nome']}' criado (ID: {premio.id})")
                created_count += 1
                
        except Exception as e:
            print(f"❌ Erro ao criar prêmio '{premio_data['nome']}': {e}")
    
    print(f"\n📊 Total de prêmios: {created_count + updated_count}")
    print(f"   🆙 Criados: {created_count}")
    print(f"   🔄 Já existiam: {updated_count}")

if __name__ == "__main__":
    asyncio.run(seed_premios())
