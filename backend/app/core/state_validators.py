"""
Validators de Transição de Estados
Garante que cada estado (Reserva, Pagamento, Hospedagem) seja independente
"""
from typing import Optional, Tuple
from datetime import datetime


# ============= ESTADOS VÁLIDOS =============
# SYS-001 FIX: Usar estados consistentes com enums.py

from app.schemas.status_enums import StatusReserva, StatusPagamento

# Estados de reserva aceitos. O banco ainda possui valores legados e novos.
ESTADOS_RESERVA = {
    "PENDENTE",
    "PENDENTE_PAGAMENTO",
    "AGUARDANDO_PAGAMENTO",
    "AGUARDANDO_COMPROVANTE",
    "EM_ANALISE",
    "PAGA_REJEITADA",
    "CONFIRMADA",
    "PAGA_APROVADA",
    "CHECKIN_LIBERADO",
    "HOSPEDADO",
    "CHECKIN_REALIZADO",
    "CHECKED_IN",
    "CHECKED_OUT",
    "CHECKOUT_REALIZADO",
    "FINALIZADA",
    "CANCELADO",
    "CANCELADA",
    "NO_SHOW",
}

# Estados de pagamento aceitos.
ESTADOS_PAGAMENTO = {
    StatusPagamento.PENDENTE.value,
    StatusPagamento.CONFIRMADO.value,
    StatusPagamento.APROVADO.value,
    StatusPagamento.NEGADO.value,
    StatusPagamento.ESTORNADO.value,
    StatusPagamento.CANCELADO.value,
    "PAGO",
    "CAPTURED",
    "AUTHORIZED",
    "APPROVED",
}

# Estados de hospedagem (mantidos como estão - sem conflito)
ESTADOS_HOSPEDAGEM = {
    "NAO_INICIADA",
    "CHECKIN_REALIZADO", 
    "CHECKOUT_REALIZADO",
    "ENCERRADA"
}


# ============= VALIDADORES DE TRANSIÇÃO =============

def _normalizar_reserva_status(status: str) -> str:
    status = (status or "").upper().strip()
    if status in {"PENDENTE", "PENDENTE_PAGAMENTO", "AGUARDANDO_PAGAMENTO"}:
        return "PENDENTE"
    if status in {"CONFIRMADA", "PAGA_APROVADA", "CHECKIN_LIBERADO", "CONFIRMADO"}:
        return "CONFIRMADA"
    if status in {"HOSPEDADO", "CHECKIN_REALIZADO", "CHECKED_IN"}:
        return "HOSPEDADO"
    if status in {"CHECKED_OUT", "CHECKOUT_REALIZADO", "FINALIZADA"}:
        return "CHECKED_OUT"
    if status in {"CANCELADO", "CANCELADA", "NO_SHOW"}:
        return "CANCELADO"
    return status


def _normalizar_pagamento_status(status: str) -> str:
    status = (status or "").upper().strip()
    if status in {"CONFIRMADO", "PAGO", "APROVADO", "APPROVED", "CAPTURED", "AUTHORIZED"}:
        return "CONFIRMADO"
    if status in {"NEGADO", "RECUSADO", "FAILED", "FALHOU"}:
        return "NEGADO"
    if status in {"CANCELADO", "ESTORNADO"}:
        return "ESTORNADO"
    return status or "PENDENTE"


class ReservaStateValidator:
    """
    SYS-001 FIX: Valida transições de estado da Reserva usando enums consistentes
    """
    
    @staticmethod
    def pode_confirmar(status_reserva: str, status_pagamento: str) -> Tuple[bool, str]:
        """
        Valida se pode confirmar reserva
        
        SYS-001 FIX: Regra atualizada para estados consistentes
        """
        if _normalizar_reserva_status(status_reserva) != "PENDENTE":
            return False, f"Reserva deve estar PENDENTE (atual: {status_reserva})"
        
        if _normalizar_pagamento_status(status_pagamento) != "CONFIRMADO":
            return False, f"Pagamento deve estar CONFIRMADO antes de confirmar (atual: {status_pagamento})"
        
        return True, ""
    
    @staticmethod
    def pode_cancelar(status_reserva: str, status_hospedagem: str) -> Tuple[bool, str]:
        """
        Valida se pode cancelar reserva
        
        SYS-001 FIX: Regra atualizada para estados consistentes
        """
        status_reserva_norm = _normalizar_reserva_status(status_reserva)
        if status_reserva_norm == "CANCELADO":
            return False, "Reserva já está cancelada"
        
        if status_reserva_norm == "CHECKED_OUT":
            return False, "Não pode cancelar reserva que já fez check-out"
        
        if status_hospedagem in ["CHECKOUT_REALIZADO", "ENCERRADA"]:
            return False, f"Não pode cancelar após checkout (hospedagem: {status_hospedagem})"
        
        return True, ""
    
    @staticmethod
    def validar_transicao(status_atual: str, status_novo: str) -> Tuple[bool, str]:
        """
        SYS-001 FIX: Valida transições usando estados consistentes com enums.py
        """
        status_atual_norm = _normalizar_reserva_status(status_atual)
        status_novo_norm = _normalizar_reserva_status(status_novo)

        if status_novo not in ESTADOS_RESERVA:
            return False, f"Status inválido: {status_novo}"
        
        # SYS-001 FIX: Transições válidas baseadas no fluxo real
        transicoes_validas = {
            "PENDENTE": ["CONFIRMADA", "CANCELADO"],
            "CONFIRMADA": ["HOSPEDADO", "CANCELADO"],
            "HOSPEDADO": ["CHECKED_OUT", "CANCELADO"],
            "CHECKED_OUT": [],  # Estado final
            "CANCELADO": []     # Estado final
        }
        
        if status_novo_norm not in transicoes_validas.get(status_atual_norm, []):
            return False, f"Transição inválida: {status_atual} → {status_novo}"
        
        return True, ""


class PagamentoStateValidator:
    """
    SYS-001 FIX: Valida transições de estado do Pagamento usando enums consistentes
    """
    
    @staticmethod
    def pode_processar(status_pagamento: str) -> Tuple[bool, str]:
        """Valida se pode processar pagamento"""
        if _normalizar_pagamento_status(status_pagamento) != "PENDENTE":
            return False, f"Pagamento deve estar PENDENTE (atual: {status_pagamento})"
        
        return True, ""
    
    @staticmethod
    def pode_estornar(status_pagamento: str) -> Tuple[bool, str]:
        """Valida se pode estornar pagamento"""
        if _normalizar_pagamento_status(status_pagamento) != "CONFIRMADO":
            return False, f"Só pode estornar pagamento CONFIRMADO (atual: {status_pagamento})"
        
        return True, ""
    
    @staticmethod
    def validar_transicao(status_atual: str, status_novo: str) -> Tuple[bool, str]:
        """
        SYS-001 FIX: Valida transições usando estados consistentes com enums.py
        """
        status_atual_norm = _normalizar_pagamento_status(status_atual)
        status_novo_norm = _normalizar_pagamento_status(status_novo)

        if status_novo not in ESTADOS_PAGAMENTO:
            return False, f"Status inválido: {status_novo}"
        
        # SYS-001 FIX: Transições válidas baseadas nos estados reais
        transicoes_validas = {
            "PENDENTE": ["CONFIRMADO", "NEGADO"],
            "CONFIRMADO": ["ESTORNADO"],
            "ESTORNADO": [],  # Estado final
            "NEGADO": ["PENDENTE"]  # Pode tentar novamente
        }
        
        if status_novo_norm not in transicoes_validas.get(status_atual_norm, []):
            return False, f"Transição inválida: {status_atual} → {status_novo}"
        
        return True, ""


class HospedagemStateValidator:
    """Valida transições de estado da Hospedagem (operacional)"""
    
    @staticmethod
    def pode_fazer_checkin(
        status_reserva: str,
        status_pagamento: str,
        status_hospedagem: str
    ) -> Tuple[bool, str]:
        """
        SYS-001 FIX: Valida check-in usando estados consistentes
        
        REGRA CRÍTICA: Check-in depende de 3 estados independentes
        """
        # 1. Reserva deve estar confirmada (SYS-001 FIX)
        if _normalizar_reserva_status(status_reserva) != "CONFIRMADA":
            return False, f"❌ Reserva deve estar CONFIRMADA (atual: {status_reserva})"
        
        # 2. Pagamento deve estar confirmado (SYS-001 FIX)
        if _normalizar_pagamento_status(status_pagamento) != "CONFIRMADO":
            return False, f"❌ Pagamento deve estar CONFIRMADO (atual: {status_pagamento})"
        
        # 3. Hospedagem não pode ter sido iniciada
        if status_hospedagem != "NAO_INICIADA":
            return False, f"❌ Check-in já foi realizado (hospedagem: {status_hospedagem})"
        
        return True, "✅ Check-in pode ser realizado"
    
    @staticmethod
    def pode_fazer_checkout(status_hospedagem: str) -> Tuple[bool, str]:
        """
        Valida se pode fazer checkout
        
        REGRA CRÍTICA: Checkout depende APENAS da hospedagem
        ⚠️ NÃO depende de pagamento (já foi pago antes)
        """
        if status_hospedagem != "CHECKIN_REALIZADO":
            return False, f"❌ Check-in deve ter sido realizado (atual: {status_hospedagem})"
        
        return True, "✅ Checkout pode ser realizado"
    
    @staticmethod
    def validar_transicao(status_atual: str, status_novo: str) -> Tuple[bool, str]:
        """Valida se transição de estado é válida"""
        if status_novo not in ESTADOS_HOSPEDAGEM:
            return False, f"Status inválido: {status_novo}"
        
        # Transições válidas
        transicoes_validas = {
            "NAO_INICIADA": ["CHECKIN_REALIZADO"],
            "CHECKIN_REALIZADO": ["CHECKOUT_REALIZADO"],
            "CHECKOUT_REALIZADO": ["ENCERRADA"],
            "ENCERRADA": []  # Estado final
        }
        
        if status_novo not in transicoes_validas.get(status_atual, []):
            return False, f"Transição inválida: {status_atual} → {status_novo}"
        
        return True, ""


# ============= VALIDADOR GERAL =============

class StateValidator:
    """Validador geral que coordena todos os estados"""
    
    reserva = ReservaStateValidator()
    pagamento = PagamentoStateValidator()
    hospedagem = HospedagemStateValidator()
    
    @classmethod
    def validar_acao_checkin(
        cls,
        reserva_status: str,
        pagamento_status: str,
        hospedagem_status: str
    ) -> Tuple[bool, str]:
        """
        Valida se pode realizar check-in
        
        Esta é a validação CRÍTICA que evita o bug original
        """
        return cls.hospedagem.pode_fazer_checkin(
            reserva_status,
            pagamento_status,
            hospedagem_status
        )
    
    @classmethod
    def validar_acao_checkout(cls, hospedagem_status: str) -> Tuple[bool, str]:
        """
        Valida se pode realizar checkout
        
        ⚠️ IMPORTANTE: Checkout NÃO depende de pagamento!
        """
        return cls.hospedagem.pode_fazer_checkout(hospedagem_status)
    
    @classmethod
    def validar_acao_confirmar_reserva(
        cls,
        reserva_status: str,
        pagamento_status: str
    ) -> Tuple[bool, str]:
        """Valida se pode confirmar reserva"""
        return cls.reserva.pode_confirmar(reserva_status, pagamento_status)
    
    @classmethod
    def validar_acao_cancelar_reserva(
        cls,
        reserva_status: str,
        hospedagem_status: str
    ) -> Tuple[bool, str]:
        """Valida se pode cancelar reserva"""
        return cls.reserva.pode_cancelar(reserva_status, hospedagem_status)


# ============= HELPERS PARA FRONTEND =============

def get_acoes_disponiveis(
    status_reserva: str,
    status_pagamento: str,
    status_hospedagem: str
) -> dict:
    """
    Retorna quais ações estão disponíveis baseado nos estados atuais
    
    Use isso no frontend para habilitar/desabilitar botões
    """
    validator = StateValidator()
    
    # Check-in
    pode_checkin, msg_checkin = validator.validar_acao_checkin(
        status_reserva,
        status_pagamento,
        status_hospedagem
    )
    
    # Checkout
    pode_checkout, msg_checkout = validator.validar_acao_checkout(
        status_hospedagem
    )
    
    # Confirmar reserva
    pode_confirmar, msg_confirmar = validator.validar_acao_confirmar_reserva(
        status_reserva,
        status_pagamento
    )
    
    # Cancelar reserva
    pode_cancelar, msg_cancelar = validator.validar_acao_cancelar_reserva(
        status_reserva,
        status_hospedagem
    )
    
    return {
        "checkin": {
            "habilitado": pode_checkin,
            "motivo": msg_checkin
        },
        "checkout": {
            "habilitado": pode_checkout,
            "motivo": msg_checkout
        },
        "confirmar": {
            "habilitado": pode_confirmar,
            "motivo": msg_confirmar
        },
        "cancelar": {
            "habilitado": pode_cancelar,
            "motivo": msg_cancelar
        }
    }


# ============= TESTES UNITÁRIOS =============

def test_validators():
    """Testa validators com casos comuns"""
    print("🧪 Testando validators de estado...\n")
    
    validator = StateValidator()
    
    # Teste 1: Check-in com tudo OK
    print("1️⃣ Check-in com estados corretos:")
    pode, msg = validator.validar_acao_checkin(
        "CONFIRMADA",
        "PAGO",
        "NAO_INICIADA"
    )
    print(f"   Resultado: {msg}")
    assert pode == True, "Deveria permitir check-in"
    
    # Teste 2: Check-in sem pagamento
    print("\n2️⃣ Check-in sem pagamento:")
    pode, msg = validator.validar_acao_checkin(
        "CONFIRMADA",
        "PENDENTE",  # ❌ Não pagou
        "NAO_INICIADA"
    )
    print(f"   Resultado: {msg}")
    assert pode == False, "NÃO deveria permitir check-in"
    
    # Teste 3: Checkout após check-in
    print("\n3️⃣ Checkout após check-in:")
    pode, msg = validator.validar_acao_checkout("CHECKIN_REALIZADO")
    print(f"   Resultado: {msg}")
    assert pode == True, "Deveria permitir checkout"
    
    # Teste 4: Checkout sem check-in
    print("\n4️⃣ Checkout sem check-in:")
    pode, msg = validator.validar_acao_checkout("NAO_INICIADA")
    print(f"   Resultado: {msg}")
    assert pode == False, "NÃO deveria permitir checkout"
    
    # Teste 5: Confirmar reserva após pagamento
    print("\n5️⃣ Confirmar reserva após pagamento:")
    pode, msg = validator.validar_acao_confirmar_reserva(
        "AGUARDANDO_PAGAMENTO",
        "PAGO"
    )
    print(f"   Resultado: {msg}")
    assert pode == True, "Deveria permitir confirmar"
    
    # Teste 6: Confirmar reserva sem pagamento
    print("\n6️⃣ Confirmar reserva sem pagamento:")
    pode, msg = validator.validar_acao_confirmar_reserva(
        "AGUARDANDO_PAGAMENTO",
        "PENDENTE"
    )
    print(f"   Resultado: {msg}")
    assert pode == False, "NÃO deveria permitir confirmar"
    
    print("\n✅ Todos os testes passaram!")


if __name__ == "__main__":
    test_validators()
