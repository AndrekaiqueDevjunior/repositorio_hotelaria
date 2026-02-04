from typing import Dict, Any, Optional
from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc, timedelta
from prisma import Client
import secrets
import string


class ConviteRepository:
    def __init__(self, db: Client):
        self.db = db
    
    def _gerar_codigo_unico(self) -> str:
        """Gerar código único de convite"""
        timestamp = now_utc().strftime('%Y%m%d%H%M%S')
        random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        return f"CONVITE-{timestamp}-{random_suffix}"
    
    async def criar_convite(
        self,
        convidante_id: int,
        usos_maximos: int = 5,
        dias_validade: int = 30
    ) -> Dict[str, Any]:
        """Criar novo convite com código único"""
        codigo = self._gerar_codigo_unico()
        expires_at = now_utc() + timedelta(days=dias_validade) if dias_validade else None
        
        convite = await self.db.convite.create(
            data={
                "codigo": codigo,
                "convidanteId": convidante_id,
                "usosMaximos": usos_maximos,
                "usosRestantes": usos_maximos,
                "ativo": True,
                "expiresAt": expires_at
            }
        )
        
        return {
            "id": convite.id,
            "codigo": convite.codigo,
            "convidante_id": convite.convidanteId,
            "usos_maximos": convite.usosMaximos,
            "usos_restantes": convite.usosRestantes,
            "ativo": convite.ativo,
            "created_at": convite.createdAt.isoformat(),
            "expires_at": convite.expiresAt.isoformat() if convite.expiresAt else None
        }
    
    async def buscar_por_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Buscar convite por código"""
        convite = await self.db.convite.find_unique(
            where={"codigo": codigo},
            include={"usos": True}
        )
        
        if not convite:
            return None
        
        return {
            "id": convite.id,
            "codigo": convite.codigo,
            "convidante_id": convite.convidanteId,
            "usos_maximos": convite.usosMaximos,
            "usos_restantes": convite.usosRestantes,
            "ativo": convite.ativo,
            "created_at": convite.createdAt.isoformat(),
            "expires_at": convite.expiresAt.isoformat() if convite.expiresAt else None,
            "total_usos": len(convite.usos) if convite.usos else 0
        }
    
    async def validar_convite(self, codigo: str, convidado_id: int) -> Dict[str, Any]:
        """
        Validar se convite pode ser usado
        Retorna: {"valido": bool, "erro": str | None}
        """
        convite = await self.buscar_por_codigo(codigo)
        
        if not convite:
            return {"valido": False, "erro": "Código de convite inválido"}
        
        if not convite["ativo"]:
            return {"valido": False, "erro": "Convite desativado"}
        
        if convite["usos_restantes"] <= 0:
            return {"valido": False, "erro": "Convite esgotado (sem usos restantes)"}
        
        # Verificar expiração
        if convite["expires_at"]:
            expires_at = datetime.fromisoformat(convite["expires_at"])
            if now_utc() > expires_at:
                return {"valido": False, "erro": "Convite expirado"}
        
        # Verificar se convidado já usou este convite
        uso_existente = await self.db.conviteuso.find_first(
            where={
                "conviteId": convite["id"],
                "convidadoId": convidado_id
            }
        )
        
        if uso_existente:
            return {"valido": False, "erro": "Você já usou este convite"}
        
        # Verificar se convidado é o próprio convidante
        if convite["convidante_id"] == convidado_id:
            return {"valido": False, "erro": "Você não pode usar seu próprio convite"}
        
        return {"valido": True, "erro": None, "convite": convite}
    
    async def registrar_uso(
        self,
        convite_id: int,
        convidado_id: int,
        pontos_ganhos: int
    ) -> Dict[str, Any]:
        """Registrar uso do convite e decrementar usos restantes"""
        # Criar registro de uso
        uso = await self.db.conviteuso.create(
            data={
                "conviteId": convite_id,
                "convidadoId": convidado_id,
                "pontosGanhos": pontos_ganhos
            }
        )
        
        # Decrementar usos restantes
        convite = await self.db.convite.update(
            where={"id": convite_id},
            data={"usosRestantes": {"decrement": 1}}
        )
        
        # Desativar se esgotou usos
        if convite.usosRestantes <= 0:
            await self.db.convite.update(
                where={"id": convite_id},
                data={"ativo": False}
            )
        
        return {
            "uso_id": uso.id,
            "convite_id": uso.conviteId,
            "convidado_id": uso.convidadoId,
            "pontos_ganhos": uso.pontosGanhos,
            "created_at": uso.createdAt.isoformat(),
            "usos_restantes": convite.usosRestantes
        }
    
    async def listar_convites_usuario(self, convidante_id: int) -> list[Dict[str, Any]]:
        """Listar todos os convites criados por um usuário"""
        convites = await self.db.convite.find_many(
            where={"convidanteId": convidante_id},
            include={"usos": True},
            order={"createdAt": "desc"}
        )
        
        return [
            {
                "id": c.id,
                "codigo": c.codigo,
                "usos_maximos": c.usosMaximos,
                "usos_restantes": c.usosRestantes,
                "total_usos": len(c.usos) if c.usos else 0,
                "ativo": c.ativo,
                "created_at": c.createdAt.isoformat(),
                "expires_at": c.expiresAt.isoformat() if c.expiresAt else None
            }
            for c in convites
        ]
    
    async def obter_estatisticas_convites(self, convidante_id: int) -> Dict[str, Any]:
        """Obter estatísticas de convites de um usuário"""
        convites = await self.db.convite.find_many(
            where={"convidanteId": convidante_id},
            include={"usos": True}
        )
        
        total_convites = len(convites)
        total_usos = sum(len(c.usos) if c.usos else 0 for c in convites)
        convites_ativos = len([c for c in convites if c.ativo])
        
        return {
            "total_convites_gerados": total_convites,
            "total_usos": total_usos,
            "convites_ativos": convites_ativos,
            "pontos_gerados_para_outros": total_usos * 100,  # 100 pontos por uso
            "pontos_ganhos_indicacao": total_usos * 1  # 1 ponto por indicação
        }
