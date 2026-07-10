import secrets
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from fastapi import HTTPException

from app.repositories.cupom_repo import CupomRepository
from app.utils.datetime_utils import now_utc, to_utc


CUPOM_AMIGO_DESCONTO_PADRAO = Decimal("10")
CUPOM_AMIGO_PONTOS_BONUS_PADRAO = 0
CUPOM_AMIGO_DIAS_VALIDADE_PADRAO = 90
CUPOM_AMIGO_LIMITE_USOS_PADRAO = 5


class CupomService:
    def __init__(self, cupom_repo: CupomRepository):
        self.cupom_repo = cupom_repo

    async def list_all(self, apenas_ativos: bool = False) -> List[Dict[str, Any]]:
        cupons = await self.cupom_repo.list_all(apenas_ativos=apenas_ativos)
        return [self._enriquecer_cupom_com_links(cupom) for cupom in cupons]

    async def get_by_id(self, cupom_id: int) -> Dict[str, Any]:
        cupom = await self.cupom_repo.get_by_id(cupom_id)
        if not cupom:
            raise HTTPException(status_code=404, detail="Cupom não encontrado")
        return cupom

    async def get_by_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        cupom = await self.cupom_repo.get_by_codigo(codigo)
        if not cupom:
            return None
        return self._enriquecer_cupom_com_links(cupom)

    async def create(self, data: Dict[str, Any], criado_por: Optional[int] = None) -> Dict[str, Any]:
        try:
            cupom = await self.cupom_repo.create(data, criado_por=criado_por)
            return self._enriquecer_cupom_com_links(cupom)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    async def criar_cupom_amigo(
        self,
        cliente_id: int,
        percentual_desconto: Decimal,
        pontos_bonus: int,
        dias_validade: int,
        limite_total_usos: int,
        telefone_destino: Optional[str] = None,
        enviar_whatsapp: bool = False,
        criado_por: Optional[int] = None,
    ) -> Dict[str, Any]:
        cliente = await self.cupom_repo.db.cliente.find_unique(where={"id": cliente_id})
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente indicador nao encontrado")

        codigo = None
        for _tentativa in range(10):
            candidato = f"AMIGO{cliente_id}{secrets.token_hex(2).upper()}"
            existente = await self.cupom_repo.get_by_codigo(candidato)
            if not existente:
                codigo = candidato
                break

        if not codigo:
            raise HTTPException(status_code=409, detail="Nao foi possivel gerar codigo unico de cupom")

        agora = now_utc()
        data = {
            "codigo": codigo,
            "descricao": f"Cupom amigo de {getattr(cliente, 'nomeCompleto', 'cliente')}",
            "tipo_desconto": "PERCENTUAL",
            "valor_desconto": percentual_desconto,
            "pontos_bonus": 0,
            "data_inicio": agora,
            "data_fim": agora + timedelta(days=int(dias_validade or 30)),
            "limite_total_usos": int(limite_total_usos or 1),
            "limite_por_cliente": 1,
            "ativo": True,
            "tipo_campanha": "CUPOM_AMIGO",
            "cliente_indicador_id": cliente_id,
        }

        cupom = await self.cupom_repo.create(data, criado_por=criado_por)
        cupom = self._enriquecer_cupom_com_links(cupom, convite_real=True)
        cupom["cliente_indicador"] = {
            "id": cliente.id,
            "nome": getattr(cliente, "nomeCompleto", None),
        }
        if enviar_whatsapp and telefone_destino:
            try:
                from app.services.whatsapp_service import get_whatsapp_service

                cupom["whatsapp_send_result"] = await get_whatsapp_service().enviar_convite_real(
                    telefone_destino=telefone_destino,
                    codigo=cupom["codigo"],
                    link=cupom.get("link_rastreado"),
                )
            except Exception as exc:
                cupom["whatsapp_send_result"] = {"success": False, "error": str(exc)}
        return self._enriquecer_cupom_com_links(cupom)

    def _status_efetivo_cupom(self, cupom: Dict[str, Any]) -> str:
        """Status real do cupom mesmo quando a marcacao no banco e lazy
        (expiracao/esgotamento so sao gravados ao tentar validar/usar)."""
        status = (cupom.get("status") or "").lower()
        if status != "active" or not cupom.get("ativo"):
            return status or "cancelled"

        data_fim = cupom.get("data_fim")
        if data_fim:
            try:
                fim = to_utc(datetime.fromisoformat(str(data_fim).replace("Z", "+00:00")))
                if fim and fim < now_utc():
                    return "expired"
            except ValueError:
                pass

        limite = cupom.get("limite_total_usos")
        if limite and int(cupom.get("total_usos") or 0) >= int(limite):
            return "max_usage_reached"

        return "active"

    async def obter_ou_criar_cupom_amigo_cliente(self, cliente_id: int) -> Dict[str, Any]:
        """Cupom Convite Real do proprio cliente: devolve o mais recente ou
        cria o primeiro automaticamente com os padroes da Jornada Real."""
        cupom = await self.cupom_repo.get_amigo_by_cliente(cliente_id)
        if not cupom:
            cupom = await self.criar_cupom_amigo(
                cliente_id=cliente_id,
                percentual_desconto=CUPOM_AMIGO_DESCONTO_PADRAO,
                pontos_bonus=CUPOM_AMIGO_PONTOS_BONUS_PADRAO,
                dias_validade=CUPOM_AMIGO_DIAS_VALIDADE_PADRAO,
                limite_total_usos=CUPOM_AMIGO_LIMITE_USOS_PADRAO,
            )
        else:
            cupom = self._enriquecer_cupom_com_links(cupom, convite_real=True)

        cupom["status_efetivo"] = self._status_efetivo_cupom(cupom)
        return cupom

    async def gerar_novo_cupom_amigo_cliente(self, cliente_id: int) -> Dict[str, Any]:
        """Gera novo cupom Convite Real quando o atual expirou/esgotou."""
        atual = await self.cupom_repo.get_amigo_by_cliente(cliente_id)
        if atual and self._status_efetivo_cupom(atual) == "active":
            raise HTTPException(
                status_code=400,
                detail="Seu cupom atual ainda esta ativo. Gere um novo apenas quando ele expirar ou esgotar.",
            )

        cupom = await self.criar_cupom_amigo(
            cliente_id=cliente_id,
            percentual_desconto=CUPOM_AMIGO_DESCONTO_PADRAO,
            pontos_bonus=CUPOM_AMIGO_PONTOS_BONUS_PADRAO,
            dias_validade=CUPOM_AMIGO_DIAS_VALIDADE_PADRAO,
            limite_total_usos=CUPOM_AMIGO_LIMITE_USOS_PADRAO,
        )
        cupom["status_efetivo"] = "active"
        return cupom

    async def listar_usos_cupom(self, codigo: str, usage_limit: int = 25) -> List[Dict[str, Any]]:
        cupom = await self.cupom_repo.get_admin_by_codigo(codigo, include_usages=True, usage_limit=usage_limit)
        return (cupom or {}).get("usages", [])

    async def criar_cupom_rastreado(
        self,
        data: Dict[str, Any],
        criado_por: Optional[int] = None,
    ) -> Dict[str, Any]:
        codigo = (data.get("codigo") or "").strip().upper()
        if not codigo:
            prefixo = "INF" if (data.get("tipo_campanha") or "").upper() == "INFLUENCER" else "DESC"
            for _tentativa in range(10):
                candidato = f"{prefixo}{secrets.token_hex(3).upper()}"
                existente = await self.cupom_repo.get_by_codigo(candidato)
                if not existente:
                    codigo = candidato
                    break
        if not codigo:
            raise HTTPException(status_code=409, detail="Nao foi possivel gerar codigo unico de cupom")

        slug_base = (data.get("influencer_nome") or codigo).strip().lower()
        slug_limpo = "".join(ch if ch.isalnum() else "-" for ch in slug_base).strip("-")
        tracking_slug = f"{slug_limpo or codigo.lower()}-{secrets.token_hex(2)}"

        agora = now_utc()
        cupom = await self.cupom_repo.create(
            {
                "codigo": codigo,
                "descricao": data.get("descricao") or f"Cupom rastreado {codigo}",
                "tipo_desconto": data.get("tipo_desconto") or "PERCENTUAL",
                "valor_desconto": data["valor_desconto"],
                "pontos_bonus": data.get("pontos_bonus") or 0,
                "min_diarias": data.get("min_diarias"),
                "suites_permitidas": data.get("suites_permitidas"),
                "data_inicio": agora,
                "data_fim": agora + timedelta(days=int(data.get("dias_validade") or 30)),
                "limite_total_usos": data.get("limite_total_usos"),
                "limite_por_cliente": data.get("limite_por_cliente"),
                "ativo": True,
                "status": "active",
                "tipo_campanha": (data.get("tipo_campanha") or "DESCONTO").upper(),
                "tracking_slug": tracking_slug,
                "influencer_nome": data.get("influencer_nome"),
                "commission_percentual": data.get("commission_percentage") or data.get("commission_percentual"),
            },
            criado_por=criado_por,
        )
        return self._enriquecer_cupom_com_links(cupom)

    async def admin_generate_coupon(
        self,
        data: Dict[str, Any],
        criado_por: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload = await self._build_admin_coupon_payload(data, creating=True)
        cupom = await self.create(payload, criado_por=criado_por)
        admin_cupom = await self.cupom_repo.get_admin_by_codigo(cupom["codigo"], include_usages=False)
        return self._to_admin_coupon_response(admin_cupom or cupom)

    async def admin_list_coupons(
        self,
        status: Optional[str] = None,
        campaign_type: Optional[str] = None,
        influencer_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        repo_status = self._admin_status_to_repo(status) if status else None
        rows = await self.cupom_repo.list_admin(
            status=repo_status,
            tipo_campanha=(campaign_type or "").strip().upper() or None,
            apenas_influencer=bool(influencer_only),
            limit=limit,
            offset=offset,
        )
        coupons = [self._to_admin_coupon_response(row) for row in rows]
        return {"success": True, "coupons": coupons, "total": len(coupons), "limit": limit, "offset": offset}

    async def admin_get_coupon(self, code: str) -> Dict[str, Any]:
        cupom = await self.cupom_repo.get_admin_by_codigo(code, include_usages=True)
        if not cupom:
            raise HTTPException(status_code=404, detail="Cupom nao encontrado")
        return self._to_admin_coupon_response(cupom)

    async def admin_update_coupon(self, code: str, data: Dict[str, Any]) -> Dict[str, Any]:
        existente = await self.cupom_repo.get_by_codigo(code)
        if not existente:
            raise HTTPException(status_code=404, detail="Cupom nao encontrado")

        payload = await self._build_admin_coupon_payload(data, creating=False, current=existente)
        cupom = await self.update(int(existente["id"]), payload)
        admin_cupom = await self.cupom_repo.get_admin_by_codigo(cupom["codigo"], include_usages=False)
        return self._to_admin_coupon_response(admin_cupom or cupom)

    async def admin_delete_coupon(self, code: str) -> Dict[str, Any]:
        existente = await self.cupom_repo.get_by_codigo(code)
        if not existente:
            raise HTTPException(status_code=404, detail="Cupom nao encontrado")
        await self.delete(int(existente["id"]))
        return {"success": True, "code": existente["codigo"], "status": "INACTIVE"}

    async def update(self, cupom_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            cupom = await self.cupom_repo.update(cupom_id, data)
            if not cupom:
                raise HTTPException(status_code=404, detail="Cupom não encontrado")
            return self._enriquecer_cupom_com_links(cupom)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    async def set_ativo(self, cupom_id: int, ativo: bool) -> Dict[str, Any]:
        try:
            cupom = await self.cupom_repo.set_ativo(cupom_id, ativo)
            if not cupom:
                raise HTTPException(status_code=404, detail="Cupom não encontrado")
            return self._enriquecer_cupom_com_links(cupom)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    async def delete(self, cupom_id: int) -> Dict[str, Any]:
        ok = await self.cupom_repo.delete(cupom_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Cupom não encontrado")
        return {"success": True, "message": "Cupom desativado com sucesso"}

    async def validar(self, **kwargs) -> Dict[str, Any]:
        try:
            return await self.cupom_repo.validar_cupom(**kwargs)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Erro ao validar cupom: {str(exc)}")

    async def aplicar_em_reserva(self, reserva_id: int, codigo: str) -> Dict[str, Any]:
        try:
            cupom_uso = await self.cupom_repo.aplicar_cupom_reserva(reserva_id, codigo)
            if (cupom_uso.get("tipo_campanha") or "").upper() == "CUPOM_AMIGO" and cupom_uso.get("cliente_indicador_id"):
                try:
                    from app.services.indicacao_service import IndicacaoService

                    cupom_uso["indicacao"] = await IndicacaoService(
                        self.cupom_repo.db
                    ).registrar_cupom_amigo_reserva(
                        reserva_id=reserva_id,
                        cliente_indicador_id=int(cupom_uso["cliente_indicador_id"]),
                    )
                except Exception as exc:
                    # Nunca engolir em silencio: sem este log, o cupom aplica,
                    # o vinculo nao nasce e o indicador fica sem os 5 pontos
                    # sem ninguem perceber (incidente de 2026-07-10).
                    print(f"[CUPOM AMIGO] Falha ao registrar indicacao da reserva {reserva_id}: {exc}")
                    cupom_uso["indicacao"] = {
                        "success": False,
                        "motivo": f"falha_ao_registrar_indicacao: {str(exc)}",
                    }
            return cupom_uso
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Erro ao aplicar cupom: {str(exc)}")

    async def remover_da_reserva(self, reserva_id: int) -> Dict[str, Any]:
        try:
            return await self.cupom_repo.remover_cupom_reserva(reserva_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Erro ao remover cupom: {str(exc)}")

    async def obter_cupom_reserva(self, reserva_id: int) -> Optional[Dict[str, Any]]:
        return await self.cupom_repo.obter_cupom_reserva(reserva_id)

    def _base_url(self) -> str:
        return (
            os.getenv("FRONTEND_BASE_URL")
            or os.getenv("PUBLIC_SITE_URL")
            or "http://localhost:3000"
        ).strip().rstrip("/")

    def _enriquecer_cupom_com_links(self, cupom: Dict[str, Any], convite_real: bool = False) -> Dict[str, Any]:
        codigo = cupom.get("codigo")
        if not codigo:
            return cupom
        slug = cupom.get("tracking_slug")
        query_params = {
            "cupom": codigo,
            "origem": cupom.get("tipo_campanha") or "cupom",
        }
        if slug:
            query_params["ref"] = slug
        query = urlencode(query_params)
        link = f"{self._base_url()}/reservar?{query}"
        cupom["link_rastreado"] = link

        if convite_real or (cupom.get("tipo_campanha") or "").upper() == "CUPOM_AMIGO":
            try:
                from app.services.whatsapp_service import get_whatsapp_service

                whatsapp = get_whatsapp_service()
                mensagem = whatsapp.montar_mensagem_convite_real(link)
                cupom["whatsapp_message"] = mensagem
                cupom["whatsapp_share_url"] = whatsapp.montar_whatsapp_share_url(mensagem)
            except Exception:
                pass
        return cupom

    async def _build_admin_coupon_payload(
        self,
        data: Dict[str, Any],
        creating: bool,
        current: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        now = now_utc()

        campaign_type = (data.get("campaign_type") or data.get("tipo_campanha") or "").strip().upper()
        influencer_name = data.get("influencer_name") or data.get("influencer_nome")
        commission_percentage = data.get("commission_percentage")
        if commission_percentage is None:
            commission_percentage = data.get("commission_percentual")
        if not campaign_type:
            campaign_type = "INFLUENCER" if influencer_name or commission_percentage is not None else "DESCONTO"

        if creating:
            codigo = (data.get("code") or data.get("codigo") or "").strip().upper()
            if not codigo:
                prefix = "INF" if campaign_type == "INFLUENCER" else "DESC"
                codigo = await self._gerar_codigo_unico(prefix)
            payload["codigo"] = codigo
            payload["data_inicio"] = data.get("valid_from") or data.get("data_inicio") or now
            payload["data_fim"] = data["valid_until"] if "valid_until" in data else data["data_fim"]
            payload["tipo_desconto"] = data["discount_type"] if "discount_type" in data else data["tipo_desconto"]
            payload["valor_desconto"] = data["discount_value"] if "discount_value" in data else data["valor_desconto"]
        else:
            if "valid_from" in data or "data_inicio" in data:
                payload["data_inicio"] = data.get("valid_from") or data.get("data_inicio")
            if "valid_until" in data or "data_fim" in data:
                payload["data_fim"] = data.get("valid_until") or data.get("data_fim")
            if "discount_type" in data or "tipo_desconto" in data:
                payload["tipo_desconto"] = data.get("discount_type") or data.get("tipo_desconto")
            if "discount_value" in data or "valor_desconto" in data:
                payload["valor_desconto"] = data.get("discount_value") or data.get("valor_desconto")

        data_inicio = to_utc(payload.get("data_inicio") or (current or {}).get("data_inicio"))
        data_fim = to_utc(payload.get("data_fim") or (current or {}).get("data_fim"))
        if data_inicio and data_fim and data_fim <= data_inicio:
            raise HTTPException(status_code=400, detail="validUntil deve ser posterior a validFrom")

        description = data.get("description") if "description" in data else data.get("descricao")
        if creating or description is not None:
            payload["descricao"] = description or f"Cupom {payload.get('codigo') or (current or {}).get('codigo')}"

        field_map = {
            "bonus_points": "pontos_bonus",
            "pontos_bonus": "pontos_bonus",
            "min_nights": "min_diarias",
            "min_diarias": "min_diarias",
            "suite_types": "suites_permitidas",
            "suites_permitidas": "suites_permitidas",
            "max_uses": "limite_total_usos",
            "limite_total_usos": "limite_total_usos",
            "per_customer_limit": "limite_por_cliente",
            "limite_por_cliente": "limite_por_cliente",
        }
        for source, target in field_map.items():
            if source in data:
                payload[target] = data.get(source)

        if creating or "campaign_type" in data or "tipo_campanha" in data:
            payload["tipo_campanha"] = campaign_type
        if creating or "influencer_name" in data or "influencer_nome" in data:
            payload["influencer_nome"] = influencer_name
        if creating or "commission_percentage" in data or "commission_percentual" in data:
            payload["commission_percentual"] = commission_percentage

        if creating:
            payload["tracking_slug"] = self._gerar_tracking_slug(
                payload.get("influencer_nome") or payload["codigo"]
            )
        if creating or "status" in data:
            status_admin = data.get("status") or "ACTIVE"
            payload["status"] = self._admin_status_to_repo(status_admin)
            payload["ativo"] = payload["status"] == "active"

        return payload

    async def _gerar_codigo_unico(self, prefix: str) -> str:
        prefix = (prefix or "CUP").strip().upper()[:8]
        for _tentativa in range(20):
            codigo = f"{prefix}{secrets.token_hex(3).upper()}"
            existente = await self.cupom_repo.get_by_codigo(codigo)
            if not existente:
                return codigo
        raise HTTPException(status_code=409, detail="Nao foi possivel gerar codigo unico de cupom")

    def _gerar_tracking_slug(self, value: str) -> str:
        slug_base = (value or "cupom").strip().lower()
        slug_limpo = "".join(ch if ch.isalnum() else "-" for ch in slug_base).strip("-")
        return f"{slug_limpo or 'cupom'}-{secrets.token_hex(2)}"

    def _admin_status_to_repo(self, status: Optional[str]) -> str:
        normalized = (status or "ACTIVE").strip().upper()
        return {
            "ACTIVE": "active",
            "INACTIVE": "cancelled",
            "EXPIRED": "expired",
            "MAXED": "max_usage_reached",
        }.get(normalized, normalized.lower())

    def _repo_status_to_admin(self, status: Optional[str]) -> str:
        normalized = (status or "active").strip().lower()
        return {
            "active": "ACTIVE",
            "cancelled": "INACTIVE",
            "expired": "EXPIRED",
            "max_usage_reached": "MAXED",
        }.get(normalized, normalized.upper())

    def _discount_type_to_admin(self, tipo: Optional[str]) -> str:
        normalized = (tipo or "").strip().upper()
        if normalized == "PERCENTUAL":
            return "PERCENTAGE"
        if normalized == "FIXO":
            return "FIXED_AMOUNT"
        return normalized or "PERCENTAGE"

    def _to_admin_coupon_response(self, cupom: Dict[str, Any]) -> Dict[str, Any]:
        cupom = self._enriquecer_cupom_com_links(dict(cupom))
        stats = cupom.get("stats") or {}
        return {
            "success": True,
            "id": cupom.get("id"),
            "code": cupom.get("codigo"),
            "codigo": cupom.get("codigo"),
            "description": cupom.get("descricao"),
            "discountType": self._discount_type_to_admin(cupom.get("tipo_desconto")),
            "discountValue": cupom.get("valor_desconto"),
            "bonusPoints": cupom.get("pontos_bonus") or 0,
            "minNights": cupom.get("min_diarias"),
            "suiteTypes": cupom.get("suites_permitidas"),
            "maxUses": cupom.get("limite_total_usos"),
            "perCustomerLimit": cupom.get("limite_por_cliente"),
            "currentUses": cupom.get("total_usos") or stats.get("usage_count") or 0,
            "validFrom": cupom.get("data_inicio"),
            "validUntil": cupom.get("data_fim"),
            "generatedBy": cupom.get("criado_por"),
            "status": self._repo_status_to_admin(cupom.get("status")),
            "active": bool(cupom.get("ativo")),
            "campaignType": cupom.get("tipo_campanha"),
            "trackingSlug": cupom.get("tracking_slug"),
            "trackingLink": cupom.get("link_rastreado"),
            "influencerName": cupom.get("influencer_nome"),
            "commissionPercentage": cupom.get("commission_percentual"),
            "stats": {
                "usageCount": stats.get("usage_count", cupom.get("total_usos", 0)),
                "uniqueCustomers": stats.get("unique_customers", 0),
                "grossAmount": stats.get("gross_amount", 0.0),
                "discountAmount": stats.get("discount_amount", 0.0),
                "netAmount": stats.get("net_amount", 0.0),
                "commissionBase": stats.get("commission_base", stats.get("net_amount", 0.0)),
                "estimatedCommission": stats.get("estimated_commission", 0.0),
            },
            "usages": cupom.get("usages", []),
            "createdAt": cupom.get("created_at"),
            "updatedAt": cupom.get("updated_at"),
        }
