"""
VALIDADOR UNIFICADO DE ESTADOS
================================
Fonte única da verdade para todas as transições do sistema
Substitui: core/state_validators.py + integra com schemas/status_enums.py
"""

from typing import Tuple, Optional
from datetime import datetime
from app.schemas.status_enums import (
    StatusReserva, StatusPagamento, StatusHospedagem,
    pode_fazer_checkin, pode_fazer_checkout, pode_confirmar_reserva
)
from app.utils.datetime_utils import now_utc


class UnifiedStateValidator:
    """
    Validador centralizado para todas as transições de estado
    Garante consistência entre frontend e backend
    """
    
    # ==================== ESTADOS PADRONIZADOS ====================
    
    @staticmethod
    def get_estados_reserva():
        """Retorna estados válidos de reserva (padrão frontend)"""
        return {
            StatusReserva.PENDENTE.value: "Aguardando Pagamento",
            StatusReserva.CONFIRMADA.value: "Reserva Confirmada", 
            StatusReserva.CANCELADO.value: "Reserva Cancelada",
            StatusReserva.NO_SHOW.value: "Cliente Não Compareceu"
        }
    
    @staticmethod
    def get_estados_pagamento():
        """Retorna estados válidos de pagamento"""
        return {
            StatusPagamento.PENDENTE.value: "Pendente",
            StatusPagamento.CONFIRMADO.value: "Confirmado",
            StatusPagamento.NEGADO.value: "Negado",
            StatusPagamento.ESTORNADO.value: "Estornado"
        }
    
    @staticmethod
    def get_estados_hospedagem():
        """Retorna estados válidos de hospedagem"""
        return {
            "NAO_INICIADA": "Aguardando Check-in",
            "CHECKIN_REALIZADO": "Hóspede no Hotel",
            "CHECKOUT_REALIZADO": "Check-out Realizado",
            "ENCERRADA": "Hospedagem Encerrada"
        }
    
    # ==================== FLUXO COMPLETO ====================
    
    @staticmethod
    def validar_fluxo_completo(reserva, pagamentos, hospedagem=None) -> dict:
        """
        Valida o estado completo do fluxo de reserva
        Retorna diagnóstico do fluxo atual
        """
        status_reserva = reserva.get('status', StatusReserva.PENDENTE.value)
        status_pagamento = None
        status_hospedagem = hospedagem.get('status') if hospedagem else "NAO_INICIADA"
        
        # Determinar status do pagamento mais recente
        if pagamentos:
            pagamento_recente = max(pagamentos, key=lambda p: p.get('created_at', ''))
            status_pagamento = pagamento_recente.get('status', StatusPagamento.PENDENTE.value)
        
        # Validações do fluxo
        validacoes = {
            "fluxo_atual": UnifiedStateValidator._identificar_fluxo(status_reserva, status_pagamento, status_hospedagem),
            "proximas_acoes": UnifiedStateValidator._acoes_disponiveis(status_reserva, status_pagamento, status_hospedagem),
            "problemas": UnifiedStateValidator._identificar_problemas(status_reserva, status_pagamento, status_hospedagem),
            "estado_normal": UnifiedStateValidator._estado_esperado(status_reserva, status_pagamento)
        }
        
        return validacoes
    
    @staticmethod
    def _identificar_fluxo(status_reserva, status_pagamento, status_hospedagem):
        """Identifica em qual fase do fluxo está"""
        if status_reserva == StatusReserva.PENDENTE.value:
            if not status_pagamento or status_pagamento == StatusPagamento.PENDENTE.value:
                return "AGUARDANDO_PAGAMENTO"
            elif status_pagamento == StatusPagamento.NEGADO.value:
                return "PAGAMENTO_NEGADO"
            elif status_pagamento in [StatusPagamento.CONFIRMADO.value, StatusPagamento.CONFIRMADO.value]:
                return "PAGAMENTO_APROVADO_AGUARDANDO_CONFIRMACAO"
        
        elif status_reserva == StatusReserva.CONFIRMADA.value:
            if status_hospedagem == "NAO_INICIADA":
                return "RESERVA_CONFIRMADA_AGUARDANDO_CHECKIN"
            elif status_hospedagem == "CHECKIN_REALIZADO":
                return "HOSPEDAGEM_EM_ANDAMENTO"
            elif status_hospedagem == "CHECKOUT_REALIZADO":
                return "HOSPEDAGEM_FINALIZADA"
        
        elif status_reserva == StatusReserva.CANCELADO.value:
            return "RESERVA_CANCELADA"
        
        elif status_reserva == StatusReserva.NO_SHOW.value:
            return "CLIENTE_NAO_COMPARECEU"
        
        return "ESTADO_DESCONHECIDO"
    
    @staticmethod
    def _acoes_disponiveis(status_reserva, status_pagamento, status_hospedagem):
        """Retorna ações disponíveis no estado atual"""
        acoes = []
        
        fluxo = UnifiedStateValidator._identificar_fluxo(status_reserva, status_pagamento, status_hospedagem)
        
        if fluxo == "AGUARDANDO_PAGAMENTO":
            acoes = ["PAGAR", "CANCELAR"]
        elif fluxo == "PAGAMENTO_NEGADO":
            acoes = ["TENTAR_NOVAMENTE", "CANCELAR"]
        elif fluxo == "PAGAMENTO_APROVADO_AGUARDANDO_CONFIRMACAO":
            acoes = ["CONFIRMAR_RESERVA"]
        elif fluxo == "RESERVA_CONFIRMADA_AGUARDANDO_CHECKIN":
            acoes = ["FAZER_CHECKIN", "CANCELAR"]
        elif fluxo == "HOSPEDAGEM_EM_ANDAMENTO":
            acoes = ["FAZER_CHECKOUT", "REGISTRAR_CONSUMO"]
        elif fluxo == "HOSPEDAGEM_FINALIZADA":
            acoes = ["GERAR_RELATORIO", "LIMPAR_QUARTO"]
        
        return acoes
    
    @staticmethod
    def _identificar_problemas(status_reserva, status_pagamento, status_hospedagem):
        """Identifica problemas no fluxo"""
        problemas = []
        
        # Problema 1: Pagamento aprovado mas reserva não confirmada
        if (status_pagamento in [StatusPagamento.CONFIRMADO.value, StatusPagamento.CONFIRMADO.value] 
            and status_reserva == StatusReserva.PENDENTE.value):
            problemas.append("Pagamento aprovado mas reserva não confirmada")
        
        # Problema 2: Reserva confirmada mas pagamento não aprovado
        if (status_reserva == StatusReserva.CONFIRMADA.value 
            and status_pagamento not in [StatusPagamento.CONFIRMADO.value, StatusPagamento.CONFIRMADO.value]):
            problemas.append("Reserva confirmada mas pagamento não aprovado")
        
        # Problema 3: Check-in feito sem reserva confirmada
        if status_hospedagem == "CHECKIN_REALIZADO" and status_reserva != StatusReserva.CONFIRMADA.value:
            problemas.append("Check-in realizado sem reserva confirmada")
        
        # Problema 4: Checkout feito sem check-in
        if status_hospedagem == "CHECKOUT_REALIZADO" and status_hospedagem != "CHECKIN_REALIZADO":
            problemas.append("Checkout realizado sem check-in prévio")
        
        return problemas
    
    @staticmethod
    def _estado_esperado(status_reserva, status_pagamento):
        """Retorna o estado esperado baseado nos status"""
        if status_pagamento in [StatusPagamento.CONFIRMADO.value, StatusPagamento.CONFIRMADO.value]:
            return StatusReserva.CONFIRMADA.value
        elif status_pagamento == StatusPagamento.NEGADO.value:
            return StatusReserva.CANCELADO.value
        return status_reserva
    
    # ==================== VALIDAÇÕES DE TRANSIÇÃO ====================
    
    @staticmethod
    def pode_criar_reserva() -> Tuple[bool, str]:
        """Validar se pode criar nova reserva"""
        return True, "Reserva pode ser criada"
    
    @staticmethod
    def pode_pagar(reserva) -> Tuple[bool, str]:
        """Validar se pode pagar reserva"""
        if reserva.get('status') == StatusReserva.CANCELADO.value:
            return False, "Reserva cancelada não pode ser paga"
        
        if reserva.get('status') == StatusReserva.NO_SHOW.value:
            return False, "Cliente não compareceu"
        
        return True, "Pode pagar reserva"
    
    @staticmethod
    def pode_confirmar_pagamento(reserva, pagamento) -> Tuple[bool, str]:
        """Validar se pode confirmar pagamento"""
        status_reserva = reserva.get('status')
        status_pagamento = pagamento.get('status')
        
        if status_reserva == StatusReserva.CANCELADO.value:
            return False, "Reserva cancelada"
        
        if status_pagamento != StatusPagamento.CONFIRMADO.value:
            return False, f"Pagamento não está confirmado: {status_pagamento}"
        
        return True, "Pagamento pode ser confirmado"
    
    @staticmethod
    def pode_fazer_checkin(reserva, pagamentos, hospedagem=None) -> Tuple[bool, str]:
        """Validar se pode fazer check-in"""
        # Usar função do schemas/status_enums.py
        status_reserva = reserva.get('status')
        
        # Determinar status do pagamento
        status_pagamento = StatusPagamento.PENDENTE.value
        if pagamentos:
            pagamento_recente = max(pagamentos, key=lambda p: p.get('created_at', ''))
            status_pagamento = pagamento_recente.get('status')
        
        status_hospedagem = hospedagem.get('status') if hospedagem else "NAO_INICIADA"
        
        return pode_fazer_checkin(status_reserva, status_pagamento, status_hospedagem)
    
    @staticmethod
    def pode_fazer_checkout(hospedagem) -> Tuple[bool, str]:
        """Validar se pode fazer checkout"""
        if not hospedagem:
            return False, "Hospedagem não encontrada"
        
        status_hospedagem = hospedagem.get('status')
        return pode_fazer_checkout(status_hospedagem)
    
    @staticmethod
    def pode_cancelar_reserva(reserva, pagamentos=[]) -> Tuple[bool, str]:
        """Validar se pode cancelar reserva"""
        status_reserva = reserva.get('status')
        
        if status_reserva == StatusReserva.CANCELADO.value:
            return False, "Reserva já cancelada"
        
        if status_reserva == StatusReserva.NO_SHOW.value:
            return False, "Cliente não compareceu"
        
        # Verificar se já fez check-in
        if pagamentos:
            for pagamento in pagamentos:
                if pagamento.get('status') == StatusPagamento.CONFIRMADO.value:
                    return False, "Reserva com pagamento confirmado não pode ser cancelada"
        
        return True, "Reserva pode ser cancelada"
    
    # ==================== UTILITÁRIOS ====================
    
    @staticmethod
    def normalizar_status_reserva(status: str) -> str:
        """Normaliza status de reserva para padrão frontend"""
        from app.schemas.status_enums import normalizar_status_reserva
        return normalizar_status_reserva(status).value
    
    @staticmethod
    def normalizar_status_pagamento(status: str) -> str:
        """Normaliza status de pagamento para padrão"""
        from app.schemas.status_enums import normalizar_status_pagamento
        return normalizar_status_pagamento(status).value
    
    @staticmethod
    def get_cor_status(status: str, tipo: str = 'reserva') -> str:
        """Retorna cor CSS para status"""
        cores = {
            'reserva': {
                StatusReserva.PENDENTE.value: 'text-yellow-600 bg-yellow-100',
                StatusReserva.CONFIRMADA.value: 'text-blue-600 bg-blue-100',
                StatusReserva.CANCELADO.value: 'text-red-600 bg-red-100',
                StatusReserva.NO_SHOW.value: 'text-orange-600 bg-orange-100'
            },
            'pagamento': {
                StatusPagamento.PENDENTE.value: 'bg-yellow-100 text-yellow-800',
                StatusPagamento.CONFIRMADO.value: 'bg-green-100 text-green-800',
                StatusPagamento.NEGADO.value: 'bg-red-100 text-red-800',
                StatusPagamento.ESTORNADO.value: 'bg-orange-100 text-orange-800'
            }
        }
        
        return cores.get(tipo, {}).get(status, 'bg-gray-100 text-gray-800')
    
    @staticmethod
    def get_label_status(status: str, tipo: str = 'reserva') -> str:
        """Retorna label amigável para status"""
        labels = {
            'reserva': UnifiedStateValidator.get_estados_reserva(),
            'pagamento': UnifiedStateValidator.get_estados_pagamento()
        }
        
        return labels.get(tipo, {}).get(status, status)
