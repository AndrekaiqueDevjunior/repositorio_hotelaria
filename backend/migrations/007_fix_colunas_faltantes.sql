-- Migration: Adicionar colunas faltantes - 2026-02-04
-- Autor: Sistema Hotel Real Cabo Frio
-- Descricao: Adiciona colunas que estavam faltando no banco de dados

BEGIN;

-- Adicionar coluna foto_url na tabela funcionarios
ALTER TABLE funcionarios ADD COLUMN IF NOT EXISTS foto_url TEXT;

-- Adicionar coluna primeiro_acesso na tabela funcionarios
ALTER TABLE funcionarios ADD COLUMN IF NOT EXISTS primeiro_acesso BOOLEAN DEFAULT true;

-- Adicionar coluna status_pagamento na tabela pagamentos
ALTER TABLE pagamentos ADD COLUMN IF NOT EXISTS status_pagamento TEXT DEFAULT 'PENDENTE';

-- Atualizar registros existentes com valores padrao
UPDATE funcionarios SET foto_url = NULL WHERE foto_url IS NULL;
UPDATE funcionarios SET primeiro_acesso = true WHERE primeiro_acesso IS NULL;
UPDATE pagamentos SET status_pagamento = 'PENDENTE' WHERE status_pagamento IS NULL;

-- Adicionar comentarios nas colunas
COMMENT ON COLUMN funcionarios.foto_url IS 'URL da foto do funcionario';
COMMENT ON COLUMN funcionarios.primeiro_acesso IS 'Indica se e o primeiro acesso do funcionario';
COMMENT ON COLUMN pagamentos.status_pagamento IS 'Status do pagamento (PENDENTE, PAGO, CANCELADO, etc.)';

-- Log da migracao (se tabela auditorias existir)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'auditorias'
    ) THEN
        INSERT INTO auditorias (funcionario_id, entidade, entidade_id, acao, payload_resumo, ip_address, user_agent, updated_at)
        SELECT
            f.id,
            'MIGRACOES',
            '2026-02-04',
            'UPDATE',
            'Migration 2026-02-04: Adicionar colunas faltantes',
            '127.0.0.1',
            'Migration Script',
            NOW()
        FROM funcionarios f
        ORDER BY f.id
        LIMIT 1;
    END IF;
END $$;

COMMIT;

-- Verificacao
SELECT 'Migration 2026-02-04 aplicada com sucesso!' as status;
