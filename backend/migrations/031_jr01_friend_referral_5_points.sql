-- JR-01 Cupom Amigo: desconto para indicado e recompensa idempotente do indicador.

-- Cupom Amigo nao concede bonus direto ao indicado; o beneficio dele e o desconto.
UPDATE cupons
SET pontos_bonus = 0
WHERE tipo_campanha = 'CUPOM_AMIGO'
  AND COALESCE(pontos_bonus, 0) <> 0;

-- Garante uma unica recompensa de indicacao por reserva, inclusive entre a
-- origem legada CONVITE_REAL e a nova origem canonica FRIEND_REFERRAL.
CREATE UNIQUE INDEX IF NOT EXISTS idx_transacoes_pontos_reserva_referral_unique
    ON transacoes_pontos(reserva_id)
    WHERE reserva_id IS NOT NULL
      AND origem IN ('FRIEND_REFERRAL', 'CONVITE_REAL');

CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_friend_referral_cliente
    ON transacoes_pontos(cliente_id, reserva_id)
    WHERE origem IN ('FRIEND_REFERRAL', 'CONVITE_REAL');
