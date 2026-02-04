"""
Repository para Comprovação de Pagamentos

Gerencia upload, validação e auditoria de comprovantes de pagamento.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from prisma import Client
from app.schemas.comprovante_schema import (
    ComprovanteUpload, 
    ValidacaoPagamento,
    TipoComprovante,
    StatusValidacao
)
from app.utils.datetime_utils import now_utc
from app.services.notification_service import NotificationService
import base64
import os
import uuid
import re

class ComprovanteRepository:
    def __init__(self, db: Client):
        self.db = db
    
    def _sanitizar_nome(self, nome: str) -> str:
        """
        Sanitiza nome para uso em caminhos de arquivo
        Remove caracteres especiais e espaços
        """
        # Remove acentos e caracteres especiais
        nome = re.sub(r'[^\w\s-]', '', nome)
        # Substitui espaços por underscores
        nome = re.sub(r'\s+', '_', nome)
        # Remove underscores múltiplos
        nome = re.sub(r'_+', '_', nome)
        # Limita o tamanho
        return nome[:50].strip('_').lower()
    
    async def upload_comprovante(self, dados: ComprovanteUpload) -> Dict[str, Any]:
        """
        Fazer upload de comprovante de pagamento
        
        Processo:
        1. Validar pagamento existe
        2. Salvar arquivo em disco
        3. Criar registro de comprovante
        4. Atualizar status do pagamento
        """
        # 1. Validar pagamento e buscar dados do cliente
        pagamento = await self.db.pagamento.find_unique(
            where={"id": dados.pagamento_id},
            include={
                "cliente": True,
                "reserva": True
            }
        )
        if not pagamento:
            raise ValueError(f"Pagamento {dados.pagamento_id} não encontrado")
        
        # 2. Criar estrutura de pastas organizada
        # Formato: uploads/comprovantes/{cliente_id}_{nome_cliente}/{ano}/{mes}/
        cliente = pagamento.cliente
        cliente_id = cliente.id
        cliente_nome = self._sanitizar_nome(cliente.nomeCompleto)
        
        # Obter data atual para organização
        agora = now_utc()
        ano = agora.strftime("%Y")
        mes = agora.strftime("%m")
        
        # Criar estrutura de diretórios
        pasta_cliente = f"uploads/comprovantes/{cliente_id}_{cliente_nome}"
        pasta_ano = f"{pasta_cliente}/{ano}"
        pasta_mes = f"{pasta_ano}/{mes}"
        
        # Criar todos os diretórios necessários
        os.makedirs(pasta_mes, exist_ok=True)
        
        # Nome do arquivo com timestamp e UUID para evitar duplicatas
        timestamp = agora.strftime("%Y%m%d_%H%M%S")
        extensao = os.path.splitext(dados.nome_arquivo)[1]
        nome_arquivo = f"comprovante_pag{dados.pagamento_id}_{timestamp}_{uuid.uuid4().hex[:8]}{extensao}"
        caminho_arquivo = f"{pasta_mes}/{nome_arquivo}"
        
        # Decodificar e salvar base64 com validações
        try:
            arquivo_bytes = base64.b64decode(dados.arquivo_base64)
            
            # Validar tamanho máximo (10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if len(arquivo_bytes) > max_size:
                raise ValueError(f"Arquivo muito grande. Tamanho máximo: 10MB")
            
            # Validar extensão permitida
            extensao = os.path.splitext(dados.nome_arquivo)[1].lower()
            extensoes_permitidas = {'.pdf', '.jpg', '.jpeg', '.png', '.webp'}
            
            if extensao not in extensoes_permitidas:
                raise ValueError(f"Extensão não permitida. Use: PDF, JPG, PNG ou WEBP")
            
            # Validar magic bytes para PDF
            if extensao == '.pdf':
                if not arquivo_bytes.startswith(b'%PDF'):
                    raise ValueError("Arquivo PDF inválido ou corrompido")
            
            with open(caminho_arquivo, "wb") as f:
                f.write(arquivo_bytes)
        except Exception as e:
            raise ValueError(f"Erro ao salvar arquivo: {str(e)}")
        
        # 3. Criar registro no banco de dados
        comprovante = await self.db.comprovantepagamento.create(
            data={
                "pagamentoId": dados.pagamento_id,
                "tipoComprovante": dados.tipo_comprovante.value,
                "nomeArquivo": nome_arquivo,
                "caminhoArquivo": caminho_arquivo,
                "observacoes": dados.observacoes,
                "valorConfirmado": dados.valor_confirmado,
                "statusValidacao": StatusValidacao.AGUARDANDO_COMPROVANTE.value,
                "dataUpload": agora,
            }
        )
        
        # 4. Atualizar status do pagamento
        await self.db.pagamento.update(
            where={"id": dados.pagamento_id},
            data={
                "statusPagamento": "PENDENTE",
                "updatedAt": agora
            }
        )
        
        # 5. Criar notificação para administradores
        try:
            notification_service = NotificationService(self.db)
            await notification_service.criar_notificacao(
                titulo="📤 Novo Comprovante Recebido",
                mensagem=f"Cliente: {cliente.nomeCompleto} | Valor: R$ {float(dados.valor_confirmado or 0):.2f} | Tipo: {dados.tipo_comprovante.value}",
                tipo="info",
                categoria="pagamento",
                perfil="ADMIN,RECEPCAO",
                pagamento_id=dados.pagamento_id,
                reserva_id=pagamento.reservaId,
                url_acao=f"/comprovantes"
            )
            print(f"[NOTIFICAÇÃO] Criada para comprovante do pagamento #{dados.pagamento_id}")
        except Exception as e:
            print(f"[NOTIFICAÇÃO] Erro ao criar notificação: {str(e)}")
        
        return {
            "success": True,
            "comprovante": comprovante,
            "message": f"Comprovante enviado com sucesso! Aguardando validação.",
            "caminho": caminho_arquivo,
            "pasta_cliente": pasta_cliente
        }
    
    async def validar_comprovante(self, dados: ValidacaoPagamento) -> Dict[str, Any]:
        """
        Validar comprovante de pagamento
        
        Processo:
        1. Buscar comprovante
        2. Atualizar status
        3. Aprovar/reprovar pagamento
        4. Registrar auditoria
        """
        # 1. Buscar comprovante
        comprovante = await self.db.comprovantepagamento.find_first(
            where={"pagamentoId": dados.pagamento_id}
        )
        if not comprovante:
            raise ValueError(f"Comprovante não encontrado para pagamento {dados.pagamento_id}")
        
        # 2. Atualizar status
        comprovante_atualizado = await self.db.comprovantepagamento.update(
            where={"id": comprovante.id},
            data={
                "statusValidacao": dados.status.value,
                "dataValidacao": now_utc(),
                "validadorId": dados.usuario_validador_id,
                "motivoRecusa": dados.motivo if dados.status == StatusValidacao.RECUSADO else None,
                "observacoesInternas": dados.observacoes_internas,
            }
        )
        
        # 3. Atualizar pagamento
        # Alinhar com StatusPagamento (CONFIRMADO/PENDENTE/NEGADO...).
        status_pagamento = "CONFIRMADO" if dados.status == StatusValidacao.APROVADO else "NEGADO"
        await self.db.pagamento.update(
            where={"id": dados.pagamento_id},
            data={
                "statusPagamento": status_pagamento,
                "updatedAt": now_utc()
            }
        )
        
        # 4. Se aprovado, liberar check-in da reserva + gatilhos adicionais
        if dados.status == StatusValidacao.APROVADO:
            pagamento = await self.db.pagamento.find_unique(
                where={"id": dados.pagamento_id},
                include={"reserva": True, "cliente": True}
            )
            if pagamento and pagamento.reservaId:
                # 4a. Atualizar status da reserva
                status_reserva = "CONFIRMADA"
                await self.db.reserva.update(
                    where={"id": pagamento.reservaId},
                    data={
                        "statusReserva": status_reserva
                    }
                )

                # 4b. Criar/atualizar hospedagem (gatilho)
                try:
                    hospedagem_existente = await self.db.hospedagem.find_first(
                        where={"reservaId": pagamento.reservaId}
                    )
                    
                    if not hospedagem_existente:
                        await self.db.hospedagem.create(
                            data={
                                "reservaId": pagamento.reservaId,
                                "statusHospedagem": "NAO_INICIADA",
                                "dataPrevistaCheckin": pagamento.reserva.checkinPrevisto,
                                "dataPrevistaCheckout": pagamento.reserva.checkoutPrevisto,
                                "created_at": now_utc()
                            }
                        )
                        print(f"[HOSPEDAGEM] Criada para reserva #{pagamento.reservaId}")
                    else:
                        await self.db.hospedagem.update(
                            where={"id": hospedagem_existente.id},
                            data={"statusHospedagem": "NAO_INICIADA"}
                        )
                        print(f"[HOSPEDAGEM] Atualizada para reserva #{pagamento.reservaId}")
                except Exception as e:
                    print(f"[HOSPEDAGEM] Erro ao criar/atualizar (não crítico): {e}")

                # 4c. Atualizar disponibilidade do quarto (gatilho)
                try:
                    if pagamento.reserva.quartoId:
                        await self.db.quarto.update(
                            where={"id": pagamento.reserva.quartoId},
                            data={"status": "RESERVADO"}  # Quarto agora reservado/confirmado
                        )
                        print(f"[QUARTO] Status atualizado para RESERVADO - Quarto #{pagamento.reserva.quartoId}")
                except Exception as e:
                    print(f"[QUARTO] Erro ao atualizar disponibilidade (não crítico): {e}")

                # 4d. Notificar cliente (gatilho)
                try:
                    notification_service = NotificationService(self.db)
                    
                    if pagamento.cliente:
                        await notification_service.criar_notificacao(
                            titulo="✅ Pagamento Aprovado!",
                            mensagem=f"Seu pagamento foi aprovado! Check-in liberado para reserva #{pagamento.reserva.codigoReserva}",
                            tipo="success",
                            categoria="reserva",
                            usuario_destino_id=pagamento.cliente.id,  # Notificar cliente específico
                            reserva_id=pagamento.reservaId,
                            pagamento_id=dados.pagamento_id,
                            url_acao=f"/minhas-reservas/{pagamento.reservaId}"
                        )
                        
                        # Notificação interna para recepção
                        await notification_service.criar_notificacao(
                            titulo="🏨 Check-in Liberado",
                            mensagem=f"Cliente {pagamento.cliente.nomeCompleto} pode fazer check-in | Reserva: #{pagamento.reserva.codigoReserva}",
                            tipo="info",
                            categoria="operacional",
                            perfil="RECEPCAO,ADMIN",
                            reserva_id=pagamento.reservaId,
                            pagamento_id=dados.pagamento_id,
                            url_acao=f"/checkin/{pagamento.reservaId}"
                        )
                        
                        print(f"[NOTIFICACAO] Cliente e recepção notificados - Reserva #{pagamento.reservaId}")
                except Exception as e:
                    print(f"[NOTIFICACAO] Erro ao notificar cliente (não crítico): {e}")

                # 4e. Trigger de pontos (se aplicável) - gatilho
                try:
                    # Verificar se já existe registro de pontos para esta reserva
                    pontos_existentes = await self.db.usuariospontos.find_first(
                        where={"clienteId": pagamento.cliente.id}
                    )
                    
                    if not pontos_existentes:
                        await self.db.usuariospontos.create(
                            data={
                                "clienteId": pagamento.cliente.id,
                                "saldoAtual": 0,
                                "rpPoints": 0,
                                "created_at": now_utc()
                            }
                        )
                        print(f"[PONTOS] Conta de pontos criada para cliente #{pagamento.cliente.id}")
                    
                    # Notificar sobre potencial de ganho de pontos no check-out
                    await notification_service.criar_notificacao(
                        titulo="💎 Pontos em Jogo!",
                        mensagem=f"Ganhe pontos RP no check-out! Fique hospedado e acumule recompensas.",
                        tipo="info",
                        categoria="pontos",
                        usuario_destino_id=pagamento.cliente.id,
                        reserva_id=pagamento.reservaId,
                        url_acao="/pontos-rp"
                    )
                    
                    print(f"[PONTOS] Trigger de pontos ativado para reserva #{pagamento.reservaId}")
                except Exception as e:
                    print(f"[PONTOS] Erro ao configurar pontos (não crítico): {e}")

                print(f"[COMPROVANTE] Todos os gatilhos executados para aprovação - Reserva #{pagamento.reservaId}")
        
        # 4b. Se rejeitado, marcar como rejeitado + gatilhos adicionais
        elif dados.status == StatusValidacao.RECUSADO:
            pagamento = await self.db.pagamento.find_unique(
                where={"id": dados.pagamento_id},
                include={"reserva": True, "cliente": True}
            )
            if pagamento and pagamento.reservaId:
                # 4b.1. Atualizar status da reserva
                await self.db.reserva.update(
                    where={"id": pagamento.reservaId},
                    data={"statusReserva": "PAGA_REJEITADA"}
                )

                # 4b.2. Liberar quarto (gatilho)
                try:
                    if pagamento.reserva.quartoId:
                        await self.db.quarto.update(
                            where={"id": pagamento.reserva.quartoId},
                            data={"status": "LIVRE"}  # Quarto liberado para nova reserva
                        )
                        print(f"[QUARTO] Liberado para nova reserva - Quarto #{pagamento.reserva.quartoId}")
                except Exception as e:
                    print(f"[QUARTO] Erro ao liberar quarto (não crítico): {e}")

                # 4b.3. Notificar cliente sobre rejeição (gatilho)
                try:
                    notification_service = NotificationService(self.db)
                    
                    if pagamento.cliente:
                        await notification_service.criar_notificacao(
                            titulo="❌ Pagamento Recusado",
                            mensagem=f"Seu comprovante foi recusado. Motivo: {dados.motivo or 'Não informado'}. Por favor, envie um novo comprovante.",
                            tipo="warning",
                            categoria="pagamento",
                            usuario_destino_id=pagamento.cliente.id,  # Notificar cliente específico
                            reserva_id=pagamento.reservaId,
                            pagamento_id=dados.pagamento_id,
                            url_acao=f"/minhas-reservas/{pagamento.reservaId}"
                        )
                        
                        # Notificação interna para recepção/admin
                        await notification_service.criar_notificacao(
                            titulo="🚫 Pagamento Recusado",
                            mensagem=f"Comprovante recusado | Cliente: {pagamento.cliente.nomeCompleto} | Motivo: {dados.motivo}",
                            tipo="warning",
                            categoria="pagamento",
                            perfil="ADMIN,RECEPCAO",
                            reserva_id=pagamento.reservaId,
                            pagamento_id=dados.pagamento_id,
                            url_acao=f"/comprovantes"
                        )
                        
                        print(f"[NOTIFICACAO] Cliente e equipe notificados sobre rejeição - Reserva #{pagamento.reservaId}")
                except Exception as e:
                    print(f"[NOTIFICACAO] Erro ao notificar sobre rejeição (não crítico): {e}")

                print(f"[COMPROVANTE] Gatilhos de rejeição executados - Reserva #{pagamento.reservaId}")
        
        # 5. Registrar auditoria (corrigido para tabela correta)
        try:
            await self.db.auditoria.create(
                data={
                    "usuarioId": dados.usuario_validador_id,
                    "entidade": "pagamento",
                    "entidadeId": str(dados.pagamento_id),
                    "acao": dados.status.value,
                    "payload_resumo": f"Validação de comprovante: {dados.motivo or 'Sem motivo'}",
                    "created_at": now_utc()
                }
            )
        except Exception as e:
            print(f"[AUDITORIA] Erro ao registrar auditoria (não crítico): {e}")
            # Não falhar se auditoria falhar
        
        # 6. Criar notificação sobre a validação (corrigido)
        try:
            notification_service = NotificationService(self.db)
            
            # Buscar dados do pagamento e cliente
            pagamento = await self.db.pagamento.find_unique(
                where={"id": dados.pagamento_id},
                include={"cliente": True, "reserva": True}
            )
            
            if pagamento and pagamento.cliente:
                if dados.status == StatusValidacao.APROVADO:
                    await notification_service.criar_notificacao(
                        titulo="✅ Comprovante Aprovado",
                        mensagem=f"Pagamento de R$ {float(pagamento.valor):.2f} aprovado | Cliente: {pagamento.cliente.nomeCompleto}",
                        tipo="success",
                        categoria="pagamento",
                        perfil="ADMIN,RECEPCAO",
                        pagamento_id=dados.pagamento_id,
                        reserva_id=pagamento.reservaId,
                        url_acao=f"/pagamentos"
                    )
                else:
                    await notification_service.criar_notificacao(
                        titulo="❌ Comprovante Recusado",
                        mensagem=f"Pagamento de R$ {float(pagamento.valor):.2f} recusado | Motivo: {dados.motivo}",
                        tipo="warning",
                        categoria="pagamento",
                        perfil="ADMIN,RECEPCAO",
                        pagamento_id=dados.pagamento_id,
                        reserva_id=pagamento.reservaId,
                        url_acao=f"/pagamentos"
                    )
            
            print(f"[NOTIFICAÇÃO] Criada para validação do pagamento #{dados.pagamento_id}")
        except Exception as e:
            print(f"[NOTIFICAÇÃO] Erro ao criar notificação de validação (não crítico): {str(e)}")
            # Não falhar se notificação falhar
        
        return {
            "success": True,
            "comprovante": comprovante_atualizado,
            "message": f"Pagamento {dados.status.value} com sucesso!"
        }
    
    async def listar_pendentes_validacao(self) -> List[Dict[str, Any]]:
        """Listar comprovantes aguardando validação"""
        comprovantes = await self.db.comprovantepagamento.find_many(
            where={
                "statusValidacao": StatusValidacao.AGUARDANDO_COMPROVANTE.value
            },
            include={
                "pagamento": {
                    "include": {
                        "reserva": {
                            "include": {
                                "cliente": True
                            }
                        }
                    }
                }
            },
            order={"dataUpload": "asc"}
        )
        
        # Serializar para dicionários
        return [self._serialize_comprovante_completo(c) for c in comprovantes]
    
    async def listar_em_analise(self) -> List[Dict[str, Any]]:
        """Listar comprovantes em análise"""
        comprovantes = await self.db.comprovantepagamento.find_many(
            where={
                "statusValidacao": StatusValidacao.EM_ANALISE.value
            },
            include={
                "pagamento": {
                    "include": {
                        "reserva": {
                            "include": {
                                "cliente": True
                            }
                        }
                    }
                }
            },
            order={"dataUpload": "asc"}
        )
        
        # Serializar para dicionários
        return [self._serialize_comprovante_completo(c) for c in comprovantes]
    
    async def dashboard_validacao(self) -> Dict[str, Any]:
        """Estatísticas para dashboard de validação"""
        hoje = now_utc().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Contagens por status
        aguardando = await self.db.comprovantepagamento.count(
            where={"statusValidacao": StatusValidacao.AGUARDANDO_COMPROVANTE.value}
        )
        
        em_analise = await self.db.comprovantepagamento.count(
            where={"statusValidacao": StatusValidacao.EM_ANALISE.value}
        )
        
        aprovados_hoje = await self.db.comprovantepagamento.count(
            where={
                "statusValidacao": StatusValidacao.APROVADO.value,
                "dataValidacao": {
                    "gte": hoje
                }
            }
        )
        
        recusados_hoje = await self.db.comprovantepagamento.count(
            where={
                "statusValidacao": StatusValidacao.RECUSADO.value,
                "dataValidacao": {
                    "gte": hoje
                }
            }
        )
        
        return {
            "aguardando_comprovante": aguardando,
            "em_analise": em_analise,
            "aprovados_hoje": aprovados_hoje,
            "recusados_hoje": recusados_hoje,
            "total_pendentes": aguardando + em_analise
        }
    
    async def get_comprovante_by_arquivo(self, nome_arquivo: str) -> Optional[Dict[str, Any]]:
        """Buscar comprovante pelo nome do arquivo"""
        comprovante = await self.db.comprovantepagamento.find_first(
            where={"nomeArquivo": nome_arquivo},
            include={"pagamento": True}
        )
        return comprovante
    
    def _serialize_comprovante_completo(self, comprovante) -> Dict[str, Any]:
        """Serializar comprovante com dados relacionados"""
        if not comprovante:
            return None
        
        result = {
            "id": comprovante.id,
            "pagamento_id": comprovante.pagamentoId,
            "tipo_comprovante": comprovante.tipoComprovante,
            "nome_arquivo": comprovante.nomeArquivo,
            "caminho_arquivo": comprovante.caminhoArquivo,
            "observacoes": comprovante.observacoes,
            "valor_confirmado": float(comprovante.valorConfirmado) if comprovante.valorConfirmado else None,
            "status_validacao": comprovante.statusValidacao,
            "data_upload": comprovante.dataUpload.isoformat() if comprovante.dataUpload else None,
            "data_validacao": comprovante.dataValidacao.isoformat() if comprovante.dataValidacao else None,
            "validador_id": comprovante.validadorId,
            "motivo_recusa": comprovante.motivoRecusa,
        }
        
        # Adicionar dados do pagamento se disponível
        if hasattr(comprovante, 'pagamento') and comprovante.pagamento:
            pagamento = comprovante.pagamento
            result["pagamento"] = {
                "id": pagamento.id,
                "valor": float(pagamento.valor),
                "metodo": pagamento.metodo,
                "status_pagamento": pagamento.statusPagamento,
            }
            
            # Adicionar dados da reserva se disponível
            if hasattr(pagamento, 'reserva') and pagamento.reserva:
                reserva = pagamento.reserva
                result["reserva"] = {
                    "id": reserva.id,
                    "codigo_reserva": reserva.codigoReserva,
                    "status_reserva": reserva.statusReserva,
                }
                
                # Adicionar dados do cliente se disponível
                if hasattr(reserva, 'cliente') and reserva.cliente:
                    cliente = reserva.cliente
                    result["cliente"] = {
                        "id": cliente.id,
                        "nome_completo": cliente.nomeCompleto,
                        "documento": cliente.documento,
                        "email": cliente.email,
                    }
        
        return result
