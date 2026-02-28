from typing import Optional, List, Dict, Any
from datetime import datetime
from prisma import Client
from app.schemas.cliente_schema import ClienteCreate, ClienteResponse


class ClienteRepository:
    def __init__(self, db: Client):
        self.db = db
    
    async def list_all(
        self, 
        search: str = None, 
        status: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Listar todos os clientes com filtros e busca"""
        where_conditions = {}
        
        # Filtro de busca (nome, documento ou email)
        if search:
            where_conditions["OR"] = [
                {"nomeCompleto": {"contains": search, "mode": "insensitive"}},
                {"documento": {"contains": search, "mode": "insensitive"}},
                {"email": {"contains": search, "mode": "insensitive"}}
            ]
        
        # Filtro de status
        if status:
            where_conditions["status"] = status
        
        # Buscar total de registros (para paginação)
        total = await self.db.cliente.count(where=where_conditions if where_conditions else None)
        
        # Buscar registros com paginação
        registros = await self.db.cliente.find_many(
            where=where_conditions if where_conditions else None,
            order={"id": "asc"},
            skip=offset,
            take=limit
        )
        
        return {
            "clientes": [self._serialize_cliente(c) for c in registros],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def create(self, cliente: ClienteCreate) -> Dict[str, Any]:
        """Criar novo cliente com validação anti-fraude"""
        from app.services.validacao_cliente_service import ValidacaoClienteService
        
        # Criar serviço de validação
        validacao_service = ValidacaoClienteService(self)
        
        # Validar cliente
        resultado_validacao = await validacao_service.validar_cliente_create({
            "nome_completo": cliente.nome_completo,
            "documento": cliente.documento,
            "telefone": cliente.telefone,
            "email": cliente.email,
        })
        
        if not resultado_validacao["valido"]:
            erros = "; ".join(resultado_validacao["erros"])
            raise ValueError(f"Validação falhou: {erros}")
        
        # Log de warnings se houver
        if resultado_validacao["warnings"]:
            for warning in resultado_validacao["warnings"]:
                print(f"[VALIDAÇÃO CLIENTE] ⚠️ {warning}")
        
        # Criar cliente
        novo_cliente = await self.db.cliente.create(
            data={
                "nomeCompleto": cliente.nome_completo,
                "documento": ValidacaoClienteService.limpar_cpf(cliente.documento),
                "telefone": cliente.telefone,
                "email": cliente.email,
            }
        )
        
        print(f"[VALIDAÇÃO CLIENTE] ✅ Cliente criado: {novo_cliente.nomeCompleto} (CPF: {novo_cliente.documento})")
        
        return self._serialize_cliente(novo_cliente)
    
    async def get_by_id(self, cliente_id: int) -> Dict[str, Any]:
        """Obter cliente por ID"""
        cliente = await self.db.cliente.find_unique(where={"id": cliente_id})
        if not cliente:
            raise ValueError("Cliente não encontrado")
        return self._serialize_cliente(cliente)
    
    async def get_by_documento(self, documento: str) -> Dict[str, Any]:
        """Obter cliente por documento"""
        documento_raw = (documento or "").strip()
        documento_limpo = ''.join(filter(str.isdigit, documento_raw))

        if not documento_limpo:
            raise ValueError("Cliente não encontrado")

        # Busca robusta: ignora pontuação e espaços no campo documento
        try:
            rows = await self.db.query_raw(
                """
                SELECT id
                FROM clientes
                WHERE regexp_replace(documento, '\\D', '', 'g') = $1
                LIMIT 1
                """,
                documento_limpo,
            )
            cliente_id = rows[0]["id"] if rows else None
        except Exception:
            cliente_id = None

        if cliente_id is None:
            # Fallback (match exato) caso query_raw não esteja disponível
            cliente = await self.db.cliente.find_first(where={"documento": documento_limpo})
        else:
            cliente = await self.db.cliente.find_unique(where={"id": int(cliente_id)})

        if not cliente:
            raise ValueError("Cliente não encontrado")

        return self._serialize_cliente(cliente)
    
    async def update(self, cliente_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualizar cliente com validação anti-fraude"""
        from app.services.validacao_cliente_service import ValidacaoClienteService
        
        # Buscar cliente atual
        cliente = await self.db.cliente.find_unique(where={"id": cliente_id})
        if not cliente:
            raise ValueError("Cliente não encontrado")
        
        # Criar serviço de validação
        validacao_service = ValidacaoClienteService(self)
        
        # Validar apenas se nome ou CPF estão sendo alterados
        if "nome_completo" in data or "documento" in data:
            resultado_validacao = await validacao_service.validar_cliente_update(cliente_id, data)
            
            if not resultado_validacao["valido"]:
                erros = "; ".join(resultado_validacao["erros"])
                raise ValueError(f"Validação falhou: {erros}")
            
            # Log de warnings se houver
            if resultado_validacao["warnings"]:
                for warning in resultado_validacao["warnings"]:
                    print(f"[VALIDAÇÃO CLIENTE] ⚠️ {warning}")
        
        # Mapear campos snake_case para camelCase do Prisma
        update_data = {}
        if "nome_completo" in data:
            update_data["nomeCompleto"] = data["nome_completo"]
        if "documento" in data:
            from app.services.validacao_cliente_service import ValidacaoClienteService
            update_data["documento"] = ValidacaoClienteService.limpar_cpf(data["documento"])
        if "telefone" in data:
            update_data["telefone"] = data["telefone"]
        if "email" in data:
            update_data["email"] = data["email"]
        if "status" in data:
            update_data["status"] = data["status"]
        
        # Atualizar cliente
        cliente_atualizado = await self.db.cliente.update(
            where={"id": cliente_id}, 
            data=update_data
        )
        
        print(f"[VALIDAÇÃO CLIENTE] ✅ Cliente atualizado: {cliente_atualizado.nomeCompleto} (ID: {cliente_id})")
        
        return self._serialize_cliente(cliente_atualizado)
    
    async def delete(self, cliente_id: int) -> Dict[str, Any]:
        """Deletar cliente"""
        cliente = await self.db.cliente.find_unique(where={"id": cliente_id})
        if not cliente:
            raise ValueError("Cliente não encontrado")
        
        # Verificar se o cliente tem reservas ativas
        reservas_ativas = await self.db.reserva.find_many(
            where={
                "clienteId": cliente_id,
                "statusReserva": {"in": ["PENDENTE", "CONFIRMADA", "HOSPEDADO"]}
            }
        )
        
        if reservas_ativas:
            raise ValueError(
                f"Não é possível excluir o cliente. Ele possui {len(reservas_ativas)} reserva(s) ativa(s). "
                "Cancele ou finalize as reservas antes de excluir."
            )
        
        # Se não houver restrições, deleta o cliente
        await self.db.cliente.delete(where={"id": cliente_id})
        
        return {
            "success": True,
            "message": "Cliente excluído com sucesso",
            "cliente_id": cliente_id
        }
    
    def _serialize_cliente(self, cliente) -> Dict[str, Any]:
        """Serializar cliente para response"""
        return {
            "id": cliente.id,
            "nome_completo": cliente.nomeCompleto,
            "documento": cliente.documento,
            "telefone": cliente.telefone,
            "email": cliente.email,
            "status": cliente.status,
            "created_at": cliente.createdAt.isoformat() if cliente.createdAt else None
        }