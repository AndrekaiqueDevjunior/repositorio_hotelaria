# Jornada Real - Status Atual & Próximos Passos

## 📊 Estado do Sistema

### Telas Implementadas ✅
- `/` → Landing page Jornada Real (home)
- `/consultar` → Entrada CPF
- `/consultar-pontos` → Dashboard de pontos
- `/entrar-jornada-real` → Perfil/Termos
- `/resgate_dos_premios` → Catálogo de prêmios
- `/nivel_jornada_real` → Tela de nível
- `/termos-jornada-real` → Termos & condições
- `/reservar` → Reserva com tema Jornada Real

**Readiness: 70% (UI/UX) | 40% (Backend Integration)**

---

## 🔴 Mocks Críticos a Corrigir

| Mock | Localização | Impacto | Prioridade |
|------|------------|--------|-----------|
| Pontos hardcoded (72) | `consultar-pontos:21` | Dados falsos | 🔴 ALTA |
| Código gerado localmente | `resgate_dos_premios:246` | Resgate não funciona | 🔴 ALTA |
| Progress 66% fixo | `consultar-pontos:25` | Barra enganosa | 🟡 MÉDIA |
| Nome "Hóspede Real" fixo | `consultar-pontos:167` | Não personaliza | 🟡 MÉDIA |
| Status de estoque fake | `resgate_dos_premios:30-31` | Estoque irreal | 🟡 MÉDIA |

---

## 📚 Documentação Criada

1. **JORNADA_REAL_MOCKS_SCHEMA.md**
   - Mapeia todos os mocks identificados
   - Mostra schema Prisma esperado
   - Lista endpoints necessários
   - Compara com implementação atual

2. **JORNADA_REAL_SKILLS.md**
   - 5 skills práticas de integração
   - Código antes/depois para cada
   - Testes e debugging tips
   - Checklist de implementação

---

## 🛠️ Próximas Tarefas

### 1️⃣ Integrar Consulta de Pontos (2-3 horas)
```bash
# Arquivo: frontend/app/consultar-pontos/page.js
# Mudança: currentPoints = 72 → GET /customers/{cpf}/loyalty
# Referência: JORNADA_REAL_SKILLS.md → Skill #1
```

### 2️⃣ Integrar Resgate de Prêmios (2-3 horas)
```bash
# Arquivo: frontend/app/resgate_dos_premios/page.js
# Mudança: code = gerado local → POST /rewards/redeem
# Referência: JORNADA_REAL_SKILLS.md → Skill #2
```

### 3️⃣ Validar CPF no Backend (1 hora)
```bash
# Arquivo: frontend/app/consultar/page.js
# Mudança: redireciona direto → GET /customers/{cpf} antes
# Referência: JORNADA_REAL_SKILLS.md → Skill #3
```

### 4️⃣ Testes E2E (2 horas)
```bash
# Fluxo: CPF → Consulta → Resgate → Confirmação
# Testes com dados reais do banco
# Tratamento de erros
```

---

## 🔌 Endpoints Necessários no Backend

**Críticos (implementar em 1º):**
- `GET /customers/{cpf}/loyalty` → pontos, nível, nome
- `POST /rewards/redeem` → resgata prêmio, retorna código

**Secundários (implementar em 2º):**
- `GET /customers/{cpf}` → validação de existência
- `GET /loyalty-levels` → níveis dinâmicos

**Já existem:**
- `GET /premios` → lista prêmios ✅

---

## 📖 Como Usar a Documentação

### Para Dev Frontend
1. Leia: `JORNADA_REAL_SKILLS.md`
2. Escolha a Skill (1-5)
3. Copie o código antes/depois
4. Substitua no arquivo
5. Teste conforme indicado

### Para Dev Backend
1. Leia: `JORNADA_REAL_MOCKS_SCHEMA.md` → Seção 2 (Endpoints)
2. Implemente os endpoints críticos
3. Returne o JSON conforme Seção 5 (Schemas JSON)
4. Comunique com frontend quando pronto

### Para QA/Testes
1. Leia: `JORNADA_REAL_MOCKS_SCHEMA.md` → Seção 4 (Tabela de Mocks)
2. Use checklist de fase 1-4 em Seção 6
3. Execute testes curl conforme Seção 7

---

## ✅ Checklist Geral

**Frontend - Integração:**
- [ ] Skill #1: Pontos dinâmicos
- [ ] Skill #2: Resgate real
- [ ] Skill #3: Validação CPF
- [ ] Skill #4: Níveis dinâmicos
- [ ] Skill #5: Error handling padrão

**Backend - APIs:**
- [ ] `GET /customers/{cpf}/loyalty`
- [ ] `POST /rewards/redeem`
- [ ] `GET /loyalty-levels`
- [ ] `GET /customers/{cpf}`

**QA - Testes:**
- [ ] Teste CPF válido/inválido
- [ ] Teste resgate com saldo suficiente
- [ ] Teste resgate com saldo insuficiente
- [ ] Teste resgate com estoque zerado
- [ ] Teste fluxo completo E2E

---

## 💾 Arquivos Atualizados

```
/repositorio_hotelaria/
├── README_JORNADA_REAL.md ← VOCÊ ESTÁ AQUI
├── JORNADA_REAL_MOCKS_SCHEMA.md ← Mapeamento técnico
├── JORNADA_REAL_SKILLS.md ← Implementação prática
└── frontend/
    ├── app/page.js (home Jornada Real) ✅ 
    ├── app/consultar/page.js
    ├── app/consultar-pontos/page.js 🔴 Pontos mock
    ├── app/resgate_dos_premios/page.js 🔴 Resgate mock
    ├── app/nivel_jornada_real/page.js
    └── app/entrar-jornada-real/page.js
```

---

## 🚀 Próxima Sessão de Dev

1. Ler `JORNADA_REAL_SKILLS.md`
2. Implementar Skill #1 (Pontos)
3. Implementar Skill #2 (Resgate)
4. Testar
5. Validar com QA

**Estimativa total: 1-2 dias**

---

## 📞 Referências

- Backend docs: `/docs/jornada-real-backend-db.md`
- Frontend status: Este arquivo
- Mocks & schema: `JORNADA_REAL_MOCKS_SCHEMA.md`
- Implementation guide: `JORNADA_REAL_SKILLS.md`
