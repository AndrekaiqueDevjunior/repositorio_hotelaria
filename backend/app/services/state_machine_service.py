from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from sqlalchemy.orm import Session

from app.models.reserva import Reserva
from app.models.checkin_checkout import CheckinRecord, CheckoutRecord
from app.models.pagamento import Pagamento
from app.core.enums import StatusReserva, StatusPagamento, StatusFinanceiro
from app.utils.datetime_utils import now_utc
from app.core.exceptions import BusinessRuleViolation, ValidationError


class TransicaoEstado(str, Enum):
    """Transições válidas entre estados"""
    CRIAR_RESERVA = "CRIAR_RESERVA"
    CONFIRMAR_PAGAMENTO = "CONFIRMAR_PAGAMENTO"
    REALIZAR_CHECKIN = "REALIZAR_CHECKIN"
    REALIZAR_CHECKOUT = "REALIZAR_CHECKOUT"
    CANCELAR_RESERVA = "CANCELAR_RESERVA"
    MARCAR_NO_SHOW = "MARCAR_NO_SHOW"


class AuditoriaTransicao:
    """Registro de auditoria para mudanças de estado"""
    def __init__(self, 
                 reserva_id: int,
                 estado_origem: StatusReserva,
                 estado_destino: StatusReserva,
                 transicao: TransicaoEstado,
                 usuario_id: int,
                 motivo: str = None,
                 dados_contexto: Dict = None):
        self.reserva_id = reserva_id
        self.estado_origem = estado_origem
        self.estado_destino = estado_destino
        self.transicao = transicao
        self.usuario_id = usuario_id
        self.motivo = motivo or f"Transição {transicao.value}"
        self.dados_contexto = dados_contexto or {}
        self.timestamp = now_utc()


class StateMachineService:
    """
    Serviço para gerenciamento rigoroso de estados e transições
    Implementa state machine com validações e auditoria completa
    """
    
    # Definição da state machine - transições válidas
    TRANSICOES_VALIDAS = {
        StatusReserva.PENDENTE: {
            TransicaoEstado.CONFIRMAR_PAGAMENTO: StatusReserva.CONFIRMADA,
            TransicaoEstado.CANCELAR_RESERVA: StatusReserva.CANCELADO,
            TransicaoEstado.MARCAR_NO_SHOW: StatusReserva.NO_SHOW
        },
        StatusReserva.CONFIRMADA: {
            TransicaoEstado.REALIZAR_CHECKIN: StatusReserva.HOSPEDADO,
            TransicaoEstado.CANCELAR_RESERVA: StatusReserva.CANCELADO,
            TransicaoEstado.MARCAR_NO_SHOW: StatusReserva.NO_SHOW
        },
        StatusReserva.HOSPEDADO: {
            TransicaoEstado.REALIZAR_CHECKOUT: StatusReserva.CHECKED_OUT
        },
        StatusReserva.CHECKED_OUT: {
            # Estado final - sem transições
        },
        StatusReserva.CANCELADO: {
            # Estado final - sem transições
        },
        StatusReserva.NO_SHOW: {
            # Estado final - sem transições
        }
    }
    
    # Condições necessárias para cada transição
    CONDICOES_TRANSICAO = {
        TransicaoEstado.CONFIRMAR_PAGAMENTO: {
            "pagamento_minimo": 0.8,  # 80% do valor
            "validacoes": ["pagamento_aprovado", "dados_cliente_completos"]
        },
        TransicaoEstado.REALIZAR_CHECKIN: {
            "pagamento_minimo": 0.8,  # 80% do valor
            "validacoes": ["pagamento_aprovado", "quarto_disponivel", "documentos_validados"]
        },
        TransicaoEstado.REALIZAR_CHECKOUT: {
            "validacoes": ["checkin_realizado", "consumos_liquidados"]
        },
        TransicaoEstado.CANCELAR_RESERVA: {
            "validacoes": ["politica_cancelamento_respeitada"]
        },
        TransicaoEstado.MARCAR_NO_SHOW: {
            "validacoes": ["prazo_checkin_expirado"]
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.auditoria_buffer = []  # Buffer para registros de auditoria
    
    def validar_transicao(
        self, 
        reserva_id: int, 
        transicao: TransicaoEstado,
        usuario_id: int,
        dados_contexto: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Valida se uma transição é permitida
        Retorna resultado detalhado da validação
        """
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        estado_atual = reserva.status_reserva
        dados_contexto = dados_contexto or {}
        
        # Verificar se transição é válida na state machine
        if estado_atual not in self.TRANSICOES_VALIDAS:
            return {
                "valida": False,
                "motivo": f"Estado atual '{estado_atual.value}' não permite transições",
                "codigo_erro": "ESTADO_FINAL"
            }
        
        transicoes_permitidas = self.TRANSICOES_VALIDAS[estado_atual]
        if transicao not in transicoes_permitidas:
            return {
                "valida": False,
                "motivo": f"Transição '{transicao.value}' não permitida a partir de '{estado_atual.value}'",
                "transicoes_permitidas": [t.value for t in transicoes_permitidas.keys()],
                "codigo_erro": "TRANSICAO_INVALIDA"
            }
        
        # Estado de destino
        estado_destino = transicoes_permitidas[transicao]
        
        # Validar condições específicas da transição
        resultado_condicoes = self._validar_condicoes_transicao(
            reserva, transicao, usuario_id, dados_contexto
        )
        
        if not resultado_condicoes["valida"]:
            return resultado_condicoes
        
        return {
            "valida": True,
            "estado_origem": estado_atual.value,
            "estado_destino": estado_destino.value,
            "transicao": transicao.value,
            "condicoes_atendidas": resultado_condicoes["condicoes_atendidas"],
            "dados_validacao": resultado_condicoes.get("dados", {})
        }
    
    def executar_transicao(
        self,
        reserva_id: int,
        transicao: TransicaoEstado,
        usuario_id: int,
        motivo: str = None,
        dados_contexto: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Executa uma transição de estado com auditoria completa
        """
        # Validar transição primeiro
        validacao = self.validar_transicao(reserva_id, transicao, usuario_id, dados_contexto)
        
        if not validacao["valida"]:
            raise BusinessRuleViolation(
                f"Transição bloqueada: {validacao['motivo']}"
            )
        
        try:
            reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
            estado_origem = reserva.status_reserva
            estado_destino = StatusReserva(validacao["estado_destino"])
            
            # Executar ações específicas da transição
            self._executar_acoes_transicao(reserva, transicao, usuario_id, dados_contexto or {})
            
            # Atualizar estado da reserva
            reserva.status_reserva = estado_destino
            reserva.atualizado_por_usuario_id = usuario_id
            reserva.updated_at = now_utc()
            
            # Registrar auditoria
            auditoria = AuditoriaTransicao(
                reserva_id=reserva_id,
                estado_origem=estado_origem,
                estado_destino=estado_destino,
                transicao=transicao,
                usuario_id=usuario_id,
                motivo=motivo,
                dados_contexto=dados_contexto
            )
            
            self._registrar_auditoria(auditoria)
            
            self.db.commit()
            
            # Log para sistema
            print(f"[STATE_MACHINE] Reserva {reserva.codigo_reserva}: {estado_origem.value} → {estado_destino.value} via {transicao.value} por usuário {usuario_id}")
            
            return {
                "sucesso": True,
                "reserva_codigo": reserva.codigo_reserva,
                "estado_anterior": estado_origem.value,
                "estado_atual": estado_destino.value,
                "transicao_executada": transicao.value,
                "executado_em": now_utc().isoformat(),
                "executado_por": usuario_id,
                "dados_transicao": validacao.get("dados_validacao", {})
            }
            
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleViolation(f"Falha na execução da transição: {str(e)}")
    
    def _validar_condicoes_transicao(
        self, 
        reserva: Reserva, 
        transicao: TransicaoEstado,
        usuario_id: int,
        dados_contexto: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Valida condições específicas para cada tipo de transição"""
        
        if transicao == TransicaoEstado.CONFIRMAR_PAGAMENTO:
            return self._validar_confirmacao_pagamento(reserva)
        
        elif transicao == TransicaoEstado.REALIZAR_CHECKIN:
            return self._validar_checkin(reserva, dados_contexto)
        
        elif transicao == TransicaoEstado.REALIZAR_CHECKOUT:
            return self._validar_checkout(reserva, dados_contexto)
        
        elif transicao == TransicaoEstado.CANCELAR_RESERVA:
            return self._validar_cancelamento(reserva, dados_contexto)
        
        elif transicao == TransicaoEstado.MARCAR_NO_SHOW:
            return self._validar_no_show(reserva)
        
        else:
            return {"valida": True, "condicoes_atendidas": []}
    
    def _validar_confirmacao_pagamento(self, reserva: Reserva) -> Dict[str, Any]:
        """Validações específicas para confirmar pagamento"""
        pagamentos_aprovados = self.db.query(Pagamento).filter(
            Pagamento.reserva_id == reserva.id,
            Pagamento.status.in_([StatusPagamento.CONFIRMADO, StatusPagamento.APROVADO])
        ).all()
        
        valor_pago = sum(float(p.valor) for p in pagamentos_aprovados)
        valor_minimo = float(reserva.valor_previsto) * 0.3  # 30% mínimo
        
        if valor_pago < valor_minimo:
            return {
                "valida": False,
                "motivo": f"Pagamento insuficiente: R$ {valor_pago:.2f} < R$ {valor_minimo:.2f} (mínimo 30%)",
                "codigo_erro": "PAGAMENTO_INSUFICIENTE"
            }
        
        return {
            "valida": True,
            "condicoes_atendidas": ["pagamento_minimo_ok"],
            "dados": {
                "valor_pago": valor_pago,
                "valor_minimo": valor_minimo,
                "percentual_pago": (valor_pago / float(reserva.valor_previsto)) * 100
            }
        }
    
    def _validar_checkin(self, reserva: Reserva, dados_contexto: Dict) -> Dict[str, Any]:
        """Validações específicas para check-in"""
        # Validar pagamento (80% mínimo)
        pagamentos_aprovados = self.db.query(Pagamento).filter(
            Pagamento.reserva_id == reserva.id,
            Pagamento.status.in_([StatusPagamento.CONFIRMADO, StatusPagamento.APROVADO])
        ).all()
        
        valor_pago = sum(float(p.valor) for p in pagamentos_aprovados)
        valor_minimo = float(reserva.valor_previsto) * 0.8
        
        if valor_pago < valor_minimo:
            return {
                "valida": False,
                "motivo": f"Check-in requer 80% do valor pago: R$ {valor_pago:.2f} < R$ {valor_minimo:.2f}",
                "codigo_erro": "PAGAMENTO_INSUFICIENTE_CHECKIN"
            }
        
        # Validar se quarto está disponível
        if reserva.quarto:
            # Verificar se há outra reserva ativa no mesmo quarto
            conflito = self.db.query(Reserva).filter(
                Reserva.quarto_id == reserva.quarto_id,
                Reserva.status_reserva == StatusReserva.HOSPEDADO,
                Reserva.id != reserva.id
            ).first()
            
            if conflito:
                return {
                    "valida": False,
                    "motivo": f"Quarto {reserva.quarto.numero} ainda ocupado por reserva {conflito.codigo_reserva}",
                    "codigo_erro": "QUARTO_OCUPADO"
                }
        
        return {
            "valida": True,
            "condicoes_atendidas": ["pagamento_ok", "quarto_disponivel"],
            "dados": {"valor_pago": valor_pago, "valor_minimo": valor_minimo}
        }
    
    def _validar_checkout(self, reserva: Reserva, dados_contexto: Dict) -> Dict[str, Any]:
        """Validações específicas para check-out"""
        # Verificar se existe check-in
        checkin = self.db.query(CheckinRecord).filter(
            CheckinRecord.reserva_id == reserva.id
        ).first()
        
        if not checkin:
            return {
                "valida": False,
                "motivo": "Check-out requer check-in prévio",
                "codigo_erro": "CHECKIN_NAO_REALIZADO"
            }
        
        # Verificar se já foi feito checkout
        checkout = self.db.query(CheckoutRecord).filter(
            CheckoutRecord.reserva_id == reserva.id
        ).first()
        
        if checkout:
            return {
                "valida": False,
                "motivo": "Check-out já foi realizado",
                "codigo_erro": "CHECKOUT_JA_REALIZADO"
            }
        
        return {
            "valida": True,
            "condicoes_atendidas": ["checkin_ok", "checkout_nao_realizado"],
            "dados": {"checkin_datetime": checkin.checkin_datetime.isoformat()}
        }
    
    def _validar_cancelamento(self, reserva: Reserva, dados_contexto: Dict) -> Dict[str, Any]:
        """Validações específicas para cancelamento"""
        # Se já está hospedado, não pode cancelar (deve fazer checkout antecipado)
        if reserva.status_reserva == StatusReserva.HOSPEDADO:
            return {
                "valida": False,
                "motivo": "Reserva em hospedagem não pode ser cancelada. Use checkout antecipado.",
                "codigo_erro": "HOSPEDAGEM_ATIVA"
            }
        
        return {
            "valida": True,
            "condicoes_atendidas": ["nao_hospedado"],
            "dados": {}
        }
    
    def _validar_no_show(self, reserva: Reserva) -> Dict[str, Any]:
        """Validações específicas para no-show"""
        agora = now_utc()
        limite_checkin = reserva.checkin_previsto.replace(hour=23, minute=59)  # Até fim do dia
        
        if agora < limite_checkin:
            return {
                "valida": False,
                "motivo": f"Muito cedo para no-show. Aguarde até {limite_checkin.strftime('%d/%m/%Y %H:%M')}",
                "codigo_erro": "PRAZO_NAO_EXPIRADO"
            }
        
        return {
            "valida": True,
            "condicoes_atendidas": ["prazo_expirado"],
            "dados": {"limite_checkin": limite_checkin.isoformat()}
        }
    
    def _executar_acoes_transicao(
        self, 
        reserva: Reserva, 
        transicao: TransicaoEstado,
        usuario_id: int,
        dados_contexto: Dict[str, Any]
    ):
        """Executa ações específicas para cada transição"""
        
        if transicao == TransicaoEstado.CONFIRMAR_PAGAMENTO:
            # Atualizar status financeiro
            reserva.status_financeiro = StatusFinanceiro.SINAL_PAGO
        
        elif transicao == TransicaoEstado.REALIZAR_CHECKIN:
            # Registrar horário real de check-in
            reserva.checkin_real = now_utc()
        
        elif transicao == TransicaoEstado.REALIZAR_CHECKOUT:
            # Registrar horário real de check-out
            reserva.checkout_real = now_utc()
        
        # Outras transições podem ter ações específicas aqui
    
    def _registrar_auditoria(self, auditoria: AuditoriaTransicao):
        """Registra auditoria da transição (implementação futura com tabela dedicada)"""
        # Por enquanto, log detalhado
        log_entry = {
            "timestamp": auditoria.timestamp.isoformat(),
            "reserva_id": auditoria.reserva_id,
            "estado_origem": auditoria.estado_origem.value,
            "estado_destino": auditoria.estado_destino.value,
            "transicao": auditoria.transicao.value,
            "usuario_id": auditoria.usuario_id,
            "motivo": auditoria.motivo,
            "contexto": auditoria.dados_contexto
        }
        
        # Log estruturado para auditoria
        print(f"[AUDITORIA_TRANSICAO] {log_entry}")
        
        # Buffer para futura implementação em tabela
        self.auditoria_buffer.append(auditoria)
    
    def obter_historico_estados(self, reserva_id: int) -> List[Dict[str, Any]]:
        """
        Obtém histórico de mudanças de estado
        (Implementação futura com tabela de auditoria)
        """
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        # Por enquanto, retorna dados básicos
        historico = [
            {
                "timestamp": reserva.created_at.isoformat(),
                "estado": "PENDENTE",
                "transicao": "CRIAR_RESERVA",
                "usuario": reserva.criado_por_usuario_id,
                "motivo": "Reserva criada"
            }
        ]
        
        # Adicionar marcos principais se existirem
        if reserva.status_reserva != StatusReserva.PENDENTE:
            historico.append({
                "timestamp": reserva.updated_at.isoformat() if reserva.updated_at else reserva.created_at.isoformat(),
                "estado": reserva.status_reserva.value,
                "transicao": "TRANSICAO_HISTORICA",
                "usuario": reserva.atualizado_por_usuario_id or reserva.criado_por_usuario_id,
                "motivo": f"Estado atual: {reserva.status_reserva.value}"
            })
        
        return historico
    
    def obter_proximas_transicoes(self, reserva_id: int) -> List[Dict[str, Any]]:
        """Retorna transições válidas para o estado atual"""
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        estado_atual = reserva.status_reserva
        
        if estado_atual not in self.TRANSICOES_VALIDAS:
            return []
        
        transicoes_disponiveis = []
        for transicao, estado_destino in self.TRANSICOES_VALIDAS[estado_atual].items():
            # Validar se a transição é possível
            try:
                validacao = self.validar_transicao(reserva_id, transicao, 0)  # usuário 0 para teste
                
                transicoes_disponiveis.append({
                    "transicao": transicao.value,
                    "estado_destino": estado_destino.value,
                    "disponivel": validacao["valida"],
                    "motivo_bloqueio": validacao.get("motivo") if not validacao["valida"] else None,
                    "descricao": self._obter_descricao_transicao(transicao)
                })
            except:
                transicoes_disponiveis.append({
                    "transicao": transicao.value,
                    "estado_destino": estado_destino.value,
                    "disponivel": False,
                    "motivo_bloqueio": "Erro na validação",
                    "descricao": self._obter_descricao_transicao(transicao)
                })
        
        return transicoes_disponiveis
    
    def _obter_descricao_transicao(self, transicao: TransicaoEstado) -> str:
        """Retorna descrição amigável da transição"""
        descricoes = {
            TransicaoEstado.CONFIRMAR_PAGAMENTO: "Confirmar pagamento e ativar reserva",
            TransicaoEstado.REALIZAR_CHECKIN: "Realizar check-in do hóspede",
            TransicaoEstado.REALIZAR_CHECKOUT: "Finalizar hospedagem com check-out",
            TransicaoEstado.CANCELAR_RESERVA: "Cancelar reserva aplicando política",
            TransicaoEstado.MARCAR_NO_SHOW: "Marcar como não comparecimento (no-show)"
        }
        return descricoes.get(transicao, transicao.value)
