from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.core.validators import ClienteValidator
from app.services.real_points_service import RealPointsService


NIVEIS_PADRAO = [
    {"codigo": 0, "nome": "ESSENCIA", "pontos_minimos": 0, "ordem": 0},
    {"codigo": 1, "nome": "EXPERIENCIA", "pontos_minimos": 50, "ordem": 1},
    {"codigo": 2, "nome": "REAL", "pontos_minimos": 90, "ordem": 2},
]


class JornadaService:
    def __init__(self, db):
        self.db = db

    async def get_config(self) -> Dict[str, Any]:
        configuracoes = await self._obter_configuracoes()
        return {
            "success": True,
            "telas": configuracoes.get("telas") or {
                "cta_principal": "Comecar agora",
                "cta_pontos": "Ver meus pontos",
                "cta_premios": "Premios exclusivos",
            },
            "regras_resumidas": {
                "pontos_liberados_apos_checkout": True,
                "prazo_liberacao_horas": 48,
                "codigo_prefixo": "REAL-",
                "codigo_validade_dias": 30,
            },
        }

    async def get_regras(self) -> Dict[str, Any]:
        niveis = await self._obter_niveis()
        return {
            "success": True,
            "pontuacao_por_suite": [
                {
                    "suite": suite,
                    "pontos_por_diaria": int(regra["rp_por_diaria"]),
                    "descricao": regra["descricao"],
                }
                for suite, regra in RealPointsService.get_tabela_oficial().items()
            ],
            "niveis": [
                {
                    "codigo": self._nivel_codigo_texto(nivel["nome"]),
                    "nome": self._display_nivel(nivel["nome"]),
                    "pontos_minimos": int(nivel["pontos_minimos"]),
                }
                for nivel in niveis
            ],
            "regras_legais": {
                "pontos_liberados_apos_checkout": True,
                "prazo_liberacao_horas": 48,
                "cancelamentos_nao_geram_pontos": True,
                "no_show_nao_gera_pontos": True,
                "fraude_chargeback_estorno_bloqueiam_pontos": True,
                "premios_sujeitos_disponibilidade": True,
            },
        }

    async def consultar_jornada_por_cpf(self, cpf: str) -> Dict[str, Any]:
        cpf_norm = self._normalizar_e_validar_cpf(cpf)
        cliente = await self._buscar_cliente_por_cpf(cpf_norm)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente nao encontrado")

        await self._registrar_log(
            cliente_id=int(cliente["id"]),
            acao="consulta_jornada_cpf",
            payload={"cpf": cpf_norm},
        )
        return await self.montar_dashboard_jornada(int(cliente["id"]))

    async def montar_dashboard_jornada(self, cliente_id: int) -> Dict[str, Any]:
        cliente = await self._buscar_cliente_por_id(cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente nao encontrado")

        saldo = await self._saldo_cliente(cliente_id)
        pendentes = await self._somar_transacoes(cliente_id, "pendente")
        bloqueados = await self._somar_transacoes(cliente_id, "bloqueado")

        nivel_atual, proximo_nivel, progresso = await self._calcular_progresso_nivel(saldo)
        beneficios_ativos = await self.listar_beneficios(cliente_id, apenas_ativos=True)
        premios = await self._listar_premios_disponiveis(saldo)
        historico_pontos = await self._historico_pontos(cliente_id, limit=5)
        historico_resgates = await self._historico_resgates(cliente_id, limit=5)

        total_premios = len(premios)
        alcancados = len([premio for premio in premios if saldo >= int(premio["custo_pontos"])])

        return {
            "success": True,
            "cliente": {
                "id": int(cliente["id"]),
                "nome": self._primeiro_nome(cliente.get("nomeCompleto") or cliente.get("nome_completo") or "Cliente"),
            },
            "pontos": {
                "saldo": saldo,
                "pendentes": pendentes,
                "bloqueados": bloqueados,
            },
            "nivel": {
                "atual": self._display_nivel(nivel_atual["nome"]),
                "codigo": self._nivel_codigo_texto(nivel_atual["nome"]),
                "pontos_inicio": int(nivel_atual["pontos_minimos"]),
                "pontos_meta": progresso["meta"],
                "pontos_atuais": saldo,
                "faltam_proximo_nivel": progresso["faltam"],
                "percentual": progresso["percentual"],
            },
            "proximo_nivel": (
                {
                    "nome": self._display_nivel(proximo_nivel["nome"]),
                    "codigo": self._nivel_codigo_texto(proximo_nivel["nome"]),
                    "pontos_minimos": int(proximo_nivel["pontos_minimos"]),
                }
                if proximo_nivel
                else None
            ),
            "progresso_premios": {
                "alcancados": alcancados,
                "total": total_premios,
            },
            "beneficios_ativos": beneficios_ativos["beneficios_ativos"],
            "beneficios_proximo_nivel": beneficios_ativos["beneficios_proximo_nivel"],
            "premios_disponiveis": premios,
            "historico_resumido": {
                "pontos": historico_pontos,
                "resgates": historico_resgates,
            },
        }

    async def obter_nivel_cliente(self, cliente_id: int) -> Dict[str, Any]:
        cliente = await self._buscar_cliente_por_id(cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente nao encontrado")
        saldo = await self._saldo_cliente(cliente_id)
        nivel_atual, proximo_nivel, progresso = await self._calcular_progresso_nivel(saldo)
        return {
            "success": True,
            "cliente_id": cliente_id,
            "nivel": {
                "atual": self._display_nivel(nivel_atual["nome"]),
                "codigo": self._nivel_codigo_texto(nivel_atual["nome"]),
                "pontos_inicio": int(nivel_atual["pontos_minimos"]),
                "pontos_meta": progresso["meta"],
                "pontos_atuais": saldo,
                "faltam_proximo_nivel": progresso["faltam"],
                "percentual": progresso["percentual"],
            },
            "proximo_nivel": (
                {
                    "nome": self._display_nivel(proximo_nivel["nome"]),
                    "pontos_minimos": int(proximo_nivel["pontos_minimos"]),
                }
                if proximo_nivel
                else None
            ),
        }

    async def listar_beneficios(self, cliente_id: int, apenas_ativos: bool = True) -> Dict[str, Any]:
        saldo = await self._saldo_cliente(cliente_id)
        nivel_atual, proximo_nivel, _ = await self._calcular_progresso_nivel(saldo)
        return {
            "success": True,
            "cliente_id": cliente_id,
            "nivel_atual": self._display_nivel(nivel_atual["nome"]),
            "beneficios_ativos": await self._beneficios_do_nivel(nivel_atual, apenas_ativos=apenas_ativos),
            "proximo_nivel": self._display_nivel(proximo_nivel["nome"]) if proximo_nivel else None,
            "beneficios_proximo_nivel": (
                await self._beneficios_do_nivel(proximo_nivel, apenas_ativos=apenas_ativos)
                if proximo_nivel
                else []
            ),
        }

    async def _obter_configuracoes(self) -> Dict[str, Any]:
        try:
            rows = await self.db.query_raw(
                """
                SELECT chave, valor_json
                FROM configuracoes_jornada
                WHERE ativo = TRUE
                """
            )
        except Exception:
            return {}

        return {row["chave"]: row.get("valor_json") for row in rows}

    async def _obter_niveis(self) -> List[Dict[str, Any]]:
        try:
            rows = await self.db.query_raw(
                """
                SELECT id, codigo, nome, pontos_minimos, ordem
                FROM niveis_fidelidade
                WHERE ativo = TRUE
                ORDER BY ordem ASC, pontos_minimos ASC
                """
            )
            if rows:
                return [
                    {
                        "id": row.get("id"),
                        "codigo": int(row.get("codigo") or 0),
                        "nome": row.get("nome") or "ESSENCIA",
                        "pontos_minimos": int(row.get("pontos_minimos") or 0),
                        "ordem": int(row.get("ordem") or 0),
                    }
                    for row in rows
                ]
        except Exception:
            pass
        return [dict(nivel) for nivel in NIVEIS_PADRAO]

    async def _calcular_progresso_nivel(self, saldo: int):
        niveis = await self._obter_niveis()
        atual = niveis[0]
        for nivel in niveis:
            if saldo >= int(nivel["pontos_minimos"]):
                atual = nivel

        proximo = None
        for nivel in niveis:
            if int(nivel["pontos_minimos"]) > int(atual["pontos_minimos"]):
                proximo = nivel
                break

        if not proximo:
            progresso = {"meta": int(atual["pontos_minimos"]), "faltam": 0, "percentual": 100}
            return atual, proximo, progresso

        inicio = int(atual["pontos_minimos"])
        meta = int(proximo["pontos_minimos"])
        intervalo = max(1, meta - inicio)
        percentual = min(100, round(((saldo - inicio) / intervalo) * 100))
        progresso = {
            "meta": meta,
            "faltam": max(0, meta - saldo),
            "percentual": max(0, percentual),
        }
        return atual, proximo, progresso

    async def _saldo_cliente(self, cliente_id: int) -> int:
        rows = await self.db.query_raw(
            """
            SELECT COALESCE(saldo, 0) AS saldo
            FROM usuarios_pontos
            WHERE cliente_id = $1
            LIMIT 1
            """,
            cliente_id,
        )
        return int(rows[0]["saldo"] or 0) if rows else 0

    async def _somar_transacoes(self, cliente_id: int, status: str) -> int:
        rows = await self.db.query_raw(
            """
            SELECT COALESCE(SUM(pontos), 0) AS total
            FROM transacoes_pontos
            WHERE cliente_id = $1
              AND status = $2
              AND pontos > 0
            """,
            cliente_id,
            status,
        )
        return int(rows[0]["total"] or 0) if rows else 0

    async def _listar_premios_disponiveis(self, saldo: int) -> List[Dict[str, Any]]:
        rows = await self.db.query_raw(
            """
            SELECT p.id,
                   p.nome,
                   p.descricao,
                   p.preco_em_pontos,
                   p.estoque,
                   COALESCE(cp.nome, p.categoria) AS categoria
            FROM premios p
            LEFT JOIN categorias_premios cp ON cp.id = p.categoria_id
            WHERE p.ativo = TRUE
              AND (p.estoque IS NULL OR p.estoque > 0)
            ORDER BY p.preco_em_pontos ASC, p.id ASC
            """
        )
        return [
            {
                "id": int(row["id"]),
                "nome": row.get("nome"),
                "descricao": row.get("descricao"),
                "categoria": row.get("categoria"),
                "custo_pontos": int(row.get("preco_em_pontos") or 0),
                "estoque": row.get("estoque"),
                "resgatavel": saldo >= int(row.get("preco_em_pontos") or 0),
                "faltam_pontos": max(0, int(row.get("preco_em_pontos") or 0) - saldo),
            }
            for row in rows
        ]

    async def _beneficios_do_nivel(self, nivel: Optional[Dict[str, Any]], apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        if not nivel or not nivel.get("id"):
            return []

        where_ativo = "AND ativo = TRUE" if apenas_ativos else ""
        rows = await self.db.query_raw(
            f"""
            SELECT id, titulo, descricao, ativo
            FROM beneficios_nivel
            WHERE nivel_id = $1
            {where_ativo}
            ORDER BY id ASC
            """,
            int(nivel["id"]),
        )
        return [
            {
                "id": int(row["id"]),
                "titulo": row.get("titulo"),
                "descricao": row.get("descricao"),
                "ativo": bool(row.get("ativo")),
            }
            for row in rows
        ]

    async def _historico_pontos(self, cliente_id: int, limit: int) -> List[Dict[str, Any]]:
        rows = await self.db.query_raw(
            """
            SELECT id, tipo, origem, pontos, status, liberar_em, motivo, created_at
            FROM transacoes_pontos
            WHERE cliente_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            cliente_id,
            limit,
        )
        return [
            {
                "id": int(row["id"]),
                "tipo": row.get("tipo"),
                "origem": row.get("origem"),
                "pontos": int(row.get("pontos") or 0),
                "status": row.get("status"),
                "liberar_em": self._iso_or_none(row.get("liberar_em")),
                "motivo": row.get("motivo"),
                "created_at": self._iso_or_none(row.get("created_at")),
            }
            for row in rows
        ]

    async def _historico_resgates(self, cliente_id: int, limit: int) -> List[Dict[str, Any]]:
        rows = await self.db.query_raw(
            """
            SELECT rp.id,
                   rp.pontos_usados,
                   rp.status,
                   p.nome AS premio_nome,
                   COALESCE(cr.codigo, rp.codigo_resgate) AS codigo,
                   COALESCE(cr.valido_ate, rp.expira_em) AS valido_ate,
                   rp.created_at
            FROM resgates_premios rp
            JOIN premios p ON p.id = rp.premio_id
            LEFT JOIN codigos_resgate cr ON cr.resgate_id = rp.id
            WHERE rp.cliente_id = $1
            ORDER BY rp.created_at DESC
            LIMIT $2
            """,
            cliente_id,
            limit,
        )
        return [
            {
                "id": int(row["id"]),
                "premio_nome": row.get("premio_nome"),
                "pontos_usados": int(row.get("pontos_usados") or 0),
                "status": row.get("status"),
                "codigo": row.get("codigo"),
                "valido_ate": self._iso_or_none(row.get("valido_ate")),
                "created_at": self._iso_or_none(row.get("created_at")),
            }
            for row in rows
        ]

    async def _buscar_cliente_por_cpf(self, cpf_norm: str) -> Optional[Dict[str, Any]]:
        rows = await self.db.query_raw(
            """
            SELECT id, "nomeCompleto", documento, telefone, email
            FROM clientes
            WHERE regexp_replace(documento, '\\D', '', 'g') = $1
            LIMIT 1
            """,
            cpf_norm,
        )
        return rows[0] if rows else None

    async def _buscar_cliente_por_id(self, cliente_id: int) -> Optional[Dict[str, Any]]:
        rows = await self.db.query_raw(
            """
            SELECT id, "nomeCompleto", documento, telefone, email
            FROM clientes
            WHERE id = $1
            LIMIT 1
            """,
            cliente_id,
        )
        return rows[0] if rows else None

    async def _registrar_log(
        self,
        cliente_id: Optional[int],
        acao: str,
        payload: Optional[Dict[str, Any]] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        try:
            import json

            await self.db.execute_raw(
                """
                INSERT INTO logs_jornada (cliente_id, acao, payload, ip, user_agent, created_at)
                VALUES ($1, $2, CAST($3 AS JSONB), $4, $5, NOW())
                """,
                cliente_id,
                acao,
                json.dumps(payload or {}),
                ip,
                user_agent,
            )
        except Exception:
            return

    def _normalizar_e_validar_cpf(self, cpf: str) -> str:
        cpf_norm = "".join(filter(str.isdigit, cpf or ""))
        try:
            ClienteValidator.validar_cpf(cpf_norm)
        except HTTPException as exc:
            raise HTTPException(status_code=400, detail=exc.detail)
        return cpf_norm

    def _display_nivel(self, nome: str) -> str:
        nome_norm = (nome or "").upper()
        mapa = {
            "ESSENCIA": "Essência",
            "INICIAL": "Essência",
            "EXPERIENCIA": "Experiência",
            "REAL": "Real",
        }
        return mapa.get(nome_norm, nome.title() if nome else "Essência")

    def _nivel_codigo_texto(self, nome: str) -> str:
        nome_norm = (nome or "").upper()
        mapa = {
            "ESSENCIA": "essencia",
            "INICIAL": "essencia",
            "EXPERIENCIA": "experiencia",
            "REAL": "real",
        }
        return mapa.get(nome_norm, nome_norm.lower())

    def _primeiro_nome(self, nome: str) -> str:
        partes = [parte for parte in (nome or "").strip().split() if parte]
        return partes[0] if partes else "Cliente"

    def _iso_or_none(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)
