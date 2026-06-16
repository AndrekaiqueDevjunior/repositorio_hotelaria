#!/usr/bin/env bash
# Seed de desenvolvimento: quartos + tarifas
# Uso: bash seed_dev.sh [BASE_URL]
set -euo pipefail

BASE="${1:-http://localhost:18000}"
COOKIE=/tmp/hotel_cookies.txt

echo "=== Hotel Real Cabo Frio - Seed Dev ==="
echo "Backend: $BASE"

# ── Login ────────────────────────────────────────────────────────────────────
echo ""
echo "--- Login ---"
curl -s -c "$COOKIE" -X POST "$BASE/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@hotelreal.com.br","password":"Admin123!"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK:', d.get('message','?'))"

# ── Quartos ──────────────────────────────────────────────────────────────────
echo ""
echo "--- Quartos ---"

criar_quarto() {
  local NUM=$1 TIPO=$2
  RESP=$(curl -s -b "$COOKIE" -X POST "$BASE/api/v1/quartos" \
    -H "Content-Type: application/json" \
    -d "{\"numero\":\"$NUM\",\"tipo_suite\":\"$TIPO\",\"status\":\"LIVRE\"}")
  echo "$RESP" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if 'id' in d:
    print(f'  ✓ Quarto {d[\"numero\"]} - {d[\"tipo_suite\"]}')
elif 'detail' in d:
    print(f'  ~ Quarto $NUM: {d[\"detail\"]}')
else:
    print(f'  ? $NUM: {d}')
" 2>/dev/null || echo "  ~ $NUM: já existe ou erro"
}

# Standard (piso 1)
criar_quarto "101" "STANDARD"
criar_quarto "102" "STANDARD"
criar_quarto "103" "STANDARD"

# Dupla (piso 1)
criar_quarto "104" "DUPLA"
criar_quarto "105" "DUPLA"

# Luxo (piso 2)
criar_quarto "201" "LUXO"
criar_quarto "202" "LUXO"
criar_quarto "203" "LUXO"

# Luxo 2º (piso 2)
criar_quarto "204" "LUXO 2º"
criar_quarto "205" "LUXO 2º"

# Luxo 3º (piso 3)
criar_quarto "301" "LUXO 3º"
criar_quarto "302" "LUXO 3º"

# Luxo 4º EC (piso 3)
criar_quarto "303" "LUXO 4º EC"

# Master (piso 4)
criar_quarto "401" "MASTER"
criar_quarto "402" "MASTER"

# Real (piso 5 - top)
criar_quarto "501" "REAL"

# Suite (piso 5 - top)
criar_quarto "502" "SUITE"

# ── Tarifas ──────────────────────────────────────────────────────────────────
echo ""
echo "--- Tarifas (válidas hoje até 31/12/2027) ---"

criar_tarifa() {
  local TIPO=$1 PRECO=$2 TEMP=$3
  RESP=$(curl -s -b "$COOKIE" -X POST "$BASE/api/v1/tarifas" \
    -H "Content-Type: application/json" \
    -d "{
      \"suite_tipo\": \"$TIPO\",
      \"temporada\": \"$TEMP\",
      \"data_inicio\": \"2026-01-01\",
      \"data_fim\": \"2027-12-31\",
      \"preco_diaria\": $PRECO,
      \"ativo\": true
    }")
  echo "$RESP" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if 'id' in d:
    print(f'  ✓ {d[\"suite_tipo\"]} R\$ {float(d[\"preco_diaria\"]):.0f}/diária ({d[\"temporada\"]})')
elif 'detail' in d:
    print(f'  ~ $TIPO: {d[\"detail\"]}')
" 2>/dev/null || echo "  ~ $TIPO: erro"
}

criar_tarifa "STANDARD"    "280"  "BASE"
criar_tarifa "DUPLA"       "380"  "BASE"
criar_tarifa "LUXO"        "450"  "BASE"
criar_tarifa "LUXO 2º"     "480"  "BASE"
criar_tarifa "LUXO 3º"     "500"  "BASE"
criar_tarifa "LUXO 4º EC"  "530"  "BASE"
criar_tarifa "MASTER"      "680"  "BASE"
criar_tarifa "REAL"        "850"  "BASE"
criar_tarifa "SUITE"       "950"  "BASE"

# Tarifas alta temporada (verão + carnaval)
criar_tarifa "STANDARD"    "420"  "ALTA"
criar_tarifa "DUPLA"       "560"  "ALTA"
criar_tarifa "LUXO"        "680"  "ALTA"
criar_tarifa "MASTER"      "980"  "ALTA"
criar_tarifa "REAL"        "1250" "ALTA"
criar_tarifa "SUITE"       "1400" "ALTA"

# ── Resumo ───────────────────────────────────────────────────────────────────
echo ""
echo "--- Resumo ---"
curl -s -b "$COOKIE" "$BASE/api/v1/quartos" \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
quartos=d.get('quartos',d) if isinstance(d,dict) else d
print(f'Total quartos: {len(quartos)}')
tipos={}
for q in quartos:
    t=q.get('tipo_suite','?')
    tipos[t]=tipos.get(t,0)+1
for t,n in sorted(tipos.items()):
    print(f'  {t}: {n}')
"

curl -s -b "$COOKIE" "$BASE/api/v1/tarifas" \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Total tarifas: {len(d)}')
"

echo ""
echo "=== Seed concluído! ==="
echo "Acesse: http://localhost:3000/reservar para testar"
