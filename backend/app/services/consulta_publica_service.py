"""
Serviço unificado para consulta pública (Voucher + Reserva)
Centraliza a lógica de busca e formatação de dados públicos
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from fastapi import HTTPException
from app.core.database import get_db
from app.schemas.consulta_publica_schema import (
    ConsultaPublicaResponse, 
    ClienteInfo, 
    QuartoInfo, 
    DatasReserva, 
    ValoresReserva,
    PagamentoInfo,
    InstrucoesCheckin,
    ErroConsultaPublica
)
import re

class ConsultaPublicaService:
    """Serviço unificado para consulta pública de vouchers e reservas"""
    
    def __init__(self, db):
        self.db = db
    
    async def consultar_codigo_unificado(self, codigo: str) -> ConsultaPublicaResponse:
        """
        Consulta unificada que detecta automaticamente se é voucher ou reserva
        
        Args:
            codigo: Código a ser consultado
            
        Returns:
            ConsultaPublicaResponse com dados unificados
            
        Raises:
            HTTPException: Se não encontrado ou erro
        """
        try:
            # Detectar tipo pelo formato do código
            tipo = self._detectar_tipo_codigo(codigo)
            
            if tipo == "VOUCHER":
                return await self._consultar_voucher_unificado(codigo)
            elif tipo == "RESERVA":
                return await self._consultar_reserva_unificada(codigo)
            else:
                # Tentar ambos os tipos se não conseguir detectar
                try:
                    return await self._consultar_voucher_unificado(codigo)
                except HTTPException:
                    return await self._consultar_reserva_unificada(codigo)
                    
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Erro na consulta unificada: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Erro ao consultar código: {str(e)}"
            )
    
    def _detectar_tipo_codigo(self, codigo: str) -> Optional[str]:
        """
        Detecta o tipo de código pelo formato
        
        Args:
            codigo: Código a ser analisado
            
        Returns:
            "VOUCHER", "RESERVA" ou None
        """
        codigo_upper = codigo.upper().strip()
        
        # Padrão voucher: HR-ANO-SEQUENCIA (ex: HR-2025-000001)
        if re.match(r'^HR-\d{4}-\d{6}$', codigo_upper):
            return "VOUCHER"
        
        # Padrão reserva: 8 caracteres alfanuméricos (ex: UYUN2KLU)
        if re.match(r'^[A-Z0-9]{8}$', codigo_upper):
            return "RESERVA"
            
        return None
    
    async def _consultar_voucher_unificado(self, codigo: str) -> ConsultaPublicaResponse:
        """Consulta voucher e formata resposta unificada"""
        codigo_upper = codigo.upper().strip()
        
        # Buscar voucher
        voucher = await self.db.voucher.find_first(
            where={'codigo': codigo_upper},
            include={
                'reserva': {
                    'include': {
                        'cliente': True,
                        'pagamentos': True
                    }
                }
            }
        )
        
        if not voucher:
            raise HTTPException(
                status_code=404,
                detail=f"Voucher {codigo_upper} não encontrado"
            )
        
        # Formatar resposta unificada
        return ConsultaPublicaResponse(
            tipo="VOUCHER",
            codigo=voucher.codigo,
            status=voucher.status,
            cliente=ClienteInfo(
                nome_completo=voucher.reserva.cliente.nomeCompleto,
                email=voucher.reserva.cliente.email,
                telefone=voucher.reserva.cliente.telefone
            ),
            quarto=QuartoInfo(
                numero=voucher.reserva.quartoNumero,
                tipo_suite=voucher.reserva.tipoSuite
            ),
            datas=DatasReserva(
                checkin_previsto=voucher.reserva.checkinPrevisto,
                checkout_previsto=voucher.reserva.checkoutPrevisto,
                checkin_realizado=voucher.checkinRealizadoEm,
                checkout_realizado=voucher.checkoutRealizadoEm,
                num_diarias=voucher.reserva.numDiarias or 1
            ),
            valores=ValoresReserva(
                valor_diaria=float(voucher.reserva.valorDiaria or 0),
                valor_total=float(voucher.reserva.valorDiaria or 0) * (voucher.reserva.numDiarias or 1)
            ),
            pagamentos=[
                PagamentoInfo(
                    id=pag.id,
                    status=pag.status,
                    valor=float(pag.valor or 0),
                    metodo=pag.metodo,
                    data=pag.createdAt
                )
                for pag in voucher.reserva.pagamentos
            ] if voucher.reserva.pagamentos else [],
            instrucoes=InstrucoesCheckin(),
            data_emissao=voucher.dataEmissao,
            links={
                "reserva": f"/public/reservas/{voucher.reserva.codigoReserva}",
                "pdf_voucher": f"/vouchers/{voucher.codigo}/pdf"
            }
        )
    
    async def _consultar_reserva_unificada(self, codigo: str) -> ConsultaPublicaResponse:
        """Consulta reserva e formata resposta unificada"""
        codigo_upper = codigo.upper().strip()
        
        # Buscar reserva
        reserva = await self.db.reserva.find_first(
            where={"codigoReserva": codigo_upper},
            include={
                'cliente': True,
                'pagamentos': True
            }
        )
        
        if not reserva:
            raise HTTPException(
                status_code=404,
                detail=f"Reserva {codigo_upper} não encontrada"
            )
        
        # Verificar se existe voucher para esta reserva
        voucher_relacionado = await self.db.voucher.find_first(
            where={'reservaId': reserva.id}
        )
        
        # Formatar resposta unificada
        return ConsultaPublicaResponse(
            tipo="RESERVA",
            codigo=reserva.codigoReserva,
            status=reserva.status,
            cliente=ClienteInfo(
                nome_completo=reserva.cliente.nomeCompleto,
                email=reserva.cliente.email,
                telefone=reserva.cliente.telefone
            ),
            quarto=QuartoInfo(
                numero=reserva.quartoNumero,
                tipo_suite=reserva.tipoSuite
            ),
            datas=DatasReserva(
                checkin_previsto=reserva.checkinPrevisto,
                checkout_previsto=reserva.checkoutPrevisto,
                checkin_realizado=reserva.checkinReal,
                checkout_realizado=reserva.checkoutReal,
                num_diarias=reserva.numDiarias or 1
            ),
            valores=ValoresReserva(
                valor_diaria=float(reserva.valorDiaria or 0),
                valor_total=float(reserva.valorDiaria or 0) * (reserva.numDiarias or 1)
            ),
            pagamentos=[
                PagamentoInfo(
                    id=pag.id,
                    status=pag.status,
                    valor=float(pag.valor or 0),
                    metodo=pag.metodo,
                    data=pag.createdAt
                )
                for pag in reserva.pagamentos
            ] if reserva.pagamentos else [],
            instrucoes=InstrucoesCheckin(),
            links={
                "voucher": f"/vouchers/{voucher_relacionado.codigo}" if voucher_relacionado else None,
                "pdf_voucher": f"/vouchers/{voucher_relacionado.codigo}/pdf" if voucher_relacionado else None
            } if voucher_relacionado else None
        )
    
    async def buscar_por_documento(self, documento: str) -> Dict[str, Any]:
        """
        Busca todas as reservas de um cliente por documento
        
        Args:
            documento: CPF do cliente
            
        Returns:
            Dicionário com reservas encontradas
        """
        try:
            # Limpar documento
            documento_limpo = re.sub(r'[^\d]', '', documento)
            
            if len(documento_limpo) != 11:
                raise HTTPException(
                    status_code=400,
                    detail="Documento inválido"
                )
            
            # Buscar cliente
            cliente = await self.db.cliente.find_first(
                where={'documento': documento_limpo}
            )
            
            if not cliente:
                raise HTTPException(
                    status_code=404,
                    detail="Cliente não encontrado"
                )
            
            # Buscar reservas do cliente
            reservas = await self.db.reserva.find_many(
                where={'clienteId': cliente.id},
                include={'pagamentos': True},
                order={'createdAt': 'desc'}
            )
            
            # Buscar vouchers relacionados
            for reserva in reservas:
                voucher = await self.db.voucher.find_first(
                    where={'reservaId': reserva.id}
                )
                reserva.voucher_relacionado = voucher
            
            return {
                "success": True,
                "cliente": {
                    "nome_completo": cliente.nomeCompleto,
                    "email": cliente.email,
                    "telefone": cliente.telefone
                },
                "reservas": reservas,
                "total_reservas": len(reservas)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Erro ao buscar por documento: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao buscar reservas: {str(e)}"
            )
