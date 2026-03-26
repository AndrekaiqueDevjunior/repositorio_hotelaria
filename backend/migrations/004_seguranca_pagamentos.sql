-- ============================================================
-- MIGRATION: Melhorar Seguranca de Pagamentos
-- Data: 21/12/2024
-- Descricao: Remove CVV e adiciona tokenizacao
-- ============================================================

-- IMPORTANTE: Fazer backup do banco antes de executar!
-- ATENCAO: Esta migration REMOVE o campo CVV permanentemente!

BEGIN;

-- ============================================================
-- STEP 1: REMOVER CVV (ma pratica PCI-DSS)
-- ============================================================

-- AVISO: CVV NUNCA deve ser armazenado apos a transacao!
ALTER TABLE pagamentos
DROP COLUMN IF EXISTS cartao_cvv;

-- ============================================================
-- STEP 2: Adicionar campo para token do cartao
-- ============================================================

-- Token gerado pela Cielo ou outro gateway
ALTER TABLE pagamentos
ADD COLUMN IF NOT EXISTS cartao_token VARCHAR(255);

-- Indice para busca rapida por token
CREATE INDEX IF NOT EXISTS idx_pagamentos_cartao_token 
ON pagamentos(cartao_token);

-- ============================================================
-- STEP 3: Adicionar flag de dados sensiveis mascarados
-- ============================================================

ALTER TABLE pagamentos
ADD COLUMN IF NOT EXISTS dados_mascarados BOOLEAN DEFAULT true;

-- ============================================================
-- STEP 4: Mascarar numeros de cartao existentes
-- ============================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'pagamentos' AND column_name = 'cartao_numero'
    ) THEN
        UPDATE pagamentos
        SET 
            cartao_numero = '???? ' || RIGHT(cartao_numero, 4),
            dados_mascarados = true
        WHERE cartao_numero IS NOT NULL
          AND cartao_numero NOT LIKE '????%'
          AND LENGTH(cartao_numero) >= 4;
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'pagamentos' AND column_name = 'cartao_ultimos4'
    ) THEN
        UPDATE pagamentos
        SET dados_mascarados = true
        WHERE cartao_ultimos4 IS NOT NULL;
    END IF;
END $$;

-- ============================================================
-- STEP 5: Adicionar comentarios de seguranca
-- ============================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'pagamentos' AND column_name = 'cartao_ultimos4'
    ) THEN
        COMMENT ON COLUMN pagamentos.cartao_ultimos4 IS
        'Ultimos 4 digitos do cartao (formato: 1234). NUNCA armazenar numero completo.';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'pagamentos' AND column_name = 'cartao_numero'
    ) THEN
        COMMENT ON COLUMN pagamentos.cartao_numero IS
        'Ultimos 4 digitos do cartao (formato: ???? 1234). NUNCA armazenar numero completo.';
    END IF;
END $$;

COMMENT ON COLUMN pagamentos.cartao_token IS 
'Token seguro do cartao gerado pelo gateway de pagamento.';

-- ============================================================
-- STEP 6: Validacao
-- ============================================================

DO $$
DECLARE
    count_pagamentos INTEGER;
    count_com_cvv INTEGER;
    count_mascarados INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_pagamentos FROM pagamentos;

    SELECT COUNT(*) INTO count_com_cvv
    FROM information_schema.columns
    WHERE table_name = 'pagamentos' 
      AND column_name = 'cartao_cvv';

    SELECT COUNT(*) INTO count_mascarados
    FROM pagamentos
    WHERE dados_mascarados = true;

    IF count_com_cvv > 0 THEN
        RAISE EXCEPTION 'ERRO: Coluna CVV ainda existe!';
    END IF;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION DE SEGURANCA CONCLUIDA!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total de pagamentos: %', count_pagamentos;
    RAISE NOTICE 'Coluna CVV removida: OK';
    RAISE NOTICE 'Pagamentos mascarados: %', count_mascarados;
    RAISE NOTICE 'Campo token adicionado: OK';
    RAISE NOTICE '========================================';
END $$;

COMMIT;
