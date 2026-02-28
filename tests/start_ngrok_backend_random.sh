#!/bin/bash
# Script para configurar ngrok com domínio aleatório para backend

# Configurar authtoken
ngrok config add-authtoken 37kj0liuHZBe3lari8sQVbG3wBw_5ctwcdGa4WjxXe85RQ2xM

# Iniciar ngrok para backend com domínio aleatório
ngrok http backend:8000
