"""
HTTP Client para testes de integracao
Gerencia autenticacao, retry logic e logging
"""
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv(".env.test")


class APIClient:
    """Cliente HTTP para testes de integracao com autenticacao"""
    
    def __init__(self):
        self.base_url = os.getenv("BASE_URL", "http://localhost:8080")
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_backoff = int(os.getenv("RETRY_BACKOFF", "1"))
        self.token: Optional[str] = None
        # Client com cookies persistentes para manter sessao
        self.client = httpx.Client(timeout=self.timeout, follow_redirects=True)
        
    def _should_retry(self, status_code: int) -> bool:
        """Verifica se deve fazer retry baseado no status code"""
        return status_code in [502, 503, 504]
    
    def _redact_sensitive(self, data: Any) -> Any:
        """Remove dados sensiveis de logs"""
        if not isinstance(data, dict):
            return data
        
        redacted = data.copy()
        sensitive_keys = ["password", "senha", "token", "authorization", "cardNumber", "securityCode"]
        
        for key in sensitive_keys:
            if key in redacted:
                redacted[key] = "***REDACTED***"
        
        return redacted
    
    def login(self, email: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """Realiza login e armazena token"""
        email = email or os.getenv("AUTH_EMAIL")
        password = password or os.getenv("AUTH_PASSWORD")
        
        response = self.request(
            "POST",
            "/api/v1/login",
            json={"email": email, "password": password},
            skip_auth=True
        )
        
        if response.status_code == 200:
            data = response.json()
            refresh_token = data.get("refresh_token")
            
            if not refresh_token:
                raise ValueError("Login bem-sucedido mas refresh_token nao encontrado")
            
            # Usar refresh_token para obter access_token válido
            refresh_response = self.request(
                "POST",
                "/api/v1/refresh",
                json={"refresh_token": refresh_token},
                skip_auth=True
            )
            
            if refresh_response.status_code == 200:
                refresh_data = refresh_response.json()
                self.token = refresh_data.get("access_token")
                if not self.token:
                    raise ValueError("Refresh bem-sucedido mas access_token nao encontrado")
            else:
                raise ValueError(f"Falha ao obter access_token: {refresh_response.status_code}")
        
        return response
    
    def request(
        self,
        method: str,
        path: str,
        skip_auth: bool = False,
        **kwargs
    ) -> httpx.Response:
        """Faz request HTTP com retry logic e logging"""
        url = f"{self.base_url}{path}"
        
        headers = kwargs.pop("headers", {})
        if not skip_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        attempt = 0
        last_error = None
        
        while attempt < self.max_retries:
            try:
                start_time = time.time()
                
                response = self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    **kwargs
                )
                
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                print(f"[{method}] {path} -> {response.status_code} ({elapsed_ms}ms)")
                
                if self._should_retry(response.status_code) and attempt < self.max_retries - 1:
                    attempt += 1
                    wait_time = self.retry_backoff * attempt
                    print(f"  Retry {attempt}/{self.max_retries} apos {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                return response
                
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                attempt += 1
                
                if attempt < self.max_retries:
                    wait_time = self.retry_backoff * attempt
                    print(f"  Erro de conexao. Retry {attempt}/{self.max_retries} apos {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Falha apos {self.max_retries} tentativas: {str(e)}")
        
        raise Exception(f"Request falhou: {last_error}")
    
    def get(self, path: str, **kwargs) -> httpx.Response:
        """GET request"""
        return self.request("GET", path, **kwargs)
    
    def post(self, path: str, **kwargs) -> httpx.Response:
        """POST request"""
        return self.request("POST", path, **kwargs)
    
    def put(self, path: str, **kwargs) -> httpx.Response:
        """PUT request"""
        return self.request("PUT", path, **kwargs)
    
    def patch(self, path: str, **kwargs) -> httpx.Response:
        """PATCH request"""
        return self.request("PATCH", path, **kwargs)
    
    def delete(self, path: str, **kwargs) -> httpx.Response:
        """DELETE request"""
        return self.request("DELETE", path, **kwargs)
    
    def close(self):
        """Fecha cliente HTTP"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
