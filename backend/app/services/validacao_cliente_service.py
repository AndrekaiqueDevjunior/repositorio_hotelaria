"""
Serviço de Validação de Clientes
Previne fraudes validando duplicação de CPF e nome
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from fastapi import HTTPException
from app.repositories.cliente_repo import ClienteRepository


class ValidacaoClienteService:
    """Serviço para validação robusta de clientes contra fraudes"""
    
    def __init__(self, cliente_repo: ClienteRepository):
        self.cliente_repo = cliente_repo
    
    @staticmethod
    def limpar_cpf(cpf: str) -> str:
        """Limpar CPF, removendo caracteres especiais"""
        if not cpf:
            return ""
        return re.sub(r'[^\d]', '', cpf)
    
    @staticmethod
    def validar_formato_cpf(cpf: str) -> bool:
        """
        Validar formato do CPF (11 dígitos)
        Não valida dígito verificador, apenas formato
        """
        if not cpf:
            return False
        
        cpf_limpo = ValidacaoClienteService.limpar_cpf(cpf)
        
        # CPF deve ter 11 dígitos
        if len(cpf_limpo) != 11:
            return False
        
        # CPF não pode ter todos os dígitos iguais
        if cpf_limpo == cpf_limpo[0] * 11:
            return False
        
        return True
    
    @staticmethod
    def normalizar_nome(nome: str) -> str:
        """Normalizar nome para comparação (remover espaços extras e converter para maiúsculas)"""
        if not nome:
            return ""
        
        # Remover espaços extras e converter para maiúsculas
        nome_normalizado = " ".join(nome.strip().split()).upper()
        
        # Remover caracteres especiais (manter apenas letras, espaços e apóstrofos)
        nome_normalizado = re.sub(r'[^\w\s\'À-ÿ]', '', nome_normalizado)
        
        return nome_normalizado
    
    async def verificar_duplicacao_cpf(self, cpf: str, cliente_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Verificar se CPF já está cadastrado
        
        Args:
            cpf: CPF a verificar
            cliente_id: ID do cliente (para edição, permite mesmo CPF)
            
        Returns:
            (tem_duplicacao, mensagem_erro)
        """
        if not cpf:
            return False, None
        
        # Validar formato do CPF
        if not self.validar_formato_cpf(cpf):
            return False, "CPF inválido. Formato esperado: XXX.XXX.XXX-XX ou 11 dígitos"
        
        cpf_limpo = self.limpar_cpf(cpf)
        
        try:
            # Buscar cliente com este CPF
            cliente_existente = await self.cliente_repo.get_by_documento(cpf_limpo)
            
            if cliente_existente and cliente_existente["id"] != cliente_id:
                return True, f"CPF {cpf} já está cadastrado para o cliente {cliente_existente['nome_completo']}"
            
            return False, None
            
        except ValueError:
            # Cliente não encontrado - CPF disponível
            return False, None
    
    async def verificar_duplicacao_nome(self, nome: str, cliente_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Verificar se nome já está cadastrado com o mesmo CPF
        
        Args:
            nome: Nome a verificar
            cliente_id: ID do cliente (para edição)
            
        Returns:
            (tem_duplicacao, mensagem_erro)
        """
        if not nome:
            return False, None
        
        nome_normalizado = self.normalizar_nome(nome)
        
        # Buscar todos os clientes com nome similar
        clientes = await self.cliente_repo.list_all(search=nome_normalizado, limit=100)
        
        for cliente in clientes["clientes"]:
            # Pular o próprio cliente (edição)
            if cliente["id"] == cliente_id:
                continue
            
            # Normalizar nome do cliente existente
            nome_existente_normalizado = self.normalizar_nome(cliente["nome_completo"])
            
            # Verificar se nomes são idênticos após normalização
            if nome_existente_normalizado == nome_normalizado:
                return True, f"Nome '{nome}' já está cadastrado para o cliente com CPF {cliente['documento']}"
        
        return False, None
    
    async def verificar_duplicacao_combinada(
        self, 
        nome: str, 
        cpf: str, 
        cliente_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Verificação completa de duplicação (CPF + Nome)
        
        Args:
            nome: Nome do cliente
            cpf: CPF do cliente
            cliente_id: ID do cliente (para edição)
            
        Returns:
            Dicionário com resultado da validação
        """
        erros = []
        warnings = []
        
        # Validar formato do CPF
        if not self.validar_formato_cpf(cpf):
            erros.append("CPF inválido. Use o formato XXX.XXX.XXX-XX ou 11 dígitos numéricos")
        
        # Verificar duplicação de CPF
        tem_cpf_duplicado, erro_cpf = await self.verificar_duplicacao_cpf(cpf, cliente_id)
        if tem_cpf_duplicado:
            erros.append(erro_cpf)
        
        # Verificar duplicação de nome
        tem_nome_duplicado, erro_nome = await self.verificar_duplicacao_nome(nome, cliente_id)
        if tem_nome_duplicado:
            erros.append(erro_nome)
        
        # Verificar nomes similares (warning)
        if not erros and nome:
            await self._verificar_nomes_similares(nome, cliente_id, warnings)
        
        return {
            "valido": len(erros) == 0,
            "erros": erros,
            "warnings": warnings,
            "cpf_normalizado": self.limpar_cpf(cpf),
            "nome_normalizado": self.normalizar_nome(nome)
        }
    
    async def _verificar_nomes_similares(
        self, 
        nome: str, 
        cliente_id: Optional[int], 
        warnings: List[str]
    ):
        """
        Verificar nomes similares para alertar sobre possíveis duplicações
        """
        nome_normalizado = self.normalizar_nome(nome)
        
        # Buscar clientes com partes do nome
        partes_nome = nome_normalizado.split()
        if len(partes_nome) >= 2:
            # Buscar pela primeira e última parte do nome
            busca = f"{partes_nome[0]} {partes_nome[-1]}"
            clientes = await self.cliente_repo.list_all(search=busca, limit=50)
            
            for cliente in clientes["clientes"]:
                if cliente["id"] == cliente_id:
                    continue
                
                nome_existente_normalizado = self.normalizar_nome(cliente["nome_completo"])
                
                # Verificar similaridade (mesmo sobrenome ou partes do nome)
                if (partes_nome[-1] in nome_existente_normalizado or 
                    partes_nome[0] in nome_existente_normalizado):
                    
                    if nome_existente_normalizado != nome_normalizado:
                        warnings.append(
                            f"Nome similar ao cliente '{cliente['nome_completo']}' "
                            f"(CPF: {cliente['documento']}). Verifique se é a mesma pessoa."
                        )
    
    async def validar_cliente_create(self, cliente_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validação completa para criação de cliente
        
        Args:
            cliente_data: Dados do cliente
            
        Returns:
            Resultado da validação
        """
        nome = cliente_data.get("nome_completo", "")
        cpf = cliente_data.get("documento", "")
        
        if not nome or not cpf:
            return {
                "valido": False,
                "erros": ["Nome e CPF são obrigatórios"]
            }
        
        # Verificação completa
        resultado = await self.verificar_duplicacao_combinada(nome, cpf)
        
        # Validações adicionais
        if len(nome.strip()) < 3:
            resultado["erros"].append("Nome deve ter pelo menos 3 caracteres")
        
        if len(resultado["erros"]) > 0:
            resultado["valido"] = False
        
        return resultado
    
    async def validar_cliente_update(
        self, 
        cliente_id: int, 
        cliente_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validação para atualização de cliente
        
        Args:
            cliente_id: ID do cliente
            cliente_data: Novos dados
            
        Returns:
            Resultado da validação
        """
        # Buscar cliente atual
        try:
            cliente_atual = await self.cliente_repo.get_by_id(cliente_id)
        except ValueError:
            return {
                "valido": False,
                "erros": ["Cliente não encontrado"]
            }
        
        nome = cliente_data.get("nome_completo", cliente_atual["nome_completo"])
        cpf = cliente_data.get("documento", cliente_atual["documento"])
        
        # Se nome e CPF não mudaram, está válido
        if (nome == cliente_atual["nome_completo"] and 
            cpf == cliente_atual["documento"]):
            return {
                "valido": True,
                "erros": [],
                "warnings": []
            }
        
        # Verificação completa com ID do cliente
        resultado = await self.verificar_duplicacao_combinada(nome, cpf, cliente_id)
        
        # Validações adicionais
        if len(nome.strip()) < 3:
            resultado["erros"].append("Nome deve ter pelo menos 3 caracteres")
        
        if len(resultado["erros"]) > 0:
            resultado["valido"] = False
        
        return resultado
    
    async def detectar_potenciais_fraudes(self, limite_similaridade: int = 5) -> List[Dict[str, Any]]:
        """
        Detectar potenciais fraudes analisando clientes com nomes similares
        
        Args:
            limite_similaridade: Número máximo de clientes com nome similar
            
        Returns:
            Lista de potenciais fraudes detectadas
        """
        fraudes_potenciais = []
        
        # Buscar todos os clientes
        todos_clientes = await self.cliente_repo.list_all(limit=1000)
        
        # Agrupar por sobrenome
        sobrenomes = {}
        for cliente in todos_clientes["clientes"]:
            nome_parts = cliente["nome_completo"].strip().split()
            if len(nome_parts) >= 2:
                sobrenome = nome_parts[-1].upper()
                if sobrenome not in sobrenomes:
                    sobrenomes[sobrenome] = []
                sobrenomes[sobrenome].append(cliente)
        
        # Verificar sobrenomes com muitos clientes
        for sobrenome, clientes_sobrenome in sobrenomes.items():
            if len(clientes_sobrenome) > limite_similaridade:
                fraudes_potenciais.append({
                    "tipo": "NOMES_SIMILARES",
                    "sobrenome": sobrenome,
                    "quantidade": len(clientes_sobrenome),
                    "clientes": [
                        {
                            "id": c["id"],
                            "nome": c["nome_completo"],
                            "cpf": c["documento"],
                            "email": c.get("email", "")
                        }
                        for c in clientes_sobrenome[:10]  # Limitar para 10 exemplos
                    ],
                    "alerta": f"Atenção: {len(clientes_sobrenome)} clientes com sobrenome '{sobrenome}'"
                })
        
        return fraudes_potenciais


# Factory para obter instância do serviço
def get_validacao_cliente_service(cliente_repo: ClienteRepository) -> ValidacaoClienteService:
    """Factory para obter instância do serviço de validação"""
    return ValidacaoClienteService(cliente_repo)
