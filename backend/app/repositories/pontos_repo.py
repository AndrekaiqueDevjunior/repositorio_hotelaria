from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from prisma import Client
from fastapi import HTTPException
from app.schemas.pontos_schema import (
    AjustarPontosRequest, SaldoResponse, TransacaoResponse,
    HistoricoTransacao, HistoricoResponse
)

# Constantes de segurança
MAX_PONTOS_POR_TRANSACAO = 1000
MIN_PONTOS_POR_TRANSACAO = -1000
ORIGENS_IDEMPOTENTES_POR_RESERVA = {"CHECKOUT", "BONUS_CUPOM", "CONVITE_REAL", "RESERVA"}


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
        
        resultado = await self.criar_transacao_pontos(
            cliente_id=request.cliente_id,
            pontos=request.pontos,
            tipo="AJUSTE" if request.pontos > 0 else "DEBITO",
            origem="AJUSTE_MANUAL",
            motivo=request.motivo,
            funcionario_id=funcionario_id,
        )

        return {
            "success": True,
            "transacao_id": resultado["transacao_id"],
            "novo_saldo": resultado["saldo_posterior"],
            "saldo_anterior": resultado["saldo_anterior"]
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
            "funcionario_nome": transacao.funcionario.nome if hasattr(transacao, 'funcionario') and transacao.funcionario else None,
            "cliente_id": transacao.clienteId if hasattr(transacao, 'clienteId') else None,
            "cliente_nome": transacao.cliente.nomeCompleto if hasattr(transacao, 'cliente') and transacao.cliente else None
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
            take=10,
            include={"cliente": True, "funcionario": True, "reserva": True}
        )

        inicio_hoje = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        transacoes_hoje = await self.db.transacaopontos.count(
            where={"createdAt": {"gte": inicio_hoje}}
        )

        return {
            "success": True,
            "total_pontos_circulacao": total_pontos,
            "total_usuarios": len(todos_usuarios),
            "usuarios_com_pontos": total_usuarios_com_pontos,
            "total_transacoes": total_transacoes,
            "transacoes_hoje": transacoes_hoje,
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
        
        origem_norm = (origem or "").strip().upper()
        origens_idempotencia = (
            ["CHECKOUT", "RESERVA"]
            if origem_norm in {"CHECKOUT", "RESERVA"}
            else [origem_norm]
        )

        async with self.db.tx() as transaction:
            if reserva_id and origem_norm in ORIGENS_IDEMPOTENTES_POR_RESERVA:
                transacao_existente = await transaction.transacaopontos.find_first(
                    where={"reservaId": reserva_id, "origem": {"in": origens_idempotencia}}
                )
                if transacao_existente:
                    return {
                        "success": True,
                        "idempotente": True,
                        "transacao_id": transacao_existente.id,
                        "saldo_anterior": getattr(transacao_existente, "saldoAnterior", 0),
                        "saldo_posterior": getattr(transacao_existente, "saldoPosterior", 0),
                        "pontos": getattr(transacao_existente, "pontos", 0),
                    }

            usuario_pontos_raw = await transaction.query_raw(
                """
                SELECT *
                FROM usuarios_pontos
                WHERE cliente_id = $1
                FOR UPDATE
                """,
                cliente_id,
            )

            if usuario_pontos_raw:
                usuario_pontos_data = usuario_pontos_raw[0]
                usuario_pontos_id = int(usuario_pontos_data["id"])
                saldo_anterior = int(usuario_pontos_data["saldo"])
            else:
                usuario_pontos = await transaction.usuariopontos.create(
                    data={"clienteId": cliente_id, "saldo": 0}
                )
                usuario_pontos_id = usuario_pontos.id
                saldo_anterior = 0

            if reserva_id and origem_norm in ORIGENS_IDEMPOTENTES_POR_RESERVA:
                transacao_existente = await transaction.transacaopontos.find_first(
                    where={"reservaId": reserva_id, "origem": {"in": origens_idempotencia}}
                )
                if transacao_existente:
                    return {
                        "success": True,
                        "idempotente": True,
                        "transacao_id": transacao_existente.id,
                        "saldo_anterior": getattr(transacao_existente, "saldoAnterior", 0),
                        "saldo_posterior": getattr(transacao_existente, "saldoPosterior", 0),
                        "pontos": getattr(transacao_existente, "pontos", 0),
                    }

            saldo_posterior = saldo_anterior + pontos

            if saldo_posterior < 0:
                raise ValueError("Saldo insuficiente para esta transação")

            await transaction.execute_raw(
                """
                UPDATE usuarios_pontos
                SET saldo = $1, updated_at = NOW()
                WHERE id = $2
                """,
                saldo_posterior,
                usuario_pontos_id,
            )

            transacao = await transaction.transacaopontos.create(
                data={
                    "clienteId": cliente_id,
                    "usuarioPontosId": usuario_pontos_id,
                    "funcionarioId": funcionario_id,
                    "reservaId": reserva_id,
                    "tipo": tipo,
                    "origem": origem_norm,
                    "pontos": pontos,
                    "saldoAnterior": saldo_anterior,
                    "saldoPosterior": saldo_posterior,
                    "motivo": motivo
                }
            )

            return {
                "success": True,
                "transacao_id": transacao.id,
                "saldo_anterior": saldo_anterior,
                "saldo_posterior": saldo_posterior,
                "pontos": pontos
            }

    async def listar_ajustes_manuais(
        self,
        cliente_id: Optional[int] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        where: Dict[str, Any] = {
            "origem": {"in": ["AJUSTE_MANUAL", "ESTORNO_AJUSTE_MANUAL"]}
        }
        if cliente_id is not None:
            where["clienteId"] = cliente_id

        transacoes = await self.db.transacaopontos.find_many(
            where=where,
            order={"createdAt": "desc"},
            take=limit,
            include={"cliente": True, "funcionario": True, "reserva": True}
        )

        return {
            "success": True,
            "transacoes": [self._serialize_transacao(t) for t in transacoes],
            "total": len(transacoes)
        }

    async def estornar_ajuste_manual(
        self,
        transacao_id: int,
        funcionario_id: int,
        motivo: Optional[str] = None
    ) -> Dict[str, Any]:
        transacao = await self.db.transacaopontos.find_unique(
            where={"id": transacao_id},
            include={"cliente": True, "funcionario": True}
        )

        if not transacao:
            raise ValueError("Transação não encontrada")

        if transacao.origem != "AJUSTE_MANUAL":
            raise ValueError("Apenas ajustes manuais podem ser estornados")

        estorno_existente = await self.db.transacaopontos.find_first(
            where={
                "origem": "ESTORNO_AJUSTE_MANUAL",
                "clienteId": transacao.clienteId,
                "motivo": {"contains": f"#{transacao_id}"},
            }
        )
        if estorno_existente:
            raise ValueError("Este ajuste manual já foi estornado")

        motivo_estorno = (
            f"Estorno da transação #{transacao_id}"
            + (f" | {motivo.strip()}" if motivo and motivo.strip() else "")
        )

        resultado = await self.criar_transacao_pontos(
            cliente_id=transacao.clienteId,
            pontos=transacao.pontos * -1,
            tipo="ESTORNO",
            origem="ESTORNO_AJUSTE_MANUAL",
            motivo=motivo_estorno,
            funcionario_id=funcionario_id
        )

        return {
            "success": True,
            "transacao_estornada_id": transacao_id,
            **resultado
        }
