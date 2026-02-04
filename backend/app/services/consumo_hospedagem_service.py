from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from decimal import Decimal

from app.models.reserva import Reserva, ItemCobranca
from app.models.checkin_checkout import CheckinRecord
from app.core.enums import StatusReserva, TipoItemCobranca
from app.utils.datetime_utils import now_utc
from app.core.exceptions import BusinessRuleViolation, ValidationError
from sqlalchemy.orm import Session


class ConsumoHospedagemService:
    """
    Serviço profissional para gestão de consumos durante a hospedagem
    Fundamental para operação hoteleira real
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def validar_hospedagem_ativa(self, reserva_id: int) -> bool:
        """Verifica se a reserva está em hospedagem ativa"""
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        if reserva.status_reserva != StatusReserva.HOSPEDADO:
            raise BusinessRuleViolation(
                f"Consumos só podem ser lançados durante hospedagem ativa. "
                f"Status atual: {reserva.status_reserva.value}"
            )
        
        # Verificar se existe check-in
        checkin = self.db.query(CheckinRecord).filter(
            CheckinRecord.reserva_id == reserva_id
        ).first()
        
        if not checkin:
            raise BusinessRuleViolation("Consumos requerem check-in realizado")
        
        return True
    
    def lancar_consumo_frigobar(
        self, 
        reserva_id: int, 
        itens_consumidos: List[Dict[str, Any]], 
        usuario_id: int
    ) -> Dict[str, Any]:
        """
        Lança consumo de frigobar
        itens_consumidos: [{"item": "Água 500ml", "quantidade": 2, "valor_unitario": 3.50}]
        """
        self.validar_hospedagem_ativa(reserva_id)
        
        total_consumo = Decimal('0')
        itens_criados = []
        
        for item in itens_consumidos:
            if not all(k in item for k in ["item", "quantidade", "valor_unitario"]):
                raise ValidationError("Item deve ter: item, quantidade, valor_unitario")
            
            if item["quantidade"] <= 0:
                raise ValidationError(f"Quantidade inválida: {item['quantidade']}")
            
            valor_unitario = Decimal(str(item["valor_unitario"]))
            quantidade = int(item["quantidade"])
            valor_total = valor_unitario * quantidade
            
            item_cobranca = ItemCobranca(
                reserva_id=reserva_id,
                tipo=TipoItemCobranca.CONSUMO_FRIGOBAR,
                descricao=f"Frigobar: {item['item']}",
                quantidade=quantidade,
                valor_unitario=valor_unitario
            )
            
            self.db.add(item_cobranca)
            self.db.flush()
            
            itens_criados.append({
                "id": item_cobranca.id,
                "item": item["item"],
                "quantidade": quantidade,
                "valor_unitario": float(valor_unitario),
                "valor_total": float(valor_total)
            })
            
            total_consumo += valor_total
        
        self.db.commit()
        
        return {
            "success": True,
            "total_consumo": float(total_consumo),
            "itens_lancados": len(itens_criados),
            "detalhes": itens_criados,
            "lancado_em": now_utc().isoformat(),
            "lancado_por": usuario_id
        }
    
    def lancar_servico_extra(
        self, 
        reserva_id: int, 
        servico: str, 
        valor: Decimal, 
        observacoes: str = None,
        usuario_id: int = None
    ) -> Dict[str, Any]:
        """
        Lança serviço extra (lavanderia, room service, spa, etc.)
        """
        self.validar_hospedagem_ativa(reserva_id)
        
        if valor <= 0:
            raise ValidationError("Valor do serviço deve ser positivo")
        
        item_cobranca = ItemCobranca(
            reserva_id=reserva_id,
            tipo=TipoItemCobranca.SERVICO_EXTRA,
            descricao=f"Serviço: {servico}" + (f" - {observacoes}" if observacoes else ""),
            quantidade=1,
            valor_unitario=valor
        )
        
        self.db.add(item_cobranca)
        self.db.commit()
        
        return {
            "success": True,
            "servico": servico,
            "valor": float(valor),
            "item_id": item_cobranca.id,
            "lancado_em": now_utc().isoformat()
        }
    
    def aplicar_multa(
        self, 
        reserva_id: int, 
        motivo: str, 
        valor: Decimal, 
        usuario_id: int
    ) -> Dict[str, Any]:
        """
        Aplica multa por infrações (fumo, barulho, danos leves, etc.)
        """
        self.validar_hospedagem_ativa(reserva_id)
        
        if valor <= 0:
            raise ValidationError("Valor da multa deve ser positivo")
        
        if len(motivo.strip()) < 10:
            raise ValidationError("Motivo da multa deve ter pelo menos 10 caracteres")
        
        item_cobranca = ItemCobranca(
            reserva_id=reserva_id,
            tipo=TipoItemCobranca.MULTA,
            descricao=f"MULTA: {motivo}",
            quantidade=1,
            valor_unitario=valor
        )
        
        self.db.add(item_cobranca)
        self.db.commit()
        
        # Log da multa para auditoria
        print(f"[MULTA] Reserva {reserva_id} - R$ {valor} - {motivo} - Por usuário {usuario_id}")
        
        return {
            "success": True,
            "tipo": "MULTA",
            "motivo": motivo,
            "valor": float(valor),
            "item_id": item_cobranca.id,
            "aplicada_em": now_utc().isoformat(),
            "aplicada_por": usuario_id
        }
    
    def registrar_dano(
        self, 
        reserva_id: int, 
        descricao_dano: str, 
        valor_reparo: Decimal, 
        evidencias: str = None,
        usuario_id: int = None
    ) -> Dict[str, Any]:
        """
        Registra dano ao quarto/propriedade
        """
        self.validar_hospedagem_ativa(reserva_id)
        
        if valor_reparo <= 0:
            raise ValidationError("Valor do reparo deve ser positivo")
        
        if len(descricao_dano.strip()) < 10:
            raise ValidationError("Descrição do dano deve ter pelo menos 10 caracteres")
        
        descricao_completa = f"DANO: {descricao_dano}"
        if evidencias:
            descricao_completa += f" | Evidências: {evidencias}"
        
        item_cobranca = ItemCobranca(
            reserva_id=reserva_id,
            tipo=TipoItemCobranca.DANO,
            descricao=descricao_completa,
            quantidade=1,
            valor_unitario=valor_reparo
        )
        
        self.db.add(item_cobranca)
        self.db.commit()
        
        # Log crítico para auditoria
        print(f"[DANO] Reserva {reserva_id} - R$ {valor_reparo} - {descricao_dano} - Por usuário {usuario_id}")
        
        return {
            "success": True,
            "tipo": "DANO",
            "descricao": descricao_dano,
            "valor_reparo": float(valor_reparo),
            "item_id": item_cobranca.id,
            "registrado_em": now_utc().isoformat(),
            "registrado_por": usuario_id
        }
    
    def aplicar_taxa_late_checkout(
        self, 
        reserva_id: int, 
        horas_excedidas: int, 
        valor_por_hora: Decimal = Decimal('50.00')
    ) -> Dict[str, Any]:
        """
        Aplica taxa de late checkout
        Padrão: R$ 50,00 por hora excedida
        """
        self.validar_hospedagem_ativa(reserva_id)
        
        if horas_excedidas <= 0:
            raise ValidationError("Horas excedidas deve ser positivo")
        
        valor_total = valor_por_hora * horas_excedidas
        
        item_cobranca = ItemCobranca(
            reserva_id=reserva_id,
            tipo=TipoItemCobranca.TAXA_LATE_CHECKOUT,
            descricao=f"Late Checkout: {horas_excedidas}h x R$ {valor_por_hora}/h",
            quantidade=horas_excedidas,
            valor_unitario=valor_por_hora
        )
        
        self.db.add(item_cobranca)
        self.db.commit()
        
        return {
            "success": True,
            "tipo": "TAXA_LATE_CHECKOUT",
            "horas_excedidas": horas_excedidas,
            "valor_por_hora": float(valor_por_hora),
            "valor_total": float(valor_total),
            "item_id": item_cobranca.id,
            "aplicada_em": now_utc().isoformat()
        }
    
    def aplicar_desconto(
        self, 
        reserva_id: int, 
        motivo: str, 
        valor: Decimal, 
        usuario_id: int,
        requer_aprovacao: bool = True
    ) -> Dict[str, Any]:
        """
        Aplica desconto (valor negativo)
        Por cortesia, compensação, etc.
        """
        self.validar_hospedagem_ativa(reserva_id)
        
        if valor <= 0:
            raise ValidationError("Valor do desconto deve ser positivo")
        
        if requer_aprovacao and not usuario_id:
            raise ValidationError("Desconto requer identificação do usuário responsável")
        
        # Valor negativo para desconto
        valor_desconto = -valor
        
        item_cobranca = ItemCobranca(
            reserva_id=reserva_id,
            tipo=TipoItemCobranca.DESCONTO,
            descricao=f"DESCONTO: {motivo}",
            quantidade=1,
            valor_unitario=valor_desconto
        )
        
        self.db.add(item_cobranca)
        self.db.commit()
        
        # Log para auditoria (descontos devem ser rastreados)
        print(f"[DESCONTO] Reserva {reserva_id} - R$ {valor} - {motivo} - Por usuário {usuario_id}")
        
        return {
            "success": True,
            "tipo": "DESCONTO",
            "motivo": motivo,
            "valor_desconto": float(valor),
            "item_id": item_cobranca.id,
            "aplicado_em": now_utc().isoformat(),
            "aplicado_por": usuario_id
        }
    
    def obter_consumos_hospedagem(self, reserva_id: int) -> Dict[str, Any]:
        """
        Consulta todos os consumos da hospedagem atual
        """
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        # Buscar todos os itens de cobrança
        itens = self.db.query(ItemCobranca).filter(
            ItemCobranca.reserva_id == reserva_id
        ).order_by(ItemCobranca.created_at.desc()).all()
        
        # Agrupar por tipo
        consumos_por_tipo = {}
        total_geral = Decimal('0')
        
        for item in itens:
            tipo = item.tipo.value
            valor_item = item.valor_unitario * item.quantidade
            
            if tipo not in consumos_por_tipo:
                consumos_por_tipo[tipo] = {
                    "itens": [],
                    "total": 0,
                    "quantidade_itens": 0
                }
            
            consumos_por_tipo[tipo]["itens"].append({
                "id": item.id,
                "descricao": item.descricao,
                "quantidade": item.quantidade,
                "valor_unitario": float(item.valor_unitario),
                "valor_total": float(valor_item),
                "data": item.created_at.isoformat()
            })
            
            consumos_por_tipo[tipo]["total"] += float(valor_item)
            consumos_por_tipo[tipo]["quantidade_itens"] += 1
            total_geral += valor_item
        
        return {
            "reserva_id": reserva_id,
            "codigo_reserva": reserva.codigo_reserva,
            "cliente": reserva.cliente.nome_completo if reserva.cliente else "N/A",
            "status_hospedagem": reserva.status_reserva.value,
            "total_consumos": float(total_geral),
            "consumos_por_tipo": consumos_por_tipo,
            "resumo_tipos": [
                {
                    "tipo": tipo,
                    "total": dados["total"],
                    "quantidade_itens": dados["quantidade_itens"]
                }
                for tipo, dados in consumos_por_tipo.items()
            ]
        }
    
    def estornar_item_consumo(
        self, 
        item_id: int, 
        motivo: str, 
        usuario_id: int
    ) -> Dict[str, Any]:
        """
        Estorna um item de consumo específico
        Cria item negativo para cancelar o original
        """
        item_original = self.db.query(ItemCobranca).filter(
            ItemCobranca.id == item_id
        ).first()
        
        if not item_original:
            raise ValidationError("Item não encontrado")
        
        # Verificar se a hospedagem ainda está ativa
        self.validar_hospedagem_ativa(item_original.reserva_id)
        
        if len(motivo.strip()) < 5:
            raise ValidationError("Motivo do estorno deve ter pelo menos 5 caracteres")
        
        # Criar item de estorno (valor negativo)
        item_estorno = ItemCobranca(
            reserva_id=item_original.reserva_id,
            tipo=item_original.tipo,
            descricao=f"ESTORNO: {item_original.descricao} - {motivo}",
            quantidade=item_original.quantidade,
            valor_unitario=-item_original.valor_unitario
        )
        
        self.db.add(item_estorno)
        self.db.commit()
        
        valor_estornado = float(item_original.valor_unitario * item_original.quantidade)
        
        # Log para auditoria
        print(f"[ESTORNO] Item {item_id} - R$ {valor_estornado} - {motivo} - Por usuário {usuario_id}")
        
        return {
            "success": True,
            "item_original_id": item_id,
            "item_estorno_id": item_estorno.id,
            "valor_estornado": valor_estornado,
            "motivo": motivo,
            "estornado_em": now_utc().isoformat(),
            "estornado_por": usuario_id
        }
    
    def obter_relatorio_consumos_dia(self, data: datetime.date) -> List[Dict[str, Any]]:
        """
        Relatório de consumos do dia para controle operacional
        """
        inicio_dia = datetime.combine(data, datetime.min.time().replace(tzinfo=timezone.utc))
        fim_dia = datetime.combine(data, datetime.max.time().replace(tzinfo=timezone.utc))
        
        itens_dia = self.db.query(ItemCobranca).filter(
            and_(
                ItemCobranca.created_at >= inicio_dia,
                ItemCobranca.created_at <= fim_dia
            )
        ).order_by(ItemCobranca.created_at).all()
        
        relatorio = []
        for item in itens_dia:
            relatorio.append({
                "hora": item.created_at.strftime("%H:%M"),
                "reserva": item.reserva.codigo_reserva,
                "cliente": item.reserva.cliente.nome_completo if item.reserva.cliente else "N/A",
                "quarto": item.reserva.quarto.numero if item.reserva.quarto else "N/A",
                "tipo": item.tipo.value,
                "descricao": item.descricao,
                "quantidade": item.quantidade,
                "valor_unitario": float(item.valor_unitario),
                "valor_total": float(item.valor_unitario * item.quantidade)
            })
        
        return relatorio
