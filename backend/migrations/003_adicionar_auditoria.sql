-- Migration 003: Adicionar sistema de auditoria
-- Registra quem fez o que, quando e como

BEGIN;

-- Criar tabela de auditoria (modelo atual)
CREATE TABLE IF NOT EXISTS auditorias (
    id SERIAL PRIMARY KEY,
    funcionario_id INTEGER NOT NULL,
    entidade VARCHAR(100) NOT NULL,
    entidade_id VARCHAR(50) NOT NULL,
    acao VARCHAR(50) NOT NULL,
    payload_resumo TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Garantir coluna funcionario_id (caso tabela exista sem ela)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'auditorias'
          AND column_name = 'funcionario_id'
    ) THEN
        ALTER TABLE auditorias ADD COLUMN funcionario_id INTEGER;
    END IF;
END $$;

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_auditorias_funcionario_id ON auditorias(funcionario_id);
CREATE INDEX IF NOT EXISTS idx_auditorias_entidade ON auditorias(entidade);
CREATE INDEX IF NOT EXISTS idx_auditorias_entidade_id ON auditorias(entidade_id);
CREATE INDEX IF NOT EXISTS idx_auditorias_acao ON auditorias(acao);
CREATE INDEX IF NOT EXISTS idx_auditorias_created_at ON auditorias(created_at);

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_auditorias_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS auditorias_updated_at_trigger ON auditorias;
CREATE TRIGGER auditorias_updated_at_trigger
    BEFORE UPDATE ON auditorias
    FOR EACH ROW
    EXECUTE FUNCTION update_auditorias_updated_at();

-- Inserir logs iniciais do sistema (se existir funcionario admin)
INSERT INTO auditorias (funcionario_id, entidade, entidade_id, acao, payload_resumo, ip_address, user_agent, updated_at)
SELECT
    f.id,
    'FUNCIONARIO',
    f.id::text,
    'MIGRATION',
    'Sistema de auditoria implementado',
    '127.0.0.1',
    'Migration Script', NOW()
FROM funcionarios f
WHERE f.perfil = 'ADMIN'
LIMIT 1;

-- Log da migration (usa primeiro funcionario disponivel)
INSERT INTO auditorias (funcionario_id, entidade, entidade_id, acao, payload_resumo, ip_address, user_agent, updated_at)
SELECT
    f.id,
    'SYSTEM',
    'MIGRATION_003',
    'CREATE',
    'Sistema de auditoria implementado com sucesso',
    '127.0.0.1',
    'Migration Script', NOW()
FROM funcionarios f
ORDER BY f.id
LIMIT 1;

COMMIT;
