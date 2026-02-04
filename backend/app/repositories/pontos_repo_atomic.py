"""
Repositório de Pontos com Transações Atômicas
Implementa operações críticas com lock pessimista para prevenir race conditions
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from prisma import Client
from fastapi import HTTPException
from app.schemas.pontos_schema import (
    AjustarPontosRequest, SaldoResponse, TransacaoResponse,
    HistoricoTransacao, HistoricoResponse
)
import logging

# Constantes de segurança
MAX_PONTOS_POR_TRANSACAO = 1000
MIN_PONTOS_POR_TRANSACAO = -1000

security_logger = logging.getLogger("security")


class PontosRepositoryAtomic:
    """
    Repositório de pontos com transações atômicas.
    Usa SELECT FOR UPDATE para prevenir race conditions.
    """
    
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
    
    async def ajustar_pontos_atomic(
        self, 
        request: AjustarPontosRequest,
        funcionario_id: int = None
    ) -> Dict[str, Any]:
        """
        Ajustar pontos com transação atômica e lock pessimista.
        
        PROTEÇÃO CONTRA RACE CONDITION:
        - Usa transação para garantir atomicidade
        - Lock pessimista no registro de pontos
        - Todas as operações são commit ou rollback juntas
        """
        # VALIDAÇÃO DE SEGURANÇA: Limites de pontos
        if request.pontos == 0:
            raise ValueError("Transação de 0 pontos não permitida")
        
        if abs(request.pontos) > MAX_PONTOS_POR_TRANSACAO:
            raise ValueError(
                f"Transação limitada a ±{MAX_PONTOS_POR_TRANSACAO} pontos. "
                f"Valor solicitado: {request.pontos}"
            )
        
        # TRANSAÇÃO ATÔMICA COM LOCK
        async with self.db.tx() as transaction:
            # 1. Buscar ou criar UsuarioPontos COM LOCK (SELECT FOR UPDATE)
            # Nota: Prisma Python não tem suporte direto para FOR UPDATE
            # Alternativa: usar query raw SQL
            usuario_pontos_raw = await transaction.query_raw(
                """
                SELECT * FROM usuarios_pontos 
                WHERE cliente_id = $1 
                FOR UPDATE
                """,
                request.cliente_id
            )
            
            if not usuario_pontos_raw:
                # Criar registro se não existir
                usuario_pontos = await transaction.usuariopontos.create(
                    data={
                        "clienteId": request.cliente_id,
                        "saldo": 0
                    }
                )
                saldo_anterior = 0
            else:
                # Usar registro existente (já locked)
                usuario_pontos_data = usuario_pontos_raw[0]
                saldo_anterior = usuario_pontos_data['saldo']
                usuario_pontos_id = usuario_pontos_data['id']
            
            # 2. Calcular novo saldo
            novo_saldo = saldo_anterior + request.pontos
            
            # 3. Validar saldo negativo
            if novo_saldo < 0:
                security_logger.warning(
                    f"Tentativa de ajuste resultaria em saldo negativo - "
                    f"Cliente: {request.cliente_id}, Saldo atual: {saldo_anterior}, "
                    f"Ajuste: {request.pontos}"
                )
                raise ValueError("Saldo insuficiente para esta transação")
            
            # 4. Atualizar saldo (dentro da transação)
            if usuario_pontos_raw:
                await transaction.execute_raw(
                    """
                    UPDATE usuarios_pontos 
                    SET saldo = $1, updated_at = NOW()
                    WHERE id = $2
                    """,
                    novo_saldo,
                    usuario_pontos_id
                )
            else:
                await transaction.usuariopontos.update(
                    where={"id": usuario_pontos.id},
                    data={"saldo": novo_saldo}
                )
                usuario_pontos_id = usuario_pontos.id
            
            # 5. Criar transação de pontos (dentro da mesma transação)
            transacao = await transaction.transacaopontos.create(
                data={
                    "clienteId": request.cliente_id,
                    "usuarioPontosId": usuario_pontos_id,
                    "funcionarioId": funcionario_id,
                    "tipo": "AJUSTE" if request.pontos > 0 else "DEBITO",
                    "pontos": request.pontos,
                    "saldoAnterior": saldo_anterior,
                    "saldoPosterior": novo_saldo,
                    "origem": "AJUSTE_MANUAL",
                    "motivo": request.motivo
                }
            )
            
            security_logger.info(
                f"Ajuste atômico realizado - Cliente: {request.cliente_id}, "
                f"Pontos: {request.pontos:+d}, Saldo: {saldo_anterior} → {novo_saldo}, "
                f"Funcionário: {funcionario_id}"
            )
            
            # Commit automático ao sair do bloco 'async with'
            return {
                "success": True,
                "transacao_id": transacao.id,
                "novo_saldo": novo_saldo,
                "saldo_anterior": saldo_anterior
            }
    
    async def criar_transacao_pontos_atomic(
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
        Criar transação de pontos com lock atômico.
        
        PROTEÇÃO CONTRA RACE CONDITION:
        - Transação atômica garante consistência
        - Lock no registro de pontos previne leituras sujas
        """
        # VALIDAÇÃO DE SEGURANÇA
        if pontos == 0:
            raise ValueError("Transação de 0 pontos não permitida")
        
        if abs(pontos) > MAX_PONTOS_POR_TRANSACAO:
            raise ValueError(
                f"Transação limitada a ±{MAX_PONTOS_POR_TRANSACAO} pontos. "
                f"Valor solicitado: {pontos}"
            )
        
        # TRANSAÇÃO ATÔMICA
        async with self.db.tx() as transaction:
            # 1. Buscar UsuarioPontos COM LOCK
            usuario_pontos_raw = await transaction.query_raw(
                """
                SELECT * FROM usuarios_pontos 
                WHERE cliente_id = $1 
                FOR UPDATE
                """,
                cliente_id
            )
            
            if not usuario_pontos_raw:
                # Criar se não existir
                usuario_pontos = await transaction.usuariopontos.create(
                    data={"clienteId": cliente_id, "saldo": 0}
                )
                saldo_anterior = 0
                usuario_pontos_id = usuario_pontos.id
            else:
                usuario_pontos_data = usuario_pontos_raw[0]
                saldo_anterior = usuario_pontos_data['saldo']
                usuario_pontos_id = usuario_pontos_data['id']
            
            # 2. Calcular novo saldo
            saldo_posterior = saldo_anterior + pontos
            
            # 3. Validar saldo negativo
            if saldo_posterior < 0:
                security_logger.warning(
                    f"Tentativa de transação resultaria em saldo negativo - "
                    f"Cliente: {cliente_id}, Tipo: {tipo}, Pontos: {pontos}"
                )
                raise ValueError("Saldo insuficiente para esta transação")
            
            # 4. Atualizar saldo
            await transaction.execute_raw(
                """
                UPDATE usuarios_pontos 
                SET saldo = $1, updated_at = NOW()
                WHERE id = $2
                """,
                saldo_posterior,
                usuario_pontos_id
            )
            
            # 5. Criar registro de transação
            transacao = await transaction.transacaopontos.create(
                data={
                    "clienteId": cliente_id,
                    "usuarioPontosId": usuario_pontos_id,
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
            
            security_logger.info(
                f"Transação atômica criada - Cliente: {cliente_id}, "
                f"Tipo: {tipo}, Pontos: {pontos:+d}, "
                f"Saldo: {saldo_anterior} → {saldo_posterior}"
            )
            
            return {
                "success": True,
                "transacao_id": transacao.id,
                "saldo_anterior": saldo_anterior,
                "saldo_posterior": saldo_posterior,
                "pontos": pontos
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
        """Serializar transação para response"""
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
