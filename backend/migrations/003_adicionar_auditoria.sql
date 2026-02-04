-- Migration 003: Adicionar sistema de auditoria
-- Registra quem fez o quê, quando e como

-- Criar tabela de auditoria
CREATE TABLE IF NOT EXISTS auditorias (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    entidade VARCHAR(100) NOT NULL,
    entidade_id VARCHAR(50) NOT NULL,
    acao VARCHAR(50) NOT NULL,
    payload_resumo TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_auditorias_usuario_id ON auditorias(usuario_id);
CREATE INDEX IF NOT EXISTS idx_auditorias_entidade ON auditorias(entidade);
CREATE INDEX IF NOT EXISTS idx_auditorias_entidade_id ON auditorias(entidade_id);
CREATE INDEX IF NOT EXISTS idx_auditorias_acao ON auditorias(acao);
CREATE INDEX IF NOT EXISTS idx_auditorias_created_at ON auditorias(created_at);

-- Adicionar relação na tabela usuarios (se não existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'usuarios' 
        AND column_name = 'auditoria_id'
    ) THEN
        -- A relação será gerenciada pelo Prisma
        NULL;
    END IF;
END $$;

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_auditorias_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER auditorias_updated_at_trigger
    BEFORE UPDATE ON auditorias
    FOR EACH ROW
    EXECUTE FUNCTION update_auditorias_updated_at();

-- Inserir logs iniciais do sistema
INSERT INTO auditorias (usuario_id, entidade, entidade_id, acao, payload_resumo, ip_address, user_agent)
SELECT 
    id,
    'USUARIO',
    id::text,
    'MIGRATION',
    'Sistema de auditoria implementado',
    '127.0.0.1',
    'Migration Script'
FROM usuarios 
WHERE perfil = 'ADMIN'
LIMIT 1;

-- Log da migration
INSERT INTO auditorias (usuario_id, entidade, entidade_id, acao, payload_resumo, ip_address, user_agent)
VALUES (
    0,
    'SYSTEM',
    'MIGRATION_003',
    'CREATE',
    'Sistema de auditoria implementado com sucesso',
    '127.0.0.1',
    'Migration Script'
);

COMMIT;
