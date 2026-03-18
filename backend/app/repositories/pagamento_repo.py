from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from prisma import Client
from app.schemas.pagamento_schema import PagamentoCreate, PagamentoResponse, CieloWebhook
from app.services.notification_service import NotificationService
from app.services.whatsapp_service import get_whatsapp_service
from app.utils.datetime_utils import to_utc, now_utc
import uuid
from pathlib import Path

class PagamentoRepository:
    def __init__(self, db: Client):
        self.db = db

    async def _notificar_whatsapp_pagamento(self, pagamento, evento: str) -> None:
        try:
            whatsapp_service = get_whatsapp_service()
            reserva = getattr(pagamento, "reserva", None)
            cliente = getattr(pagamento, "cliente", None)
            serialized = self._serialize_pagamento(pagamento)
            await whatsapp_service.enviar_notificacao_pagamento(
                evento=evento,
                codigo_reserva=getattr(reserva, "codigoReserva", None) or f"RES-{getattr(pagamento, 'reservaId', '')}",
                cliente_nome=getattr(cliente, "nomeCompleto", None) or "Cliente nao identificado",
                valor=float(getattr(pagamento, "valor", 0) or 0),
                metodo=getattr(pagamento, "metodo", None),
                status=getattr(pagamento, "statusPagamento", None),
                nsu=getattr(pagamento, "cieloPaymentId", None),
                reserva_id=getattr(pagamento, "reservaId", None),
                pagamento_id=getattr(pagamento, "id", None),
                tef_nsu=serialized.get("tef_nsu"),
                tef_autorizacao=serialized.get("tef_autorizacao"),
                tef_cupom_cliente_arquivo=serialized.get("tef_cupom_cliente_arquivo"),
                tef_cupom_estabelecimento_arquivo=serialized.get("tef_cupom_estabelecimento_arquivo"),
            )
        except Exception as whatsapp_error:
            print(f"[WHATSAPP] Erro ao notificar pagamento ({evento}): {whatsapp_error}")

    async def _obter_valor_esperado_reserva(self, reserva_id: int, reserva=None) -> float:
        reserva_obj = reserva or await self.db.reserva.find_unique(where={"id": reserva_id})
        if not reserva_obj:
            raise ValueError("Reserva não encontrada")

        valor_base = float(reserva_obj.valorDiaria or 0) * int(reserva_obj.numDiarias or 0)
        cupom_uso = await self.db.cupomuso.find_first(where={"reservaId": reserva_id})
        if cupom_uso:
            return float(cupom_uso.valorFinal or valor_base)
        return float(valor_base)
    
    async def create(self, pagamento: PagamentoCreate, idempotency_key: str = None) -> Dict[str, Any]:
        """
        Criar novo pagamento com validações
        
        PAG-002 FIX: Valida status da reserva antes de aceitar pagamento
        IDEMPOTÊNCIA OBRIGATÓRIA: Previne pagamentos duplicados
        """
        # Obter reserva para pegar o clienteId
        reserva = await self.db.reserva.find_unique(where={"id": pagamento.reserva_id})
        if not reserva:
            raise ValueError("Reserva não encontrada")

        valor_esperado = await self._obter_valor_esperado_reserva(pagamento.reserva_id, reserva)
        if abs(float(pagamento.valor) - valor_esperado) > 0.01:
            raise ValueError(
                f"Valor do pagamento divergente da reserva. Esperado: R$ {valor_esperado:.2f}"
            )
        
        # PAG-002 FIX: Validar status da reserva antes de processar pagamento
        if reserva.statusReserva in ["CANCELADO", "CHECKED_OUT"]:
            raise ValueError(
                f"❌ NÃO É POSSÍVEL PAGAR RESERVA {reserva.statusReserva}! "
                f"Reservas canceladas ou finalizadas não podem receber pagamentos. "
                f"Status atual: {reserva.statusReserva}"
            )
        
        # PAG-002 FIX: Validação adicional - reserva muito antiga
        checkout_utc = to_utc(reserva.checkoutPrevisto)
        if checkout_utc and checkout_utc < now_utc() - timedelta(days=30):
            raise ValueError(
                f"❌ RESERVA MUITO ANTIGA! "
                f"Checkout previsto: {reserva.checkoutPrevisto.strftime('%d/%m/%Y')}. "
                f"Não é possível processar pagamentos para reservas com mais de 30 dias de atraso."
            )
        
        # ⚠️ IDEMPOTÊNCIA OBRIGATÓRIA
        # Verificar se já existe pagamento com mesma chave de idempotência
        if idempotency_key:
            pagamento_existente = await self.db.pagamento.find_first(
                where={
                    "idempotencyKey": idempotency_key
                }
            )
            
            if pagamento_existente:
                # Retornar pagamento existente ao invés de criar duplicado
                print(f"[IDEMPOTÊNCIA] Pagamento já existe com key: {idempotency_key}")
                return self._serialize_pagamento(pagamento_existente)
        
        # Verificar duplicatas por valor + reserva + timestamp próximo (5 minutos)
        cinco_minutos_atras = now_utc() - timedelta(minutes=5)
        
        pagamento_duplicado = await self.db.pagamento.find_first(
            where={
                "reservaId": pagamento.reserva_id,
                "valor": pagamento.valor,
                "metodo": pagamento.metodo,
                "createdAt": {"gte": cinco_minutos_atras},
                "statusPagamento": {"in": ["PENDENTE", "APROVADO", "CONFIRMADO", "PROCESSANDO", "PAGO"]}
            }
        )
        
        if pagamento_duplicado:
            raise ValueError(
                f"⚠️ PAGAMENTO DUPLICADO DETECTADO! "
                f"Já existe um pagamento de R$ {pagamento.valor:.2f} "
                f"para esta reserva nos últimos 5 minutos. "
                f"ID do pagamento existente: {pagamento_duplicado.id}"
            )
        
        # SEGURANÇA: Mascarar dados sensíveis do cartão
        # Armazenar apenas últimos 4 dígitos do cartão
        # NUNCA armazenar CVV (PCI-DSS compliance)
        cartao_mascarado = None
        if pagamento.cartao_numero:
            numero_limpo = pagamento.cartao_numero.replace(" ", "").replace("-", "")
            cartao_mascarado = f"****{numero_limpo[-4:]}" if len(numero_limpo) >= 4 else None
        
        # Gerar chave de idempotência se não fornecida
        if not idempotency_key:
            idempotency_key = f"pag-{reserva.id}-{uuid.uuid4().hex[:16]}"
        
        # Determinar status inicial baseado no método de pagamento
        status_inicial = "PENDENTE"
        if pagamento.metodo == "na_chegada":
            # Para pagamento na chegada, já considerar como aprovado
            status_inicial = "PAGO"
        
        # Dados do pagamento
        pagamento_data = {
            "reserva": {"connect": {"id": pagamento.reserva_id}},
            "cliente": {"connect": {"id": reserva.clienteId}},
            "valor": pagamento.valor,
            "metodo": pagamento.metodo,
            "parcelas": pagamento.parcelas,
            "cartaoUltimos4": cartao_mascarado[-4:] if cartao_mascarado else None,
            "cartaoBandeira": getattr(pagamento, 'cartao_bandeira', None),
            "dadosMascarados": True,
            "idempotencyKey": idempotency_key,
            "statusPagamento": status_inicial
        }
        
        # Criar o pagamento
        novo_pagamento = await self.db.pagamento.create(data=pagamento_data)

        pago_com_relacoes = await self.db.pagamento.find_unique(
            where={"id": novo_pagamento.id},
            include={"cliente": True, "reserva": True, "operacoesAntifraude": True, "comprovantes": True}
        )
        
        return self._serialize_pagamento(pago_com_relacoes or novo_pagamento)

    async def list_all(self) -> List[Dict[str, Any]]:
        """Listar todos os pagamentos com dados relacionados"""
        registros = await self.db.pagamento.find_many(
            order={"id": "desc"},
            include={
                "cliente": True,
                "reserva": True,
                "operacoesAntifraude": True,
                "comprovantes": True
            }
        )
        return [self._serialize_pagamento(p) for p in registros]
    
    async def get_by_id(self, pagamento_id: int) -> Dict[str, Any]:
        """Obter pagamento por ID com dados relacionados"""
        pagamento = await self.db.pagamento.find_unique(
            where={"id": pagamento_id},
            include={
                "cliente": True,
                "reserva": True,
                "operacoesAntifraude": True,
                "comprovantes": True
            }
        )
        if not pagamento:
            raise ValueError("Pagamento não encontrado")
        
        # Debug: verificar se cliente foi carregado
        print(f"[DEBUG] Pagamento ID: {pagamento.id}")
        print(f"[DEBUG] Cliente carregado: {hasattr(pagamento, 'cliente')}")
        if hasattr(pagamento, 'cliente'):
            print(f"[DEBUG] Cliente: {pagamento.cliente}")
        
        return self._serialize_pagamento(pagamento)
    
    async def get_by_payment_id(self, cielo_payment_id: str) -> Dict[str, Any]:
        """Obter pagamento pelo ID da Cielo com dados relacionados"""
        pagamento = await self.db.pagamento.find_unique(
            where={"cieloPaymentId": cielo_payment_id},
            include={
                "cliente": True,
                "reserva": True,
                "operacoesAntifraude": True,
                "comprovantes": True
            }
        )
        if not pagamento:
            raise ValueError("Pagamento não encontrado")
        return self._serialize_pagamento(pagamento)
    
    async def _salvar_comprovante_tef_texto(
        self,
        pagamento_id: int,
        sufixo: str,
        conteudo: str,
        marcador: str,
        valor_confirmado: float = None,
    ) -> Optional[Dict[str, Any]]:
        if not conteudo:
            return None

        pasta = Path("media") / "comprovantes" / "tef"
        pasta.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"tef_pag{pagamento_id}_{sufixo}_{timestamp}.txt"
        caminho = pasta / nome_arquivo
        caminho.write_text(str(conteudo), encoding="utf-8")

        existente = await self.db.comprovantepagamento.find_first(
            where={
                "pagamentoId": pagamento_id,
                "observacoes": marcador
            }
        )

        data_base = {
            "tipoComprovante": "CARTAO",
            "nomeArquivo": nome_arquivo,
            "caminhoArquivo": str(caminho),
            "observacoes": marcador,
            "statusValidacao": "APROVADO",
            "valorConfirmado": valor_confirmado,
        }

        if existente:
            return await self.db.comprovantepagamento.update(
                where={"id": existente.id},
                data=data_base
            )

        return await self.db.comprovantepagamento.create(
            data={
                "pagamento": {"connect": {"id": pagamento_id}},
                **data_base
            }
        )

    async def _persistir_detalhes_tef(
        self,
        pagamento_id: int,
        nsu: str = None,
        autorizacao: str = None,
        cupom_cliente: str = None,
        cupom_estabelecimento: str = None,
        valor_confirmado: float = None,
    ) -> None:
        meta = []
        if nsu:
            meta.append(f"NSU={nsu}")
        if autorizacao:
            meta.append(f"AUTORIZACAO={autorizacao}")
        meta_texto = "; ".join(meta)

        if cupom_cliente:
            registro_cliente = await self._salvar_comprovante_tef_texto(
                pagamento_id=pagamento_id,
                sufixo="cliente",
                conteudo=cupom_cliente,
                marcador="TEF_CUPOM_CLIENTE",
                valor_confirmado=valor_confirmado,
            )
            if registro_cliente and meta_texto:
                await self.db.comprovantepagamento.update(
                    where={"id": registro_cliente.id},
                    data={"observacoesInternas": meta_texto}
                )

        if cupom_estabelecimento:
            registro_estab = await self._salvar_comprovante_tef_texto(
                pagamento_id=pagamento_id,
                sufixo="estabelecimento",
                conteudo=cupom_estabelecimento,
                marcador="TEF_CUPOM_ESTABELECIMENTO",
                valor_confirmado=valor_confirmado,
            )
            if registro_estab and meta_texto:
                await self.db.comprovantepagamento.update(
                    where={"id": registro_estab.id},
                    data={"observacoesInternas": meta_texto}
                )

    async def update_status(
        self,
        pagamento_id: int,
        status: str,
        cielo_payment_id: str = None,
        url_pagamento: str = None,
        tef_autorizacao: str = None,
        tef_cupom_cliente: str = None,
        tef_cupom_estabelecimento: str = None
    ) -> Dict[str, Any]:
        """Atualizar status do pagamento"""
        pagamento = await self.db.pagamento.find_unique(where={"id": pagamento_id})
        if not pagamento:
            raise ValueError("Pagamento não encontrado")
        
        # Mapear status para formato padronizado
        status_map = {
            "APROVADO": "PAGO",
            "CONFIRMADO": "PAGO",
            "APPROVED": "PAGO",
            "PENDENTE": "PENDENTE",
            "PROCESSANDO": "PENDENTE",
            "AGUARDANDO_PAGAMENTO": "PENDENTE",
            "RECUSADO": "FALHOU",
            "NEGADO": "FALHOU",
            "FAILED": "FALHOU",
            "CANCELADO": "ESTORNADO",
            "ESTORNADO": "ESTORNADO"
        }
        
        # Usar o status mapeado ou o status original se não estiver no mapa
        status_atualizado = status_map.get(status, status)
        
        update_data = {
            "statusPagamento": status_atualizado
        }
        
        if cielo_payment_id:
            update_data["cieloPaymentId"] = cielo_payment_id
        if url_pagamento:
            update_data["urlPagamento"] = url_pagamento
        
        await self.db.pagamento.update(
            where={"id": pagamento_id},
            data=update_data
        )

        pagamento_base = await self.db.pagamento.find_unique(where={"id": pagamento_id})
        if (
            pagamento_base and
            (pagamento_base.metodo == "tef" or tef_cupom_cliente or tef_cupom_estabelecimento or tef_autorizacao)
        ):
            await self._persistir_detalhes_tef(
                pagamento_id=pagamento_id,
                nsu=cielo_payment_id,
                autorizacao=tef_autorizacao,
                cupom_cliente=tef_cupom_cliente,
                cupom_estabelecimento=tef_cupom_estabelecimento,
                valor_confirmado=float(pagamento_base.valor) if pagamento_base.valor is not None else None,
            )
        
        updated_pagamento = await self.db.pagamento.find_unique(
            where={"id": pagamento_id},
            include={
                "cliente": True,
                "reserva": True,
                "operacoesAntifraude": True,
                "comprovantes": True
            }
        )
        
        # Criar notificações baseadas no status
        if status == "APROVADO":
            await NotificationService.notificar_pagamento_aprovado(self.db, updated_pagamento, updated_pagamento.reserva)
            await self._notificar_whatsapp_pagamento(updated_pagamento, "aprovado")
        elif status == "RECUSADO":
            await NotificationService.notificar_pagamento_recusado(self.db, updated_pagamento, updated_pagamento.reserva)
            await self._notificar_whatsapp_pagamento(updated_pagamento, "recusado")
        elif status == "PENDENTE":
            await NotificationService.notificar_pagamento_pendente(self.db, updated_pagamento, updated_pagamento.reserva)
            await self._notificar_whatsapp_pagamento(updated_pagamento, "pendente")
        
        return self._serialize_pagamento(updated_pagamento)
    
    async def list_by_reserva(self, reserva_id: int) -> List[Dict[str, Any]]:
        """Listar pagamentos de uma reserva"""
        registros = await self.db.pagamento.find_many(
            where={"reservaId": reserva_id},
            order={"id": "asc"},
            include={
                "cliente": True,
                "reserva": True,
                "operacoesAntifraude": True,
                "comprovantes": True
            }
        )
        return [self._serialize_pagamento(p) for p in registros]
    
    async def create_manual(self, pagamento_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Criar pagamento manual (maquininha) sem enviar para Cielo
        Usado quando cliente já pagou na maquininha
        """
        # Obter reserva
        reserva = await self.db.reserva.find_unique(where={"id": pagamento_data["reserva_id"]})
        if not reserva:
            raise ValueError("Reserva não encontrada")

        valor_esperado = await self._obter_valor_esperado_reserva(pagamento_data["reserva_id"], reserva)
        if abs(float(pagamento_data["valor"]) - valor_esperado) > 0.01:
            raise ValueError(
                f"Valor do pagamento divergente da reserva. Esperado: R$ {valor_esperado:.2f}"
            )
        
        # Criar pagamento com status APROVADO
        novo_pagamento = await self.db.pagamento.create(
            data={
                "reserva": {"connect": {"id": pagamento_data["reserva_id"]}},
                "cliente": {"connect": {"id": reserva.clienteId}},
                "valor": pagamento_data["valor"],
                "metodo": pagamento_data["metodo"],
                "statusPagamento": pagamento_data["status"],  # APROVADO
                "cieloPaymentId": pagamento_data.get("cielo_payment_id"),
                "dadosMascarados": True
            }
        )
        
        # Retornar com relacionamentos
        pagamento_com_relacoes = await self.db.pagamento.find_unique(
            where={"id": novo_pagamento.id},
            include={"cliente": True, "reserva": True}
        )
        
        return self._serialize_pagamento(pagamento_com_relacoes)

    def _serialize_pagamento(self, pagamento) -> Dict[str, Any]:
        """Serializar pagamento para response"""
        cliente = getattr(pagamento, "cliente", None)
        reserva = getattr(pagamento, "reserva", None)
        operacoes = getattr(pagamento, "operacoesAntifraude", []) or []
        comprovantes = getattr(pagamento, "comprovantes", []) or []

        risk_score = None
        if operacoes:
            # usa operação mais recente
            operacao = sorted(
                operacoes, key=lambda op: getattr(op, "createdAt", datetime.min), reverse=True
            )[0]
            risk_score = getattr(operacao, "riskScore", None)

        # Obter o status do pagamento, usando statusPagamento como fallback para compatibilidade
        status = getattr(pagamento, "status", None) or getattr(pagamento, "statusPagamento", None)
        nsu = getattr(pagamento, "cieloPaymentId", None) if getattr(pagamento, "metodo", None) == "tef" else None

        tef_cupom_cliente = None
        tef_cupom_estabelecimento = None
        tef_cupom_cliente_arquivo = None
        tef_cupom_estabelecimento_arquivo = None
        tef_autorizacao = None

        for comp in comprovantes:
            marcador = (getattr(comp, "observacoes", "") or "").upper()
            caminho = getattr(comp, "caminhoArquivo", None)
            if not caminho:
                continue

            if not tef_autorizacao:
                obs_int = getattr(comp, "observacoesInternas", "") or ""
                if "AUTORIZACAO=" in obs_int:
                    try:
                        tef_autorizacao = obs_int.split("AUTORIZACAO=", 1)[1].split(";", 1)[0].strip()
                    except Exception:
                        tef_autorizacao = None

            try:
                texto = Path(caminho).read_text(encoding="utf-8")
            except Exception:
                texto = None

            if marcador == "TEF_CUPOM_CLIENTE":
                tef_cupom_cliente = texto
                tef_cupom_cliente_arquivo = f"/api/v1/comprovantes/arquivo/{getattr(comp, 'nomeArquivo', '')}"
            elif marcador == "TEF_CUPOM_ESTABELECIMENTO":
                tef_cupom_estabelecimento = texto
                tef_cupom_estabelecimento_arquivo = f"/api/v1/comprovantes/arquivo/{getattr(comp, 'nomeArquivo', '')}"

        return {
            "id": pagamento.id,
            "reserva_id": pagamento.reservaId,
            "reserva_codigo": getattr(reserva, "codigoReserva", None),
            "quarto_numero": getattr(reserva, "quartoNumero", None),
            "cliente_id": pagamento.clienteId,
            "cliente_nome": getattr(cliente, "nomeCompleto", None),
            "cliente_email": getattr(cliente, "email", None),
            "cielo_payment_id": getattr(pagamento, "cieloPaymentId", None),
            "status": status,
            "status_pagamento": status,  # Para compatibilidade
            "valor": float(pagamento.valor) if hasattr(pagamento, 'valor') and pagamento.valor is not None else 0.0,
            "metodo": getattr(pagamento, "metodo", None),
            "parcelas": getattr(pagamento, "parcelas", None),
            "cartao_final": getattr(pagamento, "cartaoUltimos4", None),
            "cartao_bandeira": getattr(pagamento, "cartaoBandeira", None),
            "url_pagamento": getattr(pagamento, "urlPagamento", None),
            "data_criacao": pagamento.createdAt.isoformat() if hasattr(pagamento, 'createdAt') and pagamento.createdAt else None,
            "dataCriacao": pagamento.createdAt.isoformat() if hasattr(pagamento, 'createdAt') and pagamento.createdAt else None,
            "risk_score": risk_score,
            "riskScore": risk_score,
            "nsu": nsu,
            "authorization_code": tef_autorizacao,
            "tef_nsu": nsu,
            "tef_autorizacao": tef_autorizacao,
            "tef_cupom_cliente": tef_cupom_cliente,
            "tef_cupom_estabelecimento": tef_cupom_estabelecimento,
            "tef_cupom_cliente_arquivo": tef_cupom_cliente_arquivo,
            "tef_cupom_estabelecimento_arquivo": tef_cupom_estabelecimento_arquivo
        }
