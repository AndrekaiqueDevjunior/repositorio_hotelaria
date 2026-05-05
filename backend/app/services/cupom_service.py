import secrets
import os
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from fastapi import HTTPException

from app.repositories.cupom_repo import CupomRepository
from app.utils.datetime_utils import now_utc


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
            "pontos_bonus": pontos_bonus,
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
            },
            criado_por=criado_por,
        )
        return self._enriquecer_cupom_com_links(cupom)

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
