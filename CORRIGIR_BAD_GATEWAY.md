# 🔧 Correção do Bad Gateway - Passo a Passo

Execute estes comandos **diretamente na VPS** via SSH:

## 1️⃣ Conectar na VPS
```bash
ssh root@72.61.27.152
```

## 2️⃣ Verificar status atual
```bash
cd /opt/hotel
docker ps -a
```

## 3️⃣ Parar todos os containers
```bash
docker-compose -f docker-compose.production.yml down
```

## 4️⃣ Remover containers antigos (se necessário)
```bash
docker rm -f hotel_frontend_prod hotel_nginx_proxy_prod || true
```

## 5️⃣ Subir todos os containers novamente
```bash
docker-compose -f docker-compose.production.yml up -d
```

## 6️⃣ Verificar se estão rodando
```bash
docker ps
```

## 7️⃣ Verificar logs do frontend
```bash
docker logs --tail 30 hotel_frontend_prod
```

## 8️⃣ Verificar logs do nginx
```bash
docker logs --tail 30 hotel_nginx_proxy_prod
```

## 9️⃣ Testar conexão interna
```bash
# Testar se o frontend responde internamente
docker exec hotel_frontend_prod wget -O- http://localhost:3000 2>&1 | head -n 5

# Testar se o nginx consegue acessar o frontend
docker exec hotel_nginx_proxy_prod wget -O- http://frontend:3000 2>&1 | head -n 5
```

## 🔟 Se ainda não funcionar, verificar a rede Docker
```bash
# Listar redes
docker network ls

# Verificar se os containers estão na mesma rede
docker network inspect hotel_hotel_network | grep -E "hotel_frontend_prod|hotel_nginx_proxy_prod"
```

---

## 🚨 Solução Alternativa: Recriar tudo do zero

Se nada funcionar, execute:

```bash
cd /opt/hotel

# Parar tudo
docker-compose -f docker-compose.production.yml down -v

# Remover imagens antigas
docker rmi hotel-frontend hotel-backend || true

# Rebuild completo
docker-compose -f docker-compose.production.yml build --no-cache

# Subir tudo
docker-compose -f docker-compose.production.yml up -d

# Aguardar 30 segundos
sleep 30

# Verificar status
docker-compose -f docker-compose.production.yml ps

# Ver logs
docker-compose -f docker-compose.production.yml logs -f
```

---

## ✅ Após executar, teste:

Acesse: `http://72.61.27.152:8080`

Se ainda der Bad Gateway, me envie a saída dos comandos:
```bash
docker ps
docker logs hotel_frontend_prod --tail 50
docker logs hotel_nginx_proxy_prod --tail 50
```
