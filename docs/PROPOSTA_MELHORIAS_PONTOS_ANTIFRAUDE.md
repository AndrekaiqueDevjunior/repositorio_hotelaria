# PROPOSTAS: Sistema de Pontos e Antifraude - Modelos Realistas

**Consultor**: Arquitetura de Software e Operações Hoteleiras  
**Data**: 03/01/2026  
**Baseline**: Hotéis 4 estrelas + Programas de fidelidade brasileiros

---

## 🎁 SISTEMA DE PONTOS/FIDELIDADE - MODELO APRIMORADO

### SITUAÇÃO ATUAL

**Implementado**:
- ✅ Acúmulo: R$ 10 = 1 ponto
- ✅ Crédito no checkout
- ✅ Histórico de transações
- ✅ Sistema de convites (50 pts indicador + 30 indicado)

**Gaps**:
- ❌ Pontos não têm uso prático (não podem ser resgatados)
- ❌ Sem níveis/tiers
- ❌ Sem benefícios diferenciados
- ❌ Pontos não expiram (risco financeiro)
- ❌ Sem integração com reservas

---

### PROPOSTA 1: SISTEMA DE NÍVEIS (TIERS)

#### Estrutura de Níveis

```
┌─────────────────────────────────────────────────────┐
│              PROGRAMA REAL PLUS                     │
├─────────────────────────────────────────────────────┤
│ 💎 DIAMANTE  │ 10.000+ pts/ano │ VIP               │
│ 🥇 OURO      │ 5.000+ pts/ano  │ Premium           │
│ 🥈 PRATA     │ 2.000+ pts/ano  │ Intermediário     │
│ 🥉 BRONZE    │ 0-1.999 pts/ano │ Básico (padrão)   │
└─────────────────────────────────────────────────────┘
```

#### Benefícios por Nível

| Benefício | Bronze | Prata | Ouro | Diamante |
|-----------|--------|-------|------|----------|
| **Acúmulo de pontos** | 1x | 1.25x | 1.5x | 2x |
| **Early check-in** | - | 13h | 12h | 11h |
| **Late check-out** | - | 13h | 14h | 15h |
| **Upgrade gratuito** | - | Sob disponibilidade | Garantido 1x | Garantido 2x |
| **Desconto direto** | - | 5% | 10% | 15% |
| **Wifi premium** | - | - | ✅ | ✅ |
| **Welcome drink** | - | - | ✅ | ✅ |
| **Estacionamento** | - | - | - | Gratuito |
| **Cancelamento flexível** | 24h | 48h | 72h | Até check-in |
| **Reserva prioritária** | - | - | ✅ | ✅ |
| **Atendimento VIP** | - | - | - | ✅ |

#### Implementação - Schema

```prisma
enum NivelFidelidade {
  BRONZE
  PRATA
  OURO
  DIAMANTE
}

model UsuarioPontos {
  id                    Int      @id @default(autoincrement())
  cliente_id            Int      @unique
  
  // Atual
  pontos_atuais         Int      @default(0)
  pontos_acumulados_total Int    @default(0)
  
  // NOVO: Sistema de níveis
  nivel_atual           NivelFidelidade @default(BRONZE)
  pontos_ano_atual      Int      @default(0)  // Resetado anualmente
  ano_referencia        Int      // Ano do cálculo
  upgrades_disponiveis  Int      @default(0)  // Créditos de upgrade
  
  // NOVO: Expiração
  pontos_expiram_em     DateTime? // Data de expiração mais próxima
  
  // NOVO: Histórico de nível
  historico_niveis      HistoricoNivel[]
  
  cliente               Cliente  @relation(fields: [cliente_id], references: [id])
  updated_at            DateTime @updatedAt
}

model HistoricoNivel {
  id                Int              @id @default(autoincrement())
  usuario_pontos_id Int
  nivel_anterior    NivelFidelidade?
  nivel_novo        NivelFidelidade
  motivo            String           // "UPGRADE_ANUAL", "DOWNGRADE_ANUAL", "BONUS"
  created_at        DateTime         @default(now())
  
  usuario_pontos    UsuarioPontos    @relation(fields: [usuario_pontos_id], references: [id])
}

model TransacaoPontos {
  // ... campos existentes ...
  
  // NOVO: Expiração
  data_expiracao    DateTime?
  expirado          Boolean  @default(false)
  
  // NOVO: Multiplicador de nível
  multiplicador     Decimal  @default(1.0)
}
```

#### Regras de Negócio

**RN-PONTOS-001: Cálculo de Nível Anual**
```python
def calcular_nivel(pontos_ano: int) -> NivelFidelidade:
    if pontos_ano >= 10000:
        return "DIAMANTE"
    elif pontos_ano >= 5000:
        return "OURO"
    elif pontos_ano >= 2000:
        return "PRATA"
    else:
        return "BRONZE"

# Executar todo dia 1º de janeiro
def atualizar_niveis_anuais():
    for usuario in UsuarioPontos.all():
        nivel_novo = calcular_nivel(usuario.pontos_ano_atual)
        
        if nivel_novo != usuario.nivel_atual:
            # Registrar mudança
            HistoricoNivel.create(
                usuario_pontos_id=usuario.id,
                nivel_anterior=usuario.nivel_atual,
                nivel_novo=nivel_novo,
                motivo="UPGRADE_ANUAL" if nivel_novo > nivel_atual else "DOWNGRADE_ANUAL"
            )
        
        # Resetar contador anual
        usuario.pontos_ano_atual = 0
        usuario.nivel_atual = nivel_novo
        usuario.ano_referencia = year(now())
        usuario.save()
```

**RN-PONTOS-002: Multiplicador de Acúmulo**
```python
def creditar_pontos_checkout(reserva_id: int):
    reserva = get_reserva(reserva_id)
    cliente = reserva.cliente
    pontos_usuario = get_usuario_pontos(cliente.id)
    
    # Multiplicador baseado no nível
    multiplicadores = {
        "BRONZE": 1.0,
        "PRATA": 1.25,
        "OURO": 1.5,
        "DIAMANTE": 2.0
    }
    
    mult = multiplicadores[pontos_usuario.nivel_atual]
    
    # Cálculo base: R$ 10 = 1 ponto
    pontos_base = floor(reserva.valor_total / 10)
    pontos_final = floor(pontos_base * mult)
    
    # Creditar
    TransacaoPontos.create(
        cliente_id=cliente.id,
        reserva_id=reserva.id,
        tipo="CREDITO",
        valor=pontos_final,
        origem="CHECKOUT",
        multiplicador=mult,
        data_expiracao=now() + timedelta(days=365),  # 1 ano
        descricao=f"Checkout Reserva #{reserva.id} (Nível {pontos_usuario.nivel_atual})"
    )
```

**RN-PONTOS-003: Expiração de Pontos**
```python
# Job diário
def expirar_pontos_vencidos():
    transacoes_expiradas = TransacaoPontos.find_many(
        where={
            "data_expiracao": {"lte": now()},
            "expirado": False,
            "tipo": "CREDITO"
        }
    )
    
    for transacao in transacoes_expiradas:
        # Debitar pontos expirados
        TransacaoPontos.create(
            cliente_id=transacao.cliente_id,
            tipo="DEBITO",
            valor=transacao.valor,
            origem="EXPIRACAO",
            descricao=f"Expiração de pontos (Transação #{transacao.id})"
        )
        
        transacao.expirado = True
        transacao.save()
        
        # Notificar cliente
        enviar_notificacao(
            cliente_id=transacao.cliente_id,
            tipo="PONTOS_EXPIRADOS",
            mensagem=f"{transacao.valor} pontos expiraram"
        )
```

---

### PROPOSTA 2: RESGATE DE PONTOS

#### Opções de Resgate

```
┌────────────────────────────────────────────────────┐
│         CATÁLOGO DE RESGATES                       │
├────────────────────────────────────────────────────┤
│ 🏨 Desconto em diária      │ 100 pts = R$ 10      │
│ ⬆️  Upgrade de quarto       │ 500 pts              │
│ 🍽️  Café da manhã extra    │ 80 pts               │
│ 🚗 Estacionamento (1 dia)  │ 50 pts               │
│ 🍾 Welcome package         │ 200 pts              │
│ ⏰ Late checkout (+2h)     │ 150 pts              │
│ 🧳 Early checkin (-2h)     │ 150 pts              │
│ 🏖️  Transfer aeroporto      │ 300 pts              │
└────────────────────────────────────────────────────┘
```

#### Schema de Resgates

```prisma
enum TipoResgate {
  DESCONTO_DIARIA
  UPGRADE_QUARTO
  CAFE_EXTRA
  ESTACIONAMENTO
  WELCOME_PACKAGE
  LATE_CHECKOUT
  EARLY_CHECKIN
  TRANSFER
}

model ResgateDisponivel {
  id          Int         @id @default(autoincrement())
  tipo        TipoResgate
  nome        String
  descricao   String
  pontos      Int         // Custo em pontos
  valor_real  Decimal?    // Valor em R$ (referência)
  ativo       Boolean     @default(true)
  estoque     Int?        // NULL = ilimitado
  created_at  DateTime    @default(now())
}

model ResgateRealizado {
  id              Int              @id @default(autoincrement())
  cliente_id      Int
  reserva_id      Int?
  resgate_tipo    TipoResgate
  pontos_gastos   Int
  valor_desconto  Decimal?
  status          String           // PENDENTE, APLICADO, CANCELADO
  aplicado_em     DateTime?
  created_at      DateTime         @default(now())
  
  cliente         Cliente          @relation(fields: [cliente_id], references: [id])
  reserva         Reserva?         @relation(fields: [reserva_id], references: [id])
}
```

#### API de Resgate

```python
# Endpoint: POST /api/v1/pontos/resgatar
@router.post("/resgatar")
async def resgatar_pontos(
    cliente_id: int,
    tipo_resgate: TipoResgate,
    reserva_id: int = None
):
    # 1. Validar saldo
    pontos_usuario = await get_saldo(cliente_id)
    resgate = await db.resgate_disponivel.find_first(
        where={"tipo": tipo_resgate, "ativo": True}
    )
    
    if pontos_usuario.pontos_atuais < resgate.pontos:
        raise HTTPException(400, "Saldo insuficiente")
    
    # 2. Validar estoque
    if resgate.estoque is not None and resgate.estoque <= 0:
        raise HTTPException(400, "Resgate indisponível")
    
    # 3. Validar contexto (se precisa de reserva)
    if tipo_resgate in [TipoResgate.UPGRADE_QUARTO, TipoResgate.LATE_CHECKOUT]:
        if not reserva_id:
            raise HTTPException(400, "Resgate requer reserva ativa")
        
        reserva = await db.reserva.find_unique(where={"id": reserva_id})
        if reserva.status not in ["CONFIRMADA", "HOSPEDADO"]:
            raise HTTPException(400, "Reserva inválida para resgate")
    
    # 4. Debitar pontos
    await ajustar_pontos(
        cliente_id=cliente_id,
        valor=-resgate.pontos,
        tipo="DEBITO",
        origem="RESGATE",
        descricao=f"Resgate: {resgate.nome}"
    )
    
    # 5. Criar registro de resgate
    resgate_realizado = await db.resgate_realizado.create({
        "cliente_id": cliente_id,
        "reserva_id": reserva_id,
        "resgate_tipo": tipo_resgate,
        "pontos_gastos": resgate.pontos,
        "valor_desconto": resgate.valor_real,
        "status": "PENDENTE"
    })
    
    # 6. Aplicar benefício
    if tipo_resgate == TipoResgate.DESCONTO_DIARIA:
        # Gerar cupom de desconto
        await criar_cupom_desconto(cliente_id, resgate.valor_real)
    
    elif tipo_resgate == TipoResgate.UPGRADE_QUARTO:
        # Marcar reserva para upgrade
        await db.reserva.update(
            where={"id": reserva_id},
            data={"upgrade_solicitado": True, "upgrade_resgate_id": resgate_realizado.id}
        )
    
    # 7. Atualizar estoque
    if resgate.estoque is not None:
        await db.resgate_disponivel.update(
            where={"id": resgate.id},
            data={"estoque": resgate.estoque - 1}
        )
    
    return {"success": True, "resgate": resgate_realizado}
```

---

## 🛡️ SISTEMA ANTIFRAUDE - MODELO APRIMORADO

### SITUAÇÃO ATUAL

**Implementado**:
- ✅ Score baseado em regras
- ✅ 6 regras básicas
- ✅ Níveis de risco (BAIXO, MÉDIO, ALTO)
- ✅ Registro de operações

**Gaps**:
- ❌ Sem ação automática (só alerta)
- ❌ Sem validação de documentos
- ❌ Sem análise de IP/device
- ❌ Sem integração bureau de crédito
- ❌ Sem machine learning

---

### PROPOSTA 3: MOTOR ANTIFRAUDE MULTICAMADAS

#### Arquitetura

```
┌─────────────────────────────────────────────────────┐
│         MOTOR ANTIFRAUDE - CAMADAS                  │
├─────────────────────────────────────────────────────┤
│ Camada 1: Validação Básica   │ CPF, Email, Tel     │
│ Camada 2: Análise Comportamental │ Regras atuais │
│ Camada 3: Verificação Externa │ Bureau, Blacklist │
│ Camada 4: Análise Técnica    │ IP, Device, Geo   │
│ Camada 5: Score Final        │ Decisão           │
└─────────────────────────────────────────────────────┘
```

#### Camada 1: Validação Básica

```python
class ValidadorBasico:
    
    async def validar_cpf(self, cpf: str) -> dict:
        """Valida CPF algoritmicamente + consulta Receita"""
        # 1. Validação de formato
        if not self._validar_formato_cpf(cpf):
            return {"valido": False, "motivo": "Formato inválido"}
        
        # 2. Validação de dígitos verificadores
        if not self._validar_digitos_cpf(cpf):
            return {"valido": False, "motivo": "Dígitos verificadores inválidos"}
        
        # 3. CPFs conhecidos como inválidos
        if cpf in ["00000000000", "11111111111", ...]:
            return {"valido": False, "motivo": "CPF bloqueado"}
        
        # 4. Consulta API Receita Federal (opcional, pago)
        try:
            receita = await self._consultar_receita_federal(cpf)
            if receita["situacao"] != "REGULAR":
                return {"valido": False, "motivo": f"CPF {receita['situacao']}"}
        except:
            pass  # API indisponível, seguir sem validação
        
        return {"valido": True}
    
    async def validar_email(self, email: str) -> dict:
        """Valida email (formato + MX + blacklist)"""
        # 1. Formato
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            return {"valido": False, "motivo": "Formato inválido"}
        
        # 2. Domínio descartável (guerrillamail, 10minutemail, etc)
        domain = email.split("@")[1]
        if domain in DOMINIOS_DESCARTAVEIS:
            return {"valido": False, "motivo": "Email descartável não permitido", "score_fraude": +40}
        
        # 3. Verificar MX record
        try:
            mx_records = await self._get_mx_records(domain)
            if not mx_records:
                return {"valido": False, "motivo": "Domínio sem servidor de email"}
        except:
            pass
        
        return {"valido": True}
    
    async def validar_telefone(self, telefone: str, pais: str = "BR") -> dict:
        """Valida telefone (formato + operadora)"""
        # 1. Formato brasileiro
        telefone_limpo = re.sub(r"\D", "", telefone)
        
        if pais == "BR":
            if len(telefone_limpo) not in [10, 11]:  # (11) 98765-4321
                return {"valido": False, "motivo": "Formato inválido"}
            
            # 2. DDD válido
            ddd = telefone_limpo[:2]
            if ddd not in DDDS_VALIDOS_BR:
                return {"valido": False, "motivo": "DDD inválido"}
            
            # 3. Validar número (celular começa com 9)
            if len(telefone_limpo) == 11 and telefone_limpo[2] != "9":
                return {"valido": False, "motivo": "Celular inválido"}
        
        # 4. Opcional: Enviar SMS de verificação
        # codigo = gerar_codigo_6_digitos()
        # await enviar_sms(telefone, f"Código: {codigo}")
        
        return {"valido": True}
```

#### Camada 2: Regras Comportamentais (Aprimoradas)

```python
class MotorRegras:
    
    REGRAS = [
        # Regras existentes
        {"nome": "RESERVAS_RECENTES", "peso": 20, "limite": 3, "periodo_dias": 30},
        {"nome": "TAXA_CANCELAMENTO", "peso": 25, "limite_pct": 30},
        {"nome": "PAGAMENTOS_RECUSADOS", "peso": 30, "limite": 2},
        {"nome": "CANCELAMENTOS_CONSECUTIVOS", "peso": 35, "limite": 2},
        {"nome": "RESERVA_LONGA", "peso": 15, "limite_dias": 30},
        {"nome": "VALOR_ALTO", "peso": 15, "limite_valor": 10000},
        
        # NOVAS REGRAS
        {"nome": "PRIMEIRA_RESERVA", "peso": 10, "descricao": "Cliente novo"},
        {"nome": "VELOCIDADE_RESERVA", "peso": 25, "descricao": "Múltiplas reservas em minutos"},
        {"nome": "DADOS_DUPLICADOS", "peso": 40, "descricao": "Mesmo CPF/cartão em múltiplas contas"},
        {"nome": "HORARIO_SUSPEITO", "peso": 15, "descricao": "Reserva madrugada (2h-6h)"},
        {"nome": "PAIS_ALTO_RISCO", "peso": 20, "descricao": "IP de país com alta fraude"},
        {"nome": "VPN_PROXY", "peso": 25, "descricao": "Uso de VPN/proxy detectado"},
        {"nome": "DEVICE_NOVO", "peso": 10, "descricao": "Dispositivo nunca usado"},
        {"nome": "EMAIL_CRIADO_RECENTE", "peso": 15, "descricao": "Email criado há menos de 7 dias"},
    ]
    
    async def avaliar_velocidade_reserva(self, cliente_id: int) -> int:
        """Detecta criação rápida de múltiplas reservas"""
        reservas_ultimas_2h = await db.reserva.count(
            where={
                "cliente_id": cliente_id,
                "created_at": {"gte": now() - timedelta(hours=2)}
            }
        )
        
        if reservas_ultimas_2h >= 3:
            return 25  # Penalidade
        
        return 0
    
    async def avaliar_dados_duplicados(self, cliente_id: int) -> int:
        """Detecta mesmo CPF/cartão em múltiplas contas"""
        cliente = await db.cliente.find_unique(where={"id": cliente_id})
        
        # Buscar outros clientes com mesmo CPF
        clientes_mesmo_cpf = await db.cliente.count(
            where={
                "cpf": cliente.cpf,
                "id": {"not": cliente_id}
            }
        )
        
        if clientes_mesmo_cpf > 0:
            return 40  # ALTO risco
        
        # Buscar reservas com mesmo cartão (últimos 4 dígitos)
        pagamentos_cliente = await db.pagamento.find_many(
            where={"reserva": {"cliente_id": cliente_id}},
            select={"cielo_payload": True}
        )
        
        for pag in pagamentos_cliente:
            ultimos_4 = pag.cielo_payload.get("card_last_digits")
            if ultimos_4:
                outros_pagamentos = await db.pagamento.count(
                    where={
                        "cielo_payload": {"path": ["card_last_digits"], "equals": ultimos_4},
                        "reserva": {"cliente_id": {"not": cliente_id}}
                    }
                )
                
                if outros_pagamentos > 0:
                    return 30
        
        return 0
    
    async def avaliar_horario_suspeito(self) -> int:
        """Reservas de madrugada são suspeitas"""
        hora_atual = now().hour
        
        if 2 <= hora_atual <= 6:
            return 15
        
        return 0
```

#### Camada 3: Verificação Externa

```python
class IntegracaoExterna:
    
    async def consultar_serasa(self, cpf: str) -> dict:
        """Integração com Serasa Experian (API paga)"""
        # Exemplo de resposta
        return {
            "score_credito": 650,  # 0-1000
            "inadimplente": False,
            "protestos": 0,
            "restricoes": []
        }
    
    async def consultar_blacklist_hotel(self, cpf: str, email: str) -> dict:
        """Consulta blacklist compartilhada entre hotéis"""
        # API hipotética de blacklist hoteleira
        blacklist = await http.get(
            "https://api.hotelblacklist.com.br/v1/check",
            params={"cpf": cpf, "email": email}
        )
        
        return {
            "bloqueado": blacklist["blocked"],
            "motivo": blacklist.get("reason"),
            "hoteis_reportaram": blacklist.get("reports_count", 0)
        }
    
    async def verificar_cep(self, cep: str) -> dict:
        """Valida CEP via ViaCEP"""
        try:
            resp = await http.get(f"https://viacep.com.br/ws/{cep}/json/")
            data = resp.json()
            
            if "erro" in data:
                return {"valido": False}
            
            return {
                "valido": True,
                "cidade": data["localidade"],
                "estado": data["uf"]
            }
        except:
            return {"valido": False}
```

#### Camada 4: Análise Técnica

```python
class AnaliseTecnica:
    
    async def analisar_ip(self, ip: str) -> dict:
        """Geolocalização + detecção VPN/proxy"""
        # Usar serviço como IPQualityScore, MaxMind, IP2Location
        info = await http.get(
            f"https://ipqualityscore.com/api/json/ip/{API_KEY}/{ip}",
            params={"strictness": 1}
        )
        
        return {
            "pais": info["country_code"],
            "cidade": info["city"],
            "vpn": info["vpn"],
            "proxy": info["proxy"],
            "tor": info["tor"],
            "fraud_score": info["fraud_score"],  # 0-100
            "conexao_recente": info["recent_abuse"]
        }
    
    async def gerar_device_fingerprint(self, request) -> str:
        """Cria fingerprint único do dispositivo"""
        # Usar biblioteca como FingerprintJS (frontend)
        # Enviar para backend
        
        fingerprint_data = {
            "user_agent": request.headers.get("User-Agent"),
            "accept_language": request.headers.get("Accept-Language"),
            "screen_resolution": request.json.get("screen_resolution"),
            "timezone": request.json.get("timezone"),
            "plugins": request.json.get("plugins"),
            "canvas_hash": request.json.get("canvas_hash")
        }
        
        # Gerar hash
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_data, sort_keys=True).encode()
        ).hexdigest()
        
        return fingerprint
    
    async def verificar_device_conhecido(self, cliente_id: int, fingerprint: str) -> bool:
        """Verifica se dispositivo já foi usado pelo cliente"""
        historico = await db.device_historico.find_first(
            where={
                "cliente_id": cliente_id,
                "fingerprint": fingerprint
            }
        )
        
        return historico is not None
```

#### Camada 5: Score Final e Decisão

```python
class DecisaoAntifraude:
    
    async def analisar_completo(
        self,
        cliente_id: int,
        reserva_id: int,
        ip: str,
        device_fingerprint: str
    ) -> dict:
        """Análise completa multicamadas"""
        
        score_total = 0
        alertas = []
        recomendacao = ""
        
        # CAMADA 1: Validação básica
        cliente = await db.cliente.find_unique(where={"id": cliente_id})
        
        cpf_valido = await ValidadorBasico().validar_cpf(cliente.cpf)
        if not cpf_valido["valido"]:
            score_total += 50
            alertas.append(f"CPF inválido: {cpf_valido['motivo']}")
        
        email_valido = await ValidadorBasico().validar_email(cliente.email)
        if not email_valido["valido"]:
            score_total += email_valido.get("score_fraude", 20)
            alertas.append(f"Email suspeito: {email_valido['motivo']}")
        
        # CAMADA 2: Regras comportamentais
        motor_regras = MotorRegras()
        score_regras, alertas_regras = await motor_regras.avaliar_todas(cliente_id, reserva_id)
        score_total += score_regras
        alertas.extend(alertas_regras)
        
        # CAMADA 3: Verificações externas
        try:
            serasa = await IntegracaoExterna().consultar_serasa(cliente.cpf)
            if serasa["inadimplente"]:
                score_total += 35
                alertas.append("Cliente inadimplente (Serasa)")
            
            blacklist = await IntegracaoExterna().consultar_blacklist_hotel(
                cliente.cpf, cliente.email
            )
            if blacklist["bloqueado"]:
                score_total += 100  # Bloqueia automaticamente
                alertas.append(f"Cliente em blacklist: {blacklist['motivo']}")
        except:
            # APIs indisponíveis, continuar
            pass
        
        # CAMADA 4: Análise técnica
        ip_info = await AnaliseTecnica().analisar_ip(ip)
        if ip_info["vpn"] or ip_info["proxy"]:
            score_total += 25
            alertas.append("Uso de VPN/proxy detectado")
        
        if ip_info["fraud_score"] > 75:
            score_total += 30
            alertas.append(f"IP com alto score de fraude ({ip_info['fraud_score']})")
        
        device_conhecido = await AnaliseTecnica().verificar_device_conhecido(
            cliente_id, device_fingerprint
        )
        if not device_conhecido:
            score_total += 10
            alertas.append("Dispositivo novo")
        
        # CAMADA 5: Decisão final
        if score_total >= 80:
            nivel_risco = "ALTO"
            recomendacao = "BLOQUEAR - Revisar manualmente antes de aprovar"
        elif score_total >= 40:
            nivel_risco = "MEDIO"
            recomendacao = "REVISAR - Solicitar documentação adicional"
        else:
            nivel_risco = "BAIXO"
            recomendacao = "APROVAR - Monitorar"
        
        # Registrar
        operacao = await db.operacao_antifraude.create({
            "cliente_id": cliente_id,
            "reserva_id": reserva_id,
            "tipo_analise": "COMPLETA",
            "score_risco": score_total,
            "nivel_risco": nivel_risco,
            "regras_ativadas": alertas,
            "recomendacao": recomendacao,
            "ip_origem": ip,
            "device_fingerprint": device_fingerprint
        })
        
        # AÇÃO AUTOMÁTICA
        if nivel_risco == "ALTO":
            # Bloquear reserva
            await db.reserva.update(
                where={"id": reserva_id},
                data={"status": "BLOQUEADO_FRAUDE", "bloqueio_motivo": recomendacao}
            )
            
            # Notificar gerência
            await enviar_alerta_gerencia(
                tipo="FRAUDE_DETECTADA",
                cliente_id=cliente_id,
                reserva_id=reserva_id,
                score=score_total
            )
        
        return {
            "score": score_total,
            "nivel": nivel_risco,
            "alertas": alertas,
            "recomendacao": recomendacao,
            "operacao_id": operacao.id
        }
```

---

## 📊 COMPARAÇÃO: ANTES vs DEPOIS

### Sistema de Pontos

| Funcionalidade | Antes | Depois |
|----------------|-------|--------|
| **Níveis/Tiers** | ❌ Não | ✅ 4 níveis (Bronze → Diamante) |
| **Multiplicadores** | 1x fixo | 1x - 2x (por nível) |
| **Resgate de pontos** | ❌ Não | ✅ 8 opções de resgate |
| **Expiração** | ❌ Eternos | ✅ 12 meses |
| **Benefícios diferenciados** | ❌ Não | ✅ 11 benefícios escalonados |
| **Upgrades automáticos** | ❌ Não | ✅ Por nível/resgate |

### Sistema Antifraude

| Funcionalidade | Antes | Depois |
|----------------|-------|--------|
| **Camadas de análise** | 1 (regras) | 5 (multi-layer) |
| **Validação CPF** | ❌ Não | ✅ Algoritmo + Receita |
| **Validação email** | ❌ Não | ✅ Formato + MX + blacklist |
| **Análise de IP** | ❌ Não | ✅ Geo + VPN/proxy |
| **Device fingerprint** | ❌ Não | ✅ Canvas + UA + plugins |
| **Bureau de crédito** | ❌ Não | ✅ Serasa (opcional) |
| **Ação automática** | ❌ Só alerta | ✅ Bloqueia se ALTO |
| **Regras ativas** | 6 | 14 |

---

## 🎯 ROADMAP DE IMPLEMENTAÇÃO

### Fase 1: Pontos - Níveis (2 semanas)
- [ ] Criar schema de níveis
- [ ] Implementar cálculo anual
- [ ] Migrar pontos existentes
- [ ] UI de exibição de nível
- [ ] Job de atualização anual

### Fase 2: Pontos - Resgates (2 semanas)
- [ ] Criar catálogo de resgates
- [ ] Implementar endpoint de resgate
- [ ] Integrar com reservas (upgrade, early/late)
- [ ] UI de catálogo
- [ ] Testes E2E

### Fase 3: Pontos - Expiração (1 semana)
- [ ] Adicionar data_expiracao
- [ ] Job de expiração diária
- [ ] Notificações pré-expiração (30, 15, 7 dias)
- [ ] Migração de pontos antigos

### Fase 4: Antifraude - Validações Básicas (1 semana)
- [ ] Validador de CPF
- [ ] Validador de email
- [ ] Validador de telefone
- [ ] Integrar em criação de cliente

### Fase 5: Antifraude - Análise Técnica (2 semanas)
- [ ] Integração IP Quality Score
- [ ] Device fingerprinting (frontend)
- [ ] Armazenamento de histórico
- [ ] Dashboard de análises

### Fase 6: Antifraude - Integrações Externas (3 semanas)
- [ ] API Serasa (opcional)
- [ ] Blacklist compartilhada
- [ ] ViaCEP
- [ ] Testes de integração

### Fase 7: Antifraude - Decisões Automáticas (1 semana)
- [ ] Lógica de bloqueio automático
- [ ] Notificações gerência
- [ ] Dashboard de revisão
- [ ] Testes de segurança

**TOTAL**: 12 semanas (3 meses)

---

**FIM DAS PROPOSTAS**
