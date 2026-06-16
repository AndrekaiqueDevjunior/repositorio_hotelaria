# AGENTS.md

@/home/andre-kaique/.codex/RTK.md

## Projeto

Este repositório contém o sistema Hotel Real Cabo Frio e a Jornada Real. Para qualquer tarefa da Jornada Real, trabalhe com spec driven development.

## Leitura Obrigatória

Antes de implementar ou revisar uma funcionalidade Jornada Real, leia:

1. `JORNADA_REAL_FEATURES_CHECKLIST.md`
2. `JORNADA_REAL_SPEC_DRIVEN_DEVELOPMENT.md`
3. `JORNADA_REAL_SKILLS.md`
4. `JORNADA_REAL_LEITURA_IA.md`, se precisar separar trilha Backend/Frontend/QA/PM/IA

## Protocolo Spec Driven

- Identifique o ID da funcionalidade (`JR-01` a `JR-11`) antes de alterar código.
- Use `JORNADA_REAL_SPEC_DRIVEN_DEVELOPMENT.md` como contrato de campos, endpoints, validações e critérios de aceite.
- Comece pelo backend quando houver regra de negócio, pontos, cupons, resgate, autenticação ou WhatsApp.
- Só marque `✅` na checklist depois de teste ou validação objetiva.
- Use `🟡` quando houver equivalente funcional, mas faltar parte do contrato final.
- Escreva exatamente o que falta quando marcar parcial.

## Backend

- Pontos, bônus, saldo, resgate, estoque, desconto, cupom e OTP devem ser validados no backend.
- Não confie em valores enviados pelo frontend para conceder pontos, desconto ou autorização.
- Reutilize services, schemas e models existentes antes de criar abstrações novas.
- Endpoints novos devem seguir o padrão de `backend/app/api/v1/`.
- Mudanças de banco precisam de migration versionada.
- Twilio/WhatsApp deve passar por `backend/app/services/whatsapp_service.py` ou serviço central equivalente.

## Frontend

- Remova mocks que possam parecer dados reais para o usuário.
- Quando a API falhar, mostre estado de erro/carregamento claro.
- Jornada Real deve funcionar em mobile e desktop.
- Teste responsividade nas telas críticas: `/`, `/consultar-pontos`, `/resgate_dos_premios`, `/entrar-jornada-real` e `/reservar`.

## Checklist

Ao terminar uma tarefa Jornada Real:

- atualize o resumo executivo;
- atualize a seção da funcionalidade;
- registre o status real de Backend, Frontend e WhatsApp;
- cite testes rodados ou motivo de não execução.
