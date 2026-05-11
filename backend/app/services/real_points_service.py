"""
REAL POINTS (RP) - SISTEMA OFICIAL DE FIDELIDADE

Servico unico para a regra de pontos da Jornada Real.

Regra vigente nas telas:
- Suite Luxo: 1 ponto por diaria
- Suite Master: 2 pontos por diaria
- Suite Dupla: 3 pontos por diaria
- Suite Real: 3 pontos por diaria
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


class RealPointsService:
    """Calculo oficial de Real Points (RP)."""

    TABELA_OFICIAL_RP = {
        "LUXO": {
            "rp_por_diaria": 1,
            "descricao": "Suite Luxo - 1 ponto por diaria",
        },
        "MASTER": {
            "rp_por_diaria": 2,
            "descricao": "Suite Master - 2 pontos por diaria",
        },
        "DUPLA": {
            "rp_por_diaria": 3,
            "descricao": "Suite Dupla - 3 pontos por diaria",
        },
        "REAL": {
            "rp_por_diaria": 3,
            "descricao": "Suite Real - 3 pontos por diaria",
        },
    }

    PREMIOS_OFICIAIS = {
        "diaria_hidro_champagne": {
            "custo_rp": 25,
            "nome": "1 diaria com hidromassagem e champagne cortesia",
            "descricao": "Experiencia O Retorno do Sonho",
            "categoria": "O Retorno do Sonho",
        },
        "cafeteira_premium": {
            "custo_rp": 35,
            "nome": "Cafeteira Premium",
            "descricao": "Cafeteira Premium",
            "categoria": "Rituais do Real",
        },
        "iphone_16": {
            "custo_rp": 90,
            "nome": "iPhone 16",
            "descricao": "Smartphone iPhone 16",
            "categoria": "Tecnologia Real",
        },
    }

    @classmethod
    def calcular_rp_oficial(cls, suite: str, diarias: int, valor_total: float = 0) -> Tuple[int, str]:
        """
        Calcula RP pela regra vigente:

        RP_total = total_diarias x pontos_por_diaria_da_suite
        """
        suite_normalizada = (suite or "").upper().strip()
        if suite_normalizada not in cls.TABELA_OFICIAL_RP:
            return 0, f"Suite '{suite}' invalida"

        diarias_int = int(diarias or 0)
        if diarias_int <= 0:
            return 0, "Sem diarias validas (0 RP)"

        regra = cls.TABELA_OFICIAL_RP[suite_normalizada]
        rp_por_diaria = int(regra["rp_por_diaria"])
        rp_total = diarias_int * rp_por_diaria
        detalhe = f"{diarias_int} diaria(s) x {rp_por_diaria} RP = {rp_total} RP"
        return rp_total, detalhe

    @classmethod
    def validar_requisitos_oficiais(cls, reserva: Dict[str, Any]) -> Tuple[bool, str]:
        status = (reserva.get("status") or "").upper()
        if status not in {"CHECKED_OUT", "CHECKOUT_REALIZADO"}:
            return False, f"Reserva nao esta em checkout realizado (status: {status})"

        if not reserva.get("pagamento_confirmado", False):
            return False, "Pagamento nao confirmado"

        diarias = int(reserva.get("num_diarias", 0) or 0)
        if diarias <= 0:
            return False, f"Reserva sem diarias validas ({diarias})"

        suite = (reserva.get("tipo_suite") or "").strip()
        if not suite:
            return False, "Tipo de suite nao definido"

        if suite.upper() not in cls.TABELA_OFICIAL_RP:
            return False, f"Suite '{suite}' invalida"

        valor_total = float(reserva.get("valor_total", 0) or 0)
        if valor_total < 0:
            return False, "Valor total invalido"

        return True, "Todos os requisitos atendidos"

    @classmethod
    def validar_antifraude(cls, reserva: Dict[str, Any]) -> Tuple[bool, str]:
        checkout_realizado = reserva.get("checkout_realizado")
        if not checkout_realizado:
            return False, "Check-out nao realizado"

        data_criacao = reserva.get("created_at")
        data_checkout = reserva.get("checkout_realizado")
        if data_criacao and data_checkout:
            if isinstance(data_criacao, str):
                data_criacao = datetime.fromisoformat(data_criacao.replace("Z", "+00:00"))
            if isinstance(data_checkout, str):
                data_checkout = datetime.fromisoformat(data_checkout.replace("Z", "+00:00"))

            diferenca_horas = (data_checkout - data_criacao).total_seconds() / 3600
            if diferenca_horas < 1:
                return False, f"Reserva encerrada em menos de 1h ({diferenca_horas:.1f}h)"

        return True, "Validacoes antifraude OK"

    @classmethod
    def pode_resgatar_premio(cls, cliente_rp: int, premio_id: str) -> Tuple[bool, str]:
        if premio_id not in cls.PREMIOS_OFICIAIS:
            return False, f"Premio '{premio_id}' invalido"

        premio = cls.PREMIOS_OFICIAIS[premio_id]
        custo_rp = int(premio["custo_rp"])
        if int(cliente_rp or 0) < custo_rp:
            return False, f"RP insuficiente (tem: {cliente_rp}, precisa: {custo_rp})"

        return True, "Pode resgatar"

    @classmethod
    def get_premio(cls, premio_id: str) -> Optional[Dict[str, Any]]:
        return cls.PREMIOS_OFICIAIS.get(premio_id)

    @classmethod
    def listar_premios(cls) -> Dict[str, Dict[str, Any]]:
        return cls.PREMIOS_OFICIAIS.copy()

    @classmethod
    def get_tabela_oficial(cls) -> Dict[str, Dict[str, Any]]:
        return cls.TABELA_OFICIAL_RP.copy()

    @classmethod
    def simular_calculo(cls, suite: str, diarias: int, valor_total: float) -> Dict[str, Any]:
        reserva_simulada = {
            "status": "CHECKOUT_REALIZADO",
            "pagamento_confirmado": True,
            "num_diarias": diarias,
            "tipo_suite": suite,
            "valor_total": valor_total,
            "created_at": datetime.now(timezone.utc),
            "checkout_realizado": datetime.now(timezone.utc),
        }

        resultado = {
            "suite": suite,
            "diarias": diarias,
            "valor_total": valor_total,
            "rp_calculados": 0,
            "pode_conceder": False,
            "validacoes": [],
            "erros": [],
        }

        pode, motivo = cls.validar_requisitos_oficiais(reserva_simulada)
        if pode:
            resultado["validacoes"].append("Requisitos oficiais OK")
        else:
            resultado["erros"].append(f"Requisitos: {motivo}")

        valido, motivo = cls.validar_antifraude(reserva_simulada)
        if valido:
            resultado["validacoes"].append("Antifraude OK")
        else:
            resultado["erros"].append(f"Antifraude: {motivo}")

        if pode and valido:
            rp, detalhe = cls.calcular_rp_oficial(suite, diarias, valor_total)
            resultado["rp_calculados"] = rp
            resultado["pode_conceder"] = True
            resultado["validacoes"].append(f"Calculo: {detalhe}")

        return resultado


real_points_service = RealPointsService()


def demo_real_points():
    print("REAL POINTS (RP) - DEMONSTRACAO OFICIAL")
    print("=" * 60)
    exemplos = [
        {"suite": "LUXO", "diarias": 2, "valor": 650},
        {"suite": "REAL", "diarias": 4, "valor": 1100},
        {"suite": "MASTER", "diarias": 3, "valor": 850},
        {"suite": "DUPLA", "diarias": 2, "valor": 1300},
    ]

    for ex in exemplos:
        rp, detalhe = RealPointsService.calcular_rp_oficial(ex["suite"], ex["diarias"], ex["valor"])
        print(f"{ex['suite']} - {ex['diarias']} diarias: {rp} RP ({detalhe})")


if __name__ == "__main__":
    demo_real_points()
