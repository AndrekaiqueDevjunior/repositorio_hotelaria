# ============================================================
# Dockerfile - Frontend Next.js
# ============================================================

FROM node:20-alpine

# Metadados
LABEL maintainer="Hotel Cabo Frio"
LABEL description="Frontend Next.js para Sistema de Gestão Hoteleira"

# Diretório de trabalho
WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependências (incluindo devDependencies para build)
RUN npm install && \
    npm cache clean --force

# Copiar código da aplicação
COPY . .

# Compilar Tailwind CSS
RUN npx tailwindcss -i ./app/globals.css -o ./public/styles.css --watch=false

# Build da aplicação (para produção)
RUN npm run build

# Expor porta
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Comando padrão (desenvolvimento) - temporário para corrigir cache
CMD ["sh", "-c", "NODE_ENV=development npm run dev"]





