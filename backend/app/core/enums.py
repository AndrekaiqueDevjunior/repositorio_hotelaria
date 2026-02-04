from enum import Enum

from app.schemas.status_enums import StatusReserva, StatusPagamento


class PerfilUsuario(str, Enum):
    ADMIN = "ADMIN"
    GERENTE = "GERENTE"
    RECEPCAO = "RECEPCAO"
    FUNCIONARIO = "FUNCIONARIO"
    CLIENTE = "CLIENTE"
    RECEPCIONISTA = "RECEPCIONISTA"  # Legado
    AUDITOR = "AUDITOR"  # Legado
    HOSPEDE = "HOSPEDE"  # Legado
    
    @classmethod
    def get_all(cls):
        return [e.value for e in cls]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.get_all()
    
    @classmethod
    def normalize(cls, value: str) -> str:
        if not value:
            return ""
        normalized = value.strip().upper()
        return normalized if normalized in cls.get_all() else value


class StatusUsuario(str, Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"


class TipoDocumento(str, Enum):
    RG = "RG"
    CPF = "CPF"
    CNPJ = "CNPJ"
    CNH = "CNH"
    PASSAPORTE = "PASSAPORTE"
    OUTROS = "OUTROS"


class StatusCliente(str, Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"


class StatusFinanceiro(str, Enum):
    """Estados financeiros independentes do status da reserva"""
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    SINAL_PAGO = "SINAL_PAGO"                # Pagamento parcial
    PAGO_TOTAL = "PAGO_TOTAL"                # Totalmente pago
    ESTORNADO = "ESTORNADO"                  # Estornado
    DEVEDOR = "DEVEDOR"                      # Saldo devedor após checkout
    CREDOR = "CREDOR"                        # Saldo a favor do cliente


class OrigemReserva(str, Enum):
    TELEFONE = "TELEFONE"
    WHATSAPP = "WHATSAPP"
    SITE = "SITE"
    BALCAO = "BALCAO"
    OUTRO = "OUTRO"


class StatusQuarto(str, Enum):
    LIVRE = "LIVRE"
    OCUPADO = "OCUPADO"
    MANUTENCAO = "MANUTENCAO"
    BLOQUEADO = "BLOQUEADO"

    ATIVO = "LIVRE"
    INATIVO = "BLOQUEADO"


class MetodoPagamento(str, Enum):
    DINHEIRO = "DINHEIRO"
    DEBITO = "DEBITO"
    CREDITO = "CREDITO"
    PIX = "PIX"
    TRANSFERENCIA = "TRANSFERENCIA"
    CIELO_CARTAO = "CIELO_CARTAO"
    OUTRO = "OUTRO"


class TipoTransacaoPontos(str, Enum):
    CREDITO = "CREDITO"
    DEBITO = "DEBITO"
    BONUS = "BONUS"
    RESGATE = "RESGATE"
    AJUSTE_MANUAL = "AJUSTE_MANUAL"


class StatusAntifraude(str, Enum):
    PENDENTE = "PENDENTE"
    AUTO_APROVADO = "AUTO_APROVADO"
    RECUSADO = "RECUSADO"
    DUPLICADO = "DUPLICADO"
    MANUAL_APROVADO = "MANUAL_APROVADO"
    MANUAL_RECUSADO = "MANUAL_RECUSADO"


class TipoItemCobranca(str, Enum):
    DIARIA = "DIARIA"                        # Valor da hospedagem
    CONSUMO_FRIGOBAR = "CONSUMO_FRIGOBAR"    # Consumo do frigobar
    SERVICO_EXTRA = "SERVICO_EXTRA"          # Serviços adicionais
    TAXA_LATE_CHECKOUT = "TAXA_LATE_CHECKOUT" # Taxa por checkout tardio
    MULTA = "MULTA"                          # Multas diversas
    DANO = "DANO"                            # Danos ao quarto
    CAUCAO = "CAUCAO"                        # Caução
    DESCONTO = "DESCONTO"                    # Descontos aplicados
    OUTRO = "OUTRO"


class TipoComprovante(str, Enum):
    PIX = "PIX"
    DEPOSITO = "DEPOSITO"
    TERCEIRO = "TERCEIRO"
    OUTRO = "OUTRO"


class TipoDocumentoHospede(str, Enum):
    """Documentos aceitos para hóspedes"""
    RG = "RG"
    CPF = "CPF"
    CNH = "CNH"
    PASSAPORTE = "PASSAPORTE"
    CERTIDAO_NASCIMENTO = "CERTIDAO_NASCIMENTO"  # Para menores
    OUTRO = "OUTRO"


class MotivoCheckinBloqueado(str, Enum):
    """Motivos para bloqueio de check-in"""
    PAGAMENTO_PENDENTE = "PAGAMENTO_PENDENTE"
    DOCUMENTACAO_INCOMPLETA = "DOCUMENTACAO_INCOMPLETA"
    QUARTO_INDISPONIVEL = "QUARTO_INDISPONIVEL"
    RESERVA_CANCELADA = "RESERVA_CANCELADA"
    CHECKOUT_PENDENTE_MESMO_QUARTO = "CHECKOUT_PENDENTE_MESMO_QUARTO"
    OVERBOOKING = "OVERBOOKING"


class PoliticaCancelamento(str, Enum):
    """Políticas de cancelamento"""
    FLEXIVEL = "FLEXIVEL"                    # Cancelamento até 24h sem multa
    MODERADA = "MODERADA"                    # Cancelamento até 48h, multa 50%
    RIGIDA = "RIGIDA"                        # Cancelamento até 72h, multa 80%
    NAO_REEMBOLSAVEL = "NAO_REEMBOLSAVEL"    # Sem reembolso


class StatusVistoria(str, Enum):
    """Status da vistoria do quarto"""
    OK = "OK"                                # Quarto em perfeitas condições
    DANOS_LEVES = "DANOS_LEVES"              # Danos que não impedem uso
    DANOS_GRAVES = "DANOS_GRAVES"            # Danos que impedem uso
    MANUTENCAO_NECESSARIA = "MANUTENCAO_NECESSARIA"


class TipoRelatorio(str, Enum):
    """Tipos de relatórios operacionais"""
    OCUPACAO_DIARIA = "OCUPACAO_DIARIA"
    ENTRADAS_SAIDAS = "ENTRADAS_SAIDAS"
    RECEITA_PERIODO = "RECEITA_PERIODO"
    TAXA_OCUPACAO = "TAXA_OCUPACAO"
    CONSUMOS = "CONSUMOS"
    INADIMPLENCIA = "INADIMPLENCIA"


class TipoSuite(str, Enum):
    """Tipos de suítes do hotel para cálculo de pontos RP"""
    LUXO = "LUXO"
    DUPLA = "DUPLA"
    MASTER = "MASTER"
    REAL = "REAL"


class CategoriaPremio(str, Enum):
    """Categorias de prêmios disponíveis para resgate"""
    DIARIA = "DIARIA"
    ELETRONICO = "ELETRONICO"
    SERVICO = "SERVICO"
    VALE = "VALE"
    OUTRO = "OUTRO"
