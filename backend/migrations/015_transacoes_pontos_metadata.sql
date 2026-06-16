-- Jornada Real: metadata estruturada para auditoria de transacoes de pontos.

ALTER TABLE transacoes_pontos
    ADD COLUMN IF NOT EXISTS metadata JSONB;

COMMENT ON COLUMN transacoes_pontos.metadata IS
    'Dados estruturados de auditoria da Jornada Real, como pontos base, bonus de nivel e calculo final.';
