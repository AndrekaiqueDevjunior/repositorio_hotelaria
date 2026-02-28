import os
import uuid
import requests
from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc
from app.core.config import settings
from app.utils.datetime_utils import now_utc


class CieloAPI:
    def __init__(self):
        self.mode = (os.getenv("CIELO_MODE", "sandbox") or "").lower()
        self.mode = "production" if self.mode in ("prod", "production") else "sandbox"
        self.merchant_id = (os.getenv("CIELO_MERCHANT_ID") or "").strip()
        self.merchant_key = (os.getenv("CIELO_MERCHANT_KEY") or "").strip()
        if not self.merchant_id or not self.merchant_key:
            raise RuntimeError("Credenciais Cielo não configuradas")
        if self.mode == "production":
            self.base_sale_url = "https://api.cieloecommerce.cielo.com.br/"
            self.base_query_url = "https://apiquery.cieloecommerce.cielo.com.br/"
        else:
            self.base_sale_url = "https://apisandbox.cieloecommerce.cielo.com.br/"
            self.base_query_url = "https://apisandbox.cieloecommerce.cielo.com.br/"
        self.timeout = int(os.getenv("CIELO_TIMEOUT_MS", "8000")) // 1000
        
        self.headers = {
            "MerchantId": self.merchant_id,
            "MerchantKey": self.merchant_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "RequestId": None  # Será preenchido por requisição para idempotência
        }
    
    def consultar_vendas(self, data_inicio=None, data_fim=None, page=1, page_size=20):
        """Consulta vendas na API Cielo"""
        try:
            # Cielo não tem endpoint direto de histórico, vamos simular com dados de teste
            # Em produção, você usaria o endpoint de relatórios ou armazenaria os PaymentIds
            
            # Simulação de dados para sandbox
            vendas_simuladas = [
                {
                    "PaymentId": f"CIELO_SANDBOX_{now_utc().strftime('%Y%m%d')}_{i}",
                    "Tid": f"1006993069{i:06d}",
                    "Amount": 15000 + (i * 5000),
                    "Status": 2 if i % 3 != 0 else 1,  # 2 = Aprovado, 1 = Autorizado
                    "ReturnCode": "00" if i % 3 != 0 else "05",
                    "ReturnMessage": "Transaction Approved" if i % 3 != 0 else "Not Authorized",
                    "AuthorizationCode": f"123456" if i % 3 != 0 else None,
                    "Capture": True,
                    "CaptureDate": now_utc().isoformat(),
                    "MerchantOrderId": f"RCF-{now_utc().strftime('%Y%m%d')}-{i:06d}",
                    "Type": "CreditCard",
                    "Installments": i + 1,
                    "CreditCard": {
                        "Brand": "Visa" if i % 2 == 0 else "Master",
                        "Holder": f"CLIENTE TESTE {i}",
                        "CardNumber": f"**** **** **** {1000 + i}"
                    }
                }
                for i in range(1, 21)  # 20 vendas simuladas
            ]
            
            # Paginar resultados
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            vendas_paginadas = vendas_simuladas[start_idx:end_idx]
            
            return {
                "success": True,
                "data": vendas_paginadas,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": len(vendas_simuladas),
                    "total_pages": (len(vendas_simuladas) + page_size - 1) // page_size
                },
                "mode": self.mode,
                "api_base_url": self.base_sale_url
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "mode": self.mode
            }
    
    def consultar_pagamento(self, payment_id):
        """Consulta pagamento específico - PRODUÇÃO ou SANDBOX"""
        try:
            # Em sandbox, simulamos a resposta
            if self.mode == "sandbox":
                return {
                    "success": True,
                    "data": {
                        "PaymentId": payment_id,
                        "Status": 2,
                        "ReturnCode": "00",
                        "ReturnMessage": "Transaction Approved",
                        "AuthorizationCode": "123456",
                        "Amount": 15000,
                        "CapturedAmount": 15000,
                        "CapturedDate": now_utc().isoformat(),
                        "MerchantOrderId": "RCF-20251119-000001",
                        "Type": "CreditCard",
                        "Installments": 1
                    }
                }
            
            # PRODUÇÃO - Chamada real à API Cielo
            # URL de consulta em produção: https://apiquery.cieloecommerce.cielo.com.br/1/sales/{PaymentId}
            query_url = f"{self.base_query_url}1/sales/{payment_id}"
            
            response = requests.get(query_url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def consultar_por_tid(self, tid):
        """Consulta pagamento por TID - PRODUÇÃO ou SANDBOX"""
        try:
            # Em sandbox, simulamos a resposta
            if self.mode == "sandbox":
                return {
                    "success": True,
                    "data": {
                        "PaymentId": f"CIELO_SANDBOX_{now_utc().strftime('%Y%m%d%H%M%S')}",
                        "Tid": tid,
                        "Status": 2,
                        "ReturnCode": "00",
                        "ReturnMessage": "Transaction Approved",
                        "AuthorizationCode": "123456",
                        "Amount": 15000,
                        "CapturedAmount": 15000,
                        "CapturedDate": now_utc().isoformat(),
                        "MerchantOrderId": f"RCF-{now_utc().strftime('%Y%m%d')}-000001",
                        "Type": "CreditCard",
                        "Installments": 1
                    }
                }
            
            # PRODUÇÃO - Chamada real à API Cielo
            # URL de consulta por TID em produção: https://apiquery.cieloecommerce.cielo.com.br/1/sales/tid/{Tid}
            query_url = f"{self.base_query_url}1/sales/tid/{tid}"
            
            response = requests.get(query_url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def criar_pagamento_cartao(self, valor, cartao_numero, cartao_validade, cartao_cvv, cartao_nome, parcelas=1):
        """Criar pagamento com cartão de crédito - PRODUÇÃO ou SANDBOX"""
        try:
            # Converter valor para centavos (Cielo usa centavos)
            valor_centavos = int(float(valor) * 100)
            
            # URL correta baseada no ambiente
            url = f"{self.base_sale_url}1/sales/"
            
            # Payload conforme documentação oficial Cielo E-Commerce API 3.0
            expiration_date = cartao_validade
            if expiration_date and "/" not in expiration_date:
                if len(expiration_date) == 6:
                    expiration_date = f"{expiration_date[:2]}/{expiration_date[2:]}"
                elif len(expiration_date) == 4:
                    expiration_date = f"{expiration_date[:2]}/20{expiration_date[2:]}"

            payload = {
                "MerchantOrderId": f"RCF-{now_utc().strftime('%Y%m%d%H%M%S')}",
                "Customer": {
                    "Name": cartao_nome
                },
                "Payment": {
                    "Type": "CreditCard",
                    "Amount": valor_centavos,
                    "Installments": parcelas,
                    "SoftDescriptor": "HOTEL REAL CF",
                    "Capture": True,
                    "CreditCard": {
                        "CardNumber": cartao_numero.replace(" ", "").replace("-", ""),
                        "Holder": cartao_nome,
                        "ExpirationDate": expiration_date,
                        "SecurityCode": cartao_cvv,
                        "SaveCard": False
                    }
                }
            }
            
            # Adicionar RequestId para idempotência
            request_id = str(uuid.uuid4())
            headers = self.headers.copy()
            headers["RequestId"] = request_id
            
            mode_label = "SANDBOX" if self.mode == "sandbox" else "PRODUÇÃO"
            print(f"[CIELO {mode_label}] Enviando pagamento: R$ {valor} ({valor_centavos} centavos)")
            print(f"[CIELO {mode_label}] URL: {url}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            raw_text = response.text or ""
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type.lower() or raw_text.lstrip().startswith(("{", "[")):
                try:
                    data = response.json()
                except ValueError:
                    data = {
                        "raw": raw_text,
                        "Message": "Resposta da Cielo não retornou JSON válido"
                    }
            else:
                data = {
                    "raw": raw_text,
                    "Message": "Resposta da Cielo não retornou JSON válido"
                }
            
            # Adicionar logs para depuração
            print(f"[CIELO {mode_label}] Resposta da API: {data}")
            
            # Normalizar resposta quando a API retorna lista (ex.: lista de erros)
            if isinstance(data, list):
                data = data[0] if data and isinstance(data[0], dict) else {"Errors": data}
            
            if response.status_code in [200, 201]:
                payment = data.get("Payment", {}) if isinstance(data, dict) else {}
                status = self._mapear_status(payment.get("Status")) if payment else "UNKNOWN"
                print(f"[CIELO {mode_label}] Pagamento {status}: {payment.get('PaymentId')}")
                
                # Construir resposta de sucesso
                result = {
                    "payment_id": payment.get("PaymentId"),
                    "status": status,
                    "url": payment.get("Url"),
                    "authorization_code": payment.get("AuthorizationCode"),
                    "return_code": payment.get("ReturnCode"),
                    "return_message": payment.get("ReturnMessage"),
                    "tid": payment.get("Tid"),
                    "proof_of_sale": payment.get("ProofOfSale")
                }
                
                # Adicionar sucesso ao resultado
                result["success"] = True
                return result
            else:
                # Tratar erros da API
                error_msg = ""
                if response.status_code == 401:
                    error_msg = "CIELO_UNAUTHORIZED: verifique MerchantId/MerchantKey e endpoint do ambiente"
                if isinstance(data, dict):
                    errors = data.get("Errors")
                    if isinstance(errors, list) and errors:
                        first_error = errors[0] if isinstance(errors[0], dict) else {"Message": str(errors[0])}
                        error_msg = error_msg or first_error.get("Message") or first_error.get("Error") or str(first_error)
                    else:
                        error_msg = error_msg or data.get("Message") or data.get("Error") or str(data)
                else:
                    error_msg = error_msg or f"Resposta inesperada da API: {data}"
                
                print(f"[CIELO {mode_label}] Erro {response.status_code}: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "return_code": str(response.status_code),
                    "return_message": str(data)
                }
                
        except requests.exceptions.Timeout:
            print("❌ [CIELO PROD] Timeout na comunicação")
            return {
                "success": False,
                "error": "Timeout na comunicação com a Cielo"
            }
        except Exception as e:
            print(f"❌ [CIELO PROD] Exceção: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _detectar_bandeira(self, numero_cartao):
        """Detectar bandeira do cartão pelo número"""
        numero = numero_cartao.replace(" ", "").replace("-", "")
        if numero.startswith("4"):
            return "Visa"
        elif numero.startswith(("51", "52", "53", "54", "55")):
            return "Master"
        elif numero.startswith(("34", "37")):
            return "Amex"
        elif numero.startswith("636368"):
            return "Elo"
        elif numero.startswith(("6011", "622", "64", "65")):
            return "Discover"
        elif numero.startswith("606282"):
            return "Hipercard"
        else:
            return "Visa"
    
    def _mapear_status(self, status_code):
        """Mapear código de status Cielo para string"""
        status_map = {
            0: "NOT_FINISHED",
            1: "AUTHORIZED",
            2: "CAPTURED",
            3: "DENIED",
            10: "VOIDED",
            11: "REFUNDED",
            12: "PENDING",
            13: "ABORTED"
        }
        return status_map.get(status_code, "UNKNOWN")
    
    async def gerar_pix(self, valor, descricao):
        """Gerar PIX - PRODUÇÃO/SANDBOX"""
        try:
            # Modo SANDBOX - simular resposta
            if self.mode == "sandbox":
                import base64
                txid = f"PIX_SANDBOX_{now_utc().strftime('%Y%m%d%H%M%S')}"
                qr_code = f"00020126580014BR.GOV.BCB.PIX0136{txid}5204000053039865802BR5925HOTEL REAL CABO FRIO6009SAO PAULO62070503***6304ABCD"
                
                # Gerar QR Code base64 para exibição visual
                qr_code_base64 = base64.b64encode(qr_code.encode()).decode()
                
                print(f"✅ [CIELO PIX SANDBOX] PIX gerado: {txid}")
                
                return {
                    "success": True,
                    "txid": txid,
                    "qr_code": qr_code,
                    "qr_code_base64": qr_code_base64,
                    "valor": valor,
                    "descricao": descricao,
                    "expiration": (now_utc() + timedelta(minutes=15)).isoformat(),
                    "mode": "sandbox"
                }
            
            if self.mode == "production":
                return {
                    "success": False,
                    "error": "PIX não suportado na Cielo E-Commerce API 3.0. Use Gateway/Checkout ou outro provedor."
                }
            # URL correta baseada no ambiente para PIX (sandbox simulado)
            url = f"{self.base_sale_url}1/sales/"
            valor_centavos = int(float(valor) * 100)
            
            payload = {
                "MerchantOrderId": f"PIX-{now_utc().strftime('%Y%m%d%H%M%S')}",
                "Customer": {
                    "Name": "Cliente PIX",
                    "Identity": "12345678900",
                    "IdentityType": "CPF"
                },
                "Payment": {
                    "Type": "Pix",
                    "Amount": valor_centavos
                }
            }
            
            print(f"🔵 [CIELO PIX PROD] Gerando PIX: R$ {valor}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=self.timeout)
            data = response.json()
            
            if response.status_code in [200, 201]:
                payment = data.get("Payment", {})
                print(f"✅ [CIELO PIX PROD] PIX gerado: {payment.get('PaymentId')}")
                return {
                    "txid": payment.get("PaymentId"),
                    "qr_code": payment.get("QrCodeString"),
                    "qr_code_base64": payment.get("QrCodeBase64Image"),
                    "valor": valor,
                    "descricao": descricao,
                    "expiration": payment.get("ExpirationDate"),
                    "mode": "production"
                }
            else:
                print(f"❌ [CIELO PIX PROD] Erro: {data}")
                return {
                    "success": False,
                    "error": data.get("Message", "Erro ao gerar PIX")
                }
                
        except Exception as e:
            print(f"❌ [CIELO PIX PROD] Exceção: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cancelar_pagamento(self, payment_id):
        """Cancelar pagamento - PRODUÇÃO/SANDBOX"""
        try:
            # Modo SANDBOX - simular cancelamento
            if self.mode == "sandbox":
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "status": "CANCELLED",
                    "message": "Payment cancelled successfully (SANDBOX)"
                }
            
            # URL correta baseada no ambiente para cancelamento
            url = f"{self.base_sale_url}1/sales/{payment_id}/void"
            
            print(f"🔵 [CIELO PROD] Cancelando pagamento: {payment_id}")
            response = requests.put(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"✅ [CIELO PROD] Pagamento cancelado: {payment_id}")
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "status": "CANCELLED",
                    "message": "Payment cancelled successfully"
                }
            else:
                data = response.json() if response.content else {}
                print(f"❌ [CIELO PROD] Erro ao cancelar: {data}")
                return {
                    "success": False,
                    "error": data.get("Message", "Erro ao cancelar pagamento")
                }
                
        except Exception as e:
            print(f"❌ [CIELO PROD] Exceção: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Instância global do cliente Cielo
cielo_api = CieloAPI()