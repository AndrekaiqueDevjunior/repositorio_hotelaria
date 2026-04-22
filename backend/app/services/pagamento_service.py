from typing import Dict, Any, List
from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc
from fastapi import HTTPException
from app.schemas.pagamento_schema import PagamentoCreate, PagamentoResponse, CieloWebhook
from app.repositories.pagamento_repo import PagamentoRepository
from app.services.cielo_service import CieloAPI
from app.services.tef_service import TefService
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
        self.tef_service = TefService()

    async def _registrar_pagamento_tef_finalizado(
        self,
        reserva_id: int,
        valor: float,
        tef_response: Dict[str, Any],
    ) -> Dict[str, Any]:
        pagamento = await self.pagamento_repo.create(
            PagamentoCreate(
                reserva_id=reserva_id,
                valor=valor,
                metodo="tef",
            )
        )

        status = tef_response.get("status", "RECUSADO")
        pagamento_atualizado = await self.pagamento_repo.update_status(
            pagamento["id"],
            status,
            cielo_payment_id=tef_response.get("nsu"),
            url_pagamento=None,
            tef_autorizacao=tef_response.get("autorizacao"),
            tef_cupom_cliente=tef_response.get("cupom_cliente"),
            tef_cupom_estabelecimento=tef_response.get("cupom_estabelecimento"),
        )

        if status == "APROVADO" and self.reserva_repo:
            try:
                await self.reserva_repo.confirmar(reserva_id)
            except Exception as e:
                print(f"Erro ao confirmar reserva TEF: {e}")

        return pagamento_atualizado
    
    async def create(self, dados: PagamentoCreate) -> Dict[str, Any]:
        """Criar novo pagamento e processar com Cielo"""
        try:
            # Verificar se jÃ¡ existe pagamento para esta reserva
            pagamentos_existentes = await self.pagamento_repo.list_by_reserva(dados.reserva_id)
            
            # Se jÃ¡ existe pagamento PENDENTE ou PROCESSANDO, retornar erro
            for pg in pagamentos_existentes:
                status = getattr(pg, 'status', None) or getattr(pg, 'status_pagamento', None)
                if status in ["PENDENTE", "PROCESSANDO"]:
                    return {
                        "error": "JÃ¡ existe um pagamento em andamento para esta reserva",
                        "success": False,
                        "pagamento_id": pg.id,
                        "status": status
                    }
            
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
                        print(f"âœ… Voucher gerado automaticamente: {voucher['codigo']}")
                        
                        # Add a new line here to send a notification
                        print(f"âœ… Sending notification for voucher {voucher['codigo']}")
                    except Exception as e:
                        print(f"âš ï¸ Erro ao confirmar reserva/gerar voucher: {e}")
                
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
            
            elif dados.metodo == "tef":
                # TEF - TransferÃªncia EletrÃ´nica de Fundos
                tef_response = await self.tef_service.iniciar_pagamento(
                    valor=dados.valor,
                    reserva_id=dados.reserva_id
                )
                
                if tef_response.get("success"):
                    # Atualizar status baseado na resposta TEF
                    status = tef_response.get("status", "APROVADO")
                    pagamento_atualizado = await self.pagamento_repo.update_status(
                        pagamento["id"],
                        status,
                        cielo_payment_id=tef_response.get("nsu"),
                        url_pagamento=None,  # TEF nao tem URL
                        tef_autorizacao=tef_response.get("autorizacao"),
                        tef_cupom_cliente=tef_response.get("cupom_cliente"),
                        tef_cupom_estabelecimento=tef_response.get("cupom_estabelecimento")
                    )
                    
                    # Se aprovado, confirmar reserva
                    if status == "APROVADO" and self.reserva_repo:
                        try:
                            await self.reserva_repo.confirmar(dados.reserva_id)
                            # TODO: Gerar voucher se necessÃ¡rio
                        except Exception as e:
                            print(f"âš ï¸ Erro ao confirmar reserva TEF: {e}")
                    
                    return {
                        **pagamento_atualizado,
                        "success": True,
                        "autorizacao": tef_response.get("autorizacao"),
                        "nsu": tef_response.get("nsu"),
                        "cupom_cliente": tef_response.get("cupom_cliente"),
                        "cupom_estabelecimento": tef_response.get("cupom_estabelecimento"),
                        "message": tef_response.get("message")
                    }
                else:
                    # Pagamento recusado
                    pagamento_atualizado = await self.pagamento_repo.update_status(
                        pagamento["id"],
                        "RECUSADO"
                    )
                    return {
                        **pagamento_atualizado,
                        "success": False,
                        "error": tef_response.get("error", "Pagamento TEF recusado")
                    }
            
            return pagamento
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao processar pagamento: {str(e)}")

    async def iniciar_fluxo_tef(
        self,
        reserva_id: int,
        valor: float,
        function_id: int = 0,
        cupom_fiscal: str | None = None,
        data_fiscal: str | None = None,
        hora_fiscal: str | None = None,
        trn_additional_parameters: str | None = None,
        trn_init_parameters: str | None = None,
        session_parameters: str | None = None,
        defer_finish: bool = False,
        session_id: str | None = None,
    ) -> Dict[str, Any]:
        try:
            return await self.tef_service.iniciar_fluxo_interativo(
                valor=valor,
                reserva_id=reserva_id,
                function_id=function_id,
                cupom_fiscal=cupom_fiscal,
                data_fiscal=data_fiscal,
                hora_fiscal=hora_fiscal,
                trn_additional_parameters=trn_additional_parameters,
                trn_init_parameters=trn_init_parameters,
                session_parameters=session_parameters,
                defer_finish=defer_finish,
                session_id=session_id,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao iniciar fluxo TEF: {str(e)}")

    async def iniciar_fluxo_tef_funcao(
        self,
        function_id: int,
        valor: float | None = None,
        cupom_fiscal: str | None = None,
        data_fiscal: str | None = None,
        hora_fiscal: str | None = None,
        trn_additional_parameters: str | None = None,
        trn_init_parameters: str | None = None,
        session_parameters: str | None = None,
        cashier_operator: str | None = None,
        sitef_ip: str | None = None,
        store_id: str | None = None,
        terminal_id: str | None = None,
        justificativa: str | None = None,
        original_transaction_reference: Dict[str, Any] | None = None,
        defer_finish: bool = False,
        session_id: str | None = None,
    ) -> Dict[str, Any]:
        try:
            return await self.tef_service.iniciar_fluxo_interativo(
                valor=valor,
                reserva_id=None,
                function_id=function_id,
                cupom_fiscal=cupom_fiscal,
                data_fiscal=data_fiscal,
                hora_fiscal=hora_fiscal,
                trn_additional_parameters=trn_additional_parameters,
                trn_init_parameters=trn_init_parameters,
                session_parameters=session_parameters,
                cashier_operator=cashier_operator,
                sitef_ip=sitef_ip,
                store_id=store_id,
                terminal_id=terminal_id,
                justificativa=justificativa,
                original_transaction_reference=original_transaction_reference,
                defer_finish=defer_finish,
                session_id=session_id,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao iniciar funcao TEF: {str(e)}")

    async def continuar_fluxo_tef(self, session_id: str, continue_flag: int = 0, data: str = "") -> Dict[str, Any]:
        try:
            return await self.tef_service.continuar_fluxo_interativo(
                session_id=session_id,
                continue_flag=continue_flag,
                data=data,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao continuar fluxo TEF: {str(e)}")

    async def finalizar_fluxo_tef(
        self,
        reserva_id: int | None,
        valor: float | None,
        session_id: str,
        confirm: bool,
        param_adic: str | None = None,
    ) -> Dict[str, Any]:
        try:
            tef_response = await self.tef_service.finalizar_fluxo_interativo(
                session_id=session_id,
                confirm=confirm,
                param_adic=param_adic,
            )

            if not tef_response.get("finalizado"):
                return {
                    "success": False,
                    "error": tef_response.get("error") or "Fluxo TEF nao finalizado",
                }

            if reserva_id and valor is not None and tef_response.get("success"):
                pagamento_atualizado = await self._registrar_pagamento_tef_finalizado(
                    reserva_id=reserva_id,
                    valor=valor,
                    tef_response=tef_response,
                )
                return {
                    **pagamento_atualizado,
                    "success": True,
                    "autorizacao": tef_response.get("autorizacao"),
                    "nsu": tef_response.get("nsu"),
                    "nsu_sitef": tef_response.get("nsu_sitef"),
                    "nsu_host": tef_response.get("nsu_host"),
                    "rede_autorizadora": tef_response.get("rede_autorizadora"),
                    "bandeira": tef_response.get("bandeira"),
                    "codigo_estabelecimento": tef_response.get("codigo_estabelecimento"),
                    "data_hora_transacao": tef_response.get("data_hora_transacao"),
                    "cupom_cliente": tef_response.get("cupom_cliente"),
                    "cupom_estabelecimento": tef_response.get("cupom_estabelecimento"),
                    "tipo_campos": tef_response.get("tipo_campos", []),
                    "nfpag": tef_response.get("nfpag", {}),
                    "evento_atual": tef_response.get("evento_atual"),
                    "eventos": tef_response.get("eventos", []),
                    "reimpressao": tef_response.get("reimpressao"),
                    "referencia_reimpressao": tef_response.get("referencia_reimpressao"),
                    "message": tef_response.get("message"),
                }

            if reserva_id and valor is not None:
                pagamento_atualizado = await self._registrar_pagamento_tef_finalizado(
                    reserva_id=reserva_id,
                    valor=valor,
                    tef_response=tef_response,
                )
                return {
                    **pagamento_atualizado,
                    "success": False,
                    "error": tef_response.get("error") or tef_response.get("message") or "Pagamento TEF recusado",
                    "cupom_cliente": tef_response.get("cupom_cliente"),
                    "cupom_estabelecimento": tef_response.get("cupom_estabelecimento"),
                    "tipo_campos": tef_response.get("tipo_campos", []),
                    "nsu": tef_response.get("nsu"),
                    "nsu_sitef": tef_response.get("nsu_sitef"),
                    "nsu_host": tef_response.get("nsu_host"),
                    "rede_autorizadora": tef_response.get("rede_autorizadora"),
                    "bandeira": tef_response.get("bandeira"),
                    "codigo_estabelecimento": tef_response.get("codigo_estabelecimento"),
                    "data_hora_transacao": tef_response.get("data_hora_transacao"),
                    "autorizacao": tef_response.get("autorizacao"),
                    "nfpag": tef_response.get("nfpag", {}),
                    "evento_atual": tef_response.get("evento_atual"),
                    "eventos": tef_response.get("eventos", []),
                    "reimpressao": tef_response.get("reimpressao"),
                    "referencia_reimpressao": tef_response.get("referencia_reimpressao"),
                }

            return {
                **tef_response,
                "success": bool(tef_response.get("success")),
                "cupom_cliente": tef_response.get("cupom_cliente"),
                "cupom_estabelecimento": tef_response.get("cupom_estabelecimento"),
                "tipo_campos": tef_response.get("tipo_campos", []),
                "nsu": tef_response.get("nsu"),
                "nsu_sitef": tef_response.get("nsu_sitef"),
                "nsu_host": tef_response.get("nsu_host"),
                "rede_autorizadora": tef_response.get("rede_autorizadora"),
                "bandeira": tef_response.get("bandeira"),
                "codigo_estabelecimento": tef_response.get("codigo_estabelecimento"),
                "data_hora_transacao": tef_response.get("data_hora_transacao"),
                "autorizacao": tef_response.get("autorizacao"),
                "nfpag": tef_response.get("nfpag", {}),
                "evento_atual": tef_response.get("evento_atual"),
                "eventos": tef_response.get("eventos", []),
                "reimpressao": tef_response.get("reimpressao"),
                "referencia_reimpressao": tef_response.get("referencia_reimpressao"),
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao finalizar fluxo TEF: {str(e)}")

    async def cancelar_fluxo_tef(self, session_id: str) -> Dict[str, Any]:
        try:
            return await self.tef_service.cancelar_fluxo_interativo(session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao cancelar fluxo TEF: {str(e)}")

    async def limpar_sessao_tef(self) -> Dict[str, Any]:
        try:
            return await self.tef_service.limpar_sessao_interativa()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao limpar sessao TEF: {str(e)}")

    async def cancelar_pagamento_tef_nsu(self, nsu: str) -> Dict[str, Any]:
        try:
            resultado = await self.tef_service.cancelar_pagamento(nsu)
            if not resultado.get("success"):
                return resultado

            pagamento_atualizado = None
            try:
                pagamento = await self.pagamento_repo.get_by_payment_id(nsu)
                pagamento_atualizado = await self.pagamento_repo.update_status(pagamento["id"], "CANCELADO")
            except Exception:
                pagamento_atualizado = None

            return {
                **resultado,
                "pagamento": pagamento_atualizado
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao cancelar pagamento TEF: {str(e)}")

    async def resolver_pendencias_tef(self, confirmar: bool = True) -> Dict[str, Any]:
        try:
            return await self.tef_service.resolver_pendencias(confirmar=confirmar)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao resolver pendencias TEF: {str(e)}")
    
    async def get_by_id(self, pagamento_id: int) -> Dict[str, Any]:
        """Obter pagamento por ID"""
        try:
            return await self.pagamento_repo.get_by_id(pagamento_id)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Pagamento com ID {pagamento_id} nÃ£o encontrado"
            )
    
    async def get_by_payment_id(self, cielo_payment_id: str) -> Dict[str, Any]:
        """Obter pagamento pelo ID da Cielo"""
        try:
            return await self.pagamento_repo.get_by_payment_id(cielo_payment_id)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Pagamento com ID Cielo {cielo_payment_id} nÃ£o encontrado"
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
            
            # Enviar notificaÃ§Ã£o baseada no status
            try:
                from app.core.database import get_db
                db = next(get_db())
                
                # Obter dados completos da reserva para notificaÃ§Ã£o
                if self.reserva_repo:
                    reserva = await self.reserva_repo.get_by_id(pagamento["reserva_id"])
                    
                    if novo_status == "APROVADO":
                        await notificar_em_pagamento_aprovado(db, pagamento_atualizado, reserva)
                        print(f"[NOTIFICAÃ‡ÃƒO] Pagamento aprovado: R$ {pagamento_atualizado['valor']}")
                    else:
                        await notificar_em_pagamento_recusado(db, pagamento_atualizado, reserva)
                        print(f"[NOTIFICAÃ‡ÃƒO] Pagamento RECUSADO: R$ {pagamento_atualizado['valor']} - CRÃTICO")
                        
            except Exception as e:
                print(f"[NOTIFICAÃ‡ÃƒO] Erro ao notificar pagamento webhook: {e}")
            
            # Invalidar cache se necessÃ¡rio
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
                raise HTTPException(status_code=400, detail="Pagamento nÃ£o Ã© PIX")
            
            # Em sandbox, simular verificaÃ§Ã£o
            if self.cielo_api.mode == "sandbox":
                # Retornar status atual do banco
                return {
                    "pagamento_id": pagamento_id,
                    "status": pagamento["status"],
                    "paid": pagamento["status"] == "APROVADO"
                }
            
            # Em produÃ§Ã£o, consultar API Cielo
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
                detail=f"Pagamento com ID {pagamento_id} nÃ£o encontrado"
            )
    
    async def confirmar_pix_manual(self, pagamento_id: int) -> Dict[str, Any]:
        """Confirmar pagamento PIX manualmente (para testes em sandbox)"""
        try:
            pagamento = await self.pagamento_repo.get_by_id(pagamento_id)
            
            if pagamento["metodo"] != "pix":
                raise HTTPException(status_code=400, detail="Pagamento nÃ£o Ã© PIX")
            
            if pagamento["status"] != "AGUARDANDO_PAGAMENTO":
                raise HTTPException(status_code=400, detail="Pagamento nÃ£o estÃ¡ aguardando")
            
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
                    print(f"âœ… Voucher gerado automaticamente via PIX: {voucher['codigo']}")
                except Exception as e:
                    print(f"âš ï¸ Erro ao confirmar reserva/gerar voucher: {e}")
            
            return {
                **pagamento_atualizado,
                "success": True,
                "message": "PIX confirmado com sucesso"
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Pagamento com ID {pagamento_id} nÃ£o encontrado"
            )
    
    async def aprovar_pagamento(self, pagamento_id: int) -> Dict[str, Any]:
        """
        Aprovar pagamento manualmente e creditar pontos automaticamente.
        
        Este mÃ©todo:
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
                    "message": "Pagamento jÃ¡ estava aprovado"
                }
            
            if pagamento["status"] not in ["PENDENTE", "PROCESSANDO", "AGUARDANDO_PAGAMENTO"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Pagamento com status '{pagamento['status']}' nÃ£o pode ser aprovado"
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
            
            # Pontos sÃ£o creditados apenas no checkout via RealPointsService
            pagamento_atualizado["pontos_erro"] = "Pontos creditados apenas no checkout"
            
            return {
                **pagamento_atualizado,
                "success": True,
                "message": "Pagamento aprovado com sucesso"
            }
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    
# InstÃ¢ncia global para compatibilidade
_pagamento_service = None

async def get_pagamento_service() -> PagamentoService:
    """Factory para obter instÃ¢ncia do serviÃ§o"""
    global _pagamento_service
    if _pagamento_service is None:
        from app.core.database import get_db
        db = get_db()
        _pagamento_service = PagamentoService(PagamentoRepository(db))
    return _pagamento_service

# FunÃ§Ãµes de compatibilidade para migraÃ§Ã£o gradual
async def criar_pagamento(dados: PagamentoCreate):
    service = await get_pagamento_service()
    return await service.create(dados)

async def obter_pagamento(pagamento_id: int):
    service = await get_pagamento_service()
    return await service.get_by_id(pagamento_id)

async def listar_pagamentos_reserva(reserva_id: int):
    service = await get_pagamento_service()
    return await service.list_by_reserva(reserva_id)

