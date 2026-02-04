# Configuração do Ngrok para Acesso Externo

## 📋 Visão Geral

Este documento descreve a configuração do Ngrok para fornecer acesso externo seguro ao sistema de hotel, utilizando um domínio personalizado.

## 🛠️ Requisitos

- Docker e Docker Compose instalados
- Conta no Ngrok (gratuita ou paga)
- Token de autenticação do Ngrok

## ⚙️ Configuração

### 1. Variáveis de Ambiente

No arquivo `.env`, configure as seguintes variáveis:

```bash
# NGROK
NGROK_AUTHTOKEN=seu_token_aqui
NGROK_ENABLED=true
NGROK_DOMAIN=seu-dominio.ngrok-free.dev
NGROK_URL=https://seu-dominio.ngrok-free.dev
NEXT_PUBLIC_NGROK_URL=https://seu-dominio.ngrok-free.dev
```

### 2. Configuração do Docker Compose

O serviço Ngrok está configurado no `docker-compose.yml`:

```yaml
services:
  ngrok:
    image: ngrok/ngrok:latest
    restart: unless-stopped
    command:
      - "http"
      - "nginx:8080"
      - "--log=stdout"
      - "--log-level=info"
    ports:
      - "4040:4040"
    depends_on:
      - nginx
    networks:
      - hotel_network
    profiles:
      - ngrok
    environment:
      NGROK_AUTHTOKEN: ${NGROK_AUTHTOKEN:-}
```

## 🚀 Iniciando o Serviço

### Iniciar todos os serviços (incluindo Ngrok)

```bash
docker-compose --profile ngrok up -d
```

### Parar todos os serviços

```bash
docker-compose down
```

## 🔍 Monitoramento

### Verificar logs do Ngrok

```bash
docker logs hotel-ngrok-1
```

### Acessar painel de monitoramento

Acesse: [http://localhost:4040](http://localhost:4040)

## 🔄 Reiniciar o Serviço Ngrok

```bash
docker-compose restart ngrok
```

## 🔒 Segurança

1. Mantenha o `NGROK_AUTHTOKEN` seguro
2. O painel do Ngrok só está disponível localmente
3. Monitore os acessos regularmente

## ❓ Solução de Problemas

### Domínio já em uso

Se encontrar o erro `domain is reserved for another account`:

1. Verifique o token de autenticação
2. No painel do Ngrok, verifique a disponibilidade do domínio
3. Se necessário, use um novo subdomínio

### Conexão recusada

Verifique se o Nginx está rodando corretamente:

```bash
docker ps | grep nginx
```

## 📚 Recursos Adicionais

- [Documentação Oficial do Ngrok](https://ngrok.com/docs)
- [Gerenciamento de Túneis](https://dashboard.ngrok.com/tunnels)
- [Configuração de Domínios Personalizados](https://ngrok.com/docs/cloud-edge#domains)

---

**Última Atualização**: 22/01/2026  
**Domínio Atual**: jacoby-unshifted-kylie.ngrok-free.dev
