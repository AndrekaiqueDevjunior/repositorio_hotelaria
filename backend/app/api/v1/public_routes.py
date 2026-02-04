from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, date
from app.utils.datetime_utils import now_utc, to_utc, LOCAL_TIMEZONE
from app.repositories.quarto_repo import QuartoRepository
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.pontos_repo import PontosRepository
from app.repositories.tarifa_suite_repo import TarifaSuiteRepository
from app.core.database import get_db
import random
import string
import re
from app.services.consulta_publica_service import ConsultaPublicaService

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


async def _obter_tarifa_diaria(db, tipo_suite: str, data_ref: date) -> float:
    repo = TarifaSuiteRepository(db)
    tarifa = await repo.get_tarifa_ativa(tipo_suite, data_ref)
    if not tarifa:
        raise HTTPException(
            status_code=400,
            detail=f"Tarifa nao cadastrada para a suite {tipo_suite} na data {data_ref}. Cadastre uma tarifa antes de reservar."
        )
    return float(tarifa.get("preco_diaria", 0.0))

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
        reserva_repo = ReservaRepository(db)
        
        # Buscar reserva pelo código
        reserva = await reserva_repo.get_by_codigo(codigo)
        
        return {
            "success": True,
            "reserva": {
                "codigo": reserva["codigo_reserva"],
                "status": reserva["status"],
                "cliente_nome": reserva.get("cliente_nome"),
                "quarto_numero": reserva.get("quarto_numero"),
                "tipo_suite": reserva.get("tipo_suite"),
                "checkin_previsto": reserva.get("checkin_previsto"),
                "checkout_previsto": reserva.get("checkout_previsto"),
                "checkin_realizado": reserva.get("checkin_realizado"),
                "checkout_realizado": reserva.get("checkout_realizado"),
                "valor_diaria": float(reserva.get("valor_diaria", 0.0)),
                "num_diarias": reserva.get("num_diarias", 0),
                "valor_total": float(reserva.get("valor_total", 0.0)),
                "data_criacao": reserva.get("created_at")
            },
            "instrucoes": {
                "checkin_horario": "12:00",
                "checkout_horario": "11:00",
                "documentos": "Apresente documento de identidade e CPF",
                "contato": "(22) 2648-5900 ou contato@hotelrealcabofrio.com.br"
            }
        }
        
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar reserva: {str(e)}")


@router.get("/consulta/ajuda/formatos")
async def obter_ajuda_formatos():
    return {
        "success": True,
        "data": {
            "voucher": "HR-YYYY-000001",
            "reserva": "RCF-YYYYMM-ABC123",
            "dica": "Você pode consultar pelo código do voucher (HR-...) ou código da reserva (RCF-...)"
        }
    }


@router.get("/consulta/{codigo}")
async def consultar_codigo_unificado(codigo: str):
    try:
        db = get_db()
        service = ConsultaPublicaService(db)
        resultado = await service.consultar_codigo_unificado(codigo)
        return {
            "success": True,
            "data": resultado
        }
    except HTTPException as e:
        if e.status_code == 404:
            codigo_upper = (codigo or "").upper().strip()
            sugestoes = [
                "Verifique se o código foi digitado corretamente",
                "Códigos de voucher têm formato HR-YYYY-000001",
                "Códigos de reserva geralmente começam com RCF-"
            ]

            if re.match(r'^HR-\d{4}-\d{6}$', codigo_upper):
                sugestoes.append("Se você tem o código da reserva, tente consultar pelo código RCF-...")

            return {
                "success": False,
                "mensagem": e.detail,
                "sugestoes": sugestoes
            }
        return {
            "success": False,
            "mensagem": e.detail,
            "sugestoes": ["Tente novamente em alguns instantes"]
        }
    except Exception:
        return {
            "success": False,
            "mensagem": "Erro ao consultar código",
            "sugestoes": ["Tente novamente em alguns instantes"]
        }


@router.get("/consulta/documento/{documento}")
async def consultar_por_documento(documento: str):
    try:
        db = get_db()
        service = ConsultaPublicaService(db)
        resultado = await service.buscar_por_documento(documento)
        return {
            "success": True,
            "data": resultado
        }
    except HTTPException as e:
        if e.status_code == 404:
            return {
                "success": False,
                "mensagem": e.detail
            }
        return {
            "success": False,
            "mensagem": e.detail
        }
    except Exception:
        return {
            "success": False,
            "mensagem": "Erro ao buscar reservas"
        }

@router.get("/quartos/disponiveis")
async def verificar_disponibilidade_quartos(
    data_checkin: str = Query(...),
    data_checkout: str = Query(...)
):
    """
    Verificar disponibilidade de quartos (API Pública)
    
    Não requer autenticação - usado para consulta pública
    """
    try:
        db = get_db()

        checkin_date = datetime.strptime(data_checkin, "%Y-%m-%d")
        checkout_date = datetime.strptime(data_checkout, "%Y-%m-%d")
        if checkout_date <= checkin_date:
            raise HTTPException(status_code=400, detail="Data de check-out deve ser posterior ao check-in")

        checkin_local = checkin_date.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=LOCAL_TIMEZONE)
        checkout_local = checkout_date.replace(hour=11, minute=0, second=0, microsecond=0, tzinfo=LOCAL_TIMEZONE)
        checkin_dt = to_utc(checkin_local)
        checkout_dt = to_utc(checkout_local)

        from app.services.disponibilidade_service import DisponibilidadeService
        disponibilidade_service = DisponibilidadeService(db)
        quartos_disponiveis = await disponibilidade_service.listar_quartos_disponiveis(
            checkin_dt,
            checkout_dt,
            None
        )

        num_diarias = (checkout_date.date() - checkin_date.date()).days


        tipos_index = {}
        for q in quartos_disponiveis:
            tipo = q.get("tipo_suite")
            if not tipo:
                continue
            tipos_index.setdefault(tipo, []).append({"numero": q.get("numero")})

        tipos_disponiveis = []
        total_quartos_disponiveis = 0
        for tipo, quartos in tipos_index.items():
            preco_diaria = await _obter_tarifa_diaria(db, tipo, checkin_date.date())
            quantidade = len(quartos)
            total_quartos_disponiveis += quantidade
            tipos_disponiveis.append({
                "tipo": tipo,
                "preco_diaria": preco_diaria,
                "preco_total": preco_diaria * num_diarias,
                "quantidade_disponivel": quantidade,
                "quartos": quartos
            })

        tipos_disponiveis.sort(key=lambda x: x["tipo"])

        return {
            "success": True,
            "data_checkin": data_checkin,
            "data_checkout": data_checkout,
            "num_diarias": num_diarias,
            "total_quartos_disponiveis": total_quartos_disponiveis,
            "tipos_disponiveis": tipos_disponiveis
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar disponibilidade: {str(e)}")

@router.get("/pontos/{cpf}")
async def consultar_pontos_cliente(cpf: str):
    """
    Consultar pontos de um cliente pelo CPF (API Pública)
    
    Não requer autenticação - usado para clientes consultarem seus pontos
    """
    try:
        db = get_db()
        cliente_repo = ClienteRepository(db)
        pontos_repo = PontosRepository(db)

        documento_limpo = ''.join(filter(str.isdigit, cpf))
        if len(documento_limpo) != 11:
            raise HTTPException(status_code=400, detail="CPF inválido")

        try:
            cliente = await cliente_repo.get_by_documento(documento_limpo)
        except ValueError:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        saldo_data = await pontos_repo.get_saldo(cliente["id"])
        historico_data = await pontos_repo.get_historico(cliente["id"], limit=10)

        historico_recente = []
        for t in (historico_data.get("transacoes") or [])[:5]:
            data_str = t.get("created_at")
            try:
                data_fmt = datetime.fromisoformat(data_str).strftime("%d/%m/%Y") if data_str else ""
            except Exception:
                data_fmt = ""
            historico_recente.append({
                "origem": t.get("motivo") or t.get("origem") or "Transação",
                "data": data_fmt,
                "tipo": t.get("tipo"),
                "pontos": t.get("pontos")
            })

        return {
            "success": True,
            "cliente": {
                "nome": cliente.get("nome_completo"),
                "documento": documento_limpo
            },
            "pontos": {
                "saldo": saldo_data.get("saldo", 0),
                "historico_recente": historico_recente,
                "total_transacoes": historico_data.get("total", 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar pontos: {str(e)}")

@router.post("/reservas")
async def criar_reserva_publica(reserva_data: ReservaPublicaCreate):
    """
    Criar reserva (API Pública)
    
    Não requer autenticação - criação simplificada de reservas
    """
    try:
        db = get_db()
        cliente_repo = ClienteRepository(db)
        reserva_repo = ReservaRepository(db)

        documento_limpo = ''.join(filter(str.isdigit, reserva_data.documento))
        telefone_limpo = ''.join(filter(str.isdigit, reserva_data.telefone))

        try:
            cliente = await cliente_repo.get_by_documento(documento_limpo)
        except ValueError:
            from app.schemas.cliente_schema import ClienteCreate
            cliente = await cliente_repo.create(
                ClienteCreate(
                    nome_completo=reserva_data.nome_completo,
                    documento=documento_limpo,
                    telefone=telefone_limpo,
                    email=reserva_data.email
                )
            )

        checkin_date = datetime.strptime(reserva_data.data_checkin, "%Y-%m-%d")
        checkout_date = datetime.strptime(reserva_data.data_checkout, "%Y-%m-%d")
        if checkout_date <= checkin_date:
            raise HTTPException(status_code=400, detail="Data de check-out deve ser posterior ao check-in")

        from app.core.validators import ReservaValidator
        ReservaValidator.validar_datas(checkin_date.date(), checkout_date.date())

        checkin_local = checkin_date.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=LOCAL_TIMEZONE)
        checkout_local = checkout_date.replace(hour=11, minute=0, second=0, microsecond=0, tzinfo=LOCAL_TIMEZONE)
        checkin_dt = to_utc(checkin_local)
        checkout_dt = to_utc(checkout_local)

        from app.services.disponibilidade_service import DisponibilidadeService
        disponibilidade_service = DisponibilidadeService(db)
        disponibilidade = await disponibilidade_service.verificar_disponibilidade(
            reserva_data.quarto_numero,
            checkin_dt,
            checkout_dt,
            None
        )
        if not disponibilidade.get("disponivel"):
            raise HTTPException(status_code=400, detail="Quarto não disponível para o período solicitado")

        valor_diaria = await _obter_tarifa_diaria(db, reserva_data.tipo_suite, checkin_date.date())

        num_diarias = (checkout_date.date() - checkin_date.date()).days

        from app.schemas.reserva_schema import ReservaCreate
        from app.schemas.quarto_schema import TipoSuite

        try:
            tipo_suite = TipoSuite(reserva_data.tipo_suite)
        except Exception:
            raise HTTPException(status_code=400, detail="Tipo de suíte inválido")

        reserva_criada = await reserva_repo.create(
            ReservaCreate(
                cliente_id=cliente["id"],
                quarto_numero=reserva_data.quarto_numero,
                tipo_suite=tipo_suite,
                checkin_previsto=checkin_dt,
                checkout_previsto=checkout_dt,
                valor_diaria=valor_diaria,
                num_diarias=num_diarias
            )
        )

        return {
            "success": True,
            "reserva": {
                "codigo": reserva_criada["codigo_reserva"],
                "status": reserva_criada["status"],
                "cliente": cliente.get("nome_completo"),
                "quarto": reserva_criada.get("quarto_numero"),
                "tipo_suite": reserva_criada.get("tipo_suite"),
                "checkin": reserva_criada.get("checkin_previsto"),
                "checkout": reserva_criada.get("checkout_previsto"),
                "num_diarias": reserva_criada.get("num_diarias"),
                "valor_diaria": float(reserva_criada.get("valor_diaria", 0.0)),
                "valor_total": float(reserva_criada.get("valor_total", 0.0)),
            },
            "instrucoes": {
                "checkin_horario": "12:00",
                "checkout_horario": "11:00",
                "documentos": "Apresente documento de identidade e CPF",
                "contato": "(22) 2648-5900 ou contato@hotelrealcabofrio.com.br"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar reserva: {str(e)}")

@router.get("/premios")
async def listar_premios_publicos():
    """
    Listar prêmios disponíveis (API Pública)
    
    Não requer autenticação - consulta pública de prêmios
    """
    try:
        raise HTTPException(status_code=410, detail="Endpoint indisponível")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar prêmios: {str(e)}")

@router.get("/status")
async def status_api():
    """
    Status da API (API Pública)
    
    Endpoint para verificar se a API está funcionando
    """
    return {
        "status": "online",
        "api": "Hotel Cabo Frio - API Pública",
        "version": "1.0.0",
        "timestamp": now_utc().isoformat(),
        "endpoints": [
            "/reservas/{codigo}",
            "/quartos/disponiveis",
            "/pontos/{cpf}",
            "/reservas",
            "/premios",
            "/status"
        ]
    }
