-- 024_notificacoes_sync.sql
-- Garante que a tabela `notificacoes` exista e esteja em sincronia com o
-- model Prisma `Notificacao` (schema.prisma).
--
-- Contexto: o deploy de producao (docker-compose.production.yml) roda
-- `prisma migrate deploy` (no-op, nao ha pasta prisma/migrations) seguido das
-- migrations SQL idempotentes. Nenhuma dessas migrations criava/mantinha a
-- tabela `notificacoes` -- ao contrario de `hospedagens` (012/022). Resultado:
-- a tabela ficava com o schema do bootstrap original e qualquer find/create do
-- Prisma sobre ela (que faz SELECT de TODAS as colunas do model, incluindo as
-- nao-mapeadas "urlAcao" e "dataExpiracao") podia falhar em producao e derrubar
-- o endpoint /reservas/checkouts-pendentes-alerta com 500.
--
-- Esta migration e idempotente: cria a tabela se faltar e adiciona colunas/
-- indices/FKs que estejam faltando, sem destruir dados existentes.
--
-- ATENCAO: os campos `dataExpiracao` e `urlAcao` NAO tem @map no model, entao
-- o Prisma os consulta com o nome em camelCase exato. Por isso sao criados
-- entre aspas duplas, preservando a caixa.

-- ===== Tabela base (caso nao exista em producao) =====
CREATE TABLE IF NOT EXISTS notificacoes (
    id              SERIAL PRIMARY KEY,
    titulo          TEXT NOT NULL,
    mensagem        TEXT NOT NULL,
    tipo            TEXT NOT NULL DEFAULT 'info',
    categoria       TEXT NOT NULL,
    perfil          TEXT,
    lida            BOOLEAN NOT NULL DEFAULT false,
    data_criacao    TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dataExpiracao" TIMESTAMP(3),
    "urlAcao"       TEXT,
    reserva_id      INTEGER,
    pagamento_id    INTEGER
);

-- ===== Colunas (caso a tabela exista mas esteja dessincronizada) =====
ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS titulo          TEXT;
ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS mensagem        TEXT;
ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS tipo            TEXT NOT NULL DEFAULT 'info';
ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS categoria       TEXT;
ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS perfil          TEXT;
ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS lida            BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS data_criacao    TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS "dataExpiracao" TIMESTAMP(3);
ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS "urlAcao"       TEXT;
ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS reserva_id      INTEGER;
ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS pagamento_id    INTEGER;

-- ===== Indices (alinhados aos @@index do model) =====
CREATE INDEX IF NOT EXISTS notificacoes_reserva_id_idx   ON notificacoes (reserva_id);
CREATE INDEX IF NOT EXISTS notificacoes_pagamento_id_idx ON notificacoes (pagamento_id);
CREATE INDEX IF NOT EXISTS notificacoes_lida_idx         ON notificacoes (lida);
CREATE INDEX IF NOT EXISTS notificacoes_perfil_idx       ON notificacoes (perfil);
CREATE INDEX IF NOT EXISTS notificacoes_categoria_idx    ON notificacoes (categoria);
CREATE INDEX IF NOT EXISTS notificacoes_data_criacao_idx ON notificacoes (data_criacao);

-- ===== Foreign keys (ON DELETE CASCADE, como no model) =====
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'notificacoes_reserva_id_fkey'
    ) THEN
        ALTER TABLE notificacoes
            ADD CONSTRAINT notificacoes_reserva_id_fkey
            FOREIGN KEY (reserva_id) REFERENCES reservas (id) ON DELETE CASCADE;
    END IF;
EXCEPTION WHEN undefined_table OR undefined_column THEN NULL;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'notificacoes_pagamento_id_fkey'
    ) THEN
        ALTER TABLE notificacoes
            ADD CONSTRAINT notificacoes_pagamento_id_fkey
            FOREIGN KEY (pagamento_id) REFERENCES pagamentos (id) ON DELETE CASCADE;
    END IF;
EXCEPTION WHEN undefined_table OR undefined_column THEN NULL;
END $$;
