from typing import List, Optional
from datetime import datetime, timedelta
from app.utils.datetime_utils import now_utc

class NotificacaoRepository:
    def __init__(self, db):
        self.db = db
    
    async def create(self, notificacao_data: dict) -> dict:
        """Criar nova notificação"""
        # Remover campos que não existem no schema
        data_clean = {
            "titulo": notificacao_data.get("titulo"),
            "mensagem": notificacao_data.get("mensagem"),
            "tipo": notificacao_data.get("tipo"),
            "categoria": notificacao_data.get("categoria"),
            "perfil": notificacao_data.get("perfil"),
            "lida": notificacao_data.get("lida", False),
            "dataCriacao": notificacao_data.get("createdAt", now_utc()),
            "urlAcao": notificacao_data.get("urlAcao"),
            "reservaId": notificacao_data.get("reservaId"),
            "pagamentoId": notificacao_data.get("pagamentoId")
        }
        
        # Remover valores None
        data_clean = {k: v for k, v in data_clean.items() if v is not None}
        
        notificacao = await self.db.notificacao.create(data=data_clean)
        return self._serialize(notificacao)
    
    async def get_by_id(self, notificacao_id: int) -> Optional[dict]:
        """Obter notificação por ID"""
        notificacao = await self.db.notificacao.find_unique(where={"id": notificacao_id})
        return self._serialize(notificacao) if notificacao else None
    
    async def get_by_user(
        self, 
        usuario_id: int, 
        perfil: Optional[str] = None,
        apenas_nao_lidas: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """Obter notificações do usuário"""
        where_conditions = {}
        
        # Construir condições OR para perfil
        # Notificações podem ter perfil específico ou None (para todos)
        # Também podem ter múltiplos perfis separados por vírgula (ex: "ADMIN,RECEPCAO")
        or_conditions = []
        
        if perfil:
            # Buscar notificações sem perfil (para todos)
            or_conditions.append({"perfil": None})
            # Buscar notificações com perfil exato
            or_conditions.append({"perfil": perfil})
            # Buscar notificações com perfil que contém o perfil do usuário
            or_conditions.append({"perfil": {"contains": perfil}})
        else:
            # Se não tem perfil, busca apenas notificações sem perfil específico
            or_conditions.append({"perfil": None})
        
        if or_conditions:
            where_conditions["OR"] = or_conditions
        
        # Filtrar não lidas
        if apenas_nao_lidas:
            where_conditions["lida"] = False
        
        # Buscar notificações
        notificacoes = await self.db.notificacao.find_many(
            where=where_conditions,
            order={"dataCriacao": "desc"},
            take=limit,
            skip=offset
        )
        
        # Retornar diretamente os objetos serializados
        return [self._serialize(notif) for notif in notificacoes]
    
    async def count_nao_lidas(self, usuario_id: int, perfil: Optional[str] = None) -> int:
        """Contar notificações não lidas"""
        where_conditions = {"lida": False}
        
        # Usar a mesma lógica de filtragem por perfil
        or_conditions = []
        
        if perfil:
            # Buscar notificações sem perfil (para todos)
            or_conditions.append({"perfil": None})
            # Buscar notificações com perfil exato
            or_conditions.append({"perfil": perfil})
            # Buscar notificações com perfil que contém o perfil do usuário
            or_conditions.append({"perfil": {"contains": perfil}})
        else:
            # Se não tem perfil, busca apenas notificações sem perfil específico
            or_conditions.append({"perfil": None})
        
        if or_conditions:
            where_conditions["OR"] = or_conditions
        
        notificacoes = await self.db.notificacao.find_many(where=where_conditions)
        return len(notificacoes)
    
    async def mark_as_read(self, notificacao_id: int) -> bool:
        """Marcar notificação como lida"""
        notificacao = await self.db.notificacao.find_unique(where={"id": notificacao_id})
        if notificacao and not notificacao.lida:
            await self.db.notificacao.update(
                where={"id": notificacao_id},
                data={"lida": True}
            )
            return True
        return False
    
    async def mark_all_as_read(self, usuario_id: int, perfil: Optional[str] = None) -> int:
        """Marcar todas as notificações como lidas"""
        where_conditions = {"lida": False}
        
        # Usar a mesma lógica de filtragem por perfil
        or_conditions = []
        
        if perfil:
            # Buscar notificações sem perfil (para todos)
            or_conditions.append({"perfil": None})
            # Buscar notificações com perfil exato
            or_conditions.append({"perfil": perfil})
            # Buscar notificações com perfil que contém o perfil do usuário
            or_conditions.append({"perfil": {"contains": perfil}})
        else:
            # Se não tem perfil, busca apenas notificações sem perfil específico
            or_conditions.append({"perfil": None})
        
        if or_conditions:
            where_conditions["OR"] = or_conditions
        
        # Buscar todas as notificações não lidas
        notificacoes = await self.db.notificacao.find_many(where=where_conditions)
        
        # Atualizar em lote
        count = 0
        for notif in notificacoes:
            await self.db.notificacao.update(
                where={"id": notif.id},
                data={"lida": True}
            )
            count += 1
        
        return count
    
    async def delete_old_read(self, dias: int = 30) -> int:
        """Deletar notificações lidas antigas"""
        data_limite = now_utc() - timedelta(days=dias)
        
        # Buscar notificações antigas para deletar
        notificacoes = await self.db.notificacao.find_many(
            where={
                "lida": True,
                "dataCriacao": {"lt": data_limite}
            }
        )
        
        # Deletar uma por uma (Prisma não tem bulk delete direto)
        count = 0
        for notif in notificacoes:
            await self.db.notificacao.delete(where={"id": notif.id})
            count += 1
        
        return count
    
    async def delete_by_id(self, notificacao_id: int) -> bool:
        """Deletar notificação específica"""
        try:
            await self.db.notificacao.delete(where={"id": notificacao_id})
            return True
        except:
            return False
    
    def _serialize(self, notificacao) -> dict:
        """Serializar notificação para response"""
        if not notificacao:
            return None
            
        return {
            "id": notificacao.id,
            "titulo": notificacao.titulo,
            "mensagem": notificacao.mensagem,
            "tipo": notificacao.tipo,
            "categoria": notificacao.categoria,
            "perfil": notificacao.perfil,
            "lida": notificacao.lida,
            "reserva_id": notificacao.reservaId,
            "pagamento_id": notificacao.pagamentoId,
            "url_acao": notificacao.urlAcao,
            "created_at": notificacao.dataCriacao.isoformat() if notificacao.dataCriacao else None,
            "lida_at": None  # Não existe campo lidaAt no schema
        }
