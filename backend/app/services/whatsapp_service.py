"""
Serviço de notificação via WhatsApp
Integração com Twilio para envio de mensagens
"""
import os
import logging
from typing import Dict, Any, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Serviço para envio de mensagens via WhatsApp usando Twilio.
    
    Configuração necessária (.env):
    - TWILIO_ACCOUNT_SID: SID da conta Twilio
    - TWILIO_AUTH_TOKEN: Token de autenticação
    - TWILIO_WHATSAPP_FROM: Número WhatsApp do Twilio (formato: whatsapp:+14155238886)
    - WHATSAPP_NOTIFICACAO_NUMERO: Número para receber notificações (formato: +5511968029600)
    """
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        self.notification_number = os.getenv("WHATSAPP_NOTIFICACAO_NUMERO", "+5511968029600")
        
        # Validar configuração
        if not self.account_sid or not self.auth_token:
            logger.warning(
                "Twilio não configurado. Defina TWILIO_ACCOUNT_SID e TWILIO_AUTH_TOKEN no .env"
            )
            self.client = None
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("WhatsApp Service inicializado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao inicializar Twilio Client: {e}")
                self.client = None
    
    def _format_phone_number(self, phone: str) -> str:
        """
        Formatar número de telefone para WhatsApp.
        
        Entrada: +5511968029600 ou 11968029600
        Saída: whatsapp:+5511968029600
        """
        # Remover espaços e caracteres especiais
        phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Adicionar + se não tiver
        if not phone.startswith("+"):
            phone = f"+{phone}"
        
        # Adicionar prefixo whatsapp: se não tiver
        if not phone.startswith("whatsapp:"):
            phone = f"whatsapp:{phone}"
        
        return phone
    
    async def enviar_notificacao_resgate_premio(
        self,
        cliente_nome: str,
        cliente_telefone: Optional[str],
        cliente_endereco: Optional[str],
        premio_nome: str,
        pontos_usados: int,
        codigo_resgate: str
    ) -> Dict[str, Any]:
        """
        Enviar notificação de resgate de prêmio via WhatsApp.
        
        Args:
            cliente_nome: Nome do cliente
            cliente_telefone: Telefone do cliente (opcional)
            cliente_endereco: Endereço do cliente (opcional)
            premio_nome: Nome do prêmio resgatado
            pontos_usados: Quantidade de pontos usados
            codigo_resgate: Código único do resgate
        
        Returns:
            Dict com status do envio
        """
        if not self.client:
            logger.warning("Twilio não configurado. Mensagem não enviada.")
            return {
                "success": False,
                "error": "Serviço WhatsApp não configurado",
                "message": "Configure TWILIO_ACCOUNT_SID e TWILIO_AUTH_TOKEN no .env"
            }
        
        try:
            # Montar mensagem
            endereco_texto = cliente_endereco if cliente_endereco else "Endereço não informado"
            telefone_texto = cliente_telefone if cliente_telefone else "Telefone não informado"
            
            mensagem = f"""🎁 *NOVO RESGATE DE PRÊMIO*

👤 *Cliente:* {cliente_nome}
📱 *Telefone:* {telefone_texto}
📍 *Endereço:* {endereco_texto}

🏆 *Prêmio:* {premio_nome}
⭐ *Pontos usados:* {pontos_usados}
🔑 *Código do resgate:* {codigo_resgate}

📦 *Mensagem do cliente:*
"Olá, me chamo {cliente_nome}, acumulei {pontos_usados} pontos e resgatei o prêmio {premio_nome}.

Eu moro em {endereco_texto}.

O código do resgate é {codigo_resgate}.

Gostaria de saber como vai ser feita a entrega do item. Enviam via Correios?"

---
⚠️ *Ação necessária:* Entre em contato com o cliente para combinar a entrega."""
            
            # Enviar mensagem
            to_number = self._format_phone_number(self.notification_number)
            from_number = self.whatsapp_from
            
            logger.info(f"Enviando WhatsApp de {from_number} para {to_number}")
            
            message = self.client.messages.create(
                body=mensagem,
                from_=from_number,
                to=to_number
            )
            
            logger.info(f"WhatsApp enviado com sucesso. SID: {message.sid}")
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": to_number
            }
            
        except TwilioRestException as e:
            logger.error(f"Erro Twilio ao enviar WhatsApp: {e.code} - {e.msg}")
            return {
                "success": False,
                "error": f"Erro Twilio: {e.msg}",
                "error_code": e.code
            }
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def enviar_mensagem_customizada(
        self,
        to_number: str,
        mensagem: str
    ) -> Dict[str, Any]:
        """
        Enviar mensagem customizada via WhatsApp.
        
        Args:
            to_number: Número de destino (formato: +5511968029600)
            mensagem: Texto da mensagem
        
        Returns:
            Dict com status do envio
        """
        if not self.client:
            return {
                "success": False,
                "error": "Serviço WhatsApp não configurado"
            }
        
        try:
            to_formatted = self._format_phone_number(to_number)
            
            message = self.client.messages.create(
                body=mensagem,
                from_=self.whatsapp_from,
                to=to_formatted
            )
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status
            }
            
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp customizado: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Instância global do serviço
_whatsapp_service = None


def get_whatsapp_service() -> WhatsAppService:
    """Obter instância do serviço WhatsApp (singleton)"""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
