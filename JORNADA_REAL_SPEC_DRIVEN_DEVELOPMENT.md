# Jornada Real - Spec Driven Development

Contrato operacional para implementar a Jornada Real sem gambiarras, mantendo checklist, backend, frontend, WhatsApp e testes alinhados.

---

## 1. Fontes de Verdade

| Arquivo | Papel |
|---|---|
| `JORNADA_REAL_FEATURES_CHECKLIST.md` | Backlog, prioridade e status por funcionalidade |
| `JORNADA_REAL_SPEC_DRIVEN_DEVELOPMENT.md` | Contrato técnico, critérios de aceite e definição de pronto |
| `JORNADA_REAL_SKILLS.md` | Playbook prático de implementação por tela/fluxo |
| `SKILLS.md` | Índice das skills operacionais do projeto |
| `JORNADA_REAL_LEITURA_IA.md` | Roteiro por função: Backend, Frontend, QA, PM e IA |

Quando houver conflito, siga esta ordem:

1. Pedido mais recente do usuário.
2. `JORNADA_REAL_SPEC_DRIVEN_DEVELOPMENT.md`.
3. `JORNADA_REAL_FEATURES_CHECKLIST.md`.
4. Código existente e padrões locais.

---

## 2. Fluxo Obrigatório

Para qualquer item Jornada Real:

1. Escolha o ID da funcionalidade (`JR-01` a `JR-11`).
2. Leia o status no checklist.
3. Leia o contrato neste spec.
4. Antes de codar, confirme quais campos, endpoints, efeitos colaterais e testes fecham o item.
5. Implemente primeiro o core backend quando o contrato tiver regra de negócio.
6. Integre frontend somente depois do endpoint estar testado ou com contrato mockado explicitamente.
7. Rode testes relevantes.
8. Atualize o checklist com `✅`, `🟡` ou `❌` e uma frase objetiva do que falta.

Nenhum item deve ser marcado como `✅ completo` sem:

- contrato de API fechado;
- validações de segurança no backend;
- testes automatizados ou teste manual documentado;
- frontend sem mock enganoso para o usuário final, quando houver tela;
- WhatsApp via serviço oficial quando o item envolver mensagem.

---

## 3. Definição de Status

| Status | Significado |
|---|---|
| ✅ Completo | Contrato implementado, testado e integrado no fluxo esperado |
| 🟡 Parcial | Existe implementação equivalente, mas ainda falta parte do contrato final |
| ❌ Precisa implementar | Não existe implementação confiável ou está só em mock |
| ⛔ Bloqueado | Falta decisão externa, credencial, regra de produto ou dependência real |

Ao usar `🟡`, escreva exatamente o que falta. Exemplo: "endpoint existe, mas falta dedupe 1x por dia".

---

## 4. Regras de Arquitetura

- Pontos, bônus, cupons, resgates e autenticação devem ser calculados e validados no backend.
- O frontend nunca pode ser fonte de verdade para saldo, código de resgate, estoque, desconto, nível ou autorização.
- WhatsApp deve passar por `backend/app/services/whatsapp_service.py` ou serviço equivalente centralizado.
- Twilio deve ser configurado por variáveis de ambiente; nunca hardcode de token, SID ou telefone.
- Reutilize models e services existentes antes de criar estruturas paralelas.
- Endpoints novos devem entrar em `backend/app/api/v1/` e manter o padrão de schemas/services/repositories já usado no projeto.
- Alterações de banco precisam de migration versionada.
- Fluxos públicos devem validar CPF, telefone, cupom, resgate e rate limit no servidor.

---

## 5. Registro das Specs

| ID | Funcionalidade | Status Atual | Prioridade | Contrato Principal |
|---|---|---|---|---|
| JR-01 | Cupom Amigo | 🟡 Backend ✅ | Alta | Código único, desconto para indicado, +50 pontos para indicador no checkout do indicado |
| JR-02 | Benefícios dos Níveis | 🟡 Backend ✅ | Alta | Bônus percentual aplicado ao crédito de pontos e auditado na transação |
| JR-03 | Barras de Progresso | 🟡 Backend ✅ | Alta | API de loyalty retorna saldo, nível, próximo nível e progresso de prêmios |
| JR-04 | Aviso de Prêmio Próximo | 🟡 Backend ✅ WhatsApp ✅ | Média | Detectar cliente perto de prêmio, enviar WhatsApp e deduplicar |
| JR-05 | Mensagem Pós Check-out | 🟡 Backend ✅ WhatsApp ✅ | Média | Toda transação de pontos por checkout dispara mensagem com saldo atualizado |
| JR-06 | Som Check-out | 🟡 Backend ✅ | Média | Endpoint de alertas pendentes, marcação como visto e payload para painel |
| JR-07 | Invalidar Códigos | 🟡 Backend ✅ | Alta | Ciclo de vida consistente para cupons e códigos de resgate |
| JR-08 | Remover Suítes Reservadas | 🟡 Backend ✅ | Alta | Disponibilidade exclui quartos com sobreposição de datas |
| JR-09 | Gerador de Cupons | 🟡 Backend ✅ | Média | Admin cria, lista, desativa e mede cupons comuns/influencer |
| JR-10 | Confirmação Check-in Admin | ✅ | Média | Aprovação por código `CHK-*`, WhatsApp admin e invalidação pós-uso |
| JR-11 | Autenticar Cadastro | ✅ | Alta | CPF/customer + OTP WhatsApp antes de liberar reserva |

---

## 6. Contratos por Funcionalidade

### JR-01 - Cupom Amigo

**Entrada esperada**

- `POST /api/v1/referrals/generate`
- `GET /api/v1/referrals/{code}`
- `POST /api/v1/referrals/apply-to-reservation`

**Critérios de aceite**

- Gera código único por cliente ou reutiliza ativo de forma previsível.
- Valida status ativo, validade e limite de uso.
- Indicado recebe o benefício oficial da primeira reserva.
- Indicador recebe +50 pontos somente quando a reserva do indicado virar checkout confirmado.
- O mesmo indicado não pode gerar pontos repetidos para o mesmo indicador.
- Uso fica auditado em `CupomUso`/`Indicacao` ou equivalente.

**Testes mínimos**

- gerar cupom;
- validar cupom ativo;
- rejeitar expirado/max uso;
- aplicar na reserva;
- checkout do indicado credita +50 ao indicador uma única vez.

### JR-02 - Benefícios dos Níveis

**Contrato**

- O backend calcula pontos base.
- O backend consulta nível atual do cliente.
- O backend aplica `base_points * (1 + bonus_percentual / 100)`.
- A transação registra pontos base, bônus percentual e pontos finais em metadata/campos auditáveis.

**Critérios de aceite**

- Essência: 0% de bônus.
- Experiência: 20% de bônus.
- Real: 40% de bônus.
- O frontend pode exibir estimativa, mas o crédito final vem do backend.

**Testes mínimos**

- reserva R$500 em Essência gera 50 pontos;
- reserva R$500 em Experiência gera 60 pontos;
- reserva R$500 em Real gera 70 pontos;
- histórico permite auditar o bônus aplicado.

### JR-03 - Barras de Progresso

**Endpoint alvo**

`GET /api/v1/customers/{cpf}/loyalty`

**Payload mínimo**

```json
{
  "customer_name": "João da Silva",
  "redeemable_points": 72,
  "lifetime_points": 2150,
  "current_level": { "name": "Experiência", "min_points": 50, "bonus_percentual": 20 },
  "next_level": { "name": "Real", "min_points": 90, "bonus_percentual": 40 },
  "rewards_unlocked": 2,
  "rewards_total": 4
}
```

**Critérios de aceite**

- Frontend calcula barra de nível com dados reais.
- Frontend calcula barra de prêmios com `rewards_unlocked / rewards_total`.
- Sem fallback visual que pareça dado real quando a API falhar.

### JR-04 - Aviso de Prêmio Próximo

**Contrato**

- Detectar clientes cujo próximo prêmio esteja dentro do threshold configurado.
- Enviar WhatsApp com nome, prêmio, saldo, pontos faltantes e link de consulta.
- Deduplicar para não enviar mais de 1 vez por cliente/prêmio/dia.

**Critérios de aceite**

- Pode rodar por job, command ou endpoint administrativo protegido.
- Usa `WhatsAppService`.
- Falha de WhatsApp não quebra crédito de pontos.

### JR-05 - Mensagem Pós Check-out

**Contrato**

- Toda liberação de pontos por check-out dispara mensagem.
- Mensagem contém pontos ganhos, bônus aplicado, saldo novo e link de progresso.
- O disparo deve estar perto da criação da transação de pontos, não preso a uma única tela.

**Critérios de aceite**

- Reprocessamento não envia mensagem duplicada.
- Teste cobre checkout com e sem bônus de nível.

### JR-06 - Som Check-out

**Endpoint alvo**

`GET /api/v1/checkout-alerts/pending`

**Payload mínimo**

```json
{
  "alerts": [
    {
      "reservation_id": "res-123",
      "room": "201",
      "guest_name": "João da Silva",
      "checkout_at": "2026-06-05T11:00:00-03:00",
      "viewed": false
    }
  ]
}
```

**Critérios de aceite**

- Endpoint retorna apenas checkouts pendentes de alerta.
- Staff consegue marcar como visto.
- Frontend toca som somente após interação permitida pelo navegador ou com fallback visual claro.

### JR-07 - Invalidar Códigos

**Contrato**

- Cupons e códigos de resgate têm status explícito.
- Código expirado não passa em validação.
- Código usado não pode ser reutilizado.
- Ao renovar código de prêmio, o anterior vira `cancelled`.
- Job ou rotina administrativa expira registros vencidos.

**Testes mínimos**

- cupom atinge limite e passa para status final;
- sexta tentativa falha quando `max_uses = 5`;
- código de resgate vencido vira inválido;
- renovar cancela código anterior.

### JR-08 - Remover Suítes Reservadas

**Endpoint alvo**

`GET /api/v1/availability?checkin=YYYY-MM-DD&checkout=YYYY-MM-DD&suite_type=REAL`

**Critérios de aceite**

- Exclui quartos com qualquer sobreposição no intervalo.
- Não exclui quartos cuja reserva termina no dia do novo check-in.
- Não exclui quartos cuja reserva começa no dia do novo check-out.
- Query deve considerar status de reserva que realmente bloqueia disponibilidade.

### JR-09 - Gerador de Cupons

**Endpoints alvo**

- `POST /api/v1/admin/coupons/generate`
- `GET /api/v1/admin/coupons`
- `GET /api/v1/admin/coupons/{code}`
- `PUT /api/v1/admin/coupons/{code}`
- `DELETE /api/v1/admin/coupons/{code}` ou desativação equivalente

**Critérios de aceite**

- Admin cria cupom percentual ou valor fixo.
- Admin define validade, limite de uso e status.
- Uso é rastreado por reserva/cliente.
- Cupom influencer guarda origem, link e base para comissão.
- Dashboard retorna usos e valor estimado de comissão quando aplicável.

**Status backend**

- ✅ `POST /api/v1/admin/coupons/generate`
- ✅ `GET /api/v1/admin/coupons`
- ✅ `GET /api/v1/admin/coupons/{code}`
- ✅ `PUT /api/v1/admin/coupons/{code}`
- ✅ `DELETE /api/v1/admin/coupons/{code}`
- ✅ Campos `influencer_nome` e `commission_percentual` versionados por migration.
- ✅ Reserva pública valida/aplica cupom via `cupom_codigo`.

### JR-10 - Confirmação Check-in Admin

**Endpoints alvo**

- `POST /api/v1/checkins/request-cash-approval`
- `POST /api/v1/checkins/{code}/approve`

**Critérios de aceite**

- Código `CHK-*` expira em 30 minutos.
- WhatsApp para admin contém reserva, cliente, quarto, valor e link de aprovação.
- Aprovação valida código, autorização e expiração.
- Código aprovado não pode ser usado de novo.

**Status**

- ✅ Backend cria/aprova código CHK protegido.
- ✅ Backend lista pendências/histórico em `GET /api/v1/checkins/cash-approvals`.
- ✅ Frontend de recepção solicita CHK, lista pendências, aprova e exibe histórico.
- ✅ WhatsApp admin enviado pelo serviço central.

### JR-11 - Autenticar Cadastro

**Endpoints alvo**

- `GET /api/v1/customers/{cpf}`
- `POST /api/v1/customers/create`
- `POST /api/v1/auth/otp/generate`
- `POST /api/v1/auth/otp/validate`
- `POST /api/v1/public/reservas`

**Critérios de aceite**

- CPF tem validação de formato e dígitos verificadores.
- OTP tem 6 dígitos, expira em 5 minutos e permite no máximo 3 tentativas.
- Rate limit mínimo: 1 OTP por minuto por CPF/telefone.
- Validação retorna token com escopo `jornada_reserva` suficiente para vincular reserva ao cliente.
- Reserva pública exige `customer_auth_token` válido, não expirado e com CPF igual ao documento do payload.
- Todas as tentativas ficam auditáveis.

---

## 7. Matriz de Testes

| Área | Quando rodar | Comando/validação |
|---|---|---|
| Backend Python | Qualquer mudança em `backend/` | `pytest tests -q` dentro do ambiente do backend |
| API import | Rotas/schemas/services novos | importar `backend.app.main` com env mínima |
| Migration | Mudança de banco | aplicar migrations em banco limpo ou ambiente temporário |
| Frontend build | Mudança em `frontend/` | `npm run build` em `frontend/` |
| Frontend visual | Jornada Real UI | screenshot desktop/mobile e checagem de responsividade |
| WhatsApp | Templates/disparo | teste com mock de Twilio/WhatsAppService e log de payload |

Se algum teste não puder ser executado, registre no checklist ou resposta final o motivo exato.

---

## 8. Política Twilio/WhatsApp

- Usar Twilio para envio real quando credenciais estiverem configuradas.
- Manter envio encapsulado em serviço.
- Variáveis esperadas devem ficar em `.env.production.example`.
- Templates devem ser parametrizados e testáveis sem chamada real.
- Em desenvolvimento, preferir mock/log quando credenciais ausentes.

---

## 9. Política de Atualização do Checklist

Ao finalizar uma implementação:

1. Atualize a linha do resumo executivo.
2. Atualize o `Status Backend`, `Frontend` ou `WhatsApp` da seção específica.
3. Marque subtarefas com `✅`, `🟡` ou `❌`.
4. Acrescente uma frase curta explicando o que foi entregue e o que falta.
5. Não altere estimativa/prioridade sem decisão explícita de produto.

---

## 10. Próxima Ordem Recomendada

Como o backend core ainda está parcial na maioria dos itens, a ordem sugerida para fechar produção é:

1. Integrar/validar o painel frontend de JR-09 nos endpoints `/admin/coupons/*`.
