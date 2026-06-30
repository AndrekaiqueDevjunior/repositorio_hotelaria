-- 025_schema_models_sync.sql
-- Garante existencia idempotente das tabelas do schema Prisma que nenhuma
-- migration anterior criava/mantinha (auditoria schema-vs-migrations):
--   clientes, convite_usos, convites, operacoes_antifraude, pontos_regras,
--   quartos, usuarios, usuarios_pontos, vouchers
-- Gerado a partir do schema canonico (Prisma). Seguro e no-op em tabelas que
-- ja existem corretas: CREATE TABLE IF NOT EXISTS nao altera nada, ADD COLUMN
-- IF NOT EXISTS so adiciona faltantes (nullable-safe), e constraints/indices
-- ficam em DO-blocks guardados que nunca abortam o deploy.

-- ---------- clientes ----------
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL,
    "nomeCompleto" TEXT NOT NULL,
    documento TEXT NOT NULL,
    telefone TEXT,
    email TEXT,
    "dataNascimento" TIMESTAMP(3),
    nacionalidade TEXT,
    "enderecoCompleto" TEXT,
    cidade TEXT,
    estado TEXT,
    pais TEXT,
    observacoes TEXT,
    "tipoHospede" TEXT NOT NULL DEFAULT 'NORMAL'::text,
    "nivelFidelidade" INTEGER NOT NULL DEFAULT 0,
    "totalGasto" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalReservas" INTEGER NOT NULL DEFAULT 0,
    "ultimaVisita" TIMESTAMP(3),
    status TEXT NOT NULL DEFAULT 'ATIVO'::text,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    PRIMARY KEY (id)
);
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS "nomeCompleto" TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS documento TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS telefone TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS "dataNascimento" TIMESTAMP(3);
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS nacionalidade TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS "enderecoCompleto" TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS cidade TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS pais TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS observacoes TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS "tipoHospede" TEXT NOT NULL DEFAULT 'NORMAL'::text;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS "nivelFidelidade" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS "totalGasto" DOUBLE PRECISION NOT NULL DEFAULT 0;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS "totalReservas" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS "ultimaVisita" TIMESTAMP(3);
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'ATIVO'::text;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS "updatedAt" TIMESTAMP(3);
CREATE UNIQUE INDEX IF NOT EXISTS clientes_documento_key ON public.clientes USING btree (documento);
CREATE INDEX IF NOT EXISTS "clientes_tipoHospede_idx" ON public.clientes USING btree ("tipoHospede");
CREATE INDEX IF NOT EXISTS "clientes_nivelFidelidade_idx" ON public.clientes USING btree ("nivelFidelidade");
CREATE INDEX IF NOT EXISTS "clientes_totalGasto_idx" ON public.clientes USING btree ("totalGasto");
CREATE INDEX IF NOT EXISTS clientes_status_idx ON public.clientes USING btree (status);
CREATE INDEX IF NOT EXISTS "clientes_createdAt_idx" ON public.clientes USING btree ("createdAt");
CREATE UNIQUE INDEX IF NOT EXISTS "clientes_nomeCompleto_documento_key" ON public.clientes USING btree ("nomeCompleto", documento);

-- ---------- convite_usos ----------
CREATE TABLE IF NOT EXISTS convite_usos (
    id SERIAL,
    convite_id INTEGER NOT NULL,
    convidado_id INTEGER NOT NULL,
    pontos_ganhos INTEGER NOT NULL,
    created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
ALTER TABLE convite_usos ADD COLUMN IF NOT EXISTS convite_id INTEGER;
ALTER TABLE convite_usos ADD COLUMN IF NOT EXISTS convidado_id INTEGER;
ALTER TABLE convite_usos ADD COLUMN IF NOT EXISTS pontos_ganhos INTEGER;
ALTER TABLE convite_usos ADD COLUMN IF NOT EXISTS created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='convite_usos_convite_id_fkey') THEN
    ALTER TABLE convite_usos ADD CONSTRAINT convite_usos_convite_id_fkey FOREIGN KEY (convite_id) REFERENCES convites(id) ON UPDATE CASCADE ON DELETE RESTRICT;
  END IF;
EXCEPTION WHEN duplicate_object OR undefined_table OR undefined_column OR foreign_key_violation THEN NULL; END $$;
CREATE INDEX IF NOT EXISTS convite_usos_convidado_id_idx ON public.convite_usos USING btree (convidado_id);
CREATE UNIQUE INDEX IF NOT EXISTS convite_usos_convite_id_convidado_id_key ON public.convite_usos USING btree (convite_id, convidado_id);

-- ---------- convites ----------
CREATE TABLE IF NOT EXISTS convites (
    id SERIAL,
    codigo TEXT NOT NULL,
    convidante_id INTEGER NOT NULL,
    usos_maximos INTEGER NOT NULL DEFAULT 5,
    usos_restantes INTEGER NOT NULL DEFAULT 5,
    ativo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP(3),
    PRIMARY KEY (id)
);
ALTER TABLE convites ADD COLUMN IF NOT EXISTS codigo TEXT;
ALTER TABLE convites ADD COLUMN IF NOT EXISTS convidante_id INTEGER;
ALTER TABLE convites ADD COLUMN IF NOT EXISTS usos_maximos INTEGER NOT NULL DEFAULT 5;
ALTER TABLE convites ADD COLUMN IF NOT EXISTS usos_restantes INTEGER NOT NULL DEFAULT 5;
ALTER TABLE convites ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE convites ADD COLUMN IF NOT EXISTS created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE convites ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP(3);
CREATE UNIQUE INDEX IF NOT EXISTS convites_codigo_key ON public.convites USING btree (codigo);
CREATE INDEX IF NOT EXISTS convites_codigo_idx ON public.convites USING btree (codigo);
CREATE INDEX IF NOT EXISTS convites_convidante_id_idx ON public.convites USING btree (convidante_id);
CREATE INDEX IF NOT EXISTS convites_ativo_idx ON public.convites USING btree (ativo);

-- ---------- operacoes_antifraude ----------
CREATE TABLE IF NOT EXISTS operacoes_antifraude (
    id SERIAL,
    pagamento_id INTEGER NOT NULL,
    cliente_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDENTE'::text,
    risk_score INTEGER,
    fatores TEXT,
    analise_em TIMESTAMP(3),
    created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP(3) NOT NULL,
    PRIMARY KEY (id)
);
ALTER TABLE operacoes_antifraude ADD COLUMN IF NOT EXISTS pagamento_id INTEGER;
ALTER TABLE operacoes_antifraude ADD COLUMN IF NOT EXISTS cliente_id INTEGER;
ALTER TABLE operacoes_antifraude ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'PENDENTE'::text;
ALTER TABLE operacoes_antifraude ADD COLUMN IF NOT EXISTS risk_score INTEGER;
ALTER TABLE operacoes_antifraude ADD COLUMN IF NOT EXISTS fatores TEXT;
ALTER TABLE operacoes_antifraude ADD COLUMN IF NOT EXISTS analise_em TIMESTAMP(3);
ALTER TABLE operacoes_antifraude ADD COLUMN IF NOT EXISTS created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE operacoes_antifraude ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP(3);
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='operacoes_antifraude_cliente_id_fkey') THEN
    ALTER TABLE operacoes_antifraude ADD CONSTRAINT operacoes_antifraude_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON UPDATE CASCADE ON DELETE RESTRICT;
  END IF;
EXCEPTION WHEN duplicate_object OR undefined_table OR undefined_column OR foreign_key_violation THEN NULL; END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='operacoes_antifraude_pagamento_id_fkey') THEN
    ALTER TABLE operacoes_antifraude ADD CONSTRAINT operacoes_antifraude_pagamento_id_fkey FOREIGN KEY (pagamento_id) REFERENCES pagamentos(id) ON UPDATE CASCADE ON DELETE RESTRICT;
  END IF;
EXCEPTION WHEN duplicate_object OR undefined_table OR undefined_column OR foreign_key_violation THEN NULL; END $$;

-- ---------- pontos_regras ----------
CREATE TABLE IF NOT EXISTS pontos_regras (
    id SERIAL,
    suite_tipo TEXT NOT NULL,
    diarias_base INTEGER NOT NULL DEFAULT 2,
    rp_por_base INTEGER NOT NULL,
    temporada TEXT,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP(3) NOT NULL,
    PRIMARY KEY (id)
);
ALTER TABLE pontos_regras ADD COLUMN IF NOT EXISTS suite_tipo TEXT;
ALTER TABLE pontos_regras ADD COLUMN IF NOT EXISTS diarias_base INTEGER NOT NULL DEFAULT 2;
ALTER TABLE pontos_regras ADD COLUMN IF NOT EXISTS rp_por_base INTEGER;
ALTER TABLE pontos_regras ADD COLUMN IF NOT EXISTS temporada TEXT;
ALTER TABLE pontos_regras ADD COLUMN IF NOT EXISTS data_inicio DATE;
ALTER TABLE pontos_regras ADD COLUMN IF NOT EXISTS data_fim DATE;
ALTER TABLE pontos_regras ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE pontos_regras ADD COLUMN IF NOT EXISTS created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE pontos_regras ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP(3);
CREATE INDEX IF NOT EXISTS pontos_regras_suite_tipo_ativo_idx ON public.pontos_regras USING btree (suite_tipo, ativo);
CREATE INDEX IF NOT EXISTS pontos_regras_data_inicio_data_fim_idx ON public.pontos_regras USING btree (data_inicio, data_fim);

-- ---------- quartos ----------
CREATE TABLE IF NOT EXISTS quartos (
    id SERIAL,
    numero TEXT NOT NULL,
    tipo_suite TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'LIVRE'::text,
    created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP(3) NOT NULL,
    PRIMARY KEY (id)
);
ALTER TABLE quartos ADD COLUMN IF NOT EXISTS numero TEXT;
ALTER TABLE quartos ADD COLUMN IF NOT EXISTS tipo_suite TEXT;
ALTER TABLE quartos ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'LIVRE'::text;
ALTER TABLE quartos ADD COLUMN IF NOT EXISTS created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE quartos ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP(3);
CREATE UNIQUE INDEX IF NOT EXISTS quartos_numero_key ON public.quartos USING btree (numero);

-- ---------- usuarios ----------
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    senha_hash TEXT NOT NULL,
    perfil TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ATIVO'::text,
    created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP(3) NOT NULL,
    PRIMARY KEY (id)
);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nome TEXT;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS senha_hash TEXT;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS perfil TEXT;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'ATIVO'::text;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP(3);
CREATE UNIQUE INDEX IF NOT EXISTS usuarios_email_key ON public.usuarios USING btree (email);

-- ---------- usuarios_pontos ----------
CREATE TABLE IF NOT EXISTS usuarios_pontos (
    id SERIAL,
    cliente_id INTEGER NOT NULL,
    saldo INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP(3) NOT NULL,
    PRIMARY KEY (id)
);
ALTER TABLE usuarios_pontos ADD COLUMN IF NOT EXISTS cliente_id INTEGER;
ALTER TABLE usuarios_pontos ADD COLUMN IF NOT EXISTS saldo INTEGER NOT NULL DEFAULT 0;
ALTER TABLE usuarios_pontos ADD COLUMN IF NOT EXISTS created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE usuarios_pontos ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP(3);
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='usuarios_pontos_cliente_id_fkey') THEN
    ALTER TABLE usuarios_pontos ADD CONSTRAINT usuarios_pontos_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON UPDATE CASCADE ON DELETE RESTRICT;
  END IF;
EXCEPTION WHEN duplicate_object OR undefined_table OR undefined_column OR foreign_key_violation THEN NULL; END $$;
CREATE UNIQUE INDEX IF NOT EXISTS usuarios_pontos_cliente_id_key ON public.usuarios_pontos USING btree (cliente_id);

-- ---------- vouchers ----------
CREATE TABLE IF NOT EXISTS vouchers (
    id SERIAL,
    codigo TEXT NOT NULL,
    reserva_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'EMITIDO'::text,
    data_emissao TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    emitido_por INTEGER,
    checkin_realizado_em TIMESTAMP(3),
    checkin_realizado_por INTEGER,
    checkout_realizado_em TIMESTAMP(3),
    checkout_realizado_por INTEGER,
    observacoes TEXT,
    created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP(3) NOT NULL,
    PRIMARY KEY (id)
);
ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS codigo TEXT;
ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS reserva_id INTEGER;
ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'EMITIDO'::text;
ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS data_emissao TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS emitido_por INTEGER;
ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS checkin_realizado_em TIMESTAMP(3);
ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS checkin_realizado_por INTEGER;
ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS checkout_realizado_em TIMESTAMP(3);
ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS checkout_realizado_por INTEGER;
ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS observacoes TEXT;
ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP(3);
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='vouchers_reserva_id_fkey') THEN
    ALTER TABLE vouchers ADD CONSTRAINT vouchers_reserva_id_fkey FOREIGN KEY (reserva_id) REFERENCES reservas(id) ON UPDATE CASCADE ON DELETE RESTRICT;
  END IF;
EXCEPTION WHEN duplicate_object OR undefined_table OR undefined_column OR foreign_key_violation THEN NULL; END $$;
CREATE UNIQUE INDEX IF NOT EXISTS vouchers_codigo_key ON public.vouchers USING btree (codigo);
CREATE UNIQUE INDEX IF NOT EXISTS vouchers_reserva_id_key ON public.vouchers USING btree (reserva_id);
CREATE INDEX IF NOT EXISTS vouchers_codigo_idx ON public.vouchers USING btree (codigo);
CREATE INDEX IF NOT EXISTS vouchers_status_idx ON public.vouchers USING btree (status);
CREATE INDEX IF NOT EXISTS vouchers_data_emissao_idx ON public.vouchers USING btree (data_emissao);

