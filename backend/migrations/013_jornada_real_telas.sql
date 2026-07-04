-- Jornada Real: regras das 11 telas, pontos pendentes e codigos REAL-######.

ALTER TABLE transacoes_pontos
    ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'liberado';

ALTER TABLE transacoes_pontos
    ADD COLUMN IF NOT EXISTS liberar_em TIMESTAMPTZ;

UPDATE transacoes_pontos
SET status = 'liberado'
WHERE status IS NULL;

CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_status_liberar_em
    ON transacoes_pontos(status, liberar_em);

CREATE TABLE IF NOT EXISTS categorias_premios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    slug VARCHAR(120) NOT NULL UNIQUE,
    descricao TEXT,
    ordem INTEGER NOT NULL DEFAULT 0,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_categorias_premios_ativo_ordem
    ON categorias_premios(ativo, ordem);

ALTER TABLE premios
    ADD COLUMN IF NOT EXISTS categoria_id INTEGER REFERENCES categorias_premios(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_premios_categoria_id
    ON premios(categoria_id);

CREATE TABLE IF NOT EXISTS beneficios_nivel (
    id SERIAL PRIMARY KEY,
    nivel_id INTEGER NOT NULL REFERENCES niveis_fidelidade(id) ON DELETE CASCADE,
    titulo VARCHAR(180) NOT NULL,
    descricao TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_beneficios_nivel_nivel_ativo
    ON beneficios_nivel(nivel_id, ativo);

CREATE TABLE IF NOT EXISTS logs_jornada (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
    acao VARCHAR(120) NOT NULL,
    payload JSONB,
    ip VARCHAR(80),
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_jornada_cliente
    ON logs_jornada(cliente_id);

CREATE INDEX IF NOT EXISTS idx_logs_jornada_acao
    ON logs_jornada(acao);

CREATE INDEX IF NOT EXISTS idx_logs_jornada_created_at
    ON logs_jornada(created_at);

CREATE TABLE IF NOT EXISTS configuracoes_jornada (
    id SERIAL PRIMARY KEY,
    chave VARCHAR(120) NOT NULL UNIQUE,
    valor_json JSONB NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_configuracoes_jornada_ativo
    ON configuracoes_jornada(ativo);

CREATE TABLE IF NOT EXISTS codigos_resgate (
    id SERIAL PRIMARY KEY,
    resgate_id INTEGER NOT NULL UNIQUE REFERENCES resgates_premios(id) ON DELETE CASCADE,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    status VARCHAR(30) NOT NULL DEFAULT 'ativo',
    valido_ate TIMESTAMPTZ NOT NULL,
    utilizado_em TIMESTAMPTZ,
    funcionario_id INTEGER REFERENCES funcionarios(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_codigos_resgate_status
    ON codigos_resgate(status);

CREATE INDEX IF NOT EXISTS idx_codigos_resgate_valido_ate
    ON codigos_resgate(valido_ate);

INSERT INTO categorias_premios (nome, slug, descricao, ordem, ativo, created_at, updated_at)
VALUES
    ('Tecnologia Real', 'tecnologia-real', 'Experiencias e premios de tecnologia.', 1, TRUE, NOW(), NOW()),
    ('Rituais do Real', 'rituais-do-real', 'Premios para ampliar a experiencia do hospede.', 2, TRUE, NOW(), NOW()),
    ('O Retorno do Sonho', 'o-retorno-do-sonho', 'Experiencias de hospedagem especial.', 3, TRUE, NOW(), NOW())
ON CONFLICT (slug) DO UPDATE
SET nome = EXCLUDED.nome,
    descricao = EXCLUDED.descricao,
    ordem = EXCLUDED.ordem,
    ativo = EXCLUDED.ativo,
    updated_at = NOW();

INSERT INTO niveis_fidelidade (
    codigo, nome, pontos_minimos, bonus_percentual, beneficios, ordem, ativo, created_at, updated_at
)
VALUES
    (0, 'ESSENCIA', 0, 0, '{"descricao": "Entrada na Jornada Real"}', 0, TRUE, NOW(), NOW()),
    (1, 'EXPERIENCIA', 50, 100, '{"descricao": "Beneficios de evolucao da Jornada Real", "pontos_por_reserva": "+100%"}', 1, TRUE, NOW(), NOW()),
    (2, 'REAL', 90, 300, '{"descricao": "Nivel maximo da Jornada Real", "pontos_por_reserva": "+300%"}', 2, TRUE, NOW(), NOW())
ON CONFLICT (codigo) DO UPDATE
SET nome = EXCLUDED.nome,
    pontos_minimos = EXCLUDED.pontos_minimos,
    bonus_percentual = EXCLUDED.bonus_percentual,
    beneficios = EXCLUDED.beneficios,
    ordem = EXCLUDED.ordem,
    ativo = EXCLUDED.ativo,
    updated_at = NOW();

INSERT INTO beneficios_nivel (nivel_id, titulo, descricao, ativo, created_at, updated_at)
SELECT nf.id, b.titulo, b.descricao, TRUE, NOW(), NOW()
FROM niveis_fidelidade nf
JOIN (
    VALUES
        ('ESSENCIA', 'Entrada na Jornada Real', 'Acumulo de pontos apos checkout elegivel.'),
        ('EXPERIENCIA', 'Experiencias exclusivas', 'Acesso a beneficios e premios de maior valor.'),
        ('REAL', 'Beneficios Real', 'Acesso ao maior nivel de beneficios da Jornada Real.')
) AS b(nome, titulo, descricao) ON b.nome = nf.nome
WHERE NOT EXISTS (
    SELECT 1 FROM beneficios_nivel bn
    WHERE bn.nivel_id = nf.id AND bn.titulo = b.titulo
);

UPDATE pontos_regras
SET diarias_base = 1,
    rp_por_base = CASE UPPER(suite_tipo)
        WHEN 'LUXO' THEN 1
        WHEN 'MASTER' THEN 2
        WHEN 'DUPLA' THEN 3
        WHEN 'REAL' THEN 3
        ELSE rp_por_base
    END,
    updated_at = NOW()
WHERE ativo = TRUE
  AND UPPER(suite_tipo) IN ('LUXO', 'MASTER', 'DUPLA', 'REAL');

INSERT INTO pontos_regras (suite_tipo, diarias_base, rp_por_base, temporada, data_inicio, data_fim, ativo, created_at, updated_at)
SELECT v.suite_tipo, 1, v.rp_por_base, 'JORNADA_REAL', DATE '2020-01-01', DATE '2099-12-31', TRUE, NOW(), NOW()
FROM (
    VALUES
        ('LUXO', 1),
        ('MASTER', 2),
        ('DUPLA', 3),
        ('REAL', 3)
) AS v(suite_tipo, rp_por_base)
WHERE NOT EXISTS (
    SELECT 1 FROM pontos_regras pr
    WHERE pr.ativo = TRUE
      AND UPPER(pr.suite_tipo) = v.suite_tipo
      AND pr.diarias_base = 1
      AND pr.rp_por_base = v.rp_por_base
);

INSERT INTO premios (nome, descricao, preco_em_pontos, preco_em_rp, categoria, categoria_id, estoque, ativo, created_at, updated_at)
SELECT 'iPhone 16', 'Premio Tecnologia Real da Jornada Real.', 90, 90, cp.nome, cp.id, 1, TRUE, NOW(), NOW()
FROM categorias_premios cp
WHERE cp.slug = 'tecnologia-real'
  AND NOT EXISTS (
      SELECT 1 FROM premios p WHERE LOWER(p.nome) = LOWER('iPhone 16')
  );

UPDATE premios p
SET preco_em_pontos = 90,
    preco_em_rp = 90,
    categoria = cp.nome,
    categoria_id = cp.id,
    ativo = TRUE,
    updated_at = NOW()
FROM categorias_premios cp
WHERE cp.slug = 'tecnologia-real'
  AND LOWER(p.nome) = LOWER('iPhone 16');

INSERT INTO premios (nome, descricao, preco_em_pontos, preco_em_rp, categoria, categoria_id, estoque, ativo, created_at, updated_at)
SELECT 'Cafeteira Premium', 'Premio Rituais do Real da Jornada Real.', 35, 35, cp.nome, cp.id, 5, TRUE, NOW(), NOW()
FROM categorias_premios cp
WHERE cp.slug = 'rituais-do-real'
  AND NOT EXISTS (
      SELECT 1 FROM premios p WHERE LOWER(p.nome) = LOWER('Cafeteira Premium')
  );

UPDATE premios p
SET preco_em_pontos = 35,
    preco_em_rp = 35,
    categoria = cp.nome,
    categoria_id = cp.id,
    ativo = TRUE,
    updated_at = NOW()
FROM categorias_premios cp
WHERE cp.slug = 'rituais-do-real'
  AND LOWER(p.nome) = LOWER('Cafeteira Premium');

INSERT INTO premios (nome, descricao, preco_em_pontos, preco_em_rp, categoria, categoria_id, estoque, ativo, created_at, updated_at)
SELECT '1 diaria com hidromassagem e champagne cortesia', 'Experiencia O Retorno do Sonho.', 25, 25, cp.nome, cp.id, 3, TRUE, NOW(), NOW()
FROM categorias_premios cp
WHERE cp.slug = 'o-retorno-do-sonho'
  AND NOT EXISTS (
      SELECT 1 FROM premios p WHERE LOWER(p.nome) = LOWER('1 diaria com hidromassagem e champagne cortesia')
  );

UPDATE premios p
SET preco_em_pontos = 25,
    preco_em_rp = 25,
    categoria = cp.nome,
    categoria_id = cp.id,
    ativo = TRUE,
    updated_at = NOW()
FROM categorias_premios cp
WHERE cp.slug = 'o-retorno-do-sonho'
  AND LOWER(p.nome) = LOWER('1 diaria com hidromassagem e champagne cortesia');

INSERT INTO codigos_resgate (resgate_id, codigo, status, valido_ate, utilizado_em, funcionario_id, created_at, updated_at)
SELECT rp.id,
       rp.codigo_resgate,
       CASE LOWER(COALESCE(rp.codigo_status, 'active'))
           WHEN 'used' THEN 'utilizado'
           WHEN 'expired' THEN 'expirado'
           WHEN 'cancelled' THEN 'cancelado'
           WHEN 'ativo' THEN 'ativo'
           WHEN 'utilizado' THEN 'utilizado'
           WHEN 'expirado' THEN 'expirado'
           WHEN 'cancelado' THEN 'cancelado'
           ELSE 'ativo'
       END,
       COALESCE(rp.expira_em, rp.created_at + INTERVAL '30 days'),
       rp.usado_em,
       rp.funcionario_entrega_id,
       rp.created_at,
       rp.updated_at
FROM resgates_premios rp
WHERE rp.codigo_resgate IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM codigos_resgate cr WHERE cr.resgate_id = rp.id
  )
ON CONFLICT DO NOTHING;

INSERT INTO configuracoes_jornada (chave, valor_json, ativo, created_at, updated_at)
VALUES
    ('telas', '{"cta_principal": "Comecar agora", "cta_pontos": "Ver meus pontos", "cta_premios": "Premios exclusivos"}', TRUE, NOW(), NOW()),
    ('regras_legais', '{"pontos_liberados_apos_checkout": true, "prazo_liberacao_horas": 48, "cancelamentos_nao_geram_pontos": true, "fraude_chargeback_estorno_bloqueiam_pontos": true, "premios_sujeitos_disponibilidade": true}', TRUE, NOW(), NOW())
ON CONFLICT (chave) DO UPDATE
SET valor_json = EXCLUDED.valor_json,
    ativo = EXCLUDED.ativo,
    updated_at = NOW();
