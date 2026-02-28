from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.checkin_checkout import CheckinRecord, HospedeCheckin
from app.models.reserva import Reserva
from app.models.pagamento import Pagamento
from app.core.enums import (
    StatusReserva, StatusPagamento, StatusFinanceiro, 
    MotivoCheckinBloqueado, TipoDocumentoHospede
)
from app.utils.datetime_utils import now_utc
from app.core.exceptions import BusinessRuleViolation, ValidationError


class CheckinValidationError(Exception):
    """Erro específico para validações de check-in"""
    def __init__(self, motivo: MotivoCheckinBloqueado, detalhes: str = ""):
        self.motivo = motivo
        self.detalhes = detalhes
        super().__init__(f"{motivo.value}: {detalhes}")


class CheckinService:
    """Serviço profissional para gerenciamento de Check-in"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validar_pre_checkin(self, reserva_id: int) -> Dict[str, Any]:
        """
        Validação completa pré-check-in
        Retorna status e bloqueios encontrados
        """
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        bloqueios = []
        warnings = []
        
        # 1. VALIDAÇÃO CRÍTICA: Status deve ser CONFIRMADA
        # Regra de ouro: Check-in só pode acontecer se pagamento foi aprovado
        if reserva.status_reserva != "CONFIRMADA":
            if reserva.status_reserva == "PENDENTE_PAGAMENTO":
                bloqueios.append({
                    "motivo": MotivoCheckinBloqueado.PAGAMENTO_PENDENTE,
                    "descricao": "Reserva aguardando pagamento"
                })
            elif reserva.status_reserva == "AGUARDANDO_COMPROVANTE":
                bloqueios.append({
                    "motivo": MotivoCheckinBloqueado.PAGAMENTO_PENDENTE,
                    "descricao": "Aguardando upload do comprovante de pagamento"
                })
            elif reserva.status_reserva == "EM_ANALISE":
                bloqueios.append({
                    "motivo": MotivoCheckinBloqueado.PAGAMENTO_PENDENTE,
                    "descricao": "Comprovante em análise pelo administrador"
                })
            elif reserva.status_reserva == "PAGA_REJEITADA":
                bloqueios.append({
                    "motivo": MotivoCheckinBloqueado.PAGAMENTO_PENDENTE,
                    "descricao": "Comprovante de pagamento foi rejeitado"
                })
            elif reserva.status_reserva == "CANCELADA":
                bloqueios.append({
                    "motivo": MotivoCheckinBloqueado.RESERVA_CANCELADA,
                    "descricao": "Reserva foi cancelada"
                })
            elif reserva.status_reserva == "CHECKIN_REALIZADO":
                bloqueios.append({
                    "motivo": "JA_HOSPEDADO",
                    "descricao": "Check-in já realizado"
                })
            else:
                # Qualquer outro status não permitido
                bloqueios.append({
                    "motivo": MotivoCheckinBloqueado.PAGAMENTO_PENDENTE,
                    "descricao": f"Status da reserva não permite check-in: {reserva.status_reserva}"
                })
        
        # 2. Validar pagamentos
        pagamentos_aprovados = self.db.query(Pagamento).filter(
            Pagamento.reserva_id == reserva_id,
            Pagamento.status == StatusPagamento.CONFIRMADO
        ).all()
        
        valor_pago = sum(p.valor for p in pagamentos_aprovados)
        valor_minimo = reserva.valor_previsto * 0.8  # Exige 80% mínimo pago
        
        if valor_pago < valor_minimo:
            bloqueios.append({
                "motivo": MotivoCheckinBloqueado.PAGAMENTO_PENDENTE,
                "descricao": f"Pagamento insuficiente: R$ {valor_pago:.2f} de R$ {valor_minimo:.2f} mínimo"
            })
        elif valor_pago < reserva.valor_previsto:
            warnings.append(f"Pagamento parcial: R$ {valor_pago:.2f} de R$ {reserva.valor_previsto:.2f}")
        
        # 3. Validar disponibilidade do quarto
        if reserva.quarto:
            # Verificar se há checkout pendente no mesmo quarto
            checkout_pendente = self.db.query(Reserva).filter(
                Reserva.quarto_id == reserva.quarto_id,
                Reserva.status_reserva == StatusReserva.HOSPEDADO,
                Reserva.id != reserva.id
            ).first()
            
            if checkout_pendente:
                bloqueios.append({
                    "motivo": MotivoCheckinBloqueado.CHECKOUT_PENDENTE_MESMO_QUARTO,
                    "descricao": f"Quarto {reserva.quarto.numero} ainda ocupado por reserva #{checkout_pendente.codigo_reserva}"
                })
        
        # 4. Validar overbooking
        mesmo_periodo = self.db.query(Reserva).filter(
            Reserva.quarto_id == reserva.quarto_id,
            Reserva.status_reserva.in_([StatusReserva.CONFIRMADA, StatusReserva.HOSPEDADO]),
            Reserva.checkin_previsto <= reserva.checkout_previsto,
            Reserva.checkout_previsto >= reserva.checkin_previsto,
            Reserva.id != reserva.id
        ).count()
        
        if mesmo_periodo > 0:
            bloqueios.append({
                "motivo": MotivoCheckinBloqueado.OVERBOOKING,
                "descricao": f"Conflito: {mesmo_periodo} reserva(s) no mesmo período"
            })
        
        return {
            "pode_fazer_checkin": len(bloqueios) == 0,
            "bloqueios": bloqueios,
            "warnings": warnings,
            "reserva": {
                "id": reserva.id,
                "codigo": reserva.codigo_reserva,
                "cliente": reserva.cliente.nome_completo,
                "quarto": reserva.quarto.numero if reserva.quarto else "N/A",
                "valor_previsto": float(reserva.valor_previsto),
                "valor_pago": float(valor_pago)
            }
        }
    
    def realizar_checkin(
        self,
        reserva_id: int,
        usuario_id: int,
        dados_checkin: Dict[str, Any]
    ) -> CheckinRecord:
        """
        Realiza o check-in formal com todas as validações
        """
        # Validação pré-checkin obrigatória
        validacao = self.validar_pre_checkin(reserva_id)
        if not validacao["pode_fazer_checkin"]:
            raise CheckinValidationError(
                MotivoCheckinBloqueado.PAGAMENTO_PENDENTE,
                f"Check-in bloqueado: {'; '.join([b['descricao'] for b in validacao['bloqueios']])}"
            )
        
        # Validar dados obrigatórios
        self._validar_dados_checkin(dados_checkin)
        
        try:
            # Criar registro de check-in
            checkin_record = CheckinRecord(
                reserva_id=reserva_id,
                checkin_datetime=now_utc(),
                realizado_por_usuario_id=usuario_id,
                
                # Dados do titular
                hospede_titular_nome=dados_checkin["hospede_titular_nome"],
                hospede_titular_documento=dados_checkin["hospede_titular_documento"],
                hospede_titular_documento_tipo=dados_checkin["hospede_titular_documento_tipo"],
                
                # Validações
                pagamento_validado=dados_checkin.get("pagamento_validado", True),
                documentos_conferidos=dados_checkin.get("documentos_conferidos", True),
                termos_aceitos=dados_checkin.get("termos_aceitos", True),
                assinatura_digital=dados_checkin.get("assinatura_digital"),
                
                # Dados da hospedagem
                num_hospedes_real=dados_checkin["num_hospedes_real"],
                num_criancas=dados_checkin.get("num_criancas", 0),
                veiculo_placa=dados_checkin.get("veiculo_placa"),
                observacoes_checkin=dados_checkin.get("observacoes_checkin"),
                
                # Caução
                caucao_cobrada=dados_checkin.get("caucao_cobrada", 0),
                caucao_forma_pagamento=dados_checkin.get("caucao_forma_pagamento")
            )
            
            self.db.add(checkin_record)
            self.db.flush()  # Para obter o ID
            
            # Registrar hóspedes individuais
            if "hospedes" in dados_checkin:
                for hospede_data in dados_checkin["hospedes"]:
                    hospede = HospedeCheckin(
                        checkin_record_id=checkin_record.id,
                        nome_completo=hospede_data["nome_completo"],
                        documento=hospede_data["documento"],
                        documento_tipo=hospede_data["documento_tipo"],
                        nacionalidade=hospede_data.get("nacionalidade", "Brasil"),
                        data_nascimento=hospede_data.get("data_nascimento"),
                        telefone=hospede_data.get("telefone"),
                        email=hospede_data.get("email"),
                        e_menor=hospede_data.get("e_menor", False),
                        responsavel_nome=hospede_data.get("responsavel_nome"),
                        responsavel_documento=hospede_data.get("responsavel_documento")
                    )
                    self.db.add(hospede)
            
            # Atualizar status da reserva para CHECKIN_REALIZADO
            reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
            reserva.status_reserva = "CHECKIN_REALIZADO"
            reserva.checkin_real = checkin_record.checkin_datetime
            reserva.atualizado_por_usuario_id = usuario_id
            
            self.db.commit()
            
            return checkin_record
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Erro ao registrar check-in: {str(e)}")
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleViolation(f"Falha no check-in: {str(e)}")
    
    def _validar_dados_checkin(self, dados: Dict[str, Any]) -> None:
        """Validação dos dados obrigatórios para check-in"""
        campos_obrigatorios = [
            "hospede_titular_nome",
            "hospede_titular_documento", 
            "hospede_titular_documento_tipo",
            "num_hospedes_real"
        ]
        
        for campo in campos_obrigatorios:
            if campo not in dados or not dados[campo]:
                raise ValidationError(f"Campo obrigatório ausente: {campo}")
        
        # Validar tipo de documento
        if dados["hospede_titular_documento_tipo"] not in [t.value for t in TipoDocumentoHospede]:
            raise ValidationError(f"Tipo de documento inválido: {dados['hospede_titular_documento_tipo']}")
        
        # Validar número de hóspedes
        if dados["num_hospedes_real"] <= 0:
            raise ValidationError("Número de hóspedes deve ser maior que zero")
        
        # Validar assinatura/aceite de termos
        if not dados.get("termos_aceitos", False):
            raise ValidationError("Aceite dos termos de hospedagem é obrigatório")
    
    def consultar_checkin(self, reserva_id: int) -> Optional[Dict[str, Any]]:
        """Consulta dados completos do check-in"""
        checkin = self.db.query(CheckinRecord).filter(
            CheckinRecord.reserva_id == reserva_id
        ).first()
        
        if not checkin:
            return None
        
        return {
            "id": checkin.id,
            "checkin_datetime": checkin.checkin_datetime.isoformat(),
            "realizado_por": checkin.realizado_por.nome if checkin.realizado_por else "N/A",
            "hospede_titular": {
                "nome": checkin.hospede_titular_nome,
                "documento": checkin.hospede_titular_documento,
                "documento_tipo": checkin.hospede_titular_documento_tipo
            },
            "hospedagem": {
                "num_hospedes_real": checkin.num_hospedes_real,
                "num_criancas": checkin.num_criancas,
                "veiculo_placa": checkin.veiculo_placa,
                "observacoes": checkin.observacoes_checkin
            },
            "caucao": {
                "cobrada": float(checkin.caucao_cobrada or 0),
                "forma_pagamento": checkin.caucao_forma_pagamento
            },
            "hospedes_registrados": [
                {
                    "nome": h.nome_completo,
                    "documento": h.documento,
                    "documento_tipo": h.documento_tipo,
                    "nacionalidade": h.nacionalidade,
                    "e_menor": h.e_menor
                }
                for h in checkin.hospedes_registrados
            ]
        }
