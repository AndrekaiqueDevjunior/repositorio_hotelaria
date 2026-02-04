"""
Utilitários de Segurança para Dados Sensíveis
"""

def mask_card_number(card_number: str) -> str:
    """
    Mascara número do cartão, mostrando apenas últimos 4 dígitos
    
    Args:
        card_number: Número completo do cartão (16 dígitos)
        
    Returns:
        Número mascarado (formato: •••• 1234)
        
    Examples:
        >>> mask_card_number("1234567890123456")
        "•••• 3456"
        >>> mask_card_number("4111 1111 1111 1111")
        "•••• 1111"
    """
    if not card_number:
        return ""
    
    # Remover espaços e caracteres especiais
    clean_number = ''.join(filter(str.isdigit, card_number))
    
    # Validar tamanho mínimo
    if len(clean_number) < 4:
        return "•••• ••••"
    
    # Manter apenas últimos 4 dígitos
    last_four = clean_number[-4:]
    
    return f"•••• {last_four}"


def is_card_masked(card_number: str) -> bool:
    """
    Verifica se número do cartão já está mascarado
    
    Args:
        card_number: Número do cartão
        
    Returns:
        True se já está mascarado, False caso contrário
    """
    if not card_number:
        return False
    
    return card_number.startswith("••••") or card_number.startswith("****")


def sanitize_payment_data(payment_data: dict) -> dict:
    """
    Remove/mascara dados sensíveis de um pagamento antes de retornar
    
    Args:
        payment_data: Dicionário com dados do pagamento
        
    Returns:
        Dicionário com dados sanitizados
    """
    sanitized = payment_data.copy()
    
    # Nunca retornar CVV
    if "cartao_cvv" in sanitized:
        del sanitized["cartao_cvv"]
    
    if "cartaoCvv" in sanitized:
        del sanitized["cartaoCvv"]
    
    # Mascarar número do cartão se não estiver mascarado
    if "cartao_numero" in sanitized and sanitized["cartao_numero"]:
        if not is_card_masked(sanitized["cartao_numero"]):
            sanitized["cartao_numero"] = mask_card_number(sanitized["cartao_numero"])
    
    if "cartaoNumero" in sanitized and sanitized["cartaoNumero"]:
        if not is_card_masked(sanitized["cartaoNumero"]):
            sanitized["cartaoNumero"] = mask_card_number(sanitized["cartaoNumero"])
    
    return sanitized


def generate_card_token(card_number: str, gateway: str = "internal") -> str:
    """
    Gera um token único para o cartão (simulação - em produção usar gateway)
    
    Args:
        card_number: Número completo do cartão
        gateway: Gateway de pagamento ("cielo", "stripe", "internal")
        
    Returns:
        Token único do cartão
        
    Note:
        Em produção, este token deve ser gerado pelo gateway de pagamento (Cielo, Stripe, etc)
        e NÃO pela aplicação. Este é apenas um exemplo de estrutura.
    """
    import hashlib
    import uuid
    from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc
    
    # Remover espaços
    clean_number = ''.join(filter(str.isdigit, card_number))
    
    # Gerar hash do cartão (NÃO reversível)
    card_hash = hashlib.sha256(clean_number.encode()).hexdigest()[:16]
    
    # Timestamp
    timestamp = now_utc().strftime("%Y%m%d%H%M%S")
    
    # Identificador único
    unique_id = str(uuid.uuid4())[:8]
    
    # Token no formato: GATEWAY_HASH_TIMESTAMP_UUID
    token = f"{gateway.upper()}_{card_hash}_{timestamp}_{unique_id}"
    
    return token


def validate_pci_compliance(payment_data: dict) -> list:
    """
    Valida conformidade PCI-DSS dos dados de pagamento
    
    Args:
        payment_data: Dicionário com dados do pagamento
        
    Returns:
        Lista de violações encontradas (vazia se conforme)
    """
    violations = []
    
    # Verificar se CVV está sendo armazenado (PROIBIDO!)
    if "cartao_cvv" in payment_data or "cartaoCvv" in payment_data:
        violations.append("CRÍTICO: CVV não deve ser armazenado (PCI-DSS 3.2)")
    
    # Verificar se número do cartão não está mascarado
    card_field = payment_data.get("cartao_numero") or payment_data.get("cartaoNumero")
    if card_field and not is_card_masked(card_field):
        # Se não está mascarado, deve ter token
        token_field = payment_data.get("cartao_token") or payment_data.get("cartaoToken")
        if not token_field:
            violations.append("AVISO: Número do cartão não mascarado sem token")
    
    # Verificar se há criptografia em dados sensíveis (em produção)
    # violations.append("INFO: Implementar criptografia AES-256 para dados sensíveis")
    
    return violations


# Exemplo de uso:
if __name__ == "__main__":
    # Teste de mascaramento
    print(mask_card_number("1234567890123456"))  # •••• 3456
    print(mask_card_number("4111 1111 1111 1111"))  # •••• 1111
    
    # Teste de validação
    print(is_card_masked("•••• 1234"))  # True
    print(is_card_masked("1234567890123456"))  # False
    
    # Teste de sanitização
    payment = {
        "cartao_numero": "1234567890123456",
        "cartao_cvv": "123",
        "valor": 100.00
    }
    sanitized = sanitize_payment_data(payment)
    print(sanitized)  # CVV removido, número mascarado
    
    # Teste de token
    token = generate_card_token("1234567890123456", "cielo")
    print(f"Token: {token}")

