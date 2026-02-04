"""
Serviço de Transições Automáticas de Estado
==========================================
Implementa as transições automáticas que estavam faltando nos repositórios
Usa a máquina de estados existente (state_machine_service.py)
"""
from typing import Dict, Any, Optional
from datetime import datetime
from prisma import Client

from app.core.unified_state_validator import UnifiedStateValidator
from app.schemas.status_enums import StatusReserva, StatusPagamento, StatusHospedagem
from app.utils.datetime_utils import now_utc


class StateTransitionService:
    """
    Serviço central para executar transições automáticas de estado
    Integrado com os repositórios para garantir consistência
    """
    
    def __init__(self, db: Client):
        self.db = db
        self.validator = UnifiedStateValidator()
    
    async def transicao_apos_criacao_pagamento(self, pagamento_id: int) -> Dict[str, Any]:
        """
        Executa transição automática após criação de pagamento
        PENDENTE → AGUARDANDO_COMPROVANTE (se balcão)
        """
        # Buscar pagamento e reserva
        pagamento = await self.db.pagamento.find_unique(
            where={"id": pagamento_id},
            include={"reserva": True}
        )
        
        if not pagamento or not pagamento.reserva:
            return {"success": False, "error": "Pagamento ou reserva não encontrada"}
        
        reserva = pagamento.reserva
        
        # Se pagamento é balcão, mudar reserva para AGUARDANDO_COMPROVANTE
        if pagamento.metodo == "BALCAO" and reserva.statusReserva == StatusReserva.PENDENTE.value:
            await self.db.reserva.update(
                where={"id": reserva.id},
                data={"statusReserva": StatusReserva.AGUARDANDO_COMPROVANTE.value}
            )
            
            return {
                "success": True,
                "transicao": "PENDENTE → AGUARDANDO_COMPROVANTE",
                "motivo": "Pagamento balcão criado, aguardando comprovante",
                "reserva_id": reserva.id,
                "novo_status": StatusReserva.AGUARDANDO_COMPROVANTE.value
            }
        
        # Se pagamento online, poderia já confirmar (implementação futura)
        if pagamento.metodo in ["CARTAO", "PIX"] and reserva.statusReserva == StatusReserva.PENDENTE.value:
            await self.db.reserva.update(
                where={"id": reserva.id},
                data={"statusReserva": StatusReserva.EM_ANALISE.value}
            )
            
            return {
                "success": True,
                "transicao": "PENDENTE → EM_ANALISE",
                "motivo": "Pagamento online criado, aguardando processamento",
                "reserva_id": reserva.id,
                "novo_status": StatusReserva.EM_ANALISE.value
            }
        
        return {"success": True, "transicao": "Nenhuma transição necessária"}
    
    async def transicao_apos_upload_comprovante(self, pagamento_id: int) -> Dict[str, Any]:
        """
        Executa transição automática após upload de comprovante
        AGUARDANDO_COMPROVANTE → EM_ANALISE
        """
        # Buscar pagamento e reserva
        pagamento = await self.db.pagamento.find_unique(
            where={"id": pagamento_id},
            include={"reserva": True}
        )
        
        if not pagamento or not pagamento.reserva:
            return {"success": False, "error": "Pagamento ou reserva não encontrada"}
        
        reserva = pagamento.reserva
        
        # Mudar reserva para EM_ANALISE após upload
        if reserva.statusReserva == StatusReserva.AGUARDANDO_COMPROVANTE.value:
            await self.db.reserva.update(
                where={"id": reserva.id},
                data={"statusReserva": StatusReserva.EM_ANALISE.value}
            )
            
            return {
                "success": True,
                "transicao": "AGUARDANDO_COMPROVANTE → EM_ANALISE",
                "motivo": "Comprovante enviado, aguardando validação",
                "reserva_id": reserva.id,
                "novo_status": StatusReserva.EM_ANALISE.value
            }
        
        return {"success": True, "transicao": "Nenhuma transição necessária"}
    
    async def transicao_apos_aprovacao_pagamento(self, pagamento_id: int, usuario_id: int) -> Dict[str, Any]:
        """
        Executa transição automática após aprovação de pagamento
        EM_ANALISE → CONFIRMADA + criar hospedagem
        """
        # Buscar pagamento e reserva
        pagamento = await self.db.pagamento.find_unique(
            where={"id": pagamento_id},
            include={"reserva": True}
        )
        
        if not pagamento or not pagamento.reserva:
            return {"success": False, "error": "Pagamento ou reserva não encontrada"}
        
        reserva = pagamento.reserva
        
        # Validar se pode confirmar
        reserva_dict = {
            'id': reserva.id,
            'status': reserva.statusReserva,
            'codigo_reserva': reserva.codigoReserva,
            'cliente_id': reserva.clienteId,
            'valor_total': float(reserva.valorDiaria) * reserva.numDiarias if reserva.valorDiaria and reserva.numDiarias else 0
        }
        
        pagamento_dict = {
            'id': pagamento.id,
            'status': pagamento.statusPagamento,
            'valor': float(pagamento.valor) if pagamento.valor else 0,
            'metodo': pagamento.metodo
        }
        
        pode, motivo = self.validator.pode_confirmar_pagamento(reserva_dict, pagamento_dict)
        
        if not pode:
            return {"success": False, "error": f"Não pode confirmar: {motivo}"}
        
        # Mudar reserva para CONFIRMADA
        await self.db.reserva.update(
            where={"id": reserva.id},
            data={"statusReserva": StatusReserva.CONFIRMADA.value}
        )
        
        # Criar hospedagem se não existir
        hospedagem = await self.db.hospedagem.find_unique(
            where={"reservaId": reserva.id}
        )
        
        if not hospedagem:
            await self.db.hospedagem.create(
                data={
                    "reservaId": reserva.id,
                    "statusHospedagem": StatusHospedagem.NAO_INICIADA.value
                }
            )
            
            hospedagem_criada = True
        else:
            hospedagem_criada = False
        
        return {
            "success": True,
            "transicao": "EM_ANALISE → CONFIRMADA",
            "motivo": "Pagamento aprovado, reserva confirmada para check-in",
            "reserva_id": reserva.id,
            "novo_status": StatusReserva.CONFIRMADA.value,
            "hospedagem_criada": hospedagem_criada,
            "hospedagem_status": StatusHospedagem.NAO_INICIADA.value
        }
    
    async def transicao_apos_recusa_pagamento(self, pagamento_id: int, usuario_id: int) -> Dict[str, Any]:
        """
        Executa transição automática após recusa de pagamento
        EM_ANALISE → PAGA_REJEITADA
        """
        # Buscar pagamento e reserva
        pagamento = await self.db.pagamento.find_unique(
            where={"id": pagamento_id},
            include={"reserva": True}
        )
        
        if not pagamento or not pagamento.reserva:
            return {"success": False, "error": "Pagamento ou reserva não encontrada"}
        
        reserva = pagamento.reserva
        
        # Mudar reserva para PAGA_REJEITADA
        await self.db.reserva.update(
            where={"id": reserva.id},
            data={"statusReserva": StatusReserva.PAGA_REJEITADA.value}
        )
        
        return {
            "success": True,
            "transicao": "EM_ANALISE → PAGA_REJEITADA",
            "motivo": "Comprovante recusado, pagamento negado",
            "reserva_id": reserva.id,
            "novo_status": StatusReserva.PAGA_REJEITADA.value
        }
    
    async def transicao_apos_checkin(self, reserva_id: int, usuario_id: int) -> Dict[str, Any]:
        """
        Executa transição automática após check-in
        CONFIRMADA → HOSPEDADO
        """
        # Buscar reserva
        reserva = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include={"hospedagem": True}
        )
        
        if not reserva:
            return {"success": False, "error": "Reserva não encontrada"}
        
        # Validar se pode fazer check-in
        pagamentos = await self.db.pagamento.find_many(
            where={"reservaId": reserva_id}
        )
        
        reserva_dict = {
            'id': reserva.id,
            'status': reserva.statusReserva,
            'codigo_reserva': reserva.codigoReserva
        }
        
        pagamentos_dict = [{
            'id': p.id,
            'status': p.statusPagamento,
            'valor': float(p.valor) if p.valor else 0,
            'created_at': p.createdAt.isoformat() if p.createdAt else None
        } for p in pagamentos]
        
        hospedagem_dict = None
        if reserva.hospedagem:
            hospedagem_dict = {
                'id': reserva.hospedagem.id,
                'status': reserva.hospedagem.statusHospedagem
            }
        
        pode, motivo = self.validator.pode_fazer_checkin(
            reserva_dict, pagamentos_dict, hospedagem_dict
        )
        
        if not pode:
            return {"success": False, "error": f"Não pode fazer check-in: {motivo}"}
        
        # Mudar reserva para HOSPEDADO
        await self.db.reserva.update(
            where={"id": reserva_id},
            data={
                "statusReserva": StatusReserva.HOSPEDADO.value,
                "checkinReal": now_utc()
            }
        )
        
        # Mudar hospedagem para CHECKIN_REALIZADO
        if reserva.hospedagem:
            await self.db.hospedagem.update(
                where={"reservaId": reserva_id},
                data={
                    "statusHospedagem": StatusHospedagem.CHECKIN_REALIZADO.value,
                    "checkinRealizadoEm": now_utc(),
                    "checkinRealizadoPor": usuario_id
                }
            )
        
        return {
            "success": True,
            "transicao": "CONFIRMADA → HOSPEDADO",
            "motivo": "Check-in realizado, hóspede no hotel",
            "reserva_id": reserva_id,
            "novo_status": StatusReserva.HOSPEDADO.value,
            "hospedagem_status": StatusHospedagem.CHECKIN_REALIZADO.value
        }
    
    async def transicao_apos_checkout(self, reserva_id: int, usuario_id: int) -> Dict[str, Any]:
        """
        Executa transição automática após checkout
        HOSPEDADO → CHECKED_OUT
        """
        # Buscar reserva
        reserva = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include={"hospedagem": True}
        )
        
        if not reserva:
            return {"success": False, "error": "Reserva não encontrada"}
        
        # Validar se pode fazer checkout
        if not reserva.hospedagem:
            return {"success": False, "error": "Hospedagem não encontrada"}
        
        hospedagem_dict = {
            'id': reserva.hospedagem.id,
            'status': reserva.hospedagem.statusHospedagem
        }
        
        pode, motivo = self.validator.pode_fazer_checkout(hospedagem_dict)
        
        if not pode:
            return {"success": False, "error": f"Não pode fazer checkout: {motivo}"}
        
        # Mudar reserva para CHECKED_OUT
        await self.db.reserva.update(
            where={"id": reserva_id},
            data={
                "statusReserva": StatusReserva.CHECKED_OUT.value,
                "checkoutReal": now_utc()
            }
        )
        
        # Mudar hospedagem para CHECKOUT_REALIZADO
        await self.db.hospedagem.update(
            where={"reservaId": reserva_id},
            data={
                "statusHospedagem": StatusHospedagem.CHECKOUT_REALIZADO.value,
                "checkoutRealizadoEm": now_utc(),
                "checkoutRealizadoPor": usuario_id
            }
        )
        
        return {
            "success": True,
            "transicao": "HOSPEDADO → CHECKED_OUT",
            "motivo": "Check-out realizado, hospedagem finalizada",
            "reserva_id": reserva_id,
            "novo_status": StatusReserva.CHECKED_OUT.value,
            "hospedagem_status": StatusHospedagem.CHECKOUT_REALIZADO.value
        }
    
    async def diagnosticar_reserva(self, reserva_id: int) -> Dict[str, Any]:
        """
        Diagnostica o estado atual da reserva e identifica problemas
        """
        # Buscar dados completos
        reserva = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include={
                "pagamentos": True,
                "hospedagem": True
            }
        )
        
        if not reserva:
            return {"error": "Reserva não encontrada"}
        
        # Converter para dicionários
        reserva_dict = {
            'id': reserva.id,
            'status': reserva.statusReserva,
            'codigo_reserva': reserva.codigoReserva,
            'cliente_id': reserva.clienteId,
            'valor_total': float(reserva.valorDiaria) * reserva.numDiarias if reserva.valorDiaria and reserva.numDiarias else 0
        }
        
        pagamentos_dict = [{
            'id': p.id,
            'status': p.statusPagamento,
            'valor': float(p.valor) if p.valor else 0,
            'created_at': p.createdAt.isoformat() if p.createdAt else None
        } for p in reserva.pagamentos]
        
        hospedagem_dict = None
        if reserva.hospedagem:
            hospedagem_dict = {
                'id': reserva.hospedagem.id,
                'status': reserva.hospedagem.statusHospedagem
            }
        
        # Usar validador unificado
        diagnostico = self.validator.validar_fluxo_completo(
            reserva_dict,
            pagamentos_dict,
            hospedagem_dict
        )
        
        return {
            "reserva_id": reserva_id,
            "codigo_reserva": reserva.codigoReserva,
            "status_atual": reserva.statusReserva,
            "diagnostico": diagnostico,
            "recomendacoes": self._gerar_recomendacoes(diagnostico)
        }
    
    def _gerar_recomendacoes(self, diagnostico: dict) -> list:
        """Gera recomendações baseadas no diagnóstico"""
        recomendacoes = []
        
        problemas = diagnostico.get("problemas", [])
        fluxo = diagnostico.get("fluxo_atual", "")
        
        if "Pagamento aprovado mas reserva não confirmada" in problemas:
            recomendacoes.append("Executar transição para CONFIRMADA")
        
        if fluxo == "PAGAMENTO_APROVADO_AGUARDANDO_CONFIRMACAO":
            recomendacoes.append("Confirmar reserva para liberar check-in")
        
        if fluxo == "RESERVA_CONFIRMADA_AGUARDANDO_CHECKIN":
            recomendacoes.append("Realizar check-in do hóspede")
        
        if not problemas and fluxo in ["RESERVA_CONFIRMADA_AGUARDANDO_CHECKIN", "HOSPEDAGEM_EM_ANDAMENTO"]:
            recomendacoes.append("Fluxo normal, nenhuma ação necessária")
        
        return recomendacoes
