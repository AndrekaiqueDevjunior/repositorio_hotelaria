from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.checkin_checkout import CheckinRecord, CheckoutRecord
from app.models.reserva import Reserva, ItemCobranca
from app.models.pagamento import Pagamento
from app.core.enums import (
    StatusReserva, StatusPagamento, StatusFinanceiro, 
    StatusVistoria, TipoItemCobranca
)
from app.utils.datetime_utils import now_utc
from app.core.exceptions import BusinessRuleViolation, ValidationError


class CheckoutValidationError(Exception):
    """Erro específico para validações de check-out"""
    pass


class CheckoutService:
    """Serviço profissional para gerenciamento de Check-out"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validar_pre_checkout(self, reserva_id: int) -> Dict[str, Any]:
        """
        Validação completa pré-check-out
        Calcula acerto financeiro e identifica pendências
        """
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        # Verificar se existe check-in
        checkin_record = self.db.query(CheckinRecord).filter(
            CheckinRecord.reserva_id == reserva_id
        ).first()
        
        if not checkin_record:
            raise ValidationError("Check-in não realizado. Não é possível fazer check-out.")
        
        if reserva.status_reserva != StatusReserva.HOSPEDADO:
            raise ValidationError(f"Status inválido para check-out: {reserva.status_reserva}")
        
        # Calcular valores e consumos
        calculo_financeiro = self._calcular_acerto_financeiro(reserva_id)
        
        return {
            "pode_fazer_checkout": True,
            "checkin_datetime": checkin_record.checkin_datetime.isoformat(),
            "dias_hospedado": (now_utc().date() - checkin_record.checkin_datetime.date()).days,
            "caucao_cobrada": float(checkin_record.caucao_cobrada or 0),
            "calculo_financeiro": calculo_financeiro,
            "reserva": {
                "id": reserva.id,
                "codigo": reserva.codigo_reserva,
                "cliente": reserva.cliente.nome_completo,
                "quarto": reserva.quarto.numero if reserva.quarto else "N/A"
            }
        }
    
    def _calcular_acerto_financeiro(self, reserva_id: int) -> Dict[str, Any]:
        """Calcula o acerto financeiro completo"""
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        
        # Valor base da hospedagem
        valor_hospedagem = float(reserva.valor_previsto)
        
        # Pagamentos já realizados
        pagamentos_aprovados = self.db.query(Pagamento).filter(
            Pagamento.reserva_id == reserva_id,
            Pagamento.status.in_([StatusPagamento.CONFIRMADO, StatusPagamento.APROVADO])
        ).all()
        valor_pago = sum(float(p.valor) for p in pagamentos_aprovados)
        
        # Consumos e extras durante a hospedagem
        itens_consumo = self.db.query(ItemCobranca).filter(
            ItemCobranca.reserva_id == reserva_id
        ).all()
        
        consumos_detalhados = []
        valor_consumos = 0
        
        for item in itens_consumo:
            valor_item = float(item.valor_unitario * item.quantidade)
            valor_consumos += valor_item
            consumos_detalhados.append({
                "tipo": item.tipo.value,
                "descricao": item.descricao,
                "quantidade": item.quantidade,
                "valor_unitario": float(item.valor_unitario),
                "valor_total": valor_item
            })
        
        # Caução
        checkin_record = self.db.query(CheckinRecord).filter(
            CheckinRecord.reserva_id == reserva_id
        ).first()
        caucao_cobrada = float(checkin_record.caucao_cobrada or 0)
        
        # Cálculo final
        valor_total_final = valor_hospedagem + valor_consumos
        saldo = valor_pago + caucao_cobrada - valor_total_final
        
        return {
            "valor_hospedagem": valor_hospedagem,
            "valor_pago": valor_pago,
            "valor_consumos": valor_consumos,
            "caucao_cobrada": caucao_cobrada,
            "valor_total_final": valor_total_final,
            "saldo": saldo,
            "saldo_devedor": max(-saldo, 0),  # Valor que cliente deve
            "saldo_credor": max(saldo, 0),    # Valor a devolver ao cliente
            "consumos_detalhados": consumos_detalhados,
            "status_financeiro": self._determinar_status_financeiro(saldo)
        }
    
    def _determinar_status_financeiro(self, saldo: float) -> str:
        """Determina o status financeiro baseado no saldo"""
        if saldo > 1.0:  # Tolerância de R$ 1,00
            return StatusFinanceiro.CREDOR.value
        elif saldo < -1.0:
            return StatusFinanceiro.DEVEDOR.value
        else:
            return StatusFinanceiro.PAGO_TOTAL.value
    
    def realizar_checkout(
        self,
        reserva_id: int,
        usuario_id: int,
        dados_checkout: Dict[str, Any]
    ) -> CheckoutRecord:
        """
        Realiza o check-out formal com vistoria e acerto financeiro
        """
        # Validação pré-checkout
        validacao = self.validar_pre_checkout(reserva_id)
        
        # Validar dados obrigatórios
        self._validar_dados_checkout(dados_checkout)
        
        try:
            checkin_record = self.db.query(CheckinRecord).filter(
                CheckinRecord.reserva_id == reserva_id
            ).first()
            
            calculo = validacao["calculo_financeiro"]
            
            # Processar consumos adicionais informados no checkout
            if dados_checkout.get("consumos_adicionais"):
                for consumo in dados_checkout["consumos_adicionais"]:
                    item = ItemCobranca(
                        reserva_id=reserva_id,
                        tipo=TipoItemCobranca[consumo["tipo"]],
                        descricao=consumo["descricao"],
                        quantidade=consumo.get("quantidade", 1),
                        valor_unitario=Decimal(str(consumo["valor_unitario"]))
                    )
                    self.db.add(item)
                
                # Recalcular após novos consumos
                self.db.flush()
                calculo = self._calcular_acerto_financeiro(reserva_id)
            
            # Processar danos se houver
            valor_danos = 0
            if dados_checkout.get("danos_encontrados"):
                valor_danos = float(dados_checkout.get("valor_danos", 0))
                if valor_danos > 0:
                    item_dano = ItemCobranca(
                        reserva_id=reserva_id,
                        tipo=TipoItemCobranca.DANO,
                        descricao=f"Danos: {dados_checkout['danos_encontrados']}",
                        quantidade=1,
                        valor_unitario=Decimal(str(valor_danos))
                    )
                    self.db.add(item_dano)
                    calculo["valor_total_final"] += valor_danos
                    calculo["saldo"] -= valor_danos
            
            # Processar caução
            caucao_devolvida = float(dados_checkout.get("caucao_devolvida", 0))
            caucao_retida = float(dados_checkout.get("caucao_retida", 0))
            
            # Criar registro de checkout
            checkout_record = CheckoutRecord(
                reserva_id=reserva_id,
                checkin_record_id=checkin_record.id,
                checkout_datetime=now_utc(),
                realizado_por_usuario_id=usuario_id,
                
                # Vistoria
                vistoria_ok=dados_checkout.get("vistoria_ok", True),
                danos_encontrados=dados_checkout.get("danos_encontrados"),
                valor_danos=valor_danos,
                
                # Consumos finais (podem vir do form de checkout)
                consumo_frigobar=float(dados_checkout.get("consumo_frigobar", 0)),
                servicos_extras=float(dados_checkout.get("servicos_extras", 0)),
                taxa_late_checkout=float(dados_checkout.get("taxa_late_checkout", 0)),
                
                # Caução
                caucao_devolvida=caucao_devolvida,
                caucao_retida=caucao_retida,
                motivo_retencao=dados_checkout.get("motivo_retencao"),
                
                # Satisfação
                avaliacao_hospede=dados_checkout.get("avaliacao_hospede", 5),
                comentario_hospede=dados_checkout.get("comentario_hospede"),
                
                # Acerto financeiro
                valor_total_final=Decimal(str(calculo["valor_total_final"])),
                saldo_devedor=Decimal(str(calculo["saldo_devedor"])),
                saldo_credor=Decimal(str(calculo["saldo_credor"])),
                forma_acerto=dados_checkout.get("forma_acerto"),
                
                observacoes_checkout=dados_checkout.get("observacoes_checkout")
            )
            
            self.db.add(checkout_record)
            self.db.flush()
            
            # Atualizar status da reserva
            reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
            reserva.status_reserva = StatusReserva.CHECKED_OUT
            reserva.checkout_real = checkout_record.checkout_datetime
            reserva.atualizado_por_usuario_id = usuario_id
            
            # Se há saldo devedor, criar cobrança pendente
            if calculo["saldo_devedor"] > 0:
                # Aqui poderia integrar com sistema de cobrança
                pass
            
            # Se há saldo credor, registrar devolução
            if calculo["saldo_credor"] > 0:
                # Aqui poderia integrar com sistema de estornos
                pass
            
            self.db.commit()
            
            return checkout_record
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Erro ao registrar check-out: {str(e)}")
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleViolation(f"Falha no check-out: {str(e)}")
    
    def _validar_dados_checkout(self, dados: Dict[str, Any]) -> None:
        """Validação dos dados de check-out"""
        # Validar avaliação
        avaliacao = dados.get("avaliacao_hospede", 5)
        if not isinstance(avaliacao, int) or not (1 <= avaliacao <= 5):
            raise ValidationError("Avaliação deve ser um número entre 1 e 5")
        
        # Validar valores monetários
        campos_monetarios = ["consumo_frigobar", "servicos_extras", "valor_danos", "caucao_devolvida", "caucao_retida"]
        for campo in campos_monetarios:
            if campo in dados:
                try:
                    valor = float(dados[campo])
                    if valor < 0:
                        raise ValueError()
                except (ValueError, TypeError):
                    raise ValidationError(f"Valor inválido para {campo}")
    
    def consultar_checkout(self, reserva_id: int) -> Optional[Dict[str, Any]]:
        """Consulta dados completos do check-out"""
        checkout = self.db.query(CheckoutRecord).filter(
            CheckoutRecord.reserva_id == reserva_id
        ).first()
        
        if not checkout:
            return None
        
        return {
            "id": checkout.id,
            "checkout_datetime": checkout.checkout_datetime.isoformat(),
            "realizado_por": checkout.realizado_por.nome if checkout.realizado_por else "N/A",
            "vistoria": {
                "ok": checkout.vistoria_ok,
                "danos": checkout.danos_encontrados,
                "valor_danos": float(checkout.valor_danos or 0)
            },
            "consumos": {
                "frigobar": float(checkout.consumo_frigobar or 0),
                "servicos_extras": float(checkout.servicos_extras or 0),
                "taxa_late": float(checkout.taxa_late_checkout or 0)
            },
            "caucao": {
                "devolvida": float(checkout.caucao_devolvida or 0),
                "retida": float(checkout.caucao_retida or 0),
                "motivo_retencao": checkout.motivo_retencao
            },
            "satisfacao": {
                "avaliacao": checkout.avaliacao_hospede,
                "comentario": checkout.comentario_hospede
            },
            "financeiro": {
                "valor_total_final": float(checkout.valor_total_final),
                "saldo_devedor": float(checkout.saldo_devedor or 0),
                "saldo_credor": float(checkout.saldo_credor or 0),
                "forma_acerto": checkout.forma_acerto
            }
        }
    
    def obter_relatorio_checkouts_dia(self, data: datetime.date) -> List[Dict[str, Any]]:
        """Relatório de check-outs do dia para operação"""
        checkouts = self.db.query(CheckoutRecord).filter(
            CheckoutRecord.checkout_datetime >= datetime.combine(data, datetime.min.time().replace(tzinfo=timezone.utc)),
            CheckoutRecord.checkout_datetime < datetime.combine(data, datetime.max.time().replace(tzinfo=timezone.utc))
        ).all()
        
        relatorio = []
        for checkout in checkouts:
            relatorio.append({
                "checkout_datetime": checkout.checkout_datetime.strftime("%H:%M"),
                "reserva_codigo": checkout.reserva.codigo_reserva,
                "cliente": checkout.reserva.cliente.nome_completo,
                "quarto": checkout.reserva.quarto.numero if checkout.reserva.quarto else "N/A",
                "valor_final": float(checkout.valor_total_final),
                "saldo_devedor": float(checkout.saldo_devedor or 0),
                "avaliacao": checkout.avaliacao_hospede,
                "danos": "Sim" if checkout.valor_danos and checkout.valor_danos > 0 else "Não"
            })
        
        return sorted(relatorio, key=lambda x: x["checkout_datetime"])
