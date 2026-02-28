# Hotel Real Cabo Frio - Sistema Completo

## 🏨 Descrição

Sistema completo de gestão hoteleira para o Hotel Real Cabo Frio, desenvolvido com Next.js (frontend) e FastAPI (backend), utilizando PostgreSQL como banco de dados e Redis para cache.

## 🚀 Tecnologias

### Frontend
- **Next.js 14** - Framework React
- **TailwindCSS** - Estilização
- **TypeScript** - Tipagem
- **React Hook Form** - Formulários
- **Lucide React** - Ícones

### Backend
- **FastAPI** - Framework Python
- **Prisma** - ORM
- **PostgreSQL** - Banco de dados
- **Redis** - Cache
- **JWT** - Autenticação
- **Pydantic** - Validação

### Infraestrutura
- **Docker** - Containerização
- **Docker Compose** - Orquestração
- **Nginx** - Proxy reverso

## 📋 Funcionalidades

### 🏥 Sistema de Reservas
- Busca de disponibilidade
- Reserva online
- Check-in/Check-out
- Gestão de quartos

### 💰 Sistema de Pagamentos
- Integração com Cielo
- Múltiplos métodos de pagamento
- Comprovantes digitais
- Sistema anti-fraude

### 🎯 Sistema de Fidelidade
- Acúmulo de pontos
- Resgate de prêmios
- Níveis de fidelidade
- Histórico de transações

### 👥 Gestão de Clientes
- Cadastro de clientes
- Histórico de hospedagens
- Preferências
- Comunicações

### 📊 Dashboard Administrativo
- Métricas em tempo real
- Relatórios detalhados
- Gestão de funcionários
- Auditoria completa

## 🛠️ Instalação

### Pré-requisitos
- Docker e Docker Compose
- Node.js 18+ (para desenvolvimento local)
- Python 3.12+ (para desenvolvimento local)

### 1. Clonar o repositório
```bash
git clone https://github.com/seu-usuario/hotel-real-cabo-frio.git
cd hotel-real-cabo-frio
```

### 2. Configurar variáveis de ambiente
```bash
# Backend
cp .env.example .env
# Edite o arquivo .env com suas credenciais

# Frontend
cp frontend/.env.example frontend/.env.local
# Edite o arquivo com suas configurações
```

### 3. Iniciar com Docker
```bash
docker compose up -d
```

### 4. Acessar o sistema
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs

## 📁 Estrutura do Projeto

```
hotel-real-cabo-frio/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/            # Rotas da API
│   │   ├── core/           # Configurações core
│   │   ├── models/         # Modelos de dados
│   │   ├── repositories/   # Repositórios
│   │   └── schemas/        # Schemas Pydantic
│   ├── prisma/             # Schema do banco
│   └── requirements.txt    # Dependências Python
├── frontend/               # Aplicação Next.js
│   ├── app/               # Páginas da aplicação
│   ├── components/        # Componentes React
│   ├── public/            # Arquivos estáticos
│   └── package.json       # Dependências Node.js
├── docker-compose.yml      # Configuração Docker
└── README.md              # Este arquivo
```

## 🔧 Configuração

### Banco de Dados
O sistema usa PostgreSQL com as seguintes tabelas principais:
- `clientes` - Informações dos clientes
- `quartos` - Gestão de quartos
- `reservas` - Sistema de reservas
- `pagamentos` - Histórico de pagamentos
- `funcionarios` - Gestão de funcionários
- `pontos_*` - Sistema de fidelidade

### Autenticação
- JWT tokens para autenticação
- Refresh tokens para sessões prolongadas
- Perfis de usuário (ADMIN, RECEPCAO, etc.)
- Sistema de auditoria

## 📱 Funcionalidades Principais

### Para Clientes
- 📱 Reserva online
- 💳 Pagamento seguro
- 🎯 Acúmulo de pontos
- 📋 Histórico de hospedagens

### Para Funcionários
- 🏨 Gestão de reservas
- 👥 Cadastro de clientes
- 💰 Processamento de pagamentos
- 📊 Relatórios administrativos

### Para Administradores
- 🔐 Controle total do sistema
- 📈 Métricas e analytics
- 👥 Gestão de equipe
- ⚙️ Configurações avançadas

## 🚀 Deploy

### Produção
```bash
# Build das imagens
docker compose -f docker-compose.production.yml build

# Subida dos serviços
docker compose -f docker-compose.production.yml up -d
```

### Variáveis de Ambiente de Produção
- `DATABASE_URL`: String de conexão PostgreSQL
- `REDIS_URL`: String de conexão Redis
- `JWT_SECRET_KEY`: Chave secreta para JWT
- `CIELO_*`: Credenciais Cielo para pagamentos

## 🧪 Testes

### Testes Unitários
```bash
# Backend
cd backend && python -m pytest

# Frontend
cd frontend && npm test
```

### Testes de Integração
```bash
# Testes da API
cd backend && python -m pytest tests/integration/
```

## 📝 Desenvolvimento

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🔐 Segurança

- 🔒 Senhas hasheadas com bcrypt
- 🛡️ Proteção contra CSRF
- 🔐 Tokens JWT com expiração
- 🚫 Rate limiting
- 📊 Auditoria completa
- 🛡️ Validação de entrada

## 📞 Suporte

- **Email**: contato@hotelrealcabofrio.com
- **Telefone**: +55 22 2648-5900
- **Endereço**: Cabo Frio - RJ

## 📄 Licença

Este projeto é propriedade privada do Hotel Real Cabo Frio. © 2026 Todos os direitos reservados.

## 🤝 Contribuição

Para contribuir com este projeto:
1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

**Desenvolvido com ❤️ para o Hotel Real Cabo Frio**
