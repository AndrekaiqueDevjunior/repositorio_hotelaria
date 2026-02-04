from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.reserva import Reserva
from app.models.hotel import Quarto
from app.models.checkin_checkout import CheckinRecord, CheckoutRecord
from app.core.enums import StatusReserva, StatusQuarto
from app.utils.datetime_utils import now_utc
from app.core.exceptions import ValidationError


class OperacionalService:
    """
    Serviço para visão operacional diária do hotel
    Essencial para gestão eficiente da operação
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def obter_mapa_ocupacao(self, data_referencia: date) -> Dict[str, Any]:
        """
        Mapa completo de ocupação para a data específica
        Mostra status de cada quarto e movimentação do dia
        """
        inicio_dia = datetime.combine(data_referencia, datetime.min.time().replace(tzinfo=timezone.utc))
        fim_dia = datetime.combine(data_referencia, datetime.max.time().replace(tzinfo=timezone.utc))
        
        # Buscar todos os quartos
        quartos = self.db.query(Quarto).filter(
            Quarto.status == StatusQuarto.ATIVO
        ).order_by(Quarto.numero).all()
        
        # Buscar reservas que afetam a data
        reservas_periodo = self.db.query(Reserva).filter(
            and_(
                Reserva.checkin_previsto <= fim_dia,
                Reserva.checkout_previsto >= inicio_dia,
                Reserva.status_reserva.in_([
                    StatusReserva.CONFIRMADA, 
                    StatusReserva.HOSPEDADO, 
                    StatusReserva.CHECKED_OUT
                ])
            )
        ).all()
        
        # Mapear ocupação por quarto
        mapa_ocupacao = {}
        
        for quarto in quartos:
            # Buscar reserva ativa para este quarto na data
            reserva_ativa = None
            for reserva in reservas_periodo:
                if (reserva.quarto_id == quarto.id and 
                    reserva.checkin_previsto.date() <= data_referencia <= reserva.checkout_previsto.date()):
                    reserva_ativa = reserva
                    break
            
            if reserva_ativa:
                # Determinar status específico do dia
                status_dia = self._determinar_status_quarto_dia(reserva_ativa, data_referencia)
                
                # Buscar dados de check-in/out se houver
                checkin_info = self._obter_info_checkin(reserva_ativa.id)
                checkout_info = self._obter_info_checkout(reserva_ativa.id)
                
                mapa_ocupacao[quarto.numero] = {
                    "status": status_dia,
                    "reserva_codigo": reserva_ativa.codigo_reserva,
                    "cliente_nome": reserva_ativa.cliente.nome_completo if reserva_ativa.cliente else "N/A",
                    "checkin_previsto": reserva_ativa.checkin_previsto.strftime("%d/%m %H:%M"),
                    "checkout_previsto": reserva_ativa.checkout_previsto.strftime("%d/%m %H:%M"),
                    "checkin_real": checkin_info["datetime"] if checkin_info else None,
                    "checkout_real": checkout_info["datetime"] if checkout_info else None,
                    "num_hospedes": checkin_info["num_hospedes"] if checkin_info else reserva_ativa.hospedes_adicionais.__len__() + 1,
                    "valor_diaria": float(reserva_ativa.valor_diaria),
                    "dias_hospedagem": (reserva_ativa.checkout_previsto.date() - reserva_ativa.checkin_previsto.date()).days,
                    "tipo_suite": quarto.tipo_suite,
                    "observacoes": self._obter_observacoes_quarto(reserva_ativa.id)
                }
            else:
                # Quarto vago
                mapa_ocupacao[quarto.numero] = {
                    "status": "VAGO",
                    "tipo_suite": quarto.tipo_suite,
                    "pronto_para_ocupacao": quarto.status == StatusQuarto.ATIVO
                }
        
        # Calcular estatísticas do dia
        estatisticas = self._calcular_estatisticas_ocupacao(mapa_ocupacao, data_referencia)
        
        return {
            "data_referencia": data_referencia.isoformat(),
            "total_quartos": len(quartos),
            "mapa_ocupacao": mapa_ocupacao,
            "estatisticas": estatisticas
        }
    
    def _determinar_status_quarto_dia(self, reserva: Reserva, data: date) -> str:
        """Determina status específico do quarto para o dia"""
        hoje = date.today()
        checkin_date = reserva.checkin_previsto.date()
        checkout_date = reserva.checkout_previsto.date()
        
        if reserva.status_reserva == StatusReserva.CHECKED_OUT:
            if data == checkout_date:
                return "SAIDA_HOJE"
            else:
                return "CHECKOUT_REALIZADO"
        elif reserva.status_reservva == StatusReserva.HOSPEDADO:
            if data == checkin_date:
                return "ENTRADA_HOJE"
            elif data == checkout_date:
                return "SAIDA_HOJE"
            else:
                return "OCUPADO"
        elif reserva.status_reserva == StatusReserva.CONFIRMADA:
            if data == checkin_date:
                return "CHEGADA_PREVISTA"
            elif data == checkout_date:
                return "SAIDA_PREVISTA" 
            else:
                return "RESERVADO"
        else:
            return "INDEFINIDO"
    
    def _obter_info_checkin(self, reserva_id: int) -> Optional[Dict[str, Any]]:
        """Obtém informações do check-in se realizado"""
        checkin = self.db.query(CheckinRecord).filter(
            CheckinRecord.reserva_id == reserva_id
        ).first()
        
        if checkin:
            return {
                "datetime": checkin.checkin_datetime.strftime("%d/%m %H:%M"),
                "num_hospedes": checkin.num_hospedes_real,
                "caucao": float(checkin.caucao_cobrada or 0)
            }
        return None
    
    def _obter_info_checkout(self, reserva_id: int) -> Optional[Dict[str, Any]]:
        """Obtém informações do check-out se realizado"""
        checkout = self.db.query(CheckoutRecord).filter(
            CheckoutRecord.reserva_id == reserva_id
        ).first()
        
        if checkout:
            return {
                "datetime": checkout.checkout_datetime.strftime("%d/%m %H:%M"),
                "avaliacao": checkout.avaliacao_hospede,
                "valor_final": float(checkout.valor_total_final)
            }
        return None
    
    def _obter_observacoes_quarto(self, reserva_id: int) -> str:
        """Obtém observações relevantes do quarto/hospedagem"""
        observacoes = []
        
        # Verificar consumos pendentes
        from app.models.reserva import ItemCobranca
        consumos = self.db.query(ItemCobranca).filter(
            ItemCobranca.reserva_id == reserva_id
        ).count()
        
        if consumos > 0:
            observacoes.append(f"{consumos} consumo(s)")
        
        # Verificar late checkout
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if reserva and reserva.status_reserva == StatusReserva.HOSPEDADO:
            checkout_limite = reserva.checkout_previsto + timedelta(hours=1)
            if now_utc() > checkout_limite:
                observacoes.append("LATE CHECKOUT")
        
        return "; ".join(observacoes) if observacoes else ""
    
    def _calcular_estatisticas_ocupacao(self, mapa: Dict[str, Any], data: date) -> Dict[str, Any]:
        """Calcula estatísticas de ocupação"""
        total_quartos = len(mapa)
        quartos_ocupados = len([q for q in mapa.values() if q["status"] not in ["VAGO"]])
        quartos_vagos = total_quartos - quartos_ocupados
        
        entradas_hoje = len([q for q in mapa.values() if q["status"] in ["ENTRADA_HOJE", "CHEGADA_PREVISTA"]])
        saidas_hoje = len([q for q in mapa.values() if q["status"] in ["SAIDA_HOJE", "SAIDA_PREVISTA"]])
        
        taxa_ocupacao = (quartos_ocupados / total_quartos * 100) if total_quartos > 0 else 0
        
        return {
            "total_quartos": total_quartos,
            "quartos_ocupados": quartos_ocupados,
            "quartos_vagos": quartos_vagos,
            "taxa_ocupacao": round(taxa_ocupacao, 1),
            "entradas_hoje": entradas_hoje,
            "saidas_hoje": saidas_hoje
        }
    
    def obter_movimentacao_diaria(self, data: date) -> Dict[str, Any]:
        """
        Relatório detalhado de movimentação do dia
        Entradas, saídas e status operacional
        """
        inicio_dia = datetime.combine(data, datetime.min.time().replace(tzinfo=timezone.utc))
        fim_dia = datetime.combine(data, datetime.max.time().replace(tzinfo=timezone.utc))
        
        # Check-ins do dia
        checkins_dia = self.db.query(CheckinRecord).filter(
            and_(
                CheckinRecord.checkin_datetime >= inicio_dia,
                CheckinRecord.checkin_datetime <= fim_dia
            )
        ).order_by(CheckinRecord.checkin_datetime).all()
        
        # Check-outs do dia
        checkouts_dia = self.db.query(CheckoutRecord).filter(
            and_(
                CheckoutRecord.checkout_datetime >= inicio_dia,
                CheckoutRecord.checkout_datetime <= fim_dia
            )
        ).order_by(CheckoutRecord.checkout_datetime).all()
        
        # Check-ins esperados (mas não realizados)
        checkins_esperados = self.db.query(Reserva).filter(
            and_(
                func.date(Reserva.checkin_previsto) == data,
                Reserva.status_reserva == StatusReserva.CONFIRMADA
            )
        ).all()
        
        # Check-outs esperados (mas não realizados)
        checkouts_esperados = self.db.query(Reserva).filter(
            and_(
                func.date(Reserva.checkout_previsto) == data,
                Reserva.status_reserva == StatusReserva.HOSPEDADO
            )
        ).all()
        
        return {
            "data": data.isoformat(),
            "checkins_realizados": [
                {
                    "hora": c.checkin_datetime.strftime("%H:%M"),
                    "reserva": c.reserva.codigo_reserva,
                    "cliente": c.hospede_titular_nome,
                    "quarto": c.reserva.quarto.numero if c.reserva.quarto else "N/A",
                    "hospedes": c.num_hospedes_real,
                    "caucao": float(c.caucao_cobrada or 0)
                }
                for c in checkins_dia
            ],
            "checkouts_realizados": [
                {
                    "hora": c.checkout_datetime.strftime("%H:%M"),
                    "reserva": c.reserva.codigo_reserva,
                    "cliente": c.reserva.cliente.nome_completo if c.reserva.cliente else "N/A",
                    "quarto": c.reserva.quarto.numero if c.reserva.quarto else "N/A",
                    "avaliacao": c.avaliacao_hospede,
                    "valor_final": float(c.valor_total_final)
                }
                for c in checkouts_dia
            ],
            "checkins_pendentes": [
                {
                    "hora_prevista": r.checkin_previsto.strftime("%H:%M"),
                    "reserva": r.codigo_reserva,
                    "cliente": r.cliente.nome_completo if r.cliente else "N/A",
                    "quarto": r.quarto.numero if r.quarto else "N/A",
                    "status_pagamento": r.status_financeiro.value if r.status_financeiro else "N/A"
                }
                for r in checkins_esperados
            ],
            "checkouts_pendentes": [
                {
                    "hora_prevista": r.checkout_previsto.strftime("%H:%M"),
                    "reserva": r.codigo_reserva,
                    "cliente": r.cliente.nome_completo if r.cliente else "N/A",
                    "quarto": r.quarto.numero if r.quarto else "N/A",
                    "dias_hospedado": (now_utc().date() - r.checkin_real.date()).days if r.checkin_real else 0
                }
                for r in checkouts_esperados
            ],
            "resumo": {
                "checkins_realizados": len(checkins_dia),
                "checkouts_realizados": len(checkouts_dia),
                "checkins_pendentes": len(checkins_esperados),
                "checkouts_pendentes": len(checkouts_esperados)
            }
        }
    
    def obter_taxa_ocupacao_periodo(
        self, 
        data_inicio: date, 
        data_fim: date
    ) -> Dict[str, Any]:
        """
        Análise de taxa de ocupação por período
        Fundamental para gestão de receita
        """
        if data_fim < data_inicio:
            raise ValidationError("Data fim deve ser posterior à data início")
        
        dias_periodo = (data_fim - data_inicio).days + 1
        if dias_periodo > 90:
            raise ValidationError("Período máximo de 90 dias")
        
        # Total de quartos disponíveis
        total_quartos = self.db.query(Quarto).filter(
            Quarto.status == StatusQuarto.ATIVO
        ).count()
        
        # Análise dia a dia
        ocupacao_diaria = []
        total_quartos_noite = 0
        total_ocupados = 0
        total_receita = 0
        
        data_atual = data_inicio
        while data_atual <= data_fim:
            mapa_dia = self.obter_mapa_ocupacao(data_atual)
            quartos_ocupados_dia = mapa_dia["estatisticas"]["quartos_ocupados"]
            
            # Calcular receita do dia
            receita_dia = 0
            for quarto_info in mapa_dia["mapa_ocupacao"].values():
                if quarto_info["status"] not in ["VAGO"] and "valor_diaria" in quarto_info:
                    receita_dia += quarto_info["valor_diaria"]
            
            ocupacao_diaria.append({
                "data": data_atual.strftime("%d/%m/%Y"),
                "dia_semana": self._obter_dia_semana(data_atual),
                "quartos_disponiveis": total_quartos,
                "quartos_ocupados": quartos_ocupados_dia,
                "taxa_ocupacao": mapa_dia["estatisticas"]["taxa_ocupacao"],
                "receita": receita_dia
            })
            
            total_quartos_noite += total_quartos
            total_ocupados += quartos_ocupados_dia
            total_receita += receita_dia
            
            data_atual += timedelta(days=1)
        
        taxa_ocupacao_media = (total_ocupados / total_quartos_noite * 100) if total_quartos_noite > 0 else 0
        receita_media_diaria = total_receita / dias_periodo if dias_periodo > 0 else 0
        
        return {
            "periodo": f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
            "dias_analisados": dias_periodo,
            "taxa_ocupacao_media": round(taxa_ocupacao_media, 1),
            "receita_total": total_receita,
            "receita_media_diaria": round(receita_media_diaria, 2),
            "quartos_noite_total": total_quartos_noite,
            "quartos_noite_ocupadas": total_ocupados,
            "ocupacao_diaria": ocupacao_diaria,
            "analise": {
                "melhor_dia": max(ocupacao_diaria, key=lambda x: x["taxa_ocupacao"]) if ocupacao_diaria else None,
                "pior_dia": min(ocupacao_diaria, key=lambda x: x["taxa_ocupacao"]) if ocupacao_diaria else None,
                "maior_receita": max(ocupacao_diaria, key=lambda x: x["receita"]) if ocupacao_diaria else None
            }
        }
    
    def _obter_dia_semana(self, data: date) -> str:
        """Retorna dia da semana em português"""
        dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        return dias[data.weekday()]
    
    def obter_previsao_ocupacao(self, dias_futuro: int = 30) -> Dict[str, Any]:
        """
        Previsão de ocupação para os próximos dias
        Auxilia planejamento operacional
        """
        if dias_futuro > 365:
            raise ValidationError("Máximo 365 dias de previsão")
        
        data_inicio = date.today()
        data_fim = data_inicio + timedelta(days=dias_futuro)
        
        # Reservas confirmadas no período
        reservas_futuras = self.db.query(Reserva).filter(
            and_(
                Reserva.checkin_previsto >= datetime.combine(data_inicio, datetime.min.time().replace(tzinfo=timezone.utc)),
                Reserva.checkin_previsto <= datetime.combine(data_fim, datetime.max.time().replace(tzinfo=timezone.utc)),
                Reserva.status_reserva.in_([StatusReserva.CONFIRMADA, StatusReserva.HOSPEDADO])
            )
        ).all()
        
        # Agrupar por data
        previsao_por_data = {}
        total_quartos = self.db.query(Quarto).filter(Quarto.status == StatusQuarto.ATIVO).count()
        
        for reserva in reservas_futuras:
            data_checkin = reserva.checkin_previsto.date()
            
            if data_checkin not in previsao_por_data:
                previsao_por_data[data_checkin] = {
                    "chegadas": 0,
                    "receita_prevista": 0,
                    "status_pagamento": {"PAGO": 0, "PENDENTE": 0}
                }
            
            previsao_por_data[data_checkin]["chegadas"] += 1
            previsao_por_data[data_checkin]["receita_prevista"] += float(reserva.valor_previsto)
            
            if reserva.status_financeiro in [StatusFinanceiro.PAGO_TOTAL, StatusFinanceiro.SINAL_PAGO]:
                previsao_por_data[data_checkin]["status_pagamento"]["PAGO"] += 1
            else:
                previsao_por_data[data_checkin]["status_pagamento"]["PENDENTE"] += 1
        
        # Converter para lista ordenada
        previsao_lista = []
        data_atual = data_inicio
        
        while data_atual <= data_fim:
            dados_dia = previsao_por_data.get(data_atual, {
                "chegadas": 0, 
                "receita_prevista": 0,
                "status_pagamento": {"PAGO": 0, "PENDENTE": 0}
            })
            
            previsao_lista.append({
                "data": data_atual.strftime("%d/%m/%Y"),
                "dia_semana": self._obter_dia_semana(data_atual),
                "chegadas_previstas": dados_dia["chegadas"],
                "taxa_ocupacao_estimada": round((dados_dia["chegadas"] / total_quartos * 100), 1) if total_quartos > 0 else 0,
                "receita_prevista": dados_dia["receita_prevista"],
                "pagamentos_ok": dados_dia["status_pagamento"]["PAGO"],
                "pagamentos_pendentes": dados_dia["status_pagamento"]["PENDENTE"]
            })
            
            data_atual += timedelta(days=1)
        
        total_chegadas = sum(p["chegadas_previstas"] for p in previsao_lista)
        total_receita = sum(p["receita_prevista"] for p in previsao_lista)
        
        return {
            "periodo_previsao": f"{dias_futuro} dias",
            "data_inicio": data_inicio.strftime("%d/%m/%Y"),
            "data_fim": data_fim.strftime("%d/%m/%Y"),
            "total_chegadas_previstas": total_chegadas,
            "receita_total_prevista": total_receita,
            "receita_media_diaria": round(total_receita / dias_futuro, 2) if dias_futuro > 0 else 0,
            "previsao_diaria": previsao_lista,
            "alertas": self._gerar_alertas_previsao(previsao_lista, total_quartos)
        }
    
    def _gerar_alertas_previsao(self, previsao: List[Dict], total_quartos: int) -> List[str]:
        """Gera alertas baseados na previsão"""
        alertas = []
        
        # Dias com alta ocupação
        dias_alta = [p for p in previsao if p["taxa_ocupacao_estimada"] > 90]
        if dias_alta:
            alertas.append(f"{len(dias_alta)} dia(s) com ocupação acima de 90%")
        
        # Dias com baixa ocupação
        dias_baixa = [p for p in previsao if p["taxa_ocupacao_estimada"] < 30]
        if dias_baixa:
            alertas.append(f"{len(dias_baixa)} dia(s) com ocupação abaixo de 30%")
        
        # Pagamentos pendentes
        total_pendentes = sum(p["pagamentos_pendentes"] for p in previsao)
        if total_pendentes > 0:
            alertas.append(f"{total_pendentes} reserva(s) com pagamento pendente")
        
        return alertas
