-- Convite Real: indicacoes por CPF com credito idempotente apos checkout.

CREATE TABLE IF NOT EXISTS indicacoes (
    id SERIAL PRIMARY KEY,
    cliente_indicador_id INTEGER NOT NULL REFERENCES clientes(id),
    cliente_indicado_id INTEGER NULL REFERENCES clientes(id),
    reserva_id INTEGER NULL REFERENCES reservas(id),
    transacao_pontos_id INTEGER NULL REFERENCES transacoes_pontos(id),
    cpf_indicador VARCHAR(14) NOT NULL,
    cpf_indicado VARCHAR(14) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'enviado',
    data_envio TIMESTAMPTZ NOT NULL DEFAULT now(),
    data_reserva TIMESTAMPTZ NULL,
    data_checkin TIMESTAMPTZ NULL,
    data_checkout TIMESTAMPTZ NULL,
    pontos_creditados BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT indicacoes_status_check
        CHECK (status IN ('enviado', 'reservado', 'hospedado', 'creditado')),
    CONSTRAINT indicacoes_sem_autoindicacao_check
        CHECK (regexp_replace(cpf_indicador, '\D', '', 'g') <> regexp_replace(cpf_indicado, '\D', '', 'g')),
    CONSTRAINT indicacoes_cpf_indicado_unique UNIQUE (cpf_indicado),
    CONSTRAINT indicacoes_reserva_unique UNIQUE (reserva_id),
    CONSTRAINT indicacoes_transacao_unique UNIQUE (transacao_pontos_id)
);

CREATE INDEX IF NOT EXISTS idx_indicacoes_indicador ON indicacoes(cliente_indicador_id);
CREATE INDEX IF NOT EXISTS idx_indicacoes_indicado_cliente ON indicacoes(cliente_indicado_id);
CREATE INDEX IF NOT EXISTS idx_indicacoes_status ON indicacoes(status);
CREATE INDEX IF NOT EXISTS idx_indicacoes_pontos_creditados ON indicacoes(pontos_creditados);

