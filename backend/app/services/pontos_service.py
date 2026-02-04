from typing import Dict, Any, List
from datetime import datetime
from fastapi import HTTPException
from app.schemas.pontos_schema import (
    AjustarPontosRequest, SaldoResponse, TransacaoResponse,
    ValidarReservaRequest, ConfirmarLancamentoRequest,
    GerarConviteRequest, UsarConviteRequest,
    ValidarReservaResponse, ConviteResponse
)
from app.repositories.pontos_repo import PontosRepository
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.cliente_repo import ClienteRepository
from app.utils.cache import cache_result, invalidate_cache_pattern


class PontosService:
    def __init__(self, pontos_repo: PontosRepository, reserva_repo: ReservaRepository, cliente_repo: ClienteRepository):
        self.pontos_repo = pontos_repo
        self.reserva_repo = reserva_repo
        self.cliente_repo = cliente_repo

    @cache_result("saldo_pontos", ttl=300)
    async def get_saldo(self, cliente_id: int) -> Dict[str, Any]:
        try:
            return await self.pontos_repo.get_saldo(cliente_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao consultar saldo: {str(e)}")

    async def ajustar_pontos(
        self,
        request: AjustarPontosRequest,
        funcionario_id: int = None
    ) -> Dict[str, Any]:
        try:
            result = await self.pontos_repo.ajustar_pontos(
                request,
                funcionario_id=funcionario_id
            )

            if result["success"]:
                invalidate_cache_pattern(f"saldo_pontos:{request.cliente_id}")

            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao ajustar pontos: {str(e)}")

    async def get_historico(self, cliente_id: int, limit: int = 20) -> Dict[str, Any]:
        try:
            return await self.pontos_repo.get_historico(cliente_id, limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao consultar histórico: {str(e)}")

    async def validar_reserva_pontos(self, request: ValidarReservaRequest) -> Dict[str, Any]:
        try:
            codigo_input = (request.codigo_reserva or "").strip()
            if codigo_input.isdigit():
                reserva = await self.reserva_repo.get_by_id(int(codigo_input))
            else:
                reserva = await self.reserva_repo.get_by_codigo(codigo_input)
            if not reserva:
                return {
                    "success": False,
                    "pontos_ganhos": 0,
                    "valor_reserva": 0.0,
                    "data_checkout": "",
                    "error": "Reserva não encontrada"
                }

            if reserva["status"] != "CHECKED_OUT":
                return {
                    "success": False,
                    "pontos_ganhos": 0,
                    "valor_reserva": 0.0,
                    "data_checkout": "",
                    "error": "Reserva não está finalizada"
                }

            documento_limpo = ''.join(filter(str.isdigit, request.cpf_hospede or ""))
            if not documento_limpo or len(documento_limpo) != 11:
                return {
                    "success": False,
                    "pontos_ganhos": 0,
                    "valor_reserva": 0.0,
                    "data_checkout": "",
                    "error": "CPF inválido"
                }

            try:
                cliente = await self.cliente_repo.get_by_documento(documento_limpo)
            except Exception:
                return {
                    "success": False,
                    "pontos_ganhos": 0,
                    "valor_reserva": 0.0,
                    "data_checkout": "",
                    "error": "Cliente não encontrado"
                }

            if reserva["cliente_id"] != cliente["id"]:
                return {
                    "success": False,
                    "pontos_ganhos": 0,
                    "valor_reserva": 0.0,
                    "data_checkout": "",
                    "error": "Cliente não corresponde à reserva"
                }

            from app.services.pontos_checkout_service import buscar_regra_ativa
            from app.utils.datetime_utils import now_utc, to_utc

            tipo_suite = (reserva.get("tipo_suite") or "").upper().strip()
            num_diarias = int(reserva.get("num_diarias") or 0)

            checkout_dt = to_utc(reserva.get("checkout_realizado")) or now_utc()
            regra = await buscar_regra_ativa(self.pontos_repo.db, tipo_suite, checkout_dt.date())

            if not regra:
                pontos_ganhos = 0
            else:
                diarias_base = int(getattr(regra, "diariasBase", 2) or 2)
                rp_por_base = int(getattr(regra, "rpPorBase", 0) or 0)
                pontos_ganhos = (num_diarias // diarias_base) * rp_por_base if diarias_base > 0 else 0

            return {
                "success": True,
                "pontos_ganhos": pontos_ganhos,
                "valor_reserva": reserva.get("valor_total", reserva["valor_diaria"] * reserva["num_diarias"]),
                "data_checkout": reserva.get("checkout_realizado", "")
            }

        except Exception as e:
            return {
                "success": False,
                "pontos_ganhos": 0,
                "valor_reserva": 0.0,
                "data_checkout": "",
                "error": f"Erro ao validar reserva: {str(e)}",
            }

    async def confirmar_lancamento(self, request: ConfirmarLancamentoRequest) -> Dict[str, Any]:
        try:
            validacao = ValidarReservaRequest(
                codigo_reserva=str(request.reserva_id),
                cpf_hospede=request.cpf_hospede,
                usuario_id=request.usuario_id
            )

            resultado_validacao = await self.validar_reserva_pontos(validacao)

            if not resultado_validacao["success"]:
                return {
                    "success": False,
                    "transacao_id": 0,
                    "novo_saldo": 0,
                    "error": resultado_validacao.get("error") or "Validação falhou",
                }

            from app.services.pontos_checkout_service import creditar_rp_no_checkout

            resultado_credito = await creditar_rp_no_checkout(
                self.pontos_repo.db,
                reserva_id=request.reserva_id,
                funcionario_id=None,
                checkout_datetime=None,
            )

            if not resultado_credito.get("success"):
                return {
                    "success": False,
                    "transacao_id": 0,
                    "novo_saldo": 0,
                    "error": resultado_credito.get("error") or "Erro ao creditar pontos"
                }

            if not resultado_credito.get("creditado"):
                transacao_existente = resultado_credito.get("transacao")
                if transacao_existente and transacao_existente.get("transacao_id") is not None:
                    return {
                        "success": True,
                        "transacao_id": transacao_existente.get("transacao_id"),
                        "novo_saldo": transacao_existente.get("saldo_posterior") or 0,
                    }

                return {
                    "success": False,
                    "transacao_id": 0,
                    "novo_saldo": 0,
                    "error": resultado_credito.get("motivo") or "Pontos não creditados",
                }

            transacao = resultado_credito.get("transacao") or {}
            return {
                "success": True,
                "transacao_id": transacao.get("transacao_id"),
                "novo_saldo": transacao.get("saldo_posterior"),
            }

        except HTTPException as e:
            return {
                "success": False,
                "transacao_id": 0,
                "novo_saldo": 0,
                "error": str(e.detail),
            }
        except Exception as e:
            return {
                "success": False,
                "transacao_id": 0,
                "novo_saldo": 0,
                "error": f"Erro ao confirmar lançamento: {str(e)}",
            }

    async def gerar_convite(self, request: GerarConviteRequest) -> Dict[str, Any]:
        try:
            saldo = await self.get_saldo(request.convidante_cliente_id)

            if saldo["saldo"] < 50:
                return {
                    "success": False,
                    "error": "Saldo insuficiente para gerar convite (necessário 50 pontos)"
                }

            ajuste_request = AjustarPontosRequest(
                cliente_id=request.convidante_cliente_id,
                pontos=-50,
                motivo="Geração de convite de indicação",
                usuario_id=1
            )

            await self.ajustar_pontos(ajuste_request)

            from app.repositories.convite_repo import ConviteRepository
            from app.core.database import get_db

            db = get_db()
            convite_repo = ConviteRepository(db)

            convite = await convite_repo.criar_convite(
                convidante_id=request.convidante_cliente_id,
                usos_maximos=request.usos_maximos,
                dias_validade=30
            )

            return {
                "success": True,
                "codigo": convite["codigo"],
                "usos_maximos": convite["usos_maximos"],
                "usos_restantes": convite["usos_restantes"],
                "expires_at": convite["expires_at"]
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao gerar convite: {str(e)}")

    async def usar_convite(self, request: UsarConviteRequest) -> Dict[str, Any]:
        try:
            from app.repositories.convite_repo import ConviteRepository
            from app.core.database import get_db

            db = get_db()
            convite_repo = ConviteRepository(db)

            validacao = await convite_repo.validar_convite(request.codigo, request.cliente_id)

            if not validacao["valido"]:
                return {
                    "success": False,
                    "error": validacao["erro"]
                }

            convite = validacao["convite"]

            ajuste_convidado = AjustarPontosRequest(
                cliente_id=request.cliente_id,
                pontos=100,
                motivo=f"Bônus de indicação - Convite {request.codigo}",
                usuario_id=1
            )

            resultado_convidado = await self.ajustar_pontos(ajuste_convidado)

            if not resultado_convidado["success"]:
                return resultado_convidado

            ajuste_convidante = AjustarPontosRequest(
                cliente_id=convite["convidante_id"],
                pontos=1,
                motivo=f"Indicação aceita - Cliente {request.cliente_id}",
                usuario_id=1
            )

            await self.ajustar_pontos(ajuste_convidante)

            await convite_repo.registrar_uso(
                convite_id=convite["id"],
                convidado_id=request.cliente_id,
                pontos_ganhos=100
            )

            return {
                "success": True,
                "transacao_id": resultado_convidado["transacao_id"],
                "novo_saldo": resultado_convidado["novo_saldo"],
                "pontos_ganhos": 100,
                "convidante_bonus": 1
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao usar convite: {str(e)}")

    async def get_estatisticas(self) -> Dict[str, Any]:
        try:
            return await self.pontos_repo.get_estatisticas()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao consultar estatísticas: {str(e)}")

    @staticmethod
    def calcular_pontos_reserva(valor_total: float) -> int:
        if valor_total <= 0:
            return 0

        pontos = int(valor_total / 10)

        print(f"[PON-001] Calculando pontos: R$ {valor_total:.2f} → {pontos} pontos")

        return pontos

    async def creditar_pontos_reserva(
        self,
        cliente_id: int,
        reserva_id: int,
        pontos: int,
        motivo: str
    ) -> Dict[str, Any]:
        try:
            result = await self.pontos_repo.criar_transacao_pontos(
                cliente_id=cliente_id,
                pontos=pontos,
                tipo="CREDITO",
                origem="RESERVA",
                motivo=motivo,
                reserva_id=reserva_id
            )

            if result["success"]:
                invalidate_cache_pattern(f"saldo_pontos:{cliente_id}")

            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao creditar pontos: {str(e)}")


_pontos_service = None


async def get_pontos_service() -> PontosService:
    global _pontos_service
    if _pontos_service is None:
        from app.core.database import get_db
        db = get_db()
        _pontos_service = PontosService(
            PontosRepository(db),
            ReservaRepository(db),
            ClienteRepository(db)
        )
    return _pontos_service


async def obter_saldo_pontos(cliente_id: int):
    service = await get_pontos_service()
    return await service.get_saldo(cliente_id)


async def ajustar_pontos_cliente(request: AjustarPontosRequest):
    service = await get_pontos_service()
    return await service.ajustar_pontos(request)


async def obter_historico_pontos(cliente_id: int, limit: int = 20):
    service = await get_pontos_service()
    return await service.get_historico(cliente_id, limit)
