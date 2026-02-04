from typing import Dict, Any, List
from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc
from fastapi import HTTPException
from app.schemas.pagamento_schema import PagamentoCreate, PagamentoResponse, CieloWebhook
from app.repositories.pagamento_repo import PagamentoRepository
from app.services.cielo_service import CieloAPI
from app.utils.cache import cache_result, invalidate_cache_pattern
from app.services.integrate_notificacoes import (
    notificar_em_pagamento_aprovado,
    notificar_em_pagamento_recusado,
    notificar_em_pagamento_pendente
)


class PagamentoService:
    def __init__(self, pagamento_repo: PagamentoRepository, reserva_repo=None):
        self.pagamento_repo = pagamento_repo
        self.reserva_repo = reserva_repo
        self.cielo_api = CieloAPI()
    
    async def create(self, dados: PagamentoCreate) -> Dict[str, Any]:
        """Criar novo pagamento e processar com Cielo"""
        try:
            # Criar pagamento no banco
            pagamento = await self.pagamento_repo.create(dados)
            
            # Processar pagamento com Cielo
            if dados.metodo in ["credit_card", "debit_card"]:
                cielo_response = await self.cielo_api.criar_pagamento_cartao(
                    valor=dados.valor,
                    cartao_numero=dados.cartao_numero,
                    cartao_validade=dados.cartao_validade,
                    cartao_cvv=dados.cartao_cvv,
                    cartao_nome=dados.cartao_nome,
                    parcelas=dados.parcelas or 1
                )
                
                # Verificar se houve erro na Cielo
                if cielo_response.get("success") == False:
                    # Atualizar status para RECUSADO
                    pagamento_atualizado = await self.pagamento_repo.update_status(
                        pagamento["id"],
                        "RECUSADO"
                    )
                    return {
                        **pagamento_atualizado,
                        "error": cielo_response.get("error", "Erro ao processar pagamento"),
                        "success": False
                    }
                
                # Determinar status baseado na resposta da Cielo
                status = "APROVADO" if cielo_response.get("status") in ["AUTHORIZED", "CAPTURED"] else "PROCESSANDO"
                
                # Atualizar pagamento com ID da Cielo
                pagamento_atualizado = await self.pagamento_repo.update_status(
                    pagamento["id"],
                    status,
                    cielo_payment_id=cielo_response.get("payment_id"),
                    url_pagamento=cielo_response.get("url")
                )
                
                # Se pagamento aprovado, confirmar reserva e gerar voucher
                if status == "APROVADO" and self.reserva_repo:
                    try:
                        await self.reserva_repo.confirmar(dados.reserva_id)
                        
                        # Gerar voucher automaticamente
                        from app.services.voucher_service import gerar_voucher
                        voucher = await gerar_voucher(dados.reserva_id)
                        print(f"✅ Voucher gerado automaticamente: {voucher['codigo']}")
                        
                        # Add a new line here to send a notification
                        print(f"✅ Sending notification for voucher {voucher['codigo']}")
                    except Exception as e:
                        print(f"⚠️ Erro ao confirmar reserva/gerar voucher: {e}")
                
                return {
                    **pagamento_atualizado,
                    "success": True
                }
            
            elif dados.metodo == "pix":
                # Gerar PIX
                pix_response = await self.cielo_api.gerar_pix(
                    valor=dados.valor,
                    descricao=f"Pagamento reserva #{dados.reserva_id}"
                )
                
                if pix_response.get("success") == False:
                    return {
                        **pagamento,
                        "error": pix_response.get("error", "Erro ao gerar PIX"),
                        "success": False
                    }
                
                pagamento_atualizado = await self.pagamento_repo.update_status(
                    pagamento["id"],
                    "AGUARDANDO_PAGAMENTO",
                    cielo_payment_id=pix_response.get("txid"),
                    url_pagamento=pix_response.get("qr_code")
                )
                
                # Retornar com dados do QR Code
                return {
                    **pagamento_atualizado,
                    "success": True,
                    "qr_code": pix_response.get("qr_code"),
                    "qr_code_base64": pix_response.get("qr_code_base64"),
                    "txid": pix_response.get("txid"),
                    "expiration": pix_response.get("expiration")
                }
            
            return pagamento
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao processar pagamento: {str(e)}")
    
    async def get_by_id(self, pagamento_id: int) -> Dict[str, Any]:
        """Obter pagamento por ID"""
        try:
            return await self.pagamento_repo.get_by_id(pagamento_id)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Pagamento com ID {pagamento_id} não encontrado"
            )
    
    async def get_by_payment_id(self, cielo_payment_id: str) -> Dict[str, Any]:
        """Obter pagamento pelo ID da Cielo"""
        try:
            return await self.pagamento_repo.get_by_payment_id(cielo_payment_id)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Pagamento com ID Cielo {cielo_payment_id} não encontrado"
            )
    
    async def process_webhook(self, webhook_data: CieloWebhook) -> Dict[str, Any]:
        """Processar webhook da Cielo"""
        try:
            pagamento = await self.pagamento_repo.get_by_payment_id(webhook_data.payment_id)
            
            # Atualizar status baseado no webhook
            novo_status = "APROVADO" if webhook_data.status == "APPROVED" else "RECUSADO"
            
            pagamento_atualizado = await self.pagamento_repo.update_status(
                pagamento["id"],
                novo_status
            )
            
            # Enviar notificação baseada no status
            try:
                from app.core.database import get_db
                db = next(get_db())
                
                # Obter dados completos da reserva para notificação
                if self.reserva_repo:
                    reserva = await self.reserva_repo.get_by_id(pagamento["reserva_id"])
                    
                    if novo_status == "APROVADO":
                        await notificar_em_pagamento_aprovado(db, pagamento_atualizado, reserva)
                        print(f"[NOTIFICAÇÃO] Pagamento aprovado: R$ {pagamento_atualizado['valor']}")
                    else:
                        await notificar_em_pagamento_recusado(db, pagamento_atualizado, reserva)
                        print(f"[NOTIFICAÇÃO] Pagamento RECUSADO: R$ {pagamento_atualizado['valor']} - CRÍTICO")
                        
            except Exception as e:
                print(f"[NOTIFICAÇÃO] Erro ao notificar pagamento webhook: {e}")
            
            # Invalidar cache se necessário
            invalidate_cache_pattern(f"reserva:{pagamento['reserva_id']}")
            
            return pagamento_atualizado
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    
    async def list_by_reserva(self, reserva_id: int) -> List[Dict[str, Any]]:
        """Listar pagamentos de uma reserva"""
        return await self.pagamento_repo.list_by_reserva(reserva_id)

    async def list_all(self) -> Dict[str, Any]:
        """Listar todos os pagamentos"""
        registros = await self.pagamento_repo.list_all()
        return {
            "total": len(registros),
            "pagamentos": registros
        }
    
    async def verificar_status_pix(self, pagamento_id: int) -> Dict[str, Any]:
        """Verificar status de pagamento PIX"""
        try:
            pagamento = await self.pagamento_repo.get_by_id(pagamento_id)
            
            if pagamento["metodo"] != "pix":
                raise HTTPException(status_code=400, detail="Pagamento não é PIX")
            
            # Em sandbox, simular verificação
            if self.cielo_api.mode == "sandbox":
                # Retornar status atual do banco
                return {
                    "pagamento_id": pagamento_id,
                    "status": pagamento["status"],
                    "paid": pagamento["status"] == "APROVADO"
                }
            
            # Em produção, consultar API Cielo
            cielo_payment_id = pagamento.get("cielo_payment_id")
            if cielo_payment_id:
                cielo_status = self.cielo_api.consultar_pagamento(cielo_payment_id)
                if cielo_status.get("success") and cielo_status.get("data"):
                    status_code = cielo_status["data"].get("Status")
                    if status_code == 2:  # Capturado/Pago
                        await self.pagamento_repo.update_status(pagamento_id, "APROVADO")
                        return {
                            "pagamento_id": pagamento_id,
                            "status": "APROVADO",
                            "paid": True
                        }
            
            return {
                "pagamento_id": pagamento_id,
                "status": pagamento["status"],
                "paid": False
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Pagamento com ID {pagamento_id} não encontrado"
            )
    
    async def confirmar_pix_manual(self, pagamento_id: int) -> Dict[str, Any]:
        """Confirmar pagamento PIX manualmente (para testes em sandbox)"""
        try:
            pagamento = await self.pagamento_repo.get_by_id(pagamento_id)
            
            if pagamento["metodo"] != "pix":
                raise HTTPException(status_code=400, detail="Pagamento não é PIX")
            
            if pagamento["status"] != "AGUARDANDO_PAGAMENTO":
                raise HTTPException(status_code=400, detail="Pagamento não está aguardando")
            
            # Atualizar para APROVADO
            pagamento_atualizado = await self.pagamento_repo.update_status(
                pagamento_id,
                "APROVADO"
            )
            
            # Confirmar reserva e gerar voucher
            if self.reserva_repo:
                try:
                    await self.reserva_repo.confirmar(pagamento["reserva_id"])
                    
                    # Gerar voucher automaticamente
                    from app.services.voucher_service import gerar_voucher
                    voucher = await gerar_voucher(pagamento["reserva_id"])
                    print(f"✅ Voucher gerado automaticamente via PIX: {voucher['codigo']}")
                except Exception as e:
                    print(f"⚠️ Erro ao confirmar reserva/gerar voucher: {e}")
            
            return {
                **pagamento_atualizado,
                "success": True,
                "message": "PIX confirmado com sucesso"
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Pagamento com ID {pagamento_id} não encontrado"
            )
    
    async def aprovar_pagamento(self, pagamento_id: int) -> Dict[str, Any]:
        """
        Aprovar pagamento manualmente e creditar pontos automaticamente.
        
        Este método:
        1. Atualiza o status do pagamento para APROVADO
        2. Confirma a reserva associada
        3. Credita pontos de fidelidade ao cliente (1 ponto por R$ 10)
        4. Gera voucher automaticamente
        """
        try:
            pagamento = await self.pagamento_repo.get_by_id(pagamento_id)
            
            # Validar se pode aprovar
            if pagamento["status"] == "APROVADO":
                return {
                    **pagamento,
                    "success": True,
                    "message": "Pagamento já estava aprovado"
                }
            
            if pagamento["status"] not in ["PENDENTE", "PROCESSANDO", "AGUARDANDO_PAGAMENTO"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Pagamento com status '{pagamento['status']}' não pode ser aprovado"
                )
            
            # Atualizar status para APROVADO
            pagamento_atualizado = await self.pagamento_repo.update_status(
                pagamento_id,
                "APROVADO"
            )
            
            # Confirmar reserva e gerar voucher
            reserva_id = pagamento["reserva_id"]
            if self.reserva_repo:
                try:
                    await self.reserva_repo.confirmar(reserva_id)
                    
                    # Gerar voucher automaticamente
                    from app.services.voucher_service import gerar_voucher
                    voucher = await gerar_voucher(reserva_id)
                    print(f"[APROVAR] Voucher gerado: {voucher['codigo']}")
                except Exception as e:
                    print(f"[APROVAR] Erro ao confirmar reserva/gerar voucher: {e}")
            
            # CREDITAR PONTOS AUTOMATICAMENTE
            try:
                pontos_creditados = await self._creditar_pontos_pagamento(
                    pagamento_id=pagamento_id,
                    cliente_id=pagamento["cliente_id"],
                    reserva_id=reserva_id,
                    valor=pagamento["valor"]
                )
                pagamento_atualizado["pontos_creditados"] = pontos_creditados
                print(f"[APROVAR] Pontos creditados: {pontos_creditados}")
            except Exception as e:
                print(f"[APROVAR] Erro ao creditar pontos: {e}")
                pagamento_atualizado["pontos_erro"] = str(e)
            
            return {
                **pagamento_atualizado,
                "success": True,
                "message": "Pagamento aprovado com sucesso"
            }
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    
    async def _creditar_pontos_pagamento(
        self, 
        pagamento_id: int,
        cliente_id: int, 
        reserva_id: int, 
        valor: float
    ) -> int:
        """
        Creditar pontos de fidelidade após pagamento aprovado.
        
        Regra: 1 ponto para cada R$ 10,00 gastos
        
        Proteção contra duplicação: Verifica se já existe transação de pontos
        para este pagamento antes de creditar.
        """
        from app.core.database import get_db
        from app.repositories.pontos_repo import PontosRepository
        from app.services.pontos_service import PontosService
        
        db = get_db()
        
        # Verificar se já creditou pontos para este pagamento
        transacao_existente = await db.transacaopontos.find_first(
            where={
                "reservaId": reserva_id,
                "origem": "PAGAMENTO",
                "tipo": "CREDITO"
            }
        )
        
        if transacao_existente:
            print(f"[PONTOS] Já creditado para reserva {reserva_id} - pulando")
            return getattr(transacao_existente, 'pontos', 0)
        
        # Calcular pontos usando método centralizado
        pontos = PontosService.calcular_pontos_reserva(valor)
        
        if pontos <= 0:
            print(f"[PONTOS] Valor R$ {valor:.2f} não gera pontos")
            return 0
        
        # Creditar pontos
        pontos_repo = PontosRepository(db)
        result = await pontos_repo.criar_transacao_pontos(
            cliente_id=cliente_id,
            pontos=pontos,
            tipo="CREDITO",
            origem="PAGAMENTO",
            motivo=f"Pagamento aprovado - Reserva #{reserva_id} - R$ {valor:.2f}",
            reserva_id=reserva_id,
            funcionario_id=None
        )
        
        if result.get("success"):
            print(f"[PONTOS] Creditado {pontos} pontos para cliente {cliente_id}")
            return pontos
        else:
            raise Exception(f"Falha ao creditar pontos: {result}")
    
    async def cancelar_pagamento(self, pagamento_id: int) -> Dict[str, Any]:
        """Cancelar pagamento"""
        try:
            pagamento = await self.pagamento_repo.get_by_id(pagamento_id)
            
            if pagamento["status"] not in ["PENDENTE", "PROCESSANDO"]:
                raise HTTPException(status_code=400, detail="Pagamento não pode ser cancelado")
            
            # Cancelar na Cielo se tiver payment_id
            if pagamento["cielo_payment_id"]:
                await self.cielo_api.cancelar_pagamento(pagamento["cielo_payment_id"])
            
            # Atualizar status
            pagamento_atualizado = await self.pagamento_repo.update_status(
                pagamento_id,
                "CANCELADO"
            )
            
            return pagamento_atualizado
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))


# Instância global para compatibilidade
_pagamento_service = None

async def get_pagamento_service() -> PagamentoService:
    """Factory para obter instância do serviço"""
    global _pagamento_service
    if _pagamento_service is None:
        from app.core.database import get_db
        db = get_db()
        _pagamento_service = PagamentoService(PagamentoRepository(db))
    return _pagamento_service

# Funções de compatibilidade para migração gradual
async def criar_pagamento(dados: PagamentoCreate):
    service = await get_pagamento_service()
    return await service.create(dados)

async def obter_pagamento(pagamento_id: int):
    service = await get_pagamento_service()
    return await service.get_by_id(pagamento_id)

async def listar_pagamentos_reserva(reserva_id: int):
    service = await get_pagamento_service()
    return await service.list_by_reserva(reserva_id)