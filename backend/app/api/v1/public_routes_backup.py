from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc, timedelta
from app.repositories.quarto_repo import QuartoRepository
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.cliente_repo import ClienteRepository
from app.core.database import get_db
import random
import string

router = APIRouter(prefix="/public", tags=["public"])

# Schemas para API pública
class DisponibilidadeRequest(BaseModel):
    data_checkin: str
    data_checkout: str

class ReservaPublicaCreate(BaseModel):
    nome_completo: str
    documento: str
    email: EmailStr
    telefone: str
    quarto_numero: str
    tipo_suite: str
    data_checkin: str
    data_checkout: str
    num_hospedes: int = 1
    num_criancas: int = 0
    observacoes: Optional[str] = None
    metodo_pagamento: str = "na_chegada"

def gerar_codigo_reserva():
    """Gerar código único de reserva"""
    from datetime import datetime
    from app.utils.datetime_utils import now_utc, to_utc
    data = now_utc().strftime("%Y%m%d")
    # Buscar último código do dia
    # Por enquanto, usar formato WEB-YYYYMMDD-NNNNNN
    return f"WEB-{data}-000001"

@router.get("/reservas/{codigo}")
async def consultar_reserva_publica(codigo: str):
    """
    Consultar reserva pelo código (API Pública)
    
    Não requer autenticação - usado para clientes consultarem suas reservas
    """
    try:
        db = get_db()
        
        # Buscar reserva pelo código
        reserva = await db.reserva.find_first(
            where={"codigoReserva": codigo.upper()}
        )
        
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva não encontrada")
        
        # Buscar pagamentos da reserva
        pagamentos = await db.pagamento.find_many(
            where={"reservaId": reserva.id},
            order={"createdAt": "desc"}
        )
        
        return {
            "success": True,
            "reserva": {
                "codigo": reserva.codigoReserva,
                "status": reserva.status,
                "cliente_nome": reserva.clienteNome,
                "quarto_numero": reserva.quartoNumero,
                "tipo_suite": reserva.tipoSuite,
                "checkin_previsto": reserva.checkinPrevisto.isoformat() if reserva.checkinPrevisto else None,
                "checkout_previsto": reserva.checkoutPrevisto.isoformat() if reserva.checkoutPrevisto else None,
                "checkin_realizado": reserva.checkinReal.isoformat() if reserva.checkinReal else None,
                "checkout_realizado": reserva.checkoutReal.isoformat() if reserva.checkoutReal else None,
                "valor_diaria": float(reserva.valorDiaria) if reserva.valorDiaria else 0,
                "num_diarias": reserva.numDiarias,
                "valor_total": float(reserva.valorDiaria) * reserva.numDiarias if reserva.valorDiaria and reserva.numDiarias else 0,
                "data_criacao": reserva.createdAt.isoformat() if reserva.createdAt else None
            },
            "pagamentos": [
                {
                    "id": p.id,
                    "status": p.status,
                    "valor": float(p.valor) if p.valor else 0,
                    "metodo": p.metodo,
                    "data": p.createdAt.isoformat() if p.createdAt else None
                }
                for p in pagamentos
            ],
            "instrucoes": {
                "checkin_horario": "15:00",
                "checkout_horario": "12:00",
                "documentos": "Apresente documento de identidade e CPF",
                "contato": "(22) 2222-2222 ou reservas@hotelreal.com.br"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao consultar reserva: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar reserva: {str(e)}")

@router.get("/pontos/{cpf}")
async def consultar_pontos_publico(cpf: str):
    """
    Consultar pontos do cliente pelo CPF (API Pública)
    
    Não requer autenticação - usado para clientes consultarem seus pontos
    """
    try:
        db = get_db()
        
        # Limpar CPF
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf_limpo) != 11:
            raise HTTPException(status_code=400, detail="CPF inválido")
        
        # Buscar cliente pelo CPF
        cliente = await db.cliente.find_first(
            where={"documento": cpf_limpo}
        )
        
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Buscar transações de pontos
        transacoes = await db.transacaopontos.find_many(
            where={"clienteId": cliente.id},
            order={"createdAt": "desc"},
            take=10
        )
        
        # Calcular saldo
        saldo = sum(t.pontos for t in transacoes if t.tipo == "GANHO") - sum(t.pontos for t in transacoes if t.tipo == "GASTO")
        
        # Formatar histórico
        historico_recente = []
        for t in transacoes[:5]:
            historico_recente.append({
                "origem": t.descricao or "Transação",
                "data": t.createdAt.strftime("%d/%m/%Y") if t.createdAt else "",
                "tipo": t.tipo,
                "pontos": t.pontos
            })
        
        return {
            "success": True,
            "cliente": {
                "nome": cliente.nomeCompleto,
                "documento": cliente.documento
            },
            "pontos": {
                "saldo": saldo,
                "historico_recente": historico_recente,
                "total_transacoes": len(transacoes)
            },
            "info": {
                "como_ganhar": [
                    "Hospede-se conosco e ganhe 10 pontos por diária",
                    "Suítes Master: 15 pontos por diária",
                    "Suítes Real: 20 pontos por diária",
                    "Troque seus pontos por descontos e upgrades!"
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao consultar pontos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar pontos: {str(e)}")

@router.get("/quartos/disponiveis")
async def buscar_quartos_disponiveis(
    data_checkin: str,
    data_checkout: str
):
    """
    Buscar quartos disponíveis para as datas especificadas (API Pública)
    
    Não requer autenticação - usado pela página pública de reservas
    """
    try:
        # Validar datas
        try:
            checkin = datetime.fromisoformat(data_checkin)
            checkout = datetime.fromisoformat(data_checkout)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")
        
        if checkout <= checkin:
            raise HTTPException(status_code=400, detail="Data de checkout deve ser posterior ao checkin")
        
        db = get_db()
        quarto_repo = QuartoRepository(db)
        
        # Buscar todos os quartos
        quartos = await quarto_repo.list_all()
        
        # Filtrar quartos disponíveis (simplificado)
        quartos_disponiveis = []
        for quarto in quartos["quartos"]:
            if quarto["status"] == "LIVRE":
                quartos_disponiveis.append({
                    "numero": quarto["numero"],
                    "tipo_suite": quarto["tipo_suite"],
                    "capacidade": quarto["capacidade"],
                    "valor_diaria": quarto["valor_diaria"],
                    "descricao": quarto.get("descricao", "")
                })
        
        return {
            "success": True,
            "quartos": quartos_disponiveis,
            "total": len(quartos_disponiveis)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao buscar quartos disponíveis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar quartos disponíveis")

@router.post("/reservas")
async def criar_reserva_publica(reserva: ReservaPublicaCreate):
    """
    Criar nova reserva (API Pública)
    
    Não requer autenticação - usado pela página pública de reservas
    """
    try:
        db = get_db()
        cliente_repo = ClienteRepository(db)
        reserva_repo = ReservaRepository(db)
        quarto_repo = QuartoRepository(db)
        
        # Validar datas
        try:
            checkin = datetime.fromisoformat(reserva.data_checkin)
            checkout = datetime.fromisoformat(reserva.data_checkout)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data inválido")
        
        if checkout <= checkin:
            raise HTTPException(status_code=400, detail="Data de checkout deve ser posterior ao checkin")
        
        num_diarias = (checkout - checkin).days
        
        # Verificar se o quarto existe e está disponível
        try:
            quarto = await quarto_repo.get_by_numero(reserva.quarto_numero)
        except ValueError:
            raise HTTPException(status_code=404, detail="Quarto não encontrado")
        
        if quarto['status'] != 'LIVRE':
            raise HTTPException(status_code=400, detail="Quarto não está disponível")
        
        # Criar cliente se não existir
        try:
            cliente = await cliente_repo.get_by_documento(reserva.documento)
        except ValueError:
            # Criar novo cliente
            cliente_data = {
                "nome_completo": reserva.nome_completo,
                "documento": reserva.documento,
                "telefone": reserva.telefone,
                "email": reserva.email
            }
            cliente = await cliente_repo.create(cliente_data)
        
        # Criar reserva
        codigo_reserva = gerar_codigo_reserva()
        reserva_data = {
            "codigo_reserva": codigo_reserva,
            "cliente_id": cliente["id"],
            "quarto_numero": reserva.quarto_numero,
            "tipo_suite": reserva.tipo_suite,
            "checkin_previsto": reserva.data_checkin,
            "checkout_previsto": reserva.data_checkout,
            "num_diarias": num_diarias,
            "num_hospedes": reserva.num_hospedes,
            "num_criancas": reserva.num_criancas,
            "valor_diaria": quarto["valor_diaria"],
            "observacoes": reserva.observacoes,
            "status": "PENDENTE"
        }
        
        nova_reserva = await reserva_repo.create(reserva_data)
        
        return {
            "success": True,
            "reserva": nova_reserva,
            "mensagem": f"Reserva {codigo_reserva} criada com sucesso! Aguardando confirmação de pagamento."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao criar reserva pública: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar reserva: {str(e)}")
