-- Migration: Adicionar colunas faltantes - 2026-02-04
-- Autor: Sistema Hotel Real Cabo Frio
-- Descrição: Adiciona colunas que estavam faltando no banco de dados

-- Adicionar coluna foto_url na tabela funcionarios
ALTER TABLE funcionarios ADD COLUMN IF NOT EXISTS foto_url TEXT;

-- Adicionar coluna primeiro_acesso na tabela funcionarios  
ALTER TABLE funcionarios ADD COLUMN IF NOT EXISTS primeiro_acesso BOOLEAN DEFAULT true;

-- Adicionar coluna status_pagamento na tabela pagamentos
ALTER TABLE pagamentos ADD COLUMN IF NOT EXISTS status_pagamento TEXT DEFAULT 'PENDENTE';

-- Atualizar registros existentes com valores padrão
UPDATE funcionarios SET foto_url = NULL WHERE foto_url IS NULL;
UPDATE funcionarios SET primeiro_acesso = true WHERE primeiro_acesso IS NULL;
UPDATE pagamentos SET status_pagamento = 'PENDENTE' WHERE status_pagamento IS NULL;

-- Adicionar comentários nas colunas
COMMENT ON COLUMN funcionarios.foto_url IS 'URL da foto do funcionário';
COMMENT ON COLUMN funcionarios.primeiro_acesso IS 'Indica se é o primeiro acesso do funcionário';
COMMENT ON COLUMN pagamentos.status_pagamento IS 'Status do pagamento (PENDENTE, PAGO, CANCELADO, etc.)';

-- Log da migração
INSERT INTO auditoria (tabela, operacao, descricao, funcionario_id, created_at) 
VALUES ('migracoes', 'UPDATE', 'Migration 2026-02-04: Adicionar colunas faltantes', 1, NOW())
ON CONFLICT DO NOTHING;

COMMIT;

-- Verificação
SELECT 'Migration 2026-02-04 aplicada com sucesso!' as status;
