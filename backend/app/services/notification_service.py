"""
Serviço de Notificações
Gerencia a criação automática de notificações para eventos do sistema
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from app.repositories.notificacao_repo import NotificacaoRepository
from app.utils.datetime_utils import now_utc


class NotificationService:
    """Serviço centralizado para criar notificações do sistema"""
    
    def __init__(self, db):
        self.db = db
        self.repo = NotificacaoRepository(db)
    
    async def criar_notificacao(
        self,
        titulo: str,
        mensagem: str,
        tipo: str = "info",
        categoria: str = "sistema",
        perfil: Optional[str] = None,
        usuario_destino_id: Optional[int] = None,
        reserva_id: Optional[int] = None,
        pagamento_id: Optional[int] = None,
        url_acao: Optional[str] = None,
        dados_adicionais: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Criar notificação no banco de dados
        
        Args:
            titulo: Título da notificação
            mensagem: Mensagem detalhada
            tipo: info, warning, critical, success
            categoria: reserva, pagamento, sistema, antifraude
            perfil: Perfil do usuário (ADMIN, RECEPCAO, etc)
            usuario_destino_id: ID do usuário específico
            reserva_id: ID da reserva relacionada
            pagamento_id: ID do pagamento relacionado
            url_acao: URL para ação relacionada
            dados_adicionais: JSON com dados extras
        """
        try:
            notificacao_data = {
                "titulo": titulo,
                "mensagem": mensagem,
                "tipo": tipo,
                "categoria": categoria,
                "perfil": perfil,
                "urlAcao": url_acao,
                "reservaId": reserva_id,
                "pagamentoId": pagamento_id,
                "lida": False,
                "dataCriacao": now_utc()
            }
            
            notificacao = await self.repo.create(notificacao_data)
            
            print(f"[NOTIFICAÇÃO] Criada: {titulo} (ID: {notificacao['id']})")
            return notificacao
            
        except Exception as e:
            print(f"[NOTIFICAÇÃO] Erro ao criar: {e}")
            return None
    
    # ==================== RESERVAS ====================

    @staticmethod
    async def notificar_nova_reserva(db, reserva):
        """
        Cria uma notificação global para uma nova reserva.
        
        Args:
            db: Sessão do banco de dados
            reserva: Dicionário ou objeto contendo os dados da reserva
            
        Esta notificação será visível para os perfis ADMIN e RECEPCAO.
        """
        service = NotificationService(db)

        def _get(obj, key, default=None):
            """Helper para obter valores de objetos ou dicionários com fallback."""
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        try:
            # Obter todos os dados necessários da reserva
            reserva_id = _get(reserva, "id")
            if not reserva_id:
                print("[NOTIFICAÇÃO] Erro: ID da reserva não encontrado")
                return

            # Obter dados básicos com fallback para nomes de campos alternativos
            cliente_nome = _get(reserva, "clienteNome") or _get(reserva, "cliente_nome")
            quarto_numero = _get(reserva, "quartoNumero") or _get(reserva, "quarto_numero")
            checkin_previsto = _get(reserva, "checkinPrevisto") or _get(reserva, "checkin_previsto")
            codigo_reserva = _get(reserva, "codigoReserva") or _get(reserva, "codigo_reserva")
            valor_diaria = _get(reserva, "valorDiaria") or _get(reserva, "valor_diaria")
            num_diarias = _get(reserva, "numDiarias") or _get(reserva, "num_diarias_previstas") or _get(reserva, "num_diarias")

            # Preencher valores ausentes de campos aninhados
            if not cliente_nome:
                cliente = _get(reserva, "cliente")
                cliente_nome = _get(cliente, "nome_completo") or _get(cliente, "nomeCompleto") or "Cliente não identificado"
            
            if not quarto_numero:
                quarto = _get(reserva, "quarto")
                quarto_numero = _get(quarto, "numero") or "N/A"
            
            # Formatar data de check-in
            checkin_str = ""
            if checkin_previsto:
                try:
                    checkin_str = checkin_previsto.strftime('%d/%m/%Y')
                except (AttributeError, ValueError):
                    checkin_str = str(checkin_previsto)[:10]
            
            if not codigo_reserva:
                codigo_reserva = f"RES-{reserva_id}"

            # Calcular valor total se possível
            valor_total = 0
            try:
                if valor_diaria is not None and num_diarias is not None:
                    valor_total = float(valor_diaria) * int(num_diarias)
            except (ValueError, TypeError):
                pass

            # Formatar mensagem da notificação
            mensagem = f"🆕 Nova Reserva #{reserva_id}"
            detalhes = f"Cliente: {cliente_nome} | Quarto: {quarto_numero}"
            
            if checkin_str:
                detalhes += f" | Check-in: {checkin_str}"
            
            # Criar notificação global para ADMIN e RECEPCAO
            await service.criar_notificacao(
                titulo=mensagem,
                mensagem=detalhes,
                tipo="info",
                categoria="reserva",
                perfil="ADMIN,RECEPCAO",  # Perfis que receberão a notificação
                reserva_id=reserva_id,
                url_acao=f"/reservas/{reserva_id}",
                dados_adicionais={
                    "codigo_reserva": codigo_reserva,
                    "quarto_numero": quarto_numero,
                    "checkin_previsto": checkin_str,
                    "valor_total": valor_total,
                    "cliente_nome": cliente_nome
                }
            )
            
            # Notificação adicional para reservas de alto valor (acima de R$ 2.000,00)
            if valor_total > 2000:
                await service.criar_notificacao(
                    titulo="💰 Reserva de Alto Valor",
                    mensagem=f"Reserva #{reserva_id} - R$ {valor_total:,.2f}",
                    tipo="warning",
                    categoria="financeiro",
                    perfil="ADMIN,FINANCEIRO",
                    reserva_id=reserva_id,
                    url_acao=f"/reservas/{reserva_id}",
                    dados_adicionais={
                        "codigo_reserva": codigo_reserva,
                        "valor_total": valor_total,
                        "cliente_nome": cliente_nome,
                        "quarto_numero": quarto_numero
                    }
                )
            
            print(f"[NOTIFICAÇÃO] Notificação de nova reserva #{reserva_id} criada com sucesso")
            
        except Exception as e:
            import traceback
            error_msg = f"Erro ao criar notificação de nova reserva: {str(e)}\n{traceback.format_exc()}"
            print(f"[NOTIFICAÇÃO] {error_msg}")
            
            # Tentar notificar sobre o erro
            try:
                await service.criar_notificacao(
                    titulo="❌ Erro em notificação de reserva",
                    mensagem=f"Erro ao processar notificação para reserva: {str(e)[:100]}...",
                    tipo="critical",
                    categoria="sistema",
                    perfil="ADMIN"
                )
            except Exception as inner_e:
                print(f"[NOTIFICAÇÃO] Falha ao notificar sobre erro: {str(inner_e)}")
    
    @staticmethod
    async def notificar_checkin_realizado(db, reserva):
        service = NotificationService(db)

        def _get(obj, key, default=None):
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        reserva_id = _get(reserva, "id")
        cliente_nome = _get(reserva, "clienteNome")
        quarto_numero = _get(reserva, "quartoNumero")
        if not cliente_nome:
            cliente = _get(reserva, "cliente")
            cliente_nome = _get(cliente, "nome_completo") or _get(cliente, "nomeCompleto")
        if not quarto_numero:
            quarto = _get(reserva, "quarto")
            quarto_numero = _get(quarto, "numero")

        await service.criar_notificacao(
            titulo="✅ Check-in Realizado",
            mensagem=f"Cliente: {cliente_nome} | Quarto: {quarto_numero}",
            tipo="success",
            categoria="reserva",
            perfil="RECEPCAO",
            reserva_id=reserva_id,
        )
    
    @staticmethod
    async def notificar_checkout_realizado(db, reserva):
        service = NotificationService(db)

        def _get(obj, key, default=None):
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        reserva_id = _get(reserva, "id")
        cliente_nome = _get(reserva, "clienteNome")
        quarto_numero = _get(reserva, "quartoNumero")
        if not cliente_nome:
            cliente = _get(reserva, "cliente")
            cliente_nome = _get(cliente, "nome_completo") or _get(cliente, "nomeCompleto")
        if not quarto_numero:
            quarto = _get(reserva, "quarto")
            quarto_numero = _get(quarto, "numero")

        await service.criar_notificacao(
            titulo="🚪 Check-out Realizado",
            mensagem=f"Cliente: {cliente_nome} | Quarto: {quarto_numero}",
            tipo="info",
            categoria="reserva",
            perfil="RECEPCAO",
            reserva_id=reserva_id,
        )
    
    @staticmethod
    async def notificar_reserva_cancelada(db, reserva):
        service = NotificationService(db)

        def _get(obj, key, default=None):
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        reserva_id = _get(reserva, "id")
        codigo_reserva = _get(reserva, "codigoReserva") or _get(reserva, "codigo_reserva")
        cliente_nome = _get(reserva, "clienteNome")
        if not cliente_nome:
            cliente = _get(reserva, "cliente")
            cliente_nome = _get(cliente, "nome_completo") or _get(cliente, "nomeCompleto")

        await service.criar_notificacao(
            titulo="❌ Reserva Cancelada",
            mensagem=f"Reserva {codigo_reserva} - Cliente: {cliente_nome}",
            tipo="warning",
            categoria="reserva",
            perfil="RECEPCAO",
            reserva_id=reserva_id,
        )
    
    # ==================== PAGAMENTOS ====================
    
    @staticmethod
    async def notificar_pagamento_aprovado(db, pagamento, reserva):
        service = NotificationService(db)

        def _get(obj, key, default=None):
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        valor = _get(pagamento, "valor")
        pagamento_id = _get(pagamento, "id")
        reserva_id = _get(reserva, "id")
        codigo_reserva = _get(reserva, "codigoReserva") or _get(reserva, "codigo_reserva")
        try:
            valor_fmt = f"{float(valor):.2f}"
        except Exception:
            valor_fmt = str(valor)

        await service.criar_notificacao(
            titulo="💳 Pagamento Aprovado",
            mensagem=f"R$ {valor_fmt} - Reserva {codigo_reserva}",
            tipo="success",
            categoria="pagamento",
            perfil="ADMIN",
            pagamento_id=pagamento_id,
            reserva_id=reserva_id,
        )
    
    @staticmethod
    async def notificar_pagamento_recusado(db, pagamento, reserva):
        service = NotificationService(db)

        def _get(obj, key, default=None):
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        valor = _get(pagamento, "valor")
        pagamento_id = _get(pagamento, "id")
        reserva_id = _get(reserva, "id")
        codigo_reserva = _get(reserva, "codigoReserva") or _get(reserva, "codigo_reserva")
        try:
            valor_fmt = f"{float(valor):.2f}"
        except Exception:
            valor_fmt = str(valor)

        await service.criar_notificacao(
            titulo="❌ Pagamento Recusado",
            mensagem=f"R$ {valor_fmt} - Reserva {codigo_reserva} - AÇÃO NECESSÁRIA",
            tipo="critical",
            categoria="pagamento",
            perfil="ADMIN",
            pagamento_id=pagamento_id,
            reserva_id=reserva_id,
        )

        await service.criar_notificacao(
            titulo="⚠️ Problema no Pagamento",
            mensagem=f"Reserva {codigo_reserva} - Pagamento recusado",
            tipo="warning",
            categoria="pagamento",
            perfil="RECEPCAO",
            reserva_id=reserva_id,
        )
    
    @staticmethod
    async def notificar_pagamento_pendente(db, pagamento, reserva):
        service = NotificationService(db)

        def _get(obj, key, default=None):
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        valor = _get(pagamento, "valor")
        pagamento_id = _get(pagamento, "id")
        reserva_id = _get(reserva, "id")
        codigo_reserva = _get(reserva, "codigoReserva") or _get(reserva, "codigo_reserva")
        try:
            valor_fmt = f"{float(valor):.2f}"
        except Exception:
            valor_fmt = str(valor)

        await service.criar_notificacao(
            titulo="⏳ Pagamento Pendente",
            mensagem=f"R$ {valor_fmt} - Reserva {codigo_reserva}",
            tipo="warning",
            categoria="pagamento",
            perfil="ADMIN",
            pagamento_id=pagamento_id,
            reserva_id=reserva_id,
        )
    
    # ==================== SISTEMA ====================
    
    @staticmethod
    async def notificar_erro_sistema(db, mensagem: str):
        service = NotificationService(db)
        await service.criar_notificacao(
            titulo="🔴 Erro do Sistema",
            mensagem=mensagem,
            tipo="critical",
            categoria="sistema",
            perfil="ADMIN",
        )
    
    # ==================== MÉTODOS DE CONSULTA ====================
    
    async def listar_notificacoes_usuario(
        self, 
        usuario_id: int, 
        perfil: Optional[str] = None,
        apenas_nao_lidas: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Listar notificações do usuário"""
        return await self.repo.get_by_user(
            usuario_id=usuario_id,
            perfil=perfil,
            apenas_nao_lidas=apenas_nao_lidas,
            limit=limit,
            offset=offset
        )
    
    async def contar_nao_lidas(self, usuario_id: int, perfil: Optional[str] = None) -> int:
        """Contar notificações não lidas"""
        return await self.repo.count_nao_lidas(usuario_id=usuario_id, perfil=perfil)
    
    async def marcar_como_lida(self, notificacao_id: int) -> bool:
        """Marcar notificação como lida"""
        return await self.repo.mark_as_read(notificacao_id)
    
    async def marcar_todas_lidas(self, usuario_id: int, perfil: Optional[str] = None) -> int:
        """Marcar todas as notificações como lidas"""
        return await self.repo.mark_all_as_read(usuario_id=usuario_id, perfil=perfil)
    
    async def limpar_antigas(self, dias: int = 30) -> int:
        """Limpar notificações lidas antigas"""
        return await self.repo.delete_old_read(dias=dias)
