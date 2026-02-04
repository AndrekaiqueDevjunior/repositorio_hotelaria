#!/bin/bash
# Script para configurar e iniciar ngrok

# Configurar authtoken
ngrok config add-authtoken 37kj0liuHZBe3lari8sQVbG3wBw_5ctwcdGa4WjxXe85RQ2xM

# Verificar configuração
ngrok config check

# Iniciar ngrok para backend
ngrok http backend:8000
