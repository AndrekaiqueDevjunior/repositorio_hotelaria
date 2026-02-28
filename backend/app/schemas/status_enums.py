"""
Enums de Status Padronizados
Separação clara entre estados: Comercial, Financeiro e Operacional
"""
from enum import Enum


# ============= RESERVA (COMERCIAL) =============
class StatusReserva(str, Enum):
    """
    Estado comercial da reserva (intenção do cliente)
    
    Fluxo completo com comprovante:
    PENDENTE_PAGAMENTO → AGUARDANDO_COMPROVANTE → EM_ANALISE → 
    PAGA_APROVADA → CHECKIN_LIBERADO → CHECKIN_REALIZADO → CHECKOUT_REALIZADO
    
    Fluxos alternativos:
    - PAGA_REJEITADA: Comprovante recusado
    - CANCELADA: Cliente ou hotel cancelou
    - NO_SHOW: Cliente não apareceu no check-in
    """
    # Estados do fluxo de pagamento/comprovante
    PENDENTE_PAGAMENTO = "PENDENTE_PAGAMENTO"        # Reserva criada, aguardando escolha de pagamento
    AGUARDANDO_COMPROVANTE = "AGUARDANDO_COMPROVANTE" # Escolheu "balcão", aguardando upload
    EM_ANALISE = "EM_ANALISE"                        # Comprovante enviado, aguardando validação admin
    CONFIRMADA = "CONFIRMADA"                        # ✅ Comprovante aprovado, pagamento confirmado, PODE FAZER CHECK-IN
    PAGA_REJEITADA = "PAGA_REJEITADA"                # Comprovante rejeitado
    CHECKIN_REALIZADO = "CHECKIN_REALIZADO"          # Check-in feito, hóspede no hotel
    CHECKOUT_REALIZADO = "CHECKOUT_REALIZADO"        # Check-out realizado
    
    # Estados finais
    CANCELADA = "CANCELADA"                          # Reserva cancelada
    NO_SHOW = "NO_SHOW"                              # Cliente não compareceu
    
    # Valores legados (mantidos para compatibilidade)
    PENDENTE = "PENDENTE_PAGAMENTO"                  # Alias para PENDENTE_PAGAMENTO
    PAGA_APROVADA = "CONFIRMADA"                     # Alias legado para CONFIRMADA
    CHECKIN_LIBERADO = "CONFIRMADA"                  # Alias legado para CONFIRMADA
    CANCELADO = "CANCELADA"                          # Alias para CANCELADA
    HOSPEDADO = "CHECKIN_REALIZADO"                  # Alias para CHECKIN_REALIZADO
    CHECKED_OUT = "CHECKOUT_REALIZADO"               # Alias para CHECKOUT_REALIZADO
    CHECKED_IN = "CHECKIN_REALIZADO"                 # Alias para CHECKIN_REALIZADO
    
    # Aliases para migração gradual
    AGUARDANDO_PAGAMENTO = "PENDENTE_PAGAMENTO"


# ============= PAGAMENTO (FINANCEIRO) =============
class StatusPagamento(str, Enum):
    """
    Estado financeiro do pagamento (dinheiro)
    
    Fluxo normal:
    PENDENTE → PAGO
    
    Fluxos alternativos:
    - FALHOU: Pagamento recusado/negado
    - ESTORNADO: Pagamento foi estornado
    """
    # Valores legados (persistidos no banco) - mantidos como canonical values
    PENDENTE = "PENDENTE"        # Aguardando processamento
    PROCESSANDO = "PROCESSANDO"  # Em processamento
    CONFIRMADO = "CONFIRMADO"    # Pagamento confirmado
    APROVADO = "APROVADO"        # Alias legado usado em alguns fluxos
    NEGADO = "NEGADO"            # Pagamento recusado/negado
    ESTORNADO = "ESTORNADO"      # Pagamento foi estornado
    CANCELADO = "CANCELADO"      # Pagamento cancelado

    # Novos nomes (aliases) para migração gradual
    PAGO = "CONFIRMADO"
    FALHOU = "NEGADO"


# ============= HOSPEDAGEM (OPERACIONAL) =============
class StatusHospedagem(str, Enum):
    """
    Estado operacional da hospedagem (física)
    
    Fluxo normal:
    NAO_INICIADA → CHECKIN_REALIZADO → CHECKOUT_REALIZADO → ENCERRADA
    
    Regras:
    - NAO_INICIADA: Reserva confirmada, aguardando chegada do hóspede
    - CHECKIN_REALIZADO: Hóspede no hotel (quarto ocupado)
    - CHECKOUT_REALIZADO: Hóspede saiu (quarto liberado)
    - ENCERRADA: Hospedagem finalizada e processada
    """
    NAO_INICIADA = "NAO_INICIADA"              # Aguardando chegada do hóspede
    CHECKIN_REALIZADO = "CHECKIN_REALIZADO"    # Hóspede no hotel
    CHECKOUT_REALIZADO = "CHECKOUT_REALIZADO"  # Hóspede saiu
    ENCERRADA = "ENCERRADA"                    # Hospedagem finalizada


# ============= MAPEAMENTO DE COMPATIBILIDADE =============
# Para migração gradual de status antigos

STATUS_RESERVA_MAPPING = {
    # Antigos → Novos
    "PENDENTE": StatusReserva.AGUARDANDO_PAGAMENTO,
    "CONFIRMADO": StatusReserva.CONFIRMADA,
    "HOSPEDADO": StatusReserva.CONFIRMADA,  # Hospedado é estado operacional, não comercial
    "CHECKED_OUT": StatusReserva.CONFIRMADA,  # Checkout é estado operacional
    "CHECKED_IN": StatusReserva.CONFIRMADA,
    "FINALIZADA": StatusReserva.CONFIRMADA,
    "CANCELADO": StatusReserva.CANCELADA,
}

STATUS_PAGAMENTO_MAPPING = {
    # Antigos → Novos
    "APROVADO": StatusPagamento.PAGO,
    "CONFIRMADO": StatusPagamento.PAGO,
    "APPROVED": StatusPagamento.PAGO,
    "PROCESSANDO": StatusPagamento.PENDENTE,
    "RECUSADO": StatusPagamento.FALHOU,
    "NEGADO": StatusPagamento.FALHOU,
    "FAILED": StatusPagamento.FALHOU,
}

STATUS_HOSPEDAGEM_MAPPING = {
    # Antigos → Novos
    "PENDENTE": StatusHospedagem.NAO_INICIADA,
    "CONFIRMADA": StatusHospedagem.NAO_INICIADA,
    "HOSPEDADO": StatusHospedagem.CHECKIN_REALIZADO,
    "CHECKED_IN": StatusHospedagem.CHECKIN_REALIZADO,
    "CHECKED_OUT": StatusHospedagem.CHECKOUT_REALIZADO,
    "FINALIZADA": StatusHospedagem.ENCERRADA,
}


# ============= FUNÇÕES AUXILIARES =============

def normalizar_status_reserva(status: str) -> StatusReserva:
    """Converte status antigo para novo padrão"""
    if status in [e.value for e in StatusReserva]:
        return StatusReserva(status)
    return STATUS_RESERVA_MAPPING.get(status, StatusReserva.AGUARDANDO_PAGAMENTO)


def normalizar_status_pagamento(status: str) -> StatusPagamento:
    """Converte status antigo para novo padrão"""
    if status in [e.value for e in StatusPagamento]:
        return StatusPagamento(status)
    return STATUS_PAGAMENTO_MAPPING.get(status, StatusPagamento.PENDENTE)


def normalizar_status_hospedagem(status: str) -> StatusHospedagem:
    """Converte status antigo para novo padrão"""
    if status in [e.value for e in StatusHospedagem]:
        return StatusHospedagem(status)
    return STATUS_HOSPEDAGEM_MAPPING.get(status, StatusHospedagem.NAO_INICIADA)


# ============= REGRAS DE NEGÓCIO =============

def pode_fazer_checkin(status_reserva: str, status_pagamento: str, status_hospedagem: str) -> tuple[bool, str]:
    """
    Valida se pode fazer check-in
    
    Regras:
    1. Reserva deve estar CONFIRMADA
    2. Pagamento deve estar PAGO
    3. Hospedagem deve estar NAO_INICIADA
    
    Returns:
        (pode_fazer, motivo_se_nao_pode)
    """
    if status_reserva != StatusReserva.CONFIRMADA.value:
        return False, f"Reserva deve estar CONFIRMADA (atual: {status_reserva})"
    
    if status_pagamento != StatusPagamento.PAGO.value:
        return False, f"Pagamento deve estar PAGO (atual: {status_pagamento})"
    
    if status_hospedagem != StatusHospedagem.NAO_INICIADA.value:
        return False, f"Hospedagem já foi iniciada (atual: {status_hospedagem})"
    
    return True, ""


def pode_fazer_checkout(status_hospedagem: str) -> tuple[bool, str]:
    """
    Valida se pode fazer checkout
    
    Regras:
    1. Hospedagem deve estar CHECKIN_REALIZADO
    
    Returns:
        (pode_fazer, motivo_se_nao_pode)
    """
    if status_hospedagem != StatusHospedagem.CHECKIN_REALIZADO.value:
        return False, f"Check-in deve ter sido realizado (atual: {status_hospedagem})"
    
    return True, ""


def pode_confirmar_reserva(status_reserva: str, status_pagamento: str) -> tuple[bool, str]:
    """
    Valida se pode confirmar reserva
    
    Regras:
    1. Reserva deve estar AGUARDANDO_PAGAMENTO
    2. Pagamento deve estar PAGO
    
    Returns:
        (pode_fazer, motivo_se_nao_pode)
    """
    if status_reserva != StatusReserva.AGUARDANDO_PAGAMENTO.value:
        return False, f"Reserva já foi confirmada ou cancelada (atual: {status_reserva})"
    
    if status_pagamento != StatusPagamento.PAGO.value:
        return False, f"Pagamento deve estar PAGO antes de confirmar (atual: {status_pagamento})"
    
    return True, ""
