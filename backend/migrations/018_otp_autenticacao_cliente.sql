-- Jornada Real: OTP para autenticar cliente antes da reserva publica.
-- Guarda apenas hash do codigo, status, expiracao, tentativas e auditoria basica.

CREATE TABLE IF NOT EXISTS otp_verificacoes (
    id TEXT PRIMARY KEY,
    cliente_id INTEGER NULL REFERENCES clientes(id) ON DELETE SET NULL,
    documento TEXT NOT NULL,
    telefone TEXT NOT NULL,
    codigo_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    tentativas INTEGER NOT NULL DEFAULT 0,
    max_tentativas INTEGER NOT NULL DEFAULT 3,
    expira_em TIMESTAMPTZ NOT NULL,
    validado_em TIMESTAMPTZ NULL,
    ultimo_envio_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip TEXT NULL,
    user_agent TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_otp_verificacoes_cliente_id
    ON otp_verificacoes(cliente_id);

CREATE INDEX IF NOT EXISTS idx_otp_verificacoes_documento
    ON otp_verificacoes(documento);

CREATE INDEX IF NOT EXISTS idx_otp_verificacoes_telefone
    ON otp_verificacoes(telefone);

CREATE INDEX IF NOT EXISTS idx_otp_verificacoes_status
    ON otp_verificacoes(status);

CREATE INDEX IF NOT EXISTS idx_otp_verificacoes_expira_em
    ON otp_verificacoes(expira_em);

CREATE INDEX IF NOT EXISTS idx_otp_verificacoes_ultimo_envio
    ON otp_verificacoes(ultimo_envio_em);
