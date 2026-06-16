# Skills - Hotel Real / Jornada Real

Índice operacional das skills do projeto. Use este arquivo para escolher o fluxo certo antes de mexer na Jornada Real.

---

## Skill: jornada-real-spec

**Use quando:** criar, alterar, revisar ou concluir qualquer item da `JORNADA_REAL_FEATURES_CHECKLIST.md`.

**Entradas**

- ID da funcionalidade (`JR-01` a `JR-11`).
- Status atual no checklist.
- Contrato em `JORNADA_REAL_SPEC_DRIVEN_DEVELOPMENT.md`.

**Passos**

1. Leia a seção correspondente no checklist.
2. Leia o contrato do mesmo ID no spec.
3. Liste campos, endpoints, validações, efeitos colaterais e testes necessários.
4. Implemente somente o escopo daquele ID, salvo dependência explícita.
5. Rode testes relevantes.
6. Atualize checklist com status real.

**Pronto quando**

- Critérios de aceite do spec estão atendidos.
- Testes foram executados ou impedimento foi documentado.
- Checklist foi atualizado sem mascarar pendências.

---

## Skill: jornada-real-backend

**Use quando:** a tarefa envolver pontos, cupons, resgate, disponibilidade, check-in, OTP, Twilio ou WhatsApp.

**Passos**

1. Comece pelo contrato de API.
2. Verifique models/services existentes.
3. Adicione schema de request/response quando necessário.
4. Implemente service antes de rota quando houver regra de negócio.
5. Garanta que efeitos financeiros/pontos sejam calculados no servidor.
6. Adicione teste unitário ou teste de rota.
7. Atualize migrations quando houver mudança de banco.

**Pronto quando**

- Endpoint responde no contrato esperado.
- Validações rejeitam fraude, duplicidade e dados expirados.
- Testes backend passam.

---

## Skill: jornada-real-frontend

**Use quando:** a tarefa envolver telas da Jornada Real, responsividade ou remoção de mocks.

**Telas críticas**

- `/`
- `/consultar`
- `/consultar-pontos`
- `/entrar-jornada-real`
- `/resgate_dos_premios`
- `/nivel_jornada_real`
- `/reservar`

**Passos**

1. Leia `JORNADA_REAL_SKILLS.md` para o playbook prático.
2. Troque mock por API real somente se o contrato backend estiver pronto.
3. Adicione loading, erro e estado vazio.
4. Garanta mobile e desktop sem sobreposição.
5. Rode build e validação visual quando tocar layout.

**Pronto quando**

- Não há dado fake apresentado como saldo/código real.
- Desktop e mobile estão utilizáveis.
- Fluxo principal funciona com API ou erro claro.

---

## Skill: jornada-real-qa

**Use quando:** validar uma entrega antes de marcar `✅`.

**Passos**

1. Monte cenário feliz.
2. Monte cenário de erro ou fraude.
3. Teste limite: expirado, usado, saldo insuficiente, CPF inválido ou reserva sobreposta.
4. Confirme payload da API.
5. Confirme checklist atualizado.

**Pronto quando**

- Existe evidência de teste.
- Pendências estão marcadas como `🟡` ou `❌`.
- Nenhum item parcial foi promovido para completo sem prova.

---

## Skill: jornada-real-twilio

**Use quando:** houver envio de WhatsApp/SMS, OTP, aviso de prêmio, pós-checkout ou aprovação admin.

**Passos**

1. Use serviço central de WhatsApp.
2. Configure variáveis em `.env.production.example`.
3. Faça template parametrizado.
4. Teste sem chamada real quando credenciais estiverem ausentes.
5. Garanta dedupe/rate limit conforme o contrato.

**Pronto quando**

- Nenhum token está hardcoded.
- Payload pode ser testado por mock/log.
- Falha de envio não corrompe pontos, reserva ou check-in.

---

## Referências

- Spec central: `JORNADA_REAL_SPEC_DRIVEN_DEVELOPMENT.md`
- Checklist/status: `JORNADA_REAL_FEATURES_CHECKLIST.md`
- Playbook prático: `JORNADA_REAL_SKILLS.md`
- Roteiro por função: `JORNADA_REAL_LEITURA_IA.md`
