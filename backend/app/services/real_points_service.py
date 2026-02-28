"""
📘 REAL POINTS (RP) - SISTEMA OFICIAL DE FIDELIDADE
==================================================

Implementação única e oficial do sistema de pontos Real Points (RP)
baseado exclusivamente na regra de negócio fornecida.

Regra Principal:
- Baseado em estadias concluídas (CHECKED_OUT)
- Pontos a cada 2 diárias completas
- Apenas checkout gera pontos
- Tabela oficial por tipo de suíte
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from decimal import Decimal


class RealPointsService:
    """
    Serviço oficial de cálculo e gestão de Real Points (RP)
    
    Implementa 100% a regra de negócio oficial do Hotel Real Cabo Frio
    """
    
    # 📋 TABELA OFICIAL DE PONTOS - REGRA DE NEGÓCIO
    TABELA_OFICIAL_RP = {
        "LUXO": {
            "rp_por_bloco": 3,
            "valor_min_diaria": 300,
            "valor_max_diaria": 350,
            "valor_min_2_diarias": 600,
            "valor_max_2_diarias": 700,
            "descricao": "Suíte Luxo - 2 diárias R$ 600-700 = 3 RP"
        },
        "DUPLA": {
            "rp_por_bloco": 4,
            "valor_min_diaria": 600,
            "valor_max_diaria": 700,
            "valor_min_2_diarias": 1200,
            "valor_max_2_diarias": 1400,
            "descricao": "Suíte Dupla - 2 diárias R$ 1200-1400 = 4 RP"
        },
        "MASTER": {
            "rp_por_bloco": 4,
            "valor_min_diaria": 400,
            "valor_max_diaria": 450,
            "valor_min_2_diarias": 800,
            "valor_max_2_diarias": 900,
            "descricao": "Suíte Master - 2 diárias R$ 800-900 = 4 RP"
        },
        "REAL": {
            "rp_por_bloco": 5,
            "valor_min_diaria": 500,
            "valor_max_diaria": 600,
            "valor_min_2_diarias": 1000,
            "valor_max_2_diarias": 1200,
            "descricao": "Suíte Real - 2 diárias R$ 1000-1200 = 5 RP"
        }
    }
    
    # 🎁 SISTEMA OFICIAL DE PRÊMIOS
    PREMIOS_OFICIAIS = {
        "1_diaria_luxo": {
            "custo_rp": 20,
            "nome": "1 diária na Suíte Luxo",
            "descricao": "Estadia de 1 diária na Suíte Luxo",
            "categoria": "hospedagem"
        },
        "luminaria": {
            "custo_rp": 25,
            "nome": "Luminária com carregador",
            "descricao": "Luminária LED com portas USB",
            "categoria": "eletronico"
        },
        "cafeteira": {
            "custo_rp": 35,
            "nome": "Cafeteira",
            "descricao": "Cafeteira elétrica",
            "categoria": "eletrodomestico"
        },
        "iphone_16": {
            "custo_rp": 100,
            "nome": "iPhone 16",
            "descricao": "Smartphone iPhone 16",
            "categoria": "smartphone"
        }
    }
    
    @classmethod
    def calcular_rp_oficial(cls, suite: str, diarias: int, valor_total: float) -> Tuple[int, str]:
        """
        Calcula RP segundo a fórmula oficial:
        
        blocos = floor(total_diarias / 2)
        RP_total = blocos × RP_por_tipo_de_suite
        
        Args:
            suite: Tipo de suíte (LUXO, DUPLA, MASTER, REAL)
            diarias: Número total de diárias
            valor_total: Valor total da reserva
            
        Returns:
            Tuple[int, str]: (RP calculados, detalhe do cálculo)
        """
        # Normalizar nome da suíte
        suite_normalizada = suite.upper().strip()
        
        # Validar suíte
        if suite_normalizada not in cls.TABELA_OFICIAL_RP:
            return 0, f"Suíte '{suite}' inválida"
        
        # Regra: menos de 2 diárias = 0 RP
        if diarias < 2:
            return 0, "Menos de 2 diárias (0 RP)"
        
        # Obter regra da suíte
        regra = cls.TABELA_OFICIAL_RP[suite_normalizada]
        rp_por_bloco = regra["rp_por_bloco"]
        
        # Calcular blocos de 2 diárias
        blocos = diarias // 2
        
        # Calcular RP total
        rp_total = blocos * rp_por_bloco
        
        # Detalhe do cálculo
        detalhe = f"{blocos} bloco(s) × {rp_por_bloco} RP = {rp_total} RP"
        
        return rp_total, detalhe
    
    @classmethod
    def validar_requisitos_oficiais(cls, reserva: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida todos os requisitos obrigatórios antes de conceder RP
        
        Args:
            reserva: Dicionário com dados da reserva
            
        Returns:
            Tuple[bool, str]: (pode_conceder, motivo)
        """
        # 1. Status da reserva = CHECKED_OUT
        status = reserva.get("status", "").upper()
        if status != "CHECKED_OUT":
            return False, f"Reserva não está CHECKED_OUT (status: {status})"
        
        # 2. Pagamento confirmado
        pagamento_confirmado = reserva.get("pagamento_confirmado", False)
        if not pagamento_confirmado:
            return False, "Pagamento não confirmado"
        
        # 3. Número de diárias ≥ 2
        diarias = int(reserva.get("num_diarias", 0) or 0)
        if diarias < 2:
            return False, f"Menos de 2 diárias ({diarias})"
        
        # 4. Tipo de suíte definido e válido
        suite = reserva.get("tipo_suite", "").strip()
        if not suite:
            return False, "Tipo de suíte não definido"
        
        suite_normalizada = suite.upper()
        if suite_normalizada not in cls.TABELA_OFICIAL_RP:
            return False, f"Suíte '{suite}' inválida"
        
        # 5. Validar valor total (opcional, para antifraude)
        valor_total = float(reserva.get("valor_total", 0) or 0)
        if valor_total <= 0:
            return False, "Valor total inválido"
        
        return True, "Todos os requisitos atendidos"
    
    @classmethod
    def validar_antifraude(cls, reserva: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validações antifraude essenciais
        
        Args:
            reserva: Dicionário com dados da reserva
            
        Returns:
            Tuple[bool, str]: (valido, motivo)
        """
        # 1. Check-out manual sem hospedagem real
        checkout_realizado = reserva.get("checkout_realizado")
        if not checkout_realizado:
            return False, "Check-out não realizado"
        
        # 2. Reserva criada e encerrada no mesmo dia (sem pernoite)
        data_criacao = reserva.get("created_at")
        data_checkout = reserva.get("checkout_realizado")
        
        if data_criacao and data_checkout:
            if isinstance(data_criacao, str):
                data_criacao = datetime.fromisoformat(data_criacao.replace('Z', '+00:00'))
            if isinstance(data_checkout, str):
                data_checkout = datetime.fromisoformat(data_checkout.replace('Z', '+00:00'))
            
            # Calcular diferença em horas
            diferenca_horas = (data_checkout - data_criacao).total_seconds() / 3600
            
            if diferenca_horas < 24:  # Menos de 24 horas
                return False, f"Reserva encerrada em menos de 24h ({diferenca_horas:.1f}h)"
        
        # 3. Alteração de datas após checkout (simulação)
        # Em implementação real, verificaria logs de alteração
        
        return True, "Validações antifraude OK"
    
    @classmethod
    def pode_resgatar_premio(cls, cliente_rp: int, premio_id: str) -> Tuple[bool, str]:
        """
        Verifica se cliente pode resgatar prêmio
        
        Args:
            cliente_rp: Saldo atual de RP do cliente
            premio_id: ID do prêmio desejado
            
        Returns:
            Tuple[bool, str]: (pode_resgatar, motivo)
        """
        # Validar prêmio
        if premio_id not in cls.PREMIOS_OFICIAIS:
            return False, f"Prêmio '{premio_id}' inválido"
        
        premio = cls.PREMIOS_OFICIAIS[premio_id]
        custo_rp = premio["custo_rp"]
        
        # Verificar saldo suficiente
        if cliente_rp < custo_rp:
            return False, f"RP insuficiente (tem: {cliente_rp}, precisa: {custo_rp})"
        
        return True, "Pode resgatar"
    
    @classmethod
    def get_premio(cls, premio_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes do prêmio
        
        Args:
            premio_id: ID do prêmio
            
        Returns:
            Dict com detalhes do prêmio ou None
        """
        return cls.PREMIOS_OFICIAIS.get(premio_id)
    
    @classmethod
    def listar_premios(cls) -> Dict[str, Dict[str, Any]]:
        """
        Lista todos os prêmios disponíveis
        
        Returns:
            Dict com todos os prêmios
        """
        return cls.PREMIOS_OFICIAIS.copy()
    
    @classmethod
    def get_tabela_oficial(cls) -> Dict[str, Dict[str, Any]]:
        """
        Obtém tabela oficial de pontos
        
        Returns:
            Dict com tabela oficial de RP
        """
        return cls.TABELA_OFICIAL_RP.copy()
    
    @classmethod
    def simular_calculo(cls, suite: str, diarias: int, valor_total: float) -> Dict[str, Any]:
        """
        Simula cálculo completo com todas as validações
        
        Args:
            suite: Tipo de suíte
            diarias: Número de diárias
            valor_total: Valor total
            
        Returns:
            Dict com resultado completo da simulação
        """
        resultado = {
            "suite": suite,
            "diarias": diarias,
            "valor_total": valor_total,
            "rp_calculados": 0,
            "pode_conceder": False,
            "validacoes": [],
            "erros": []
        }
        
        # Simular reserva para validação
        reserva_simulada = {
            "status": "CHECKED_OUT",
            "pagamento_confirmado": True,
            "num_diarias": diarias,
            "tipo_suite": suite,
            "valor_total": valor_total,
            "created_at": datetime.now(timezone.utc),
            "checkout_realizado": datetime.now(timezone.utc)
        }
        
        # Validar requisitos oficiais
        pode, motivo = cls.validar_requisitos_oficiais(reserva_simulada)
        if pode:
            resultado["validacoes"].append("✅ Requisitos oficiais OK")
        else:
            resultado["erros"].append(f"❌ Requisitos: {motivo}")
        
        # Validar antifraude
        valido, motivo = cls.validar_antifraude(reserva_simulada)
        if valido:
            resultado["validacoes"].append("✅ Antifraude OK")
        else:
            resultado["erros"].append(f"❌ Antifraude: {motivo}")
        
        # Calcular RP se passou nas validações
        if pode and valido:
            rp, detalhe = cls.calcular_rp_oficial(suite, diarias, valor_total)
            resultado["rp_calculados"] = rp
            resultado["pode_conceder"] = True
            resultado["validacoes"].append(f"✅ Cálculo: {detalhe}")
        
        return resultado


# 🎯 INSTÂNCIA GLOBAL PARA COMPATIBILIDADE
real_points_service = RealPointsService()


# 🧪 FUNÇÕES DE TESTE E DEMONSTRAÇÃO
def demo_real_points():
    """Demonstração do sistema Real Points"""
    
    print("📘 REAL POINTS (RP) - DEMONSTRAÇÃO OFICIAL")
    print("=" * 60)
    
    # Exemplos oficiais
    exemplos = [
        {"suite": "LUXO", "diarias": 2, "valor": 650},
        {"suite": "REAL", "diarias": 4, "valor": 1100},
        {"suite": "MASTER", "diarias": 3, "valor": 850},
        {"suite": "DUPLA", "diarias": 2, "valor": 1300},
        {"suite": "LUXO", "diarias": 1, "valor": 350},
        {"suite": "REAL", "diarias": 6, "valor": 1650}
    ]
    
    print("\n📊 EXEMPLOS OFICIAIS:")
    for ex in exemplos:
        rp, detalhe = RealPointsService.calcular_rp_oficial(ex["suite"], ex["diarias"], ex["valor"])
        print(f"   {ex['suite']} - {ex['diarias']} diárias: {rp} RP ({detalhe})")
    
    print("\n🎁 PRÊMIOS DISPONÍVEIS:")
    for premio_id, premio in RealPointsService.PREMIOS_OFICIAIS.items():
        print(f"   {premio['custo_rp']} RP - {premio['nome']}")
    
    print("\n📋 TABELA OFICIAL DE PONTOS:")
    for suite, regra in RealPointsService.TABELA_OFICIAL_RP.items():
        print(f"   {suite}: {regra['rp_por_bloco']} RP por 2 diárias")
        print(f"      Faixa: R$ {regra['valor_min_2_diarias']}-{regra['valor_max_2_diarias']}")


if __name__ == "__main__":
    demo_real_points()
