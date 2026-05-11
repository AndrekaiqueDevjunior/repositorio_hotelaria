-- Campos operacionais para reserva, voucher, check-in e check-out

ALTER TABLE reservas
ADD COLUMN IF NOT EXISTS valor_total DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS forma_pagamento VARCHAR(50),
ADD COLUMN IF NOT EXISTS observacoes TEXT,
ADD COLUMN IF NOT EXISTS telefone_contato VARCHAR(30),
ADD COLUMN IF NOT EXISTS email_contato VARCHAR(255);

ALTER TABLE hospedagens
ADD COLUMN IF NOT EXISTS assinatura_checkin TEXT,
ADD COLUMN IF NOT EXISTS assinatura_checkout TEXT,
ADD COLUMN IF NOT EXISTS checkin_dados JSONB,
ADD COLUMN IF NOT EXISTS checkout_dados JSONB;

CREATE INDEX IF NOT EXISTS idx_reservas_origem ON reservas(origem);
CREATE INDEX IF NOT EXISTS idx_reservas_forma_pagamento ON reservas(forma_pagamento);
