-- Migration 003: Implementar Sistema de Pontos RP
-- Data: 2026-01-05
-- Descrição: Criar tabelas para o novo sistema de pontos baseado em regras RP

-- ========================================
-- 1. TABELA DE CLIENTES RP
-- ========================================
CREATE TABLE IF NOT EXISTS clientes_rp (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL UNIQUE REFERENCES clientes(id) ON DELETE CASCADE,
    saldo_rp INTEGER DEFAULT 0 NOT NULL,
    diarias_pendentes_para_pontos INTEGER DEFAULT 0 NOT NULL,
    total_pontos_ganhos INTEGER DEFAULT 0 NOT NULL,
    total_pontos_gastos INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT saldo_rp_positive CHECK (saldo_rp >= 0),
    CONSTRAINT diarias_pendentes_positive CHECK (diarias_pendentes_para_pontos >= 0)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_clientes_rp_cliente_id ON clientes_rp(cliente_id);
CREATE INDEX IF NOT EXISTS idx_clientes_rp_saldo ON clientes_rp(saldo_rp);

-- ========================================
-- 2. TABELA DE HISTÓRICO RP
-- ========================================
CREATE TABLE IF NOT EXISTS historico_rp (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    reserva_id INTEGER NOT NULL REFERENCES reservas(id) ON DELETE CASCADE,
    tipo_suite VARCHAR(50) NOT NULL,
    num_diarias INTEGER NOT NULL,
    diarias_usadas_acumuladas INTEGER NOT NULL,
    diarias_pendentes_antes INTEGER DEFAULT 0 NOT NULL,
    pontos_gerados INTEGER NOT NULL,
    detalhamento TEXT,
    data TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT num_diarias_positive CHECK (num_diarias > 0),
    CONSTRAINT pontos_gerados_positive CHECK (pontos_gerados >= 0),
    CONSTRAINT diarias_usadas_positive CHECK (diarias_usadas_acumuladas >= 0),
    
    -- Única entrada por reserva
    UNIQUE(reserva_id)
);

-- Índices para performance e consultas
CREATE INDEX IF NOT EXISTS idx_historico_rp_cliente_id ON historico_rp(cliente_id);
CREATE INDEX IF NOT EXISTS idx_historico_rp_reserva_id ON historico_rp(reserva_id);
CREATE INDEX IF NOT EXISTS idx_historico_rp_data ON historico_rp(data);
CREATE INDEX IF NOT EXISTS idx_historico_rp_tipo_suite ON historico_rp(tipo_suite);

-- ========================================
-- 3. TABELA DE PRÊMIOS RP
-- ========================================
CREATE TABLE IF NOT EXISTS premios_rp (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    rp_necessario INTEGER NOT NULL,
    categoria VARCHAR(50) DEFAULT 'GERAL',
    ativo BOOLEAN DEFAULT TRUE,
    estoque_disponivel INTEGER NULL, -- NULL = ilimitado
    imagem_url VARCHAR(500),
    ordem_exibicao INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT rp_necessario_positive CHECK (rp_necessario > 0),
    CONSTRAINT estoque_positive CHECK (estoque_disponivel IS NULL OR estoque_disponivel >= 0)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_premios_rp_ativo ON premios_rp(ativo);
CREATE INDEX IF NOT EXISTS idx_premios_rp_categoria ON premios_rp(categoria);
CREATE INDEX IF NOT EXISTS idx_premios_rp_ordem ON premios_rp(ordem_exibicao);

-- ========================================
-- 4. TABELA DE RESGATES RP
-- ========================================
CREATE TABLE IF NOT EXISTS resgates_rp (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    premio_id INTEGER NOT NULL REFERENCES premios_rp(id) ON DELETE RESTRICT,
    rp_utilizados INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'SOLICITADO' NOT NULL,
    data_solicitacao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_entrega TIMESTAMP WITH TIME ZONE NULL,
    data_cancelamento TIMESTAMP WITH TIME ZONE NULL,
    funcionario_entrega_id INTEGER REFERENCES usuarios(id),
    observacoes TEXT,
    
    -- Constraints
    CONSTRAINT rp_utilizados_positive CHECK (rp_utilizados > 0),
    CONSTRAINT status_valido CHECK (status IN ('SOLICITADO', 'PROCESSANDO', 'ENTREGUE', 'CANCELADO')),
    
    -- Validações de datas
    CONSTRAINT data_entrega_posterior CHECK (data_entrega IS NULL OR data_entrega >= data_solicitacao),
    CONSTRAINT data_cancelamento_posterior CHECK (data_cancelamento IS NULL OR data_cancelamento >= data_solicitacao)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_resgates_rp_cliente_id ON resgates_rp(cliente_id);
CREATE INDEX IF NOT EXISTS idx_resgates_rp_premio_id ON resgates_rp(premio_id);
CREATE INDEX IF NOT EXISTS idx_resgates_rp_status ON resgates_rp(status);
CREATE INDEX IF NOT EXISTS idx_resgates_rp_data_solicitacao ON resgates_rp(data_solicitacao);

-- ========================================
-- 5. TRIGGER PARA ATUALIZAR updated_at
-- ========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger nas tabelas relevantes
DROP TRIGGER IF EXISTS update_clientes_rp_updated_at ON clientes_rp;
CREATE TRIGGER update_clientes_rp_updated_at 
    BEFORE UPDATE ON clientes_rp 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_premios_rp_updated_at ON premios_rp;
CREATE TRIGGER update_premios_rp_updated_at 
    BEFORE UPDATE ON premios_rp 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- 6. INSERIR DADOS INICIAIS - CATÁLOGO DE PRÊMIOS
-- ========================================
INSERT INTO premios_rp (nome, descricao, rp_necessario, categoria, ordem_exibicao, ativo) VALUES
('1 diária em Suíte Luxo', 'Diária gratuita em Suíte Luxo (válida por 12 meses)', 20, 'HOSPEDAGEM', 1, TRUE),
('Luminária com carregador', 'Luminária LED moderna com porta USB para carregamento', 25, 'ELETRONICOS', 2, TRUE),
('Cafeteira', 'Cafeteira elétrica para até 12 xícaras', 35, 'ELETRODOMESTICOS', 3, TRUE),
('iPhone 16', 'iPhone 16 128GB - Cor disponível conforme estoque', 100, 'PREMIUM', 4, TRUE),

-- Prêmios adicionais para engajamento
('Kit Amenities Premium', 'Kit de amenities premium para levar para casa', 10, 'AMENITIES', 5, TRUE),
('Upgrade para Suíte Master', 'Upgrade gratuito para Suíte Master na próxima reserva', 15, 'HOSPEDAGEM', 6, TRUE),
('Jantar Romântico', 'Jantar romântico para casal no restaurante do hotel', 30, 'GASTRONOMIA', 7, TRUE),
('Spa Day', 'Day use completo no spa do hotel', 40, 'WELLNESS', 8, TRUE),
('Fone de Ouvido Bluetooth', 'Fone de ouvido Bluetooth de alta qualidade', 45, 'ELETRONICOS', 9, TRUE),
('Notebook Básico', 'Notebook para uso básico e estudos', 150, 'PREMIUM', 10, FALSE); -- Desabilitado inicialmente

-- ========================================
-- 7. MIGRAÇÃO DE DADOS EXISTENTES
-- ========================================
-- Migrar saldos existentes do sistema antigo para o novo
INSERT INTO clientes_rp (cliente_id, saldo_rp, total_pontos_ganhos)
SELECT 
    up.cliente_id,
    COALESCE(up.saldo_atual, 0) as saldo_rp,
    COALESCE(up.saldo_atual, 0) as total_pontos_ganhos
FROM usuarios_pontos up
WHERE up.cliente_id IS NOT NULL
ON CONFLICT (cliente_id) DO UPDATE SET
    saldo_rp = GREATEST(EXCLUDED.saldo_rp, clientes_rp.saldo_rp),
    total_pontos_ganhos = GREATEST(EXCLUDED.total_pontos_ganhos, clientes_rp.total_pontos_ganhos);

-- ========================================
-- 8. VIEWS PARA RELATÓRIOS
-- ========================================
CREATE OR REPLACE VIEW vw_estatisticas_rp AS
SELECT 
    'total_clientes_ativos' as metrica,
    COUNT(*) as valor
FROM clientes_rp 
WHERE saldo_rp > 0

UNION ALL

SELECT 
    'total_pontos_em_circulacao' as metrica,
    SUM(saldo_rp) as valor
FROM clientes_rp

UNION ALL

SELECT 
    'total_pontos_ja_resgatados' as metrica,
    SUM(total_pontos_gastos) as valor
FROM clientes_rp

UNION ALL

SELECT 
    'resgates_pendentes' as metrica,
    COUNT(*) as valor
FROM resgates_rp 
WHERE status = 'SOLICITADO';

-- View para histórico detalhado
CREATE OR REPLACE VIEW vw_historico_rp_detalhado AS
SELECT 
    h.id,
    h.cliente_id,
    c.nome_completo as cliente_nome,
    h.reserva_id,
    r.codigo_reserva,
    h.tipo_suite,
    h.num_diarias,
    h.diarias_usadas_acumuladas,
    h.diarias_pendentes_antes,
    h.pontos_gerados,
    h.detalhamento,
    h.data,
    r.checkin_previsto,
    r.checkout_previsto
FROM historico_rp h
JOIN clientes c ON c.id = h.cliente_id
JOIN reservas r ON r.id = h.reserva_id
ORDER BY h.data DESC;

-- ========================================
-- 9. COMENTÁRIOS E DOCUMENTAÇÃO
-- ========================================
COMMENT ON TABLE clientes_rp IS 'Tabela principal do sistema RP - armazena saldos e estatísticas de cada cliente';
COMMENT ON COLUMN clientes_rp.saldo_rp IS 'Saldo atual de pontos RP do cliente';
COMMENT ON COLUMN clientes_rp.diarias_pendentes_para_pontos IS 'Diárias acumuladas que ainda não geraram pontos (aguardando completar bloco de 2)';

COMMENT ON TABLE historico_rp IS 'Histórico de pontos RP gerados por checkout - auditoria completa';
COMMENT ON COLUMN historico_rp.diarias_usadas_acumuladas IS 'Total de diárias usadas para gerar os pontos (incluindo pendentes anteriores)';

COMMENT ON TABLE premios_rp IS 'Catálogo de prêmios disponíveis para resgate com pontos RP';
COMMENT ON TABLE resgates_rp IS 'Histórico de resgates realizados pelos clientes';

-- ========================================
-- 10. GRANT DE PERMISSÕES
-- ========================================
-- Garantir que a aplicação tenha acesso às novas tabelas
GRANT SELECT, INSERT, UPDATE, DELETE ON clientes_rp TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON historico_rp TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON premios_rp TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON resgates_rp TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- ========================================
-- FINALIZAÇÃO
-- ========================================
-- Registrar execução da migration
INSERT INTO schema_migrations (version, executed_at) VALUES ('003_implementar_sistema_rp', NOW())
ON CONFLICT (version) DO UPDATE SET executed_at = NOW();
