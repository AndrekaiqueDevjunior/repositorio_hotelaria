-- Cria tabelas cupons e cupons_usos (modelos Cupom/CupomUso em schema.prisma)
-- Faltavam migrations SQL para essas tabelas (so existiam no schema.prisma,
-- nunca foram versionadas como migration -- causava 500 em /api/v1/reservas
-- por TableNotFoundError ao tentar incluir o relacionamento cupom_uso).

CREATE TABLE IF NOT EXISTS cupons (
    id SERIAL PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE,
    descricao TEXT,
    tipo_desconto TEXT NOT NULL,
    valor_desconto NUMERIC(10, 2) NOT NULL,
    pontos_bonus INTEGER,
    min_diarias INTEGER,
    suites_permitidas TEXT,
    data_inicio TIMESTAMP(3) NOT NULL,
    data_fim TIMESTAMP(3) NOT NULL,
    limite_total_usos INTEGER,
    limite_por_cliente INTEGER,
    total_usos INTEGER NOT NULL DEFAULT 0,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    status TEXT NOT NULL DEFAULT 'active',
    tracking_slug TEXT UNIQUE,
    criado_por INTEGER,
    tipo_campanha TEXT,
    influencer_nome TEXT,
    commission_percentual NUMERIC(5, 2),
    cliente_indicador_id INTEGER REFERENCES clientes(id),
    created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cupons_codigo ON cupons(codigo);
CREATE INDEX IF NOT EXISTS idx_cupons_ativo ON cupons(ativo);
CREATE INDEX IF NOT EXISTS idx_cupons_status ON cupons(status);
CREATE INDEX IF NOT EXISTS idx_cupons_data_inicio_fim ON cupons(data_inicio, data_fim);
CREATE INDEX IF NOT EXISTS idx_cupons_tipo_campanha ON cupons(tipo_campanha);
CREATE INDEX IF NOT EXISTS idx_cupons_cliente_indicador_id ON cupons(cliente_indicador_id);

CREATE TABLE IF NOT EXISTS cupons_usos (
    id SERIAL PRIMARY KEY,
    cupom_id INTEGER NOT NULL REFERENCES cupons(id),
    reserva_id INTEGER NOT NULL UNIQUE REFERENCES reservas(id),
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    valor_original NUMERIC(10, 2) NOT NULL,
    valor_desconto NUMERIC(10, 2) NOT NULL,
    valor_final NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cupons_usos_cupom_id ON cupons_usos(cupom_id);
CREATE INDEX IF NOT EXISTS idx_cupons_usos_cliente_id ON cupons_usos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_cupons_usos_created_at ON cupons_usos(created_at);
