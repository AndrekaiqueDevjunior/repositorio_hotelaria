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
WHERE tp.usuario_pontos_id = up.id
  AND tp.cliente_id IS NULL;

-- Add foreign key constraints
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_transacoes_pontos_cliente') THEN
    ALTER TABLE transacoes_pontos
      ADD CONSTRAINT fk_transacoes_pontos_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        ON DELETE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_transacoes_pontos_funcionario') THEN
    ALTER TABLE transacoes_pontos
      ADD CONSTRAINT fk_transacoes_pontos_funcionario
        FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
        ON DELETE SET NULL;
  END IF;
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_cliente ON transacoes_pontos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_funcionario ON transacoes_pontos(funcionario_id);
CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_reserva ON transacoes_pontos(reserva_id);

-- Make cliente_id NOT NULL after population
DO $$
DECLARE
  null_count INTEGER;
  v_is_nullable TEXT;
BEGIN
  SELECT is_nullable INTO v_is_nullable
  FROM information_schema.columns
  WHERE table_name = 'transacoes_pontos'
    AND column_name = 'cliente_id';

  IF v_is_nullable = 'YES' THEN
    SELECT COUNT(*) INTO null_count
    FROM transacoes_pontos
    WHERE cliente_id IS NULL;

    IF null_count = 0 THEN
      ALTER TABLE transacoes_pontos
        ALTER COLUMN cliente_id SET NOT NULL;
    END IF;
  END IF;
END $$;

COMMENT ON COLUMN transacoes_pontos.cliente_id IS 'Cliente que recebeu/perdeu pontos';
COMMENT ON COLUMN transacoes_pontos.funcionario_id IS 'Funcionário que realizou ajuste manual (se aplicável)';
COMMENT ON COLUMN transacoes_pontos.saldo_anterior IS 'Saldo antes da transação (auditoria)';
COMMENT ON COLUMN transacoes_pontos.saldo_posterior IS 'Saldo após a transação (auditoria)';
