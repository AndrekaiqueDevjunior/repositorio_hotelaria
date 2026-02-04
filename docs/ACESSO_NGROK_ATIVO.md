# Sistema Hotel Cabo Frio - Acesso via ngrok

## Status: ATIVO E FUNCIONANDO

### URL Publica (ngrok)
**https://sublenticulate-shannan-resinous.ngrok-free.dev**

Este link funciona de qualquer lugar da internet!

---

## Acessos ao Sistema

### 1. Frontend (Interface Web)
- **URL**: https://sublenticulate-shannan-resinous.ngrok-free.dev
- **Descricao**: Interface principal do sistema de gestao hoteleira

### 2. Backend API
- **URL Base**: https://sublenticulate-shannan-resinous.ngrok-free.dev/api/v1
- **Documentacao**: https://sublenticulate-shannan-resinous.ngrok-free.dev/api/v1/docs
- **Health Check**: https://sublenticulate-shannan-resinous.ngrok-free.dev/health

### 3. Dashboard ngrok (Local)
- **URL**: http://localhost:4040
- **Descricao**: Monitoramento de trafego e requisicoes em tempo real

---

## Credenciais de Acesso

### Usuario Administrador
- **Email**: admin@hotelreal.com.br
- **Senha**: admin123
- **Perfil**: ADMIN

---

## Servicos Ativos

| Servico | Container | Status | Porta |
|---------|-----------|--------|-------|
| Redis | app_hotel_cabo_frio-redis-1 | Healthy | 6379 |
| PostgreSQL | app_hotel_cabo_frio-postgres-1 | Healthy | 5432 |
| Backend | app_hotel_cabo_frio-backend-1 | Healthy | 8000 |
| Frontend | app_hotel_cabo_frio-frontend-1 | Healthy | 3000 |
| Nginx Proxy | app_hotel_cabo_frio-nginx-proxy-1 | Running | 8080 |
| ngrok | app_hotel_cabo_frio-ngrok-1 | Running | 4040 |

---

## Arquitetura

```
Internet
    |
    v
[ngrok Tunnel] <- URL Publica
    |
    v
[Nginx Proxy] <- Roteamento Inteligente
    |
    +---> /api/* -----> [Backend FastAPI:8000]
    |                        |
    |                        +---> [PostgreSQL:5432] (Prisma Cloud)
    |                        +---> [Redis:6379]
    |
    +---> /* ---------> [Frontend Next.js:3000]
```

**Vantagens desta arquitetura:**
- Um unico link para frontend e backend
- Frontend e backend comunicam-se internamente via Docker
- CORS configurado corretamente
- ngrok expoe tudo de forma unificada

---

## Comandos Uteis

### Ver status dos containers
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Ver logs em tempo real
```powershell
# Backend
docker logs -f app_hotel_cabo_frio-backend-1

# Frontend
docker logs -f app_hotel_cabo_frio-frontend-1

# ngrok
docker logs -f app_hotel_cabo_frio-ngrok-1
```

### Reiniciar servico especifico
```powershell
docker restart app_hotel_cabo_frio-frontend-1
docker restart app_hotel_cabo_frio-backend-1
```

### Parar todos os servicos
```powershell
docker-compose --profile ngrok down
```

### Iniciar sistema completo novamente
```powershell
.\INICIAR_SISTEMA_NGROK.ps1
```

---

## Observacoes Importantes

### Aviso de Seguranca do ngrok
- O ngrok free pode mostrar uma tela de aviso antes de acessar o site
- **Clique em "Visit Site"** para continuar
- Isso e normal e esperado na versao gratuita

### URL Dinamica
- A URL do ngrok pode mudar se o container for reiniciado
- Use sempre o script `INICIAR_SISTEMA_NGROK.ps1` que atualiza automaticamente

### CORS Configurado
- CORS permite todas as origens (*) em desenvolvimento
- Cookies e autenticacao JWT funcionam corretamente

### Persistencia de Dados
- Dados persistem em volumes Docker
- PostgreSQL hospedado no Prisma Data Platform (remoto)
- Redis mantem cache de sessoes

---

## Resolucao de Problemas

### Frontend nao carrega
```powershell
docker restart app_hotel_cabo_frio-frontend-1
```

### API retorna erro 502
```powershell
docker restart app_hotel_cabo_frio-backend-1
docker restart app_hotel_cabo_frio-nginx-proxy-1
```

### ngrok nao conecta
1. Verifique o token no arquivo `.env`
2. Reinicie o container: `docker restart app_hotel_cabo_frio-ngrok-1`
3. Verifique o dashboard: http://localhost:4040

---

## Monitoramento

### Dashboard ngrok
Acesse http://localhost:4040 para ver:
- Requisicoes em tempo real
- Tempo de resposta
- Erros e status codes
- Historico de trafego

### Logs consolidados
```powershell
docker-compose --profile ngrok logs -f
```

---

**Sistema configurado e testado em**: 03/01/2026
**Desenvolvido para**: Hotel Real Cabo Frio
