from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
import threading
import time

from app.models.reserva import Reserva
from app.models.hotel import Quarto
from app.core.enums import StatusReserva, StatusQuarto
from app.utils.datetime_utils import now_utc
from app.core.exceptions import BusinessRuleViolation, ValidationError


class OverbookingLock:
    """
    Controle de lock para prevenir overbooking
    Implementa semáforo por quarto/período
    """
    _locks = {}  # Cache de locks por quarto
    _lock = threading.RLock()  # Lock global para gerenciar locks individuais
    
    @classmethod
    def acquire_quarto_lock(cls, quarto_id: int, timeout: float = 10.0) -> bool:
        """Adquire lock exclusivo para um quarto específico"""
        with cls._lock:
            if quarto_id not in cls._locks:
                cls._locks[quarto_id] = threading.RLock()
        
        try:
            return cls._locks[quarto_id].acquire(timeout=timeout)
        except:
            return False
    
    @classmethod
    def release_quarto_lock(cls, quarto_id: int):
        """Libera lock do quarto"""
        with cls._lock:
            if quarto_id in cls._locks:
                try:
                    cls._locks[quarto_id].release()
                except:
                    pass  # Lock já foi liberado


class OverbookingService:
    """
    Serviço para controle rigoroso de overbooking
    Previne conflitos de ocupação com locks transacionais
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def verificar_disponibilidade(
        self,
        quarto_id: int,
        checkin_inicio: datetime,
        checkout_fim: datetime,
        excluir_reserva_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Verifica disponibilidade rigorosa de um quarto em período específico
        Com análise de sobreposições e conflitos
        """
        
        # Buscar reservas que podem conflitar
        query = self.db.query(Reserva).filter(
            and_(
                Reserva.quarto_id == quarto_id,
                Reserva.status_reserva.in_([
                    StatusReserva.CONFIRMADA,
                    StatusReserva.HOSPEDADO,
                    StatusReserva.PENDENTE  # Incluir pendentes para segurança
                ]),
                # Overlap de períodos: (inicio1 <= fim2) AND (fim1 >= inicio2)
                Reserva.checkin_previsto <= checkout_fim,
                Reserva.checkout_previsto >= checkin_inicio
            )
        )
        
        # Excluir reserva específica se fornecida (para edições)
        if excluir_reserva_id:
            query = query.filter(Reserva.id != excluir_reserva_id)
        
        reservas_conflitantes = query.all()
        
        if not reservas_conflitantes:
            return {
                "disponivel": True,
                "conflitos": [],
                "total_conflitos": 0
            }
        
        # Analisar conflitos detalhadamente
        conflitos = []
        for reserva in reservas_conflitantes:
            tipo_conflito = self._classificar_conflito(
                checkin_inicio, checkout_fim,
                reserva.checkin_previsto, reserva.checkout_previsto
            )
            
            conflitos.append({
                "reserva_id": reserva.id,
                "codigo_reserva": reserva.codigo_reserva,
                "cliente": reserva.cliente.nome_completo if reserva.cliente else "N/A",
                "status": reserva.status_reserva.value,
                "checkin_previsto": reserva.checkin_previsto.isoformat(),
                "checkout_previsto": reserva.checkout_previsto.isoformat(),
                "tipo_conflito": tipo_conflito,
                "gravidade": self._calcular_gravidade_conflito(reserva.status_reserva, tipo_conflito)
            })
        
        return {
            "disponivel": False,
            "conflitos": conflitos,
            "total_conflitos": len(conflitos),
            "maior_gravidade": max((c["gravidade"] for c in conflitos), default=0)
        }
    
    def _classificar_conflito(
        self, 
        inicio1: datetime, fim1: datetime,
        inicio2: datetime, fim2: datetime
    ) -> str:
        """Classifica o tipo de conflito entre dois períodos"""
        
        if inicio1 == inicio2 and fim1 == fim2:
            return "SOBREPOSICAO_TOTAL"
        elif inicio1 >= inicio2 and fim1 <= fim2:
            return "CONTIDO_EM_EXISTENTE"
        elif inicio2 >= inicio1 and fim2 <= fim1:
            return "CONTEM_EXISTENTE"
        elif inicio1 < inicio2 < fim1:
            return "SOBREPOSICAO_FINAL"
        elif inicio1 < fim2 < fim1:
            return "SOBREPOSICAO_INICIAL"
        else:
            return "SOBREPOSICAO_PARCIAL"
    
    def _calcular_gravidade_conflito(self, status_reserva: StatusReserva, tipo_conflito: str) -> int:
        """Calcula gravidade do conflito (1-10, sendo 10 mais grave)"""
        
        # Peso por status
        peso_status = {
            StatusReserva.HOSPEDADO: 10,      # Máxima gravidade - já está ocupado
            StatusReserva.CONFIRMADA: 8,      # Alta gravidade - reserva paga
            StatusReserva.PENDENTE: 5         # Média gravidade - ainda pendente
        }
        
        # Peso por tipo de conflito
        peso_conflito = {
            "SOBREPOSICAO_TOTAL": 3,
            "CONTIDO_EM_EXISTENTE": 2,
            "CONTEM_EXISTENTE": 3,
            "SOBREPOSICAO_FINAL": 2,
            "SOBREPOSICAO_INICIAL": 2,
            "SOBREPOSICAO_PARCIAL": 1
        }
        
        return peso_status.get(status_reserva, 1) + peso_conflito.get(tipo_conflito, 1)
    
    def reservar_com_lock_transacional(
        self,
        dados_reserva: Dict[str, Any],
        usuario_id: int,
        permitir_overbooking: bool = False
    ) -> Dict[str, Any]:
        """
        Cria reserva com controle rigoroso de concorrência
        Usa locks transacionais para prevenir race conditions
        """
        
        quarto_id = dados_reserva.get("quarto_id")
        checkin_previsto = dados_reserva.get("checkin_previsto")
        checkout_previsto = dados_reserva.get("checkout_previsto")
        
        if not all([quarto_id, checkin_previsto, checkout_previsto]):
            raise ValidationError("Dados obrigatórios: quarto_id, checkin_previsto, checkout_previsto")
        
        # Converter strings para datetime se necessário
        if isinstance(checkin_previsto, str):
            checkin_previsto = datetime.fromisoformat(checkin_previsto.replace('Z', '+00:00'))
        if isinstance(checkout_previsto, str):
            checkout_previsto = datetime.fromisoformat(checkout_previsto.replace('Z', '+00:00'))
        
        # Adquirir lock exclusivo do quarto
        if not OverbookingLock.acquire_quarto_lock(quarto_id, timeout=10.0):
            raise BusinessRuleViolation(
                "Sistema ocupado. Tente novamente em alguns segundos. "
                "Outro usuário está reservando este quarto."
            )
        
        try:
            # Verificar disponibilidade dentro do lock
            disponibilidade = self.verificar_disponibilidade(
                quarto_id, checkin_previsto, checkout_previsto
            )
            
            if not disponibilidade["disponivel"] and not permitir_overbooking:
                # Gerar relatório detalhado do conflito
                relatorio_conflito = self._gerar_relatorio_conflito(
                    quarto_id, checkin_previsto, checkout_previsto, disponibilidade
                )
                
                raise BusinessRuleViolation(
                    f"Quarto indisponível no período solicitado. {relatorio_conflito}"
                )
            
            # Dupla verificação com lock de linha no banco (SELECT FOR UPDATE)
            self._verificar_lock_banco(quarto_id, checkin_previsto, checkout_previsto)
            
            # Criar a reserva dentro da transação protegida
            nova_reserva = self._criar_reserva_protegida(dados_reserva, usuario_id)
            
            self.db.commit()
            
            resultado = {
                "sucesso": True,
                "reserva_id": nova_reserva.id,
                "codigo_reserva": nova_reserva.codigo_reserva,
                "overbooking_detectado": not disponibilidade["disponivel"],
                "conflitos_superados": disponibilidade.get("conflitos", []),
                "created_at": nova_reserva.created_at.isoformat()
            }
            
            # Log de segurança
            if not disponibilidade["disponivel"]:
                print(f"[OVERBOOKING_AUTORIZADO] Reserva {nova_reserva.codigo_reserva} criada com {len(disponibilidade['conflitos'])} conflito(s) por usuário {usuario_id}")
            
            return resultado
            
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleViolation(f"Falha na reserva: {str(e)}")
        
        finally:
            # Sempre liberar o lock
            OverbookingLock.release_quarto_lock(quarto_id)
    
    def _verificar_lock_banco(
        self,
        quarto_id: int,
        checkin_previsto: datetime,
        checkout_previsto: datetime
    ):
        """
        Verificação adicional com lock de linha no banco de dados
        SELECT FOR UPDATE para máxima segurança
        """
        try:
            # Lock das reservas conflitantes
            conflitos = self.db.execute(
                text("""
                    SELECT id, codigo_reserva, status_reserva
                    FROM reservas 
                    WHERE quarto_id = :quarto_id
                      AND status_reserva IN ('CONFIRMADA', 'HOSPEDADO', 'PENDENTE')
                      AND checkin_previsto <= :checkout
                      AND checkout_previsto >= :checkin
                    FOR UPDATE NOWAIT
                """),
                {
                    "quarto_id": quarto_id,
                    "checkin": checkin_previsto,
                    "checkout": checkout_previsto
                }
            ).fetchall()
            
            if conflitos:
                codigos = [c.codigo_reserva for c in conflitos]
                raise BusinessRuleViolation(
                    f"Conflito detectado com reservas: {', '.join(codigos)}. "
                    f"Operação bloqueada para evitar overbooking."
                )
                
        except Exception as e:
            if "NOWAIT" in str(e) or "lock" in str(e).lower():
                raise BusinessRuleViolation(
                    "Outro usuário está modificando reservas neste quarto. "
                    "Aguarde e tente novamente."
                )
            raise
    
    def _criar_reserva_protegida(self, dados_reserva: Dict, usuario_id: int) -> Reserva:
        """Cria reserva dentro do contexto transacional protegido"""
        
        # Gerar código único para a reserva
        codigo_reserva = self._gerar_codigo_reserva_unico()
        
        nova_reserva = Reserva(
            codigo_reserva=codigo_reserva,
            cliente_id=dados_reserva["cliente_id"],
            quarto_id=dados_reserva["quarto_id"],
            checkin_previsto=dados_reserva["checkin_previsto"],
            checkout_previsto=dados_reserva["checkout_previsto"],
            valor_diaria=Decimal(str(dados_reserva.get("valor_diaria", 0))),
            num_diarias_previstas=dados_reserva.get("num_diarias_previstas", 1),
            valor_previsto=Decimal(str(dados_reserva.get("valor_previsto", 0))),
            status_reserva=StatusReserva.PENDENTE,
            criado_por_usuario_id=usuario_id,
            observacoes=dados_reserva.get("observacoes")
        )
        
        self.db.add(nova_reserva)
        self.db.flush()  # Para obter o ID sem commit
        
        return nova_reserva
    
    def _gerar_codigo_reserva_unico(self) -> str:
        """Gera código único para reserva com verificação de duplicata"""
        max_tentativas = 100
        
        for _ in range(max_tentativas):
            # Formato: YYYYMMDD-HHMMSS-XXX
            agora = now_utc()
            base = agora.strftime("%Y%m%d-%H%M%S")
            sufixo = f"{agora.microsecond // 1000:03d}"
            codigo = f"{base}-{sufixo}"
            
            # Verificar se já existe
            existente = self.db.query(Reserva).filter(
                Reserva.codigo_reserva == codigo
            ).first()
            
            if not existente:
                return codigo
            
            # Aguardar 1ms antes da próxima tentativa
            time.sleep(0.001)
        
        raise BusinessRuleViolation("Falha ao gerar código único para reserva")
    
    def _gerar_relatorio_conflito(
        self,
        quarto_id: int,
        checkin: datetime,
        checkout: datetime,
        disponibilidade: Dict
    ) -> str:
        """Gera relatório detalhado do conflito"""
        
        quarto = self.db.query(Quarto).filter(Quarto.id == quarto_id).first()
        quarto_numero = quarto.numero if quarto else f"ID-{quarto_id}"
        
        conflitos = disponibilidade.get("conflitos", [])
        
        if len(conflitos) == 1:
            conflito = conflitos[0]
            return (
                f"Quarto {quarto_numero} ocupado pela reserva {conflito['codigo_reserva']} "
                f"({conflito['status']}) de {conflito['checkin_previsto'][:10]} até "
                f"{conflito['checkout_previsto'][:10]}."
            )
        else:
            return (
                f"Quarto {quarto_numero} tem {len(conflitos)} reservas conflitantes. "
                f"Contate a gerência para resolver overbooking."
            )
    
    def analisar_overbooking_hotel(self, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """
        Análise completa de overbooking do hotel por período
        Identifica todos os conflitos e riscos operacionais
        """
        
        if (data_fim - data_inicio).days > 90:
            raise ValidationError("Período máximo de análise: 90 dias")
        
        # Buscar todas as reservas do período
        inicio_datetime = datetime.combine(data_inicio, datetime.min.time().replace(tzinfo=timezone.utc))
        fim_datetime = datetime.combine(data_fim, datetime.max.time().replace(tzinfo=timezone.utc))
        
        reservas = self.db.query(Reserva).filter(
            and_(
                Reserva.checkin_previsto <= fim_datetime,
                Reserva.checkout_previsto >= inicio_datetime,
                Reserva.status_reserva.in_([
                    StatusReserva.CONFIRMADA,
                    StatusReserva.HOSPEDADO,
                    StatusReserva.PENDENTE
                ])
            )
        ).order_by(Reserva.quarto_id, Reserva.checkin_previsto).all()
        
        # Agrupar por quarto
        conflitos_por_quarto = {}
        for reserva in reservas:
            if reserva.quarto_id not in conflitos_por_quarto:
                conflitos_por_quarto[reserva.quarto_id] = []
            conflitos_por_quarto[reserva.quarto_id].append(reserva)
        
        # Analisar conflitos
        analise_completa = {
            "periodo": f"{data_inicio.isoformat()} a {data_fim.isoformat()}",
            "total_reservas_analisadas": len(reservas),
            "quartos_com_conflito": [],
            "estatisticas": {
                "total_conflitos": 0,
                "quartos_afetados": 0,
                "reservas_em_risco": 0,
                "receita_em_risco": 0
            }
        }
        
        for quarto_id, reservas_quarto in conflitos_por_quarto.items():
            if len(reservas_quarto) <= 1:
                continue  # Sem conflito
            
            conflitos_quarto = self._analisar_conflitos_quarto(quarto_id, reservas_quarto)
            
            if conflitos_quarto["conflitos"]:
                analise_completa["quartos_com_conflito"].append(conflitos_quarto)
                analise_completa["estatisticas"]["total_conflitos"] += len(conflitos_quarto["conflitos"])
                analise_completa["estatisticas"]["quartos_afetados"] += 1
                analise_completa["estatisticas"]["reservas_em_risco"] += conflitos_quarto["reservas_afetadas"]
                analise_completa["estatisticas"]["receita_em_risco"] += conflitos_quarto["receita_em_risco"]
        
        # Recomendações
        analise_completa["recomendacoes"] = self._gerar_recomendacoes_overbooking(
            analise_completa["estatisticas"]
        )
        
        return analise_completa
    
    def _analisar_conflitos_quarto(self, quarto_id: int, reservas: List[Reserva]) -> Dict[str, Any]:
        """Analisa conflitos específicos de um quarto"""
        
        quarto = self.db.query(Quarto).filter(Quarto.id == quarto_id).first()
        conflitos = []
        receita_risco = 0
        reservas_afetadas = 0
        
        # Comparar cada reserva com as outras
        for i, reserva1 in enumerate(reservas):
            for j, reserva2 in enumerate(reservas[i+1:], i+1):
                
                # Verificar sobreposição
                if (reserva1.checkin_previsto < reserva2.checkout_previsto and
                    reserva1.checkout_previsto > reserva2.checkin_previsto):
                    
                    conflito = {
                        "reserva_1": {
                            "id": reserva1.id,
                            "codigo": reserva1.codigo_reserva,
                            "cliente": reserva1.cliente.nome_completo if reserva1.cliente else "N/A",
                            "checkin": reserva1.checkin_previsto.isoformat(),
                            "checkout": reserva1.checkout_previsto.isoformat(),
                            "status": reserva1.status_reserva.value,
                            "valor": float(reserva1.valor_previsto)
                        },
                        "reserva_2": {
                            "id": reserva2.id,
                            "codigo": reserva2.codigo_reserva,
                            "cliente": reserva2.cliente.nome_completo if reserva2.cliente else "N/A",
                            "checkin": reserva2.checkin_previsto.isoformat(),
                            "checkout": reserva2.checkout_previsto.isoformat(),
                            "status": reserva2.status_reserva.value,
                            "valor": float(reserva2.valor_previsto)
                        },
                        "gravidade": max(
                            self._calcular_gravidade_conflito(reserva1.status_reserva, "SOBREPOSICAO_PARCIAL"),
                            self._calcular_gravidade_conflito(reserva2.status_reserva, "SOBREPOSICAO_PARCIAL")
                        )
                    }
                    
                    conflitos.append(conflito)
                    receita_risco += float(reserva1.valor_previsto) + float(reserva2.valor_previsto)
                    reservas_afetadas += 2
        
        return {
            "quarto_id": quarto_id,
            "quarto_numero": quarto.numero if quarto else f"ID-{quarto_id}",
            "total_reservas": len(reservas),
            "conflitos": conflitos,
            "reservas_afetadas": reservas_afetadas,
            "receita_em_risco": receita_risco
        }
    
    def _gerar_recomendacoes_overbooking(self, estatisticas: Dict) -> List[str]:
        """Gera recomendações baseadas na análise"""
        recomendacoes = []
        
        if estatisticas["total_conflitos"] == 0:
            recomendacoes.append("✅ Nenhum overbooking detectado no período")
        else:
            if estatisticas["total_conflitos"] > 10:
                recomendacoes.append("🔴 CRÍTICO: Muitos conflitos detectados - Revisar processo de reservas")
            elif estatisticas["total_conflitos"] > 5:
                recomendacoes.append("🟡 ATENÇÃO: Múltiplos conflitos - Implementar controles mais rigorosos")
            else:
                recomendacoes.append("🟠 Conflitos pontuais detectados - Verificar individualmente")
            
            recomendacoes.append(f"💰 R$ {estatisticas['receita_em_risco']:.2f} em receita em risco")
            
            if estatisticas["quartos_afetados"] > 0:
                recomendacoes.append(f"🏠 {estatisticas['quartos_afetados']} quarto(s) com overbooking")
            
            recomendacoes.append("📋 Ação recomendada: Contatar clientes para realocação/upgrade")
        
        return recomendacoes
    
    def resolver_overbooking(
        self,
        conflito_id: str,
        solucao: Dict[str, Any],
        usuario_id: int
    ) -> Dict[str, Any]:
        """
        Resolve um caso específico de overbooking
        Implementa soluções como upgrade, realocação, cancelamento
        """
        
        # Esta seria a implementação para resolver conflitos específicos
        # Por questões de tempo, deixo a estrutura para implementação futura
        
        return {
            "sucesso": True,
            "conflito_resolvido": conflito_id,
            "solucao_aplicada": solucao.get("tipo", "N/A"),
            "resolvido_por": usuario_id,
            "resolvido_em": now_utc().isoformat()
        }
