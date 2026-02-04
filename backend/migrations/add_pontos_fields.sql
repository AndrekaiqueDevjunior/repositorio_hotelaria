-- Migration: Add missing fields to transacoes_pontos
-- Date: 2024-12-26
-- Description: Add clienteId, funcionarioId, saldoAnterior, saldoPosterior to support full audit trail

-- Add new columns
ALTER TABLE transacoes_pontos 
  ADD COLUMN IF NOT EXISTS cliente_id INTEGER,
  ADD COLUMN IF NOT EXISTS funcionario_id INTEGER,
  ADD COLUMN IF NOT EXISTS saldo_anterior INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS saldo_posterior INTEGER DEFAULT 0;

-- Populate cliente_id from usuarios_pontos
UPDATE transacoes_pontos tp
SET cliente_id = up.cliente_id
FROM usuarios_pontos up
WHERE tp.usuario_id = up.id
  AND tp.cliente_id IS NULL;

-- Add foreign key constraints
ALTER TABLE transacoes_pontos
  ADD CONSTRAINT fk_transacoes_pontos_cliente
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    ON DELETE CASCADE;

ALTER TABLE transacoes_pontos
  ADD CONSTRAINT fk_transacoes_pontos_funcionario
    FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
    ON DELETE SET NULL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_cliente ON transacoes_pontos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_funcionario ON transacoes_pontos(funcionario_id);
CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_reserva ON transacoes_pontos(reserva_id);

-- Make cliente_id NOT NULL after population
ALTER TABLE transacoes_pontos
  ALTER COLUMN cliente_id SET NOT NULL;

COMMENT ON COLUMN transacoes_pontos.cliente_id IS 'Cliente que recebeu/perdeu pontos';
COMMENT ON COLUMN transacoes_pontos.funcionario_id IS 'Funcionário que realizou ajuste manual (se aplicável)';
COMMENT ON COLUMN transacoes_pontos.saldo_anterior IS 'Saldo antes da transação (auditoria)';
COMMENT ON COLUMN transacoes_pontos.saldo_posterior IS 'Saldo após a transação (auditoria)';
