"""
Validadores de Negócio
Validações robustas para prevenir duplicações e garantir integridade
"""

from datetime import datetime, date
from typing import Optional
from fastapi import HTTPException


class ReservaValidator:
    """Validações de regras de negócio para reservas"""
    
    @staticmethod
    def validar_datas(checkin: date, checkout: date):
        """Validar datas de check-in e check-out"""
        
        # Check-in não pode ser no passado
        if checkin < date.today():
            raise HTTPException(
                status_code=400,
                detail="Data de check-in não pode ser no passado"
            )
        
        # Check-out deve ser após check-in
        if checkout <= checkin:
            raise HTTPException(
                status_code=400,
                detail="Data de check-out deve ser posterior ao check-in"
            )
        
        # Máximo de 30 dias
        dias = (checkout - checkin).days
        if dias > 30:
            raise HTTPException(
                status_code=400,
                detail="Reserva não pode exceder 30 dias"
            )
        
        return True
    
    @staticmethod
    def validar_transicao_status(status_atual: str, novo_status: str):
        """Validar se transição de status é permitida"""
        
        if status_atual == "CANCELADA":
            status_atual = "CANCELADO"
        if novo_status == "CANCELADA":
            novo_status = "CANCELADO"
        
        # Mapeamento de transições válidas
        transicoes_validas = {
            "PENDENTE": ["CONFIRMADA", "CANCELADO"],
            "CONFIRMADA": ["HOSPEDADO", "CANCELADO"],
            "HOSPEDADO": ["CHECKED_OUT"],
            "CHECKED_OUT": [],  # Estado final
            "CANCELADO": []     # Estado final
        }
        
        if status_atual not in transicoes_validas:
            raise HTTPException(
                status_code=400,
                detail=f"Status atual inválido: {status_atual}"
            )
        
        if novo_status not in transicoes_validas[status_atual]:
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível mudar de {status_atual} para {novo_status}"
            )
        
        return True
    
    @staticmethod
    def validar_cancelamento(reserva):
        """Validar se reserva pode ser cancelada"""
        
        # Não pode cancelar se já está hospedado
        if reserva.statusReserva == "HOSPEDADO":
            raise HTTPException(
                status_code=400,
                detail="Não é possível cancelar reserva com hóspede já hospedado"
            )
        
        # Não pode cancelar se já fez check-out
        if reserva.statusReserva == "CHECKED_OUT":
            raise HTTPException(
                status_code=400,
                detail="Não é possível cancelar reserva já finalizada"
            )
        
        # Não pode cancelar se já está cancelada
        if reserva.statusReserva in ("CANCELADO", "CANCELADA"):
            raise HTTPException(
                status_code=400,
                detail="Reserva já está cancelada"
            )
        
        return True
    
    @staticmethod
    def validar_checkin(reserva):
        """Validar se pode fazer check-in"""
        
        # Deve estar confirmada
        if reserva.statusReserva != "CONFIRMADA":
            raise HTTPException(
                status_code=400,
                detail=f"Check-in só pode ser feito em reservas confirmadas. Status atual: {reserva.statusReserva}"
            )
        
        # Verificar se é o dia do check-in (ou próximo)
        hoje = date.today()
        checkin_previsto = reserva.checkinPrevisto.date() if isinstance(reserva.checkinPrevisto, datetime) else reserva.checkinPrevisto
        
        # Permitir check-in 1 dia antes ou depois
        dias_diferenca = abs((checkin_previsto - hoje).days)
        if dias_diferenca > 1:
            raise HTTPException(
                status_code=400,
                detail=f"Check-in previsto para {checkin_previsto}. Hoje é {hoje}."
            )
        
        return True
    
    @staticmethod
    def validar_checkout(reserva):
        """Validar se pode fazer check-out"""
        
        # Deve estar hospedado
        status_atual = getattr(reserva, "statusReserva", None) or getattr(reserva, "status", None)
        if status_atual not in ("HOSPEDADO", "CHECKIN_REALIZADO", "CHECKED_IN"):
            raise HTTPException(
                status_code=400,
                detail=f"Check-out só pode ser feito em reservas com status HOSPEDADO ou CHECKIN_REALIZADO. Status atual: {status_atual}"
            )
        
        return True


class PagamentoValidator:
    """Validações de regras de negócio para pagamentos"""
    
    @staticmethod
    def validar_valor(valor: float):
        """Validar valor do pagamento"""
        
        if valor <= 0:
            raise HTTPException(
                status_code=400,
                detail="Valor do pagamento deve ser maior que zero"
            )
        
        if valor > 100000:  # Limite de R$ 100.000
            raise HTTPException(
                status_code=400,
                detail="Valor do pagamento excede o limite permitido (R$ 100.000)"
            )
        
        return True
    
    @staticmethod
    def validar_metodo(metodo: str):
        """Validar método de pagamento"""
        
        metodos_validos = ["CREDITO", "DEBITO", "PIX", "DINHEIRO", "TRANSFERENCIA"]
        
        if metodo not in metodos_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Método de pagamento inválido. Métodos válidos: {', '.join(metodos_validos)}"
            )
        
        return True
    
    @staticmethod
    def validar_duplicacao_transaction_id(transaction_id: str, db):
        """Validar se transaction_id já existe (prevenir duplicação)"""
        
        if not transaction_id:
            return True
        
        # Verificar se já existe
        existing = db.pagamento.find_first(
            where={"gatewayTransactionId": transaction_id}
        )
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Pagamento com transaction_id {transaction_id} já existe"
            )
        
        return True


class PontosValidator:
    """Validações de regras de negócio para pontos"""
    
    @staticmethod
    def validar_saldo_suficiente(saldo_atual: int, pontos_debito: int):
        """Validar se tem saldo suficiente para débito"""
        
        if pontos_debito <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantidade de pontos deve ser maior que zero"
            )
        
        if saldo_atual < pontos_debito:
            raise HTTPException(
                status_code=400,
                detail=f"Saldo insuficiente. Saldo atual: {saldo_atual}, Tentando debitar: {pontos_debito}"
            )
        
        return True
    
    @staticmethod
    def validar_quantidade_pontos(pontos: int):
        """Validar quantidade de pontos"""
        
        if pontos <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantidade de pontos deve ser maior que zero"
            )
        
        if pontos > 1000000:  # Limite de 1 milhão de pontos
            raise HTTPException(
                status_code=400,
                detail="Quantidade de pontos excede o limite permitido (1.000.000)"
            )
        
        return True
    
    @staticmethod
    def validar_tipo_origem(tipo: str, origem: str):
        """Validar tipo e origem da transação"""
        
        tipos_validos = ["CREDITO", "DEBITO"]
        origens_validas = ["RESERVA", "CHECKOUT", "AJUSTE_MANUAL", "RESGATE", "BONUS", "CONVITE"]
        
        if tipo not in tipos_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo inválido. Tipos válidos: {', '.join(tipos_validos)}"
            )
        
        if origem not in origens_validas:
            raise HTTPException(
                status_code=400,
                detail=f"Origem inválida. Origens válidas: {', '.join(origens_validas)}"
            )
        
        return True


class ClienteValidator:
    """Validações de regras de negócio para clientes"""
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Validar CPF com dígito verificador"""
        
        # Remover formatação
        cpf = ''.join(filter(str.isdigit, cpf))
        
        # Verificar tamanho
        if len(cpf) != 11:
            raise HTTPException(
                status_code=400,
                detail="CPF deve ter 11 dígitos"
            )
        
        # Verificar se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            raise HTTPException(
                status_code=400,
                detail="CPF inválido"
            )
        
        # Calcular primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = 11 - (soma % 11)
        digito1 = 0 if digito1 > 9 else digito1
        
        # Calcular segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = 11 - (soma % 11)
        digito2 = 0 if digito2 > 9 else digito2
        
        # Verificar dígitos
        if cpf[-2:] != f"{digito1}{digito2}":
            raise HTTPException(
                status_code=400,
                detail="CPF inválido (dígito verificador incorreto)"
            )
        
        return True
    
    @staticmethod
    def validar_email(email: str) -> bool:
        """Validar formato de email"""
        
        import re
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            raise HTTPException(
                status_code=400,
                detail="Formato de email inválido"
            )
        
        return True
    
    @staticmethod
    def validar_telefone(telefone: str) -> bool:
        """Validar formato de telefone"""
        
        # Remover formatação
        telefone = ''.join(filter(str.isdigit, telefone))
        
        # Verificar tamanho (10 ou 11 dígitos)
        if len(telefone) not in [10, 11]:
            raise HTTPException(
                status_code=400,
                detail="Telefone deve ter 10 ou 11 dígitos (com DDD)"
            )
        
        return True


class QuartoValidator:
    """Validações de regras de negócio para quartos"""
    
    @staticmethod
    async def validar_disponibilidade(
        quarto_numero: str,
        checkin: date,
        checkout: date,
        db,
        reserva_id_excluir: Optional[int] = None
    ):
        """
        Validar se quarto está disponível no período
        
        Args:
            quarto_numero: Número do quarto
            checkin: Data de check-in
            checkout: Data de check-out
            db: Instância do banco
            reserva_id_excluir: ID da reserva a excluir da verificação (para updates)
        """
        
        # Converter dates para datetime se necessário
        from datetime import datetime as dt
        if isinstance(checkin, date) and not isinstance(checkin, dt):
            checkin = dt.combine(checkin, dt.min.time())
        if isinstance(checkout, date) and not isinstance(checkout, dt):
            checkout = dt.combine(checkout, dt.min.time())
        
        # Buscar reservas conflitantes
        where_clause = {
            "quartoNumero": quarto_numero,
            "statusReserva": {
                "in": ["PENDENTE", "CONFIRMADA", "HOSPEDADO"]
            },
            "OR": [
                # Check-in durante período existente
                {
                    "checkinPrevisto": {"lte": checkout},
                    "checkoutPrevisto": {"gte": checkin}
                }
            ]
        }
        
        # Excluir reserva atual se for update
        if reserva_id_excluir:
            where_clause["id"] = {"not": reserva_id_excluir}
        
        conflitos = await db.reserva.find_many(where=where_clause)
        
        if conflitos:
            datas_conflito = [
                f"{r.checkinPrevisto.date()} a {r.checkoutPrevisto.date()}"
                for r in conflitos
            ]
            raise HTTPException(
                status_code=409,
                detail=f"Quarto {quarto_numero} não disponível. Conflito com reservas: {', '.join(datas_conflito)}"
            )
        
        return True
