"""
Serviço de Cálculo de Pontos RP (Reais Pontos)
Implementa as regras específicas do Hotel Real Cabo Frio
"""

from typing import Dict, Optional
from app.core.enums import TipoSuite
from app.utils.datetime_utils import now_utc
from decimal import Decimal

class PontosRPService:
    """
    Serviço para cálculo e gestão de pontos RP conforme regras do hotel
    
    Regras:
    - Suíte Luxo: 2 diárias = R$ 600-700 = 3 RP
    - Suíte Dupla: 2 diárias = R$ 1200-1400 = 4 RP  
    - Suíte Master: 2 diárias = R$ 800-900 = 4 RP
    - Suíte Real: 2 diárias = R$ 1000-1200 = 5 RP
    
    Regra geral: "a cada duas diárias"
    """
    
    # Configuração das regras de pontos por tipo de suíte
    REGRAS_PONTOS_RP: Dict[TipoSuite, Dict] = {
        TipoSuite.LUXO: {
            "valor_min": Decimal("600.00"),
            "valor_max": Decimal("700.00"),
            "pontos": 3,
            "descricao": "Suíte Luxo - 2 diárias R$ 600-700 = 3 RP"
        },
        TipoSuite.DUPLA: {
            "valor_min": Decimal("1200.00"),
            "valor_max": Decimal("1400.00"),
            "pontos": 4,
            "descricao": "Suíte Dupla - 2 diárias R$ 1200-1400 = 4 RP"
        },
        TipoSuite.MASTER: {
            "valor_min": Decimal("800.00"),
            "valor_max": Decimal("900.00"),
            "pontos": 4,
            "descricao": "Suíte Master - 2 diárias R$ 800-900 = 4 RP"
        },
        TipoSuite.REAL: {
            "valor_min": Decimal("1000.00"),
            "valor_max": Decimal("1200.00"),
            "pontos": 5,
            "descricao": "Suíte Real - 2 diárias R$ 1000-1200 = 5 RP"
        }
    }
    
    @classmethod
    def calcular_pontos_rp(cls, tipo_suite: TipoSuite, valor_total: Decimal) -> int:
        """
        Calcula pontos RP baseado no tipo de suíte e valor total
        
        Args:
            tipo_suite: Tipo da suíte (LUXO, DUPLA, MASTER, REAL)
            valor_total: Valor total da reserva (2 diárias)
            
        Returns:
            int: Quantidade de pontos RP earned
        """
        if tipo_suite not in cls.REGRAS_PONTOS_RP:
            return 0
            
        regra = cls.REGRAS_PONTOS_RP[tipo_suite]
        
        # Verificar se o valor está dentro da faixa permitida
        if regra["valor_min"] <= valor_total <= regra["valor_max"]:
            return regra["pontos"]
            
        return 0
    
    @classmethod
    def validar_regra_pontos(cls, tipo_suite: TipoSuite, valor_total: Decimal) -> Dict:
        """
        Valida se a reserva segue as regras de pontos
        
        Args:
            tipo_suite: Tipo da suíte
            valor_total: Valor total da reserva
            
        Returns:
            Dict: Resultado da validação com detalhes
        """
        if tipo_suite not in cls.REGRAS_PONTOS_RP:
            return {
                "valido": False,
                "motivo": f"Tipo de suíte {tipo_suite.value} não possui regra de pontos",
                "pontos": 0
            }
        
        regra = cls.REGRAS_PONTOS_RP[tipo_suite]
        pontos = cls.calcular_pontos_rp(tipo_suite, valor_total)
        
        if pontos > 0:
            return {
                "valido": True,
                "motivo": regra["descricao"],
                "pontos": pontos,
                "valor_min": float(regra["valor_min"]),
                "valor_max": float(regra["valor_max"]),
                "valor_informado": float(valor_total)
            }
        else:
            return {
                "valido": False,
                "motivo": f"Valor R$ {valor_total:.2f} fora da faixa permitida (R$ {regra['valor_min']:.2f} - R$ {regra['valor_max']:.2f})",
                "pontos": 0,
                "valor_min": float(regra["valor_min"]),
                "valor_max": float(regra["valor_max"]),
                "valor_informado": float(valor_total)
            }
    
    @classmethod
    def get_todas_regras(cls) -> Dict:
        """
        Retorna todas as regras de pontos RP configuradas
        
        Returns:
            Dict: Todas as regras de pontos
        """
        return {
            suite.value: {
                "valor_min": float(regra["valor_min"]),
                "valor_max": float(regra["valor_max"]),
                "pontos": regra["pontos"],
                "descricao": regra["descricao"]
            }
            for suite, regra in cls.REGRAS_PONTOS_RP.items()
        }
    
    @classmethod
    def simular_pontos(cls, valor_total: Decimal) -> Dict:
        """
        Simula quantos pontos seriam earned para cada tipo de suíte
        
        Args:
            valor_total: Valor total para simulação
            
        Returns:
            Dict: Simulação para todos os tipos de suíte
        """
        simulacao = {}
        
        for suite, regra in cls.REGRAS_PONTOS_RP.items():
            pontos = cls.calcular_pontos_rp(suite, valor_total)
            simulacao[suite.value] = {
                "pontos": pontos,
                "valido": pontos > 0,
                "descricao": regra["descricao"],
                "valor_min": float(regra["valor_min"]),
                "valor_max": float(regra["valor_max"]),
                "valor_informado": float(valor_total)
            }
        
        return simulacao
