"""
SERVIÇO DE FLUXO DE RESERVAS
==============================
Orquestra o fluxo completo: Criar → Pagar → Confirmar → Check-in → Checkout
Garante que cada etapa siga a sequência correta
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime
from app.core.unified_state_validator import UnifiedStateValidator
from app.schemas.status_enums import StatusReserva, StatusPagamento
from app.utils.datetime_utils import now_utc
from app.core.database import get_db


class FluxoReservaService:
    """
    Serviço que orquestra o fluxo completo de reservas
    Implementa a sequência: CRIADA → PAGAMENTO → CONFIRMADA → CHECKIN → CHECKOUT
    """
    
    def __init__(self, db):
        self.db = db
        self.validator = UnifiedStateValidator()
    
    # ==================== ETAPA 1: CRIAR RESERVA ====================
    
    async def criar_reserva(self, dados_reserva: Dict[str, Any]) -> Dict[str, Any]:
        """
        Etapa 1: Criar nova reserva
        Status inicial: PENDENTE
        """
        # Validar se pode criar
        pode, motivo = self.validator.pode_criar_reserva()
        if not pode:
            raise ValueError(f"Não pode criar reserva: {motivo}")
        
        # Criar reserva com status PENDENTE
        dados_reserva['status'] = StatusReserva.PENDENTE.value
        dados_reserva['created_at'] = now_utc()
        
        # Inserir no banco (simulação)
        reserva = {
            'id': 1,  # Simulação
            **dados_reserva,
            'status': StatusReserva.PENDENTE.value,
            'fluxo_atual': 'CRIADA_AGUARDANDO_PAGAMENTO'
        }
        
        print(f"[FLUXO] Reserva criada: {reserva['id']} - Status: {reserva['status']}")
        return reserva
    
    # ==================== ETAPA 2: PROCESSAR PAGAMENTO ====================
    
    async def processar_pagamento(self, reserva_id: int, dados_pagamento: Dict[str, Any]) -> Dict[str, Any]:
        """
        Etapa 2: Processar pagamento da reserva
        Transição: PENDENTE → (pagamento) → CONFIRMADA
        """
        # Buscar reserva
        reserva = await self._buscar_reserva(reserva_id)
        
        # Validar se pode pagar
        pode, motivo = self.validator.pode_pagar(reserva)
        if not pode:
            raise ValueError(f"Não pode pagar: {motivo}")
        
        # Criar pagamento
        pagamento = {
            'id': 1,  # Simulação
            'reserva_id': reserva_id,
            'valor': dados_pagamento['valor'],
            'metodo': dados_pagamento['metodo'],
            'status': StatusPagamento.CONFIRMADO.value,  # Simulação de aprovação
            'created_at': now_utc()
        }
        
        # Se pagamento aprovado, confirmar reserva automaticamente
        if pagamento['status'] == StatusPagamento.CONFIRMADO.value:
            reserva = await self.confirmar_reserva_apos_pagamento(reserva, pagamento)
            # Retornar reserva atualizada também
            pagamento['reserva_atualizada'] = reserva
        
        print(f"[FLUXO] Pagamento processado: {pagamento['id']} - Status: {pagamento['status']}")
        return pagamento
    
    async def confirmar_reserva_apos_pagamento(self, reserva: Dict[str, Any], pagamento: Dict[str, Any]) -> Dict[str, Any]:
        """
        Confirma reserva automaticamente após pagamento aprovado
        """
        # Validar se pode confirmar
        pode, motivo = self.validator.pode_confirmar_pagamento(reserva, pagamento)
        if not pode:
            raise ValueError(f"Não pode confirmar: {motivo}")
        
        # Atualizar status da reserva
        reserva['status'] = StatusReserva.CONFIRMADA.value
        reserva['fluxo_atual'] = 'CONFIRMADA_AGUARDANDO_CHECKIN'
        reserva['data_confirmacao'] = now_utc()
        
        print(f"[FLUXO] Reserva confirmada: {reserva['id']} - Status: {reserva['status']}")
        return reserva
    
    # ==================== ETAPA 3: FAZER CHECK-IN ====================
    
    async def fazer_checkin(self, reserva_id: int, dados_checkin: Dict[str, Any]) -> Dict[str, Any]:
        """
        Etapa 3: Realizar check-in
        Transição: CONFIRMADA → CHECKIN_REALIZADO
        """
        # Buscar reserva e pagamentos
        reserva = await self._buscar_reserva(reserva_id)
        pagamentos = await self._buscar_pagamentos(reserva_id)
        
        # Validar se pode fazer check-in
        pode, motivo = self.validator.pode_fazer_checkin(reserva, pagamentos)
        if not pode:
            raise ValueError(f"Não pode fazer check-in: {motivo}")
        
        # Criar registro de hospedagem
        hospedagem = {
            'id': 1,  # Simulação
            'reserva_id': reserva_id,
            'status': 'CHECKIN_REALIZADO',
            'data_checkin': now_utc(),
            'funcionario_id': dados_checkin.get('funcionario_id'),
            'observacoes': dados_checkin.get('observacoes', '')
        }
        
        # Atualizar fluxo
        reserva['fluxo_atual'] = 'HOSPEDAGEM_EM_ANDAMENTO'
        
        print(f"[FLUXO] Check-in realizado: {hospedagem['id']} - Reserva: {reserva_id}")
        return hospedagem
    
    # ==================== ETAPA 4: FAZER CHECK-OUT ====================
    
    async def fazer_checkout(self, reserva_id: int, dados_checkout: Dict[str, Any]) -> Dict[str, Any]:
        """
        Etapa 4: Realizar check-out
        Transição: CHECKIN_REALIZADO → CHECKOUT_REALIZADO
        """
        # Buscar hospedagem
        hospedagem = await self._buscar_hospedagem(reserva_id)
        
        # Validar se pode fazer checkout
        pode, motivo = self.validator.pode_fazer_checkout(hospedagem)
        if not pode:
            raise ValueError(f"Não pode fazer checkout: {motivo}")
        
        # Atualizar hospedagem
        hospedagem['status'] = 'CHECKOUT_REALIZADO'
        hospedagem['data_checkout'] = now_utc()
        hospedagem['observacoes_checkout'] = dados_checkout.get('observacoes', '')
        
        # Atualizar fluxo da reserva
        reserva = await self._buscar_reserva(reserva_id)
        reserva['fluxo_atual'] = 'HOSPEDAGEM_FINALIZADA'
        
        print(f"[FLUXO] Check-out realizado: {hospedagem['id']} - Reserva: {reserva_id}")
        return hospedagem
    
    # ==================== CANCELAMENTO ====================
    
    async def cancelar_reserva(self, reserva_id: int, motivo: str = None) -> Dict[str, Any]:
        """
        Cancelar reserva (fluxo alternativo)
        """
        # Buscar reserva
        reserva = await self._buscar_reserva(reserva_id)
        pagamentos = await self._buscar_pagamentos(reserva_id)
        
        # Validar se pode cancelar
        pode, motivo_validacao = self.validator.pode_cancelar_reserva(reserva, pagamentos)
        if not pode:
            raise ValueError(f"Não pode cancelar: {motivo_validacao}")
        
        # Atualizar status
        reserva['status'] = StatusReserva.CANCELADO.value
        reserva['fluxo_atual'] = 'RESERVA_CANCELADA'
        reserva['data_cancelamento'] = now_utc()
        reserva['motivo_cancelamento'] = motivo
        
        # Estornar pagamentos se houver
        if pagamentos:
            for pagamento in pagamentos:
                if pagamento['status'] == StatusPagamento.CONFIRMADO.value:
                    pagamento['status'] = StatusPagamento.ESTORNADO.value
                    pagamento['data_estorno'] = now_utc()
        
        print(f"[FLUXO] Reserva cancelada: {reserva_id} - Motivo: {motivo}")
        return reserva
    
    # ==================== MÉTODOS DE CONSULTA ====================
    
    async def diagnosticar_fluxo(self, reserva_id: int) -> Dict[str, Any]:
        """
        Diagnostica o estado atual do fluxo de uma reserva
        """
        # Buscar dados completos
        reserva = await self._buscar_reserva(reserva_id)
        pagamentos = await self._buscar_pagamentos(reserva_id)
        hospedagem = await self._buscar_hospedagem(reserva_id)
        
        # Usar validador unificado
        diagnostico = self.validator.validar_fluxo_completo(reserva, pagamentos, hospedagem)
        
        # Adicionar informações adicionais
        diagnostico.update({
            'reserva_id': reserva_id,
            'status_reserva': reserva.get('status'),
            'status_pagamento': pagamentos[-1]['status'] if pagamentos else None,
            'status_hospedagem': hospedagem.get('status') if hospedagem else None,
            'data_criacao': reserva.get('created_at'),
            'recomendacoes': self._gerar_recomendacoes(diagnostico)
        })
        
        return diagnostico
    
    def _gerar_recomendacoes(self, diagnostico: Dict[str, Any]) -> List[str]:
        """Gera recomendações baseadas no diagnóstico"""
        recomendacoes = []
        fluxo = diagnostico.get('fluxo_atual', '')
        problemas = diagnostico.get('problemas', [])
        
        if fluxo == 'AGUARDANDO_PAGAMENTO':
            recomendacoes.append("Cliente precisa pagar para confirmar reserva")
        
        if fluxo == 'PAGAMENTO_NEGADO':
            recomendacoes.append("Entrar em contato com cliente para novo pagamento")
        
        if fluxo == 'PAGAMENTO_APROVADO_AGUARDANDO_CONFIRMACAO':
            recomendacoes.append("Confirmar reserva automaticamente")
        
        if 'Pagamento aprovado mas reserva não confirmada' in problemas:
            recomendacoes.append("URGENTE: Confirmar reserva com pagamento aprovado")
        
        if fluxo == 'RESERVA_CONFIRMADA_AGUARDANDO_CHECKIN':
            recomendacoes.append("Preparar quarto para check-in")
        
        if fluxo == 'HOSPEDAGEM_EM_ANDAMENTO':
            recomendacoes.append("Monitorar consumo e satisfazer hóspede")
        
        if fluxo == 'HOSPEDAGEM_FINALIZADA':
            recomendacoes.append("Limpar quarto e preparar para próxima hospedagem")
        
        return recomendacoes
    
    # ==================== MÉTODOS PRIVADOS (SIMULAÇÃO) ====================
    
    async def _buscar_reserva(self, reserva_id: int) -> Dict[str, Any]:
        """Simulação de busca de reserva (substituir por repository real)"""
        # Em um cenário real, isso buscaria do banco
        # Para testes, vamos simular diferentes estados baseado no ID
        if reserva_id == 1:
            return {
                'id': reserva_id,
                'status': StatusReserva.PENDENTE.value,
                'created_at': now_utc()
            }
        else:
            return {
                'id': reserva_id,
                'status': StatusReserva.CONFIRMADA.value,
                'created_at': now_utc()
            }
    
    async def _buscar_pagamentos(self, reserva_id: int) -> List[Dict[str, Any]]:
        """Simulação de busca de pagamentos"""
        # Simular pagamento confirmado se reserva_id = 1
        if reserva_id == 1:
            return [{
                'id': 1,
                'reserva_id': reserva_id,
                'status': StatusPagamento.CONFIRMADO.value,
                'created_at': now_utc()
            }]
        return []
    
    async def _buscar_hospedagem(self, reserva_id: int) -> Dict[str, Any]:
        """Simulação de busca de hospedagem"""
        # Simular check-in realizado se reserva_id = 1
        if reserva_id == 1:
            return {
                'id': 1,
                'reserva_id': reserva_id,
                'status': 'CHECKIN_REALIZADO',
                'data_checkin': now_utc()
            }
        return None
    
    # ==================== MÉTODOS ESTATÍTICOS ====================
    
    @staticmethod
    def get_fluxo_esperado() -> Dict[str, List[str]]:
        """
        Retorna o fluxo esperado do sistema
        """
        return {
            'fluxo_principal': [
                'CRIADA',
                'PAGAMENTO_PROCESSADO', 
                'RESERVA_CONFIRMADA',
                'CHECKIN_REALIZADO',
                'HOSPEDAGEM_EM_ANDAMENTO',
                'CHECKOUT_REALIZADO',
                'HOSPEDAGEM_FINALIZADA'
            ],
            'fluxos_alternativos': [
                'PAGAMENTO_NEGADO → CANCELAR',
                'CLIENTE_NAO_COMPARECEU → NO_SHOW',
                'CHECKIN_ANTECIPADO → BLOQUEAR'
            ],
            'regras_fluxo': [
                'Não pode pagar reserva cancelada',
                'Não pode check-in sem pagamento confirmado',
                'Não pode checkout sem check-in prévio',
                'Pagamento aprovado deve confirmar reserva automaticamente'
            ]
        }
    
    @staticmethod
    def validar_sequencia_fluxo(sequencia: List[str]) -> Tuple[bool, str]:
        """
        Valida se uma sequência de eventos segue o fluxo correto
        """
        fluxo_esperado = FluxoReservaService.get_fluxo_esperado()['fluxo_principal']
        
        # Verificar se todos os eventos estão na ordem correta
        for i, evento in enumerate(sequencia):
            if i >= len(fluxo_esperado):
                return False, f"Evento extra: {evento}"
            
            if evento != fluxo_esperado[i]:
                return False, f"Sequência incorreta em {i}: esperado {fluxo_esperado[i]}, recebido {evento}"
        
        return True, "Sequência válida"
