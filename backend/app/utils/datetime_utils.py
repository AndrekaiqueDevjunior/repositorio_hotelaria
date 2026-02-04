"""
Utilitários para tratamento seguro de datetime
Resolve problemas de timezone e comparações inválidas
"""

from datetime import datetime, timezone, timedelta
from typing import Union, Optional

# Timezone padrão do sistema
DEFAULT_TIMEZONE = timezone.utc
# Brazil timezone (UTC-3)
LOCAL_TIMEZONE = timezone(timedelta(hours=-3))


def now_utc() -> datetime:
    """
    Retorna datetime atual em UTC com timezone
    Uso correto para evitar erros de comparação
    """
    return datetime.now(timezone.utc)


def now_utc_naive() -> datetime:
    """
    Retorna datetime atual em UTC sem timezone (naive)
    Usado para compatibilidade com cookies e sistemas legados
    """
    return datetime.utcnow()


def cookie_expires(seconds: int) -> datetime:
    """
    Retorna datetime para expiração de cookies (UTC naive)
    Formato compatível com format_datetime(usegmt=True)
    """
    from datetime import datetime
    return datetime.utcnow() + timedelta(seconds=seconds)


def cookie_expires_formatted(seconds: int) -> str:
    """
    Retorna string formatada para expiração de cookies
    Evita problemas com format_datetime(usegmt=True)
    """
    from datetime import datetime, timezone
    import email.utils
    
    expires = datetime.utcnow() + timedelta(seconds=seconds)
    return email.utils.formatdate(expires.timestamp(), usegmt=True)


def now_local() -> datetime:
    """
    Retorna datetime atual no timezone local (America/Sao_Paulo)
    """
    return datetime.now(LOCAL_TIMEZONE)


def to_utc(dt: Union[datetime, str, None]) -> Optional[datetime]:
    """
    Converte qualquer datetime para UTC com timezone
    
    Args:
        dt: datetime objeto ou string ISO
        
    Returns:
        datetime em UTC com timezone ou None
    """
    if dt is None:
        return None
    
    if isinstance(dt, str):
        # Converter de string ISO
        try:
            if 'Z' in dt:
                # UTC timezone
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            else:
                # Sem timezone info, assumir UTC
                dt = datetime.fromisoformat(dt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    
    # Se já tiver timezone, converter para UTC
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc)
    
    # Se não tiver timezone, assumir UTC
    return dt.replace(tzinfo=timezone.utc)


def to_local(dt: Union[datetime, str, None]) -> Optional[datetime]:
    """
    Converte qualquer datetime para timezone local
    
    Args:
        dt: datetime objeto ou string ISO
        
    Returns:
        datetime em timezone local ou None
    """
    if dt is None:
        return None
    
    utc_dt = to_utc(dt)
    if utc_dt is None:
        return None
    
    return utc_dt.astimezone(LOCAL_TIMEZONE)


def safe_compare(dt1: Union[datetime, str, None], 
                 dt2: Union[datetime, str, None]) -> bool:
    """
    Compara dois datetimes de forma segura
    
    Args:
        dt1: Primeiro datetime
        dt2: Segundo datetime
        
    Returns:
        True se dt1 < dt2, False caso contrário
    """
    dt1_utc = to_utc(dt1)
    dt2_utc = to_utc(dt2)
    
    if dt1_utc is None or dt2_utc is None:
        return False
    
    return dt1_utc < dt2_utc


def is_expired(dt: Union[datetime, str, None], 
               days: int = 0, 
               hours: int = 0, 
               minutes: int = 0) -> bool:
    """
    Verifica se datetime está expirado
    
    Args:
        dt: Datetime a verificar
        days: Dias para expirar
        hours: Horas para expirar
        minutes: Minutos para expirar
        
    Returns:
        True se expirado, False caso contrário
    """
    if dt is None:
        return False
    
    dt_utc = to_utc(dt)
    if dt_utc is None:
        return False
    
    expiration_time = now_utc() + timedelta(days=days, hours=hours, minutes=minutes)
    return dt_utc < expiration_time


def format_local(dt: Union[datetime, str, None], 
                 fmt: str = "%d/%m/%Y %H:%M:%S") -> str:
    """
    Formata datetime para timezone local
    
    Args:
        dt: Datetime a formatar
        fmt: Formato de string
        
    Returns:
        String formatada ou vazia
    """
    dt_local = to_local(dt)
    if dt_local is None:
        return ""
    
    return dt_local.strftime(fmt)


def format_iso(dt: Union[datetime, str, None]) -> str:
    """
    Formata datetime para ISO string UTC
    
    Args:
        dt: Datetime a formatar
        
    Returns:
        String ISO ou vazia
    """
    dt_utc = to_utc(dt)
    if dt_utc is None:
        return ""
    
    return dt_utc.isoformat()


def add_business_days(dt: Union[datetime, str, None], days: int) -> Optional[datetime]:
    """
    Adiciona dias úteis a um datetime
    
    Args:
        dt: Datetime base
        days: Dias úteis a adicionar
        
    Returns:
        Novo datetime ou None
    """
    dt_utc = to_utc(dt)
    if dt_utc is None:
        return None
    
    result = dt_utc
    added_days = 0
    
    while added_days < days:
        result += timedelta(days=1)
        # Verificar se é dia útil (segunda a sexta)
        if result.weekday() < 5:  # 0-4 = segunda a sexta
            added_days += 1
    
    return result


# Constantes para uso no sistema
DATETIME_FORMATS = {
    'iso': "%Y-%m-%dT%H:%M:%S",
    'date': "%d/%m/%Y",
    'datetime': "%d/%m/%Y %H:%M:%S",
    'time': "%H:%M:%S",
    'filename': "%Y%m%d_%H%M%S"
}


# Helper functions para casos comuns
def today_start_utc() -> datetime:
    """Início do dia atual em UTC"""
    now = now_utc()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def today_end_utc() -> datetime:
    """Fim do dia atual em UTC"""
    now = now_utc()
    return now.replace(hour=23, minute=59, second=59, microsecond=999999)


def days_ago_utc(days: int) -> datetime:
    """Data de N dias atrás em UTC"""
    return now_utc() - timedelta(days=days)


def days_from_now_utc(days: int) -> datetime:
    """Data daqui a N dias em UTC"""
    return now_utc() + timedelta(days=days)


# Validação
def validate_datetime_string(dt_str: str) -> bool:
    """
    Valida se string pode ser convertida para datetime
    
    Args:
        dt_str: String a validar
        
    Returns:
        True se válida, False caso contrário
    """
    try:
        if 'Z' in dt_str:
            datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        else:
            datetime.fromisoformat(dt_str)
        return True
    except ValueError:
        return False


# Importações necessárias
from datetime import timedelta
