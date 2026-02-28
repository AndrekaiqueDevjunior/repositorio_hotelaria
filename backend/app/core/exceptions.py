"""
🔥 CORE EXCEPTIONS
==================

Exceções personalizadas do sistema
"""

class BusinessRuleViolation(Exception):
    """Violação de regra de negócio"""
    pass

class ValidationError(Exception):
    """Erro de validação"""
    pass

class AuthenticationError(Exception):
    """Erro de autenticação"""
    pass

class AuthorizationError(Exception):
    """Erro de autorização"""
    pass

class ResourceNotFound(Exception):
    """Recurso não encontrado"""
    pass

class DatabaseError(Exception):
    """Erro de banco de dados"""
    pass

class ExternalServiceError(Exception):
    """Erro de serviço externo"""
    pass

class RateLimitError(Exception):
    """Limite de requisições excedido"""
    pass

class PaymentError(Exception):
    """Erro de pagamento"""
    pass

class ReservationError(Exception):
    """Erro de reserva"""
    pass

class PointsError(Exception):
    """Erro de pontos"""
    pass

class VoucherError(Exception):
    """Erro de voucher"""
    pass

class NotificationError(Exception):
    """Erro de notificação"""
    pass

class AntiFraudError(Exception):
    """Erro de antifraude"""
    pass
