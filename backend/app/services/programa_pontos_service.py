import math
import os
from typing import Any, Dict, List, Optional


def _int_env(name: str, default: int) -> int:
    try:
        return int((os.getenv(name) or "").strip() or default)
    except Exception:
        return default


NIVEL_INICIAL = 0
NIVEL_EXPERIENCIA = 1
NIVEL_REAL = 2

PONTOS_EXPERIENCIA = _int_env("FIDELIDADE_EXPERIENCIA_PONTOS", 20)
PONTOS_REAL = _int_env("FIDELIDADE_REAL_PONTOS", 60)
PREMIO_PROXIMO_LIMITE_PONTOS = _int_env("PREMIO_PROXIMO_LIMITE_PONTOS", 3)
PREMIO_PROXIMO_PERCENTUAL = _int_env("PREMIO_PROXIMO_PERCENTUAL", 20)


NIVEIS_FIDELIDADE = [
    {
        "codigo": NIVEL_INICIAL,
        "nome": "INICIAL",
        "pontos_minimos": 0,
        "bonus_percentual": 0,
        "multiplicador": 1.0,
    },
    {
        "codigo": NIVEL_EXPERIENCIA,
        "nome": "EXPERIENCIA",
        "pontos_minimos": PONTOS_EXPERIENCIA,
        "bonus_percentual": 20,
        "multiplicador": 1.2,
    },
    {
        "codigo": NIVEL_REAL,
        "nome": "REAL",
        "pontos_minimos": PONTOS_REAL,
        "bonus_percentual": 40,
        "multiplicador": 1.4,
    },
]


class ProgramaPontosService:
    def __init__(self, db):
        self.db = db
        self._niveis_cache: Optional[List[Dict[str, Any]]] = None

    @staticmethod
    def nivel_por_codigo(codigo: Optional[int]) -> Dict[str, Any]:
        codigo_norm = int(codigo or 0)
        for nivel in reversed(NIVEIS_FIDELIDADE):
            if codigo_norm >= nivel["codigo"]:
                return dict(nivel)
        return dict(NIVEIS_FIDELIDADE[0])

    @staticmethod
    def nivel_por_pontos(total_pontos_nivel: int) -> Dict[str, Any]:
        total = int(total_pontos_nivel or 0)
        atual = NIVEIS_FIDELIDADE[0]
        for nivel in NIVEIS_FIDELIDADE:
            if total >= int(nivel["pontos_minimos"]):
                atual = nivel
        return dict(atual)

    @staticmethod
    def aplicar_bonus_nivel(pontos_base: int, nivel: Dict[str, Any]) -> Dict[str, Any]:
        pontos_base = int(pontos_base or 0)
        if pontos_base <= 0:
            return {
                "pontos_base": 0,
                "pontos_bonus_nivel": 0,
                "pontos_total": 0,
                "nivel": nivel,
            }

        multiplicador = float(nivel.get("multiplicador") or 1.0)
        pontos_total = math.ceil(pontos_base * multiplicador)
        pontos_bonus = max(0, pontos_total - pontos_base)
        return {
            "pontos_base": pontos_base,
            "pontos_bonus_nivel": pontos_bonus,
            "pontos_total": pontos_total,
            "nivel": nivel,
        }

    async def obter_nivel_efetivo_cliente(self, cliente_id: int) -> Dict[str, Any]:
        cliente = await self.db.cliente.find_unique(where={"id": cliente_id})
        if not cliente:
            return self.nivel_por_codigo(0)

        total_pontos_nivel = await self._calcular_total_pontos_nivel(cliente_id)
        niveis = await self._obter_niveis_configurados()
        nivel_por_pontos = self._nivel_por_pontos_configurado(total_pontos_nivel, niveis)
        nivel_cadastrado = self._nivel_por_codigo_configurado(getattr(cliente, "nivelFidelidade", 0), niveis)

        if nivel_por_pontos["codigo"] >= nivel_cadastrado["codigo"]:
            return nivel_por_pontos
        return nivel_cadastrado

    async def obter_programa_cliente(self, cliente_id: int) -> Dict[str, Any]:
        cliente = await self.db.cliente.find_unique(where={"id": cliente_id})
        if not cliente:
            return {"success": False, "error": "Cliente nao encontrado"}

        saldo_atual = await self._obter_saldo(cliente_id)
        total_pontos_nivel = await self._calcular_total_pontos_nivel(cliente_id)
        total_resgatado = await self._calcular_total_resgatado(cliente_id)

        niveis = await self._obter_niveis_configurados()
        nivel_por_pontos = self._nivel_por_pontos_configurado(total_pontos_nivel, niveis)
        nivel_cadastrado = self._nivel_por_codigo_configurado(getattr(cliente, "nivelFidelidade", 0), niveis)
        nivel_atual = nivel_por_pontos if nivel_por_pontos["codigo"] >= nivel_cadastrado["codigo"] else nivel_cadastrado
        proximo_nivel = self._proximo_nivel(nivel_atual, niveis)
        barra_nivel = self._montar_barra_nivel(total_pontos_nivel, nivel_atual, proximo_nivel)

        proximo_premio = await self.obter_proximo_premio(saldo_atual)
        barra_premio = self._montar_barra_premio(saldo_atual, proximo_premio)
        premio_proximo = self._is_premio_proximo(barra_premio)

        return {
            "success": True,
            "cliente_id": cliente_id,
            "nivel": nivel_atual,
            "saldo_atual": saldo_atual,
            "total_pontos_nivel": total_pontos_nivel,
            "total_resgatado": total_resgatado,
            "barra_nivel": barra_nivel,
            "barra_premios": barra_premio,
            "proximo_premio": proximo_premio,
            "faltam_pontos_para_proximo_premio": barra_premio["faltam_pontos"],
            "premio_proximo": premio_proximo,
        }

    async def obter_proximo_premio(self, saldo_atual: int) -> Optional[Dict[str, Any]]:
        premio = await self.db.premio.find_first(
            where={"ativo": True, "precoEmPontos": {"gt": int(saldo_atual or 0)}},
            order={"precoEmPontos": "asc"},
        )
        if not premio:
            return None
        return {
            "id": premio.id,
            "nome": premio.nome,
            "preco_em_pontos": premio.precoEmPontos,
            "categoria": getattr(premio, "categoria", None),
        }

    async def _obter_saldo(self, cliente_id: int) -> int:
        usuario_pontos = await self.db.usuariopontos.find_unique(where={"clienteId": cliente_id})
        if not usuario_pontos:
            return 0
        return int(getattr(usuario_pontos, "saldo", 0) or 0)

    async def _calcular_total_pontos_nivel(self, cliente_id: int) -> int:
        rows = await self.db.query_raw(
            """
            SELECT COALESCE(SUM(pontos), 0) AS total
            FROM transacoes_pontos
            WHERE cliente_id = $1
              AND pontos > 0
            """,
            cliente_id,
        )
        return int(rows[0]["total"] or 0) if rows else 0

    async def _calcular_total_resgatado(self, cliente_id: int) -> int:
        rows = await self.db.query_raw(
            """
            SELECT COALESCE(SUM(ABS(pontos)), 0) AS total
            FROM transacoes_pontos
            WHERE cliente_id = $1
              AND pontos < 0
            """,
            cliente_id,
        )
        return int(rows[0]["total"] or 0) if rows else 0

    async def _obter_niveis_configurados(self) -> List[Dict[str, Any]]:
        if self._niveis_cache is not None:
            return self._niveis_cache

        niveis = [dict(nivel) for nivel in NIVEIS_FIDELIDADE]

        # Em testes usamos fakes simples. No Prisma real usamos SQL para nao
        # depender de client regenerado em ambientes antigos.
        modulo_db = getattr(self.db.__class__, "__module__", "")
        if modulo_db.startswith("prisma"):
            try:
                rows = await self.db.query_raw(
                    """
                    SELECT codigo, nome, pontos_minimos, bonus_percentual, beneficios, ordem
                    FROM niveis_fidelidade
                    WHERE ativo = TRUE
                    ORDER BY ordem ASC, pontos_minimos ASC
                    """
                )
                configurados = []
                for row in rows:
                    bonus = float(row.get("bonus_percentual") or 0)
                    configurados.append({
                        "codigo": int(row.get("codigo") or 0),
                        "nome": row.get("nome") or "NIVEL",
                        "pontos_minimos": int(row.get("pontos_minimos") or 0),
                        "bonus_percentual": bonus,
                        "multiplicador": 1 + (bonus / 100),
                        "beneficios": row.get("beneficios"),
                    })
                if configurados:
                    niveis = configurados
            except Exception:
                niveis = [dict(nivel) for nivel in NIVEIS_FIDELIDADE]

        self._niveis_cache = niveis
        return niveis

    def _nivel_por_codigo_configurado(self, codigo: Optional[int], niveis: List[Dict[str, Any]]) -> Dict[str, Any]:
        codigo_norm = int(codigo or 0)
        atual = niveis[0]
        for nivel in niveis:
            if codigo_norm >= int(nivel.get("codigo") or 0):
                atual = nivel
        return dict(atual)

    def _nivel_por_pontos_configurado(self, total_pontos_nivel: int, niveis: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = int(total_pontos_nivel or 0)
        atual = niveis[0]
        for nivel in niveis:
            if total >= int(nivel.get("pontos_minimos") or 0):
                atual = nivel
        return dict(atual)

    def _proximo_nivel(self, nivel_atual: Dict[str, Any], niveis: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        niveis_ref = niveis or NIVEIS_FIDELIDADE
        codigo_atual = int(nivel_atual.get("codigo") or 0)
        for nivel in niveis_ref:
            if int(nivel["codigo"]) > codigo_atual:
                return dict(nivel)
        return None

    def _montar_barra_nivel(
        self,
        total_pontos_nivel: int,
        nivel_atual: Dict[str, Any],
        proximo_nivel: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        total = int(total_pontos_nivel or 0)
        minimo_atual = int(nivel_atual.get("pontos_minimos") or 0)
        if not proximo_nivel:
            return {
                "tipo": "nivel",
                "pontos": total,
                "meta": total,
                "percentual": 100,
                "faltam_pontos": 0,
                "proximo_nivel": None,
                "descricao": "Nivel maximo atingido",
            }

        meta = int(proximo_nivel["pontos_minimos"])
        intervalo = max(1, meta - minimo_atual)
        avancado = max(0, total - minimo_atual)
        percentual = min(100, round((avancado / intervalo) * 100))

        return {
            "tipo": "nivel",
            "pontos": total,
            "meta": meta,
            "percentual": percentual,
            "faltam_pontos": max(0, meta - total),
            "proximo_nivel": proximo_nivel,
            "descricao": "Progresso continuo por pontos acumulados",
        }

    def _montar_barra_premio(
        self,
        saldo_atual: int,
        proximo_premio: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        saldo = int(saldo_atual or 0)
        if not proximo_premio:
            return {
                "tipo": "premios",
                "pontos": saldo,
                "meta": saldo,
                "percentual": 100 if saldo > 0 else 0,
                "faltam_pontos": None,
                "descricao": "Sem premio ativo acima do saldo atual",
            }

        meta = int(proximo_premio["preco_em_pontos"] or 0)
        percentual = 100 if meta <= 0 else min(100, round((saldo / meta) * 100))
        return {
            "tipo": "premios",
            "pontos": saldo,
            "meta": meta,
            "percentual": percentual,
            "faltam_pontos": max(0, meta - saldo),
            "descricao": "Saldo disponivel para resgate; resgates reduzem esta barra",
        }

    def _is_premio_proximo(self, barra_premio: Dict[str, Any]) -> bool:
        faltam = barra_premio.get("faltam_pontos")
        meta = int(barra_premio.get("meta") or 0)
        if faltam is None or meta <= 0:
            return False
        faltam_int = int(faltam)
        limite_percentual = math.ceil(meta * (PREMIO_PROXIMO_PERCENTUAL / 100))
        limite_absoluto = int(PREMIO_PROXIMO_LIMITE_PONTOS or 0)
        limite = max(limite_percentual, limite_absoluto)
        return faltam_int <= limite
