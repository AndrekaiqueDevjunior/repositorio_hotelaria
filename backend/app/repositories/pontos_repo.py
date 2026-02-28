from typing import Optional, List, Dict, Any
from datetime import datetime
from prisma import Client
from fastapi import HTTPException
from app.schemas.pontos_schema import (
    AjustarPontosRequest, SaldoResponse, TransacaoResponse,
    HistoricoTransacao, HistoricoResponse
)

# Constantes de segurança
MAX_PONTOS_POR_TRANSACAO = 1000
MIN_PONTOS_POR_TRANSACAO = -1000


class PontosRepository:
    def __init__(self, db: Client):
        self.db = db
    
    async def get_saldo(self, cliente_id: int) -> Dict[str, Any]:
        """Obter saldo de pontos do cliente"""
        # Primeiro verificar se o cliente existe
        cliente = await self.db.cliente.find_first(
            where={"id": cliente_id}
        )
        
        if not cliente:
            return {
                "success": False,
                "error": f"Cliente com ID {cliente_id} não encontrado",
                "saldo": 0
            }
        
        usuario_pontos = await self.db.usuariopontos.find_first(
            where={"clienteId": cliente_id}
        )
        
        if not usuario_pontos:
            # Criar registro se não existir (cliente já validado)
            usuario_pontos = await self.db.usuariopontos.create(
                data={
                    "clienteId": cliente_id,
                    "saldo": 0
                }
            )
        
        return {
            "success": True,
            "saldo": usuario_pontos.saldo,
            "usuario_pontos_id": usuario_pontos.id,
            "cliente_nome": cliente.nomeCompleto
        }
    
    async def ajustar_pontos(
        self, 
        request: AjustarPontosRequest,
        funcionario_id: int = None
    ) -> Dict[str, Any]:
        """Ajustar pontos (creditar/debitar) com rastreabilidade"""
        # VALIDAÇÃO DE SEGURANÇA: Limites de pontos
        if request.pontos == 0:
            raise ValueError("Transação de 0 pontos não permitida")
        
        if abs(request.pontos) > MAX_PONTOS_POR_TRANSACAO:
            raise ValueError(
                f"Transação limitada a ±{MAX_PONTOS_POR_TRANSACAO} pontos. "
                f"Valor solicitado: {request.pontos}"
            )
        
        # Obter ou criar registro de pontos
        usuario_pontos = await self.db.usuariopontos.find_first(
            where={"clienteId": request.cliente_id}
        )
        
        if not usuario_pontos:
            usuario_pontos = await self.db.usuariopontos.create(
                data={
                    "clienteId": request.cliente_id,
                    "saldo": 0
                }
            )
        
        saldo_anterior = usuario_pontos.saldo
        novo_saldo = saldo_anterior + request.pontos
        
        # Validar saldo negativo
        if novo_saldo < 0:
            raise ValueError("Saldo insuficiente para esta transação")
        
        # Atualizar saldo
        await self.db.usuariopontos.update(
            where={"id": usuario_pontos.id},
            data={"saldo": novo_saldo}
        )
        
        # Criar transação COM TODOS OS RELACIONAMENTOS
        transacao = await self.db.transacaopontos.create(
            data={
                "clienteId": request.cliente_id,
                "usuarioPontosId": usuario_pontos.id,
                "funcionarioId": funcionario_id,
                "tipo": "AJUSTE" if request.pontos > 0 else "DEBITO",
                "pontos": request.pontos,
                "saldoAnterior": saldo_anterior,
                "saldoPosterior": novo_saldo,
                "origem": "AJUSTE_MANUAL",
                "motivo": request.motivo
            }
        )
        
        return {
            "success": True,
            "transacao_id": transacao.id,
            "novo_saldo": novo_saldo,
            "saldo_anterior": saldo_anterior
        }
    
    async def get_historico(self, cliente_id: int, limit: int = 20) -> Dict[str, Any]:
        """Obter histórico de transações com relacionamentos"""
        transacoes = await self.db.transacaopontos.find_many(
            where={"clienteId": cliente_id},
            order={"createdAt": "desc"},
            take=limit,
            include={
                "reserva": True,
                "funcionario": True
            }
        )
        
        return {
            "success": True,
            "transacoes": [self._serialize_transacao(t) for t in transacoes],
            "total": len(transacoes)
        }
    
    def _serialize_transacao(self, transacao) -> Dict[str, Any]:
        """Serializar transação para response com relacionamentos"""
        return {
            "id": transacao.id,
            "tipo": transacao.tipo,
            "pontos": transacao.pontos,
            "saldo_anterior": transacao.saldoAnterior if hasattr(transacao, 'saldoAnterior') and transacao.saldoAnterior is not None else 0,
            "saldo_posterior": transacao.saldoPosterior if hasattr(transacao, 'saldoPosterior') and transacao.saldoPosterior is not None else 0,
            "origem": transacao.origem,
            "motivo": transacao.motivo if hasattr(transacao, 'motivo') else None,
            "created_at": transacao.createdAt.isoformat() if transacao.createdAt else None,
            "reserva_id": transacao.reservaId if hasattr(transacao, 'reservaId') else None,
            "reserva_codigo": transacao.reserva.codigoReserva if hasattr(transacao, 'reserva') and transacao.reserva else None,
            "funcionario_id": transacao.funcionarioId if hasattr(transacao, 'funcionarioId') else None,
            "funcionario_nome": transacao.funcionario.nome if hasattr(transacao, 'funcionario') and transacao.funcionario else None
        }
    
    async def get_estatisticas(self) -> Dict[str, Any]:
        """Obter estatísticas gerais do sistema de pontos"""
        # Total de pontos em circulação
        todos_usuarios = await self.db.usuariopontos.find_many()
        total_pontos = sum(u.saldo for u in todos_usuarios)
        total_usuarios_com_pontos = len([u for u in todos_usuarios if u.saldo > 0])
        
        # Total de transações
        total_transacoes = await self.db.transacaopontos.count()
        
        # Transações recentes
        transacoes_recentes = await self.db.transacaopontos.find_many(
            order={"createdAt": "desc"},
            take=10
        )
        
        return {
            "success": True,
            "total_pontos_circulacao": total_pontos,
            "total_usuarios": len(todos_usuarios),
            "usuarios_com_pontos": total_usuarios_com_pontos,
            "total_transacoes": total_transacoes,
            "transacoes_recentes": [self._serialize_transacao(t) for t in transacoes_recentes]
        }
    
    async def criar_transacao_pontos(
        self,
        cliente_id: int,
        pontos: int,
        tipo: str,
        origem: str,
        motivo: str = None,
        reserva_id: int = None,
        funcionario_id: int = None
    ) -> Dict[str, Any]:
        """
        Criar transação de pontos completa com todos os relacionamentos
        
        Args:
            cliente_id: ID do cliente
            pontos: Quantidade de pontos (pode ser negativo para débito)
            tipo: CREDITO, DEBITO, AJUSTE, ESTORNO
            origem: RESERVA, AJUSTE_MANUAL, CONVITE, etc
            motivo: Descrição da transação
            reserva_id: ID da reserva relacionada (se aplicável)
            funcionario_id: ID do funcionário que fez ajuste (se aplicável)
        """
        # VALIDAÇÃO DE SEGURANÇA: Limites de pontos
        if pontos == 0:
            raise ValueError("Transação de 0 pontos não permitida")
        
        if abs(pontos) > MAX_PONTOS_POR_TRANSACAO:
            raise ValueError(
                f"Transação limitada a ±{MAX_PONTOS_POR_TRANSACAO} pontos. "
                f"Valor solicitado: {pontos}"
            )
        
        # Obter ou criar UsuarioPontos
        usuario_pontos = await self.db.usuariopontos.find_first(
            where={"clienteId": cliente_id}
        )
        
        if not usuario_pontos:
            usuario_pontos = await self.db.usuariopontos.create(
                data={"clienteId": cliente_id, "saldo": 0}
            )
        
        saldo_anterior = usuario_pontos.saldo
        saldo_posterior = saldo_anterior + pontos
        
        # Validar saldo negativo
        if saldo_posterior < 0:
            raise ValueError("Saldo insuficiente para esta transação")
        
        # Criar transação COM TODOS OS RELACIONAMENTOS (campos obrigatórios)
        transacao = await self.db.transacaopontos.create(
            data={
                "clienteId": cliente_id,
                "usuarioPontosId": usuario_pontos.id,
                "funcionarioId": funcionario_id,
                "reservaId": reserva_id,
                "tipo": tipo,
                "origem": origem,
                "pontos": pontos,
                "saldoAnterior": saldo_anterior,
                "saldoPosterior": saldo_posterior,
                "motivo": motivo
            }
        )
        
        # Atualizar saldo
        await self.db.usuariopontos.update(
            where={"id": usuario_pontos.id},
            data={"saldo": saldo_posterior}
        )
        
        return {
            "success": True,
            "transacao_id": transacao.id,
            "saldo_anterior": saldo_anterior,
            "saldo_posterior": saldo_posterior,
            "pontos": pontos
        }