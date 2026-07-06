# Guia de Telas — Jornada Real (Hotel Real Cabo Frio)

Onde fica cada tela, o que ela mostra e como o cliente/admin chega nela.
Domínio de produção: `https://hotelrealcabofrio.com`

---

## 🌐 Telas públicas do cliente (Jornada Real)

Todas as telas do cliente são identificadas pelo CPF na URL (`?cpf=...`). O fluxo
normal começa em `/consultar`, que pede o CPF e redireciona com o parâmetro preenchido.

| Tela | URL | O que mostra |
|---|---|---|
| Entrada de CPF | `/consultar` | Cliente digita o CPF para acessar sua jornada |
| **Minha Jornada** (principal) | `/consultar-pontos?cpf=...` | Pontos atuais, barra de nível, barra de prêmios, badge de bônus do nível ("seus pontos valem 2x/4x"), prêmios em destaque e botão **"Convidar amigos — Meu Cupom"** |
| **Meu Cupom** 🆕 | `/meu-cupom?cpf=...` | Cupom Convite Real do cliente: código, status ("Cupom ativo · X/5 usos", validade), botão **Compartilhar no WhatsApp** (mensagem pronta), **Copiar link**, "Gerar novo cupom" quando expirado/esgotado, e histórico de amigos que usaram + pontos ganhos |
| Níveis | `/nivel_jornada_real?cpf=...` | Detalhe dos níveis Essência / Experiência / Real e benefícios de cada um |
| **Resgatar Prêmios** | `/resgate_dos_premios?cpf=...` | Catálogo de prêmios para resgate + seção **"Meus resgates"** 🆕 com cada código (ativo / utilizado / expirado / cancelado), validade e botão **"Renovar código"** para códigos vencidos |
| Reservar | `/reservar` | Reserva pública: aceita cupom por link (`?cupom=CODIGO`) ou digitação, autenticação por CPF + OTP no WhatsApp, estimativa de pontos com o multiplicador do nível, e só mostra suítes livres no período |
| Entrar na Jornada | `/entrar-jornada-real` | Cadastro/perfil do cliente no programa |
| Termos | `/termos-jornada-real` | Regulamento do programa |

### Como o cliente navega
1. `/consultar` → digita CPF → cai em `/consultar-pontos`.
2. A barra de navegação inferior leva a: Início, Minha Jornada, Prêmios, Perfil.
3. O botão **"Convidar amigos"** (no card de progresso de prêmios) abre o **Meu Cupom**.
4. O link compartilhado pelo amigo abre `/reservar?cupom=AMIGO...` já com o desconto aplicado.

---

## 🔐 Telas administrativas (exigem login de funcionário)

Login: `/login` (staff). Depois:

| Tela | URL | O que mostra |
|---|---|---|
| Dashboard recepção | `/dashboard` | Operação do dia + **alerta sonoro de checkout** às 11h com quarto/cliente e notificação do navegador |
| **Pontos Admin** | `/pontos-admin` | Painel do programa de pontos, em abas: consulta de saldo/histórico por cliente, ajustes manuais, regras de pontuação, cadastro de prêmios, **gerador de cupons**, promoção "primeiros clientes" e **validação de resgate** (recepção valida/da baixa no código `REAL-...`) |
| Gerador de cupons (aba Cupons) | `/pontos-admin` → aba Cupons | Criar/editar/desativar cupons de desconto e influencer (com comissão), botão **"Copiar link"** rastreado 🆕 e botão **"Detalhes"** 🆕 com métricas: usos, clientes únicos, valor bruto/desconto/líquido, comissão estimada e últimos usos |
| Reservas | `/reservas` | Gestão de reservas, aprovação de check-in em dinheiro (código `CHK-...` via WhatsApp do admin) |

---

## 🔌 Endpoints novos que servem essas telas (referência rápida)

| Endpoint | Uso |
|---|---|
| `GET /api/v1/jornada/meu-cupom?cpf=` | Cupom do cliente (cria o primeiro automaticamente) |
| `POST /api/v1/jornada/meu-cupom/gerar` | Gera novo cupom quando o atual expirou/esgotou |
| `GET /api/v1/jornada/meus-resgates?cpf=` | Lista resgates do cliente com status do código |
| `POST /api/v1/jornada/resgates/{id}/renovar` | Renova código expirado (valida posse por CPF) |
| `GET /api/v1/admin/coupons/{code}` | Detalhes/métricas do cupom para o modal do admin |

---

*Atualizado em 2026-07-06, junto com o fechamento dos itens 1️⃣, 7️⃣ e 9️⃣ do
[checklist de funcionalidades](JORNADA_REAL_FEATURES_CHECKLIST.md).*
