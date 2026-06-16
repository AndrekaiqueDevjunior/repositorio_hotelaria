-- Jornada Real: aprovacoes CHK-* para liberar check-in com pagamento em dinheiro.

CREATE TABLE IF NOT EXISTS checkin_cash_approvals (
    id SERIAL PRIMARY KEY,
    reserva_id INTEGER NOT NULL REFERENCES reservas(id) ON DELETE CASCADE,
    codigo TEXT NOT NULL UNIQUE,
    valor NUMERIC(10, 2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    expira_em TIMESTAMPTZ NOT NULL,
    aprovado_em TIMESTAMPTZ NULL,
    aprovado_por INTEGER NULL REFERENCES funcionarios(id) ON DELETE SET NULL,
    pagamento_id INTEGER NULL REFERENCES pagamentos(id) ON DELETE SET NULL,
    payload JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_checkin_cash_approvals_reserva_id
    ON checkin_cash_approvals(reserva_id);

CREATE INDEX IF NOT EXISTS idx_checkin_cash_approvals_status
    ON checkin_cash_approvals(status);

CREATE INDEX IF NOT EXISTS idx_checkin_cash_approvals_expira_em
    ON checkin_cash_approvals(expira_em);
