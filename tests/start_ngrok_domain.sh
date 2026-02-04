#!/bin/bash
# Script para configurar ngrok com domínio personalizado

# Configurar authtoken
ngrok config add-authtoken 37kj0liuHZBe3lari8sQVbG3wBw_5ctwcdGa4WjxXe85RQ2xM

# Iniciar ngrok para backend com domínio personalizado
ngrok http --domain=sublenticulate-shannan-resinous.ngrok-free.dev backend:8000
