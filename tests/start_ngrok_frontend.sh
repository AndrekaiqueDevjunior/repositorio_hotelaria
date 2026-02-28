#!/bin/bash
# Script para configurar ngrok para frontend

# Configurar authtoken
ngrok config add-authtoken 37kj0liuHZBe3lari8sQVbG3wBw_5ctwcdGa4WjxXe85RQ2xM

# Iniciar ngrok para frontend
ngrok http frontend:3000
