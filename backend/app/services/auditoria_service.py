"""
Serviço de Auditoria
Registra automaticamente todas as ações importantes do sistema
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import Request
from app.core.database import get_db

audit_logger = logging.getLogger("audit")


class AuditoriaService:
    """Serviço centralizado para registrar auditoria"""
    
    @staticmethod
    async def registrar_acao(
        funcionario_id: int,
        entidade: str,
        entidade_id: str,
        acao: str,
        payload: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        detalhes: Optional[str] = None
    ):
        """
        Registrar uma ação no sistema
        
        Args:
            funcionario_id: ID do funcionário que realizou a ação
            entidade: Tipo da entidade (RESERVA, PAGAMENTO, PONTOS, etc.)
            entidade_id: ID da entidade afetada
            acao: Ação realizada (CREATE, UPDATE, DELETE, etc.)
            payload: Dados da ação (será resumido)
            request: Objeto Request para extrair IP e User-Agent
            detalhes: Detalhes adicionais da ação
        """
        try:
            db = get_db()
            
            # Extrair informações da requisição
            ip_address = None
            user_agent = None
            
            if request:
                ip_address = request.client.host
                user_agent = request.headers.get("user-agent", "Unknown")[:500]
            
            # Criar resumo do payload
            payload_resumo = None
            if payload:
                try:
                    # Limitar tamanho e remover dados sensíveis
                    payload_limpo = AuditoriaService._limpar_payload(payload)
                    payload_resumo = json.dumps(payload_limpo, ensure_ascii=False)[:1000]
                except Exception:
                    payload_resumo = str(payload)[:500]
            
            # Adicionar detalhes ao resumo
            if detalhes:
                if payload_resumo:
                    payload_resumo += f" | {detalhes}"
                else:
                    payload_resumo = detalhes
            
            # Registrar no banco
            await db.auditoria.create(
                data={
                    "funcionarioId": funcionario_id,
                    "entidade": entidade.upper(),
                    "entidadeId": str(entidade_id),
                    "acao": acao.upper(),
                    "payloadResumo": payload_resumo,
                    "ipAddress": ip_address,
                    "userAgent": user_agent
                }
            )
            
            # Log de auditoria
            audit_logger.info(
                f"AUDITORIA: Funcionário {funcionario_id} realizou {acao} em {entidade}:{entidade_id}"
            )
            
        except Exception as e:
            # Não falhar a operação principal se auditoria falhar
            audit_logger.error(f"Erro ao registrar auditoria: {str(e)}")
    
    @staticmethod
    def _limpar_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Remover dados sensíveis do payload"""
        campos_sensiveis = ['senha', 'senhaHash', 'password', 'token', 'apiKey', 'secret']
        
        if isinstance(payload, dict):
            payload_limpo = {}
            for key, value in payload.items():
                if any(sensivel in key.lower() for sensivel in campos_sensiveis):
                    payload_limpo[key] = "***REDACTED***"
                elif isinstance(value, dict):
                    payload_limpo[key] = AuditoriaService._limpar_payload(value)
                elif isinstance(value, list):
                    payload_limpo[key] = [
                        AuditoriaService._limpar_payload(item) if isinstance(item, dict) else item
                        for item in value[:5]  # Limitar listas
                    ]
                else:
                    payload_limpo[key] = value
            return payload_limpo
        
        return payload
    
    @staticmethod
    async def registrar_login(funcionario_id: int, request: Optional[Request] = None):
        """Registrar login de funcionário"""
        await AuditoriaService.registrar_acao(
            funcionario_id=funcionario_id,
            entidade="FUNCIONARIO",
            entidade_id=str(funcionario_id),
            acao="LOGIN",
            request=request,
            detalhes="Funcionário fez login no sistema"
        )
    
    @staticmethod
    async def registrar_logout(funcionario_id: int, request: Optional[Request] = None):
        """Registrar logout de funcionário"""
        await AuditoriaService.registrar_acao(
            funcionario_id=funcionario_id,
            entidade="FUNCIONARIO",
            entidade_id=str(funcionario_id),
            acao="LOGOUT",
            request=request,
            detalhes="Funcionário fez logout do sistema"
        )
    
    @staticmethod
    async def registrar_criacao_reserva(funcionario_id: int, reserva_id: int, dados_reserva: Dict[str, Any], request: Optional[Request] = None):
        """Registrar criação de reserva"""
        await AuditoriaService.registrar_acao(
            funcionario_id=funcionario_id,
            entidade="RESERVA",
            entidade_id=str(reserva_id),
            acao="CREATE",
            payload=dados_reserva,
            request=request,
            detalhes=f"Reserva criada para cliente {dados_reserva.get('clienteId', 'N/A')}"
        )
    
    @staticmethod
    async def registrar_atualizacao_reserva(funcionario_id: int, reserva_id: int, dados_antigos: Dict[str, Any], dados_novos: Dict[str, Any], request: Optional[Request] = None):
        """Registrar atualização de reserva"""
        payload = {
            "antes": dados_antigos,
            "depois": dados_novos,
            "alteracoes": AuditoriaService._detectar_alteracoes(dados_antigos, dados_novos)
        }
        
        await AuditoriaService.registrar_acao(
            funcionario_id=funcionario_id,
            entidade="RESERVA",
            entidade_id=str(reserva_id),
            acao="UPDATE",
            payload=payload,
            request=request,
            detalhes=f"Reserva atualizada: {len(payload['alteracoes'])} campos alterados"
        )
    
    @staticmethod
    async def registrar_criacao_pagamento(funcionario_id: int, pagamento_id: int, dados_pagamento: Dict[str, Any], request: Optional[Request] = None):
        """Registrar criação de pagamento"""
        await AuditoriaService.registrar_acao(
            funcionario_id=funcionario_id,
            entidade="PAGAMENTO",
            entidade_id=str(pagamento_id),
            acao="CREATE",
            payload=dados_pagamento,
            request=request,
            detalhes=f"Pagamento criado: R$ {dados_pagamento.get('valor', 0):.2f}"
        )
    
    @staticmethod
    async def registrar_confirmacao_pagamento(funcionario_id: int, pagamento_id: int, request: Optional[Request] = None):
        """Registrar confirmação de pagamento"""
        await AuditoriaService.registrar_acao(
            funcionario_id=funcionario_id,
            entidade="PAGAMENTO",
            entidade_id=str(pagamento_id),
            acao="CONFIRM",
            request=request,
            detalhes="Pagamento confirmado"
        )
    
    @staticmethod
    async def registrar_operacao_pontos(funcionario_id: int, cliente_id: int, pontos: int, origem: str, request: Optional[Request] = None):
        """Registrar operação de pontos"""
        await AuditoriaService.registrar_acao(
            funcionario_id=funcionario_id,
            entidade="PONTOS",
            entidade_id=str(cliente_id),
            acao="CREDITO" if pontos > 0 else "DEBITO",
            payload={"pontos": pontos, "origem": origem},
            request=request,
            detalhes=f"{'Crédito' if pontos > 0 else 'Débito'} de {pontos} pontos - Origem: {origem}"
        )
    
    @staticmethod
    async def registrar_resgate_premio(funcionario_id: int, resgate_id: int, dados_resgate: Dict[str, Any], request: Optional[Request] = None):
        """Registrar resgate de prêmio"""
        await AuditoriaService.registrar_acao(
            funcionario_id=funcionario_id,
            entidade="RESGATE",
            entidade_id=str(resgate_id),
            acao="CREATE",
            payload=dados_resgate,
            request=request,
            detalhes=f"Prêmio resgatado: {dados_resgate.get('premioNome', 'N/A')} (-{dados_resgate.get('pontosUsados', 0)} pts)"
        )
    
    @staticmethod
    async def registrar_confirmacao_entrega(funcionario_id: int, resgate_id: int, request: Optional[Request] = None):
        """Registrar confirmação de entrega de prêmio"""
        await AuditoriaService.registrar_acao(
            funcionario_id=funcionario_id,
            entidade="RESGATE",
            entidade_id=str(resgate_id),
            acao="DELIVER",
            request=request,
            detalhes="Prêmio marcado como entregue"
        )
    
    @staticmethod
    async def registrar_checkin(funcionario_id: int, reserva_id: int, request: Optional[Request] = None):
        """Registrar check-in"""
        await AuditoriaService.registrar_acao(
            funcionario_id=funcionario_id,
            entidade="CHECKIN",
            entidade_id=str(reserva_id),
            acao="CREATE",
            request=request,
            detalhes="Check-in realizado"
        )
    
    @staticmethod
    async def registrar_checkout(funcionario_id: int, reserva_id: int, request: Optional[Request] = None):
        """Registrar check-out"""
        await AuditoriaService.registrar_acao(
            funcionario_id=funcionario_id,
            entidade="CHECKOUT",
            entidade_id=str(reserva_id),
            acao="CREATE",
            request=request,
            detalhes="Check-out realizado"
        )
    
    @staticmethod
    async def registrar_acesso_negado(funcionario_id: Optional[int], entidade: str, entidade_id: str, acao: str, request: Optional[Request] = None):
        """Registrar tentativa de acesso negado"""
        try:
            db = get_db()
            
            ip_address = request.client.host if request else None
            user_agent = request.headers.get("user-agent", "Unknown")[:500] if request else None
            
            await db.auditoria.create(
                data={
                    "funcionarioId": funcionario_id or 0,  # 0 para sistema/anônimo
                    "entidade": entidade.upper(),
                    "entidadeId": str(entidade_id),
                    "acao": f"ACCESS_DENIED_{acao.upper()}",
                    "payloadResumo": "Tentativa de acesso não autorizado",
                    "ipAddress": ip_address,
                    "userAgent": user_agent
                }
            )
            
            audit_logger.warning(
                f"ACESSO NEGADO: Funcionário {funcionario_id} tentou {acao} em {entidade}:{entidade_id}"
            )
            
        except Exception as e:
            audit_logger.error(f"Erro ao registrar acesso negado: {str(e)}")
    
    @staticmethod
    def _detectar_alteracoes(dados_antigos: Dict[str, Any], dados_novos: Dict[str, Any]) -> List[str]:
        """Detectar quais campos foram alterados"""
        alteracoes = []
        
        for key, valor_novo in dados_novos.items():
            valor_antigo = dados_antigos.get(key)
            
            if valor_antigo != valor_novo:
                if valor_antigo is None:
                    alteracoes.append(f"{key}: NULL → {valor_novo}")
                elif valor_novo is None:
                    alteracoes.append(f"{key}: {valor_antigo} → NULL")
                else:
                    alteracoes.append(f"{key}: {valor_antigo} → {valor_novo}")
        
        return alteracoes


# Função auxiliar para middleware
async def auditoria_middleware(
    funcionario_id: int,
    entidade: str,
    entidade_id: str,
    acao: str,
    payload: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
):
    """Função auxiliar para uso em middleware"""
    await AuditoriaService.registrar_acao(
        funcionario_id=funcionario_id,
        entidade=entidade,
        entidade_id=entidade_id,
        acao=acao,
        payload=payload,
        request=request
    )
