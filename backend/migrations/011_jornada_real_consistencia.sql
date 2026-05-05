-- Jornada Real: travas adicionais de consistencia para ledger e codigos.

CREATE UNIQUE INDEX IF NOT EXISTS idx_transacoes_pontos_reserva_checkout_unique
    ON transacoes_pontos(reserva_id)
    WHERE reserva_id IS NOT NULL
      AND origem IN ('CHECKOUT', 'RESERVA');

CREATE UNIQUE INDEX IF NOT EXISTS idx_transacoes_pontos_reserva_origem_beneficio_unique
    ON transacoes_pontos(reserva_id, origem)
    WHERE reserva_id IS NOT NULL
      AND origem IN ('BONUS_CUPOM', 'CONVITE_REAL');

CREATE INDEX IF NOT EXISTS idx_cupons_amigo_indicador_status
    ON cupons(cliente_indicador_id, status)
    WHERE tipo_campanha = 'CUPOM_AMIGO';
