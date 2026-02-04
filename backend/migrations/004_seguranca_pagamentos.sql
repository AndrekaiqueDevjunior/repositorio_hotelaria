-- ============================================================
-- MIGRATION: Melhorar Segurança de Pagamentos
-- Data: 21/12/2024
-- Descrição: Remove CVV e adiciona tokenização
-- ============================================================

-- ⚠️ IMPORTANTE: Fazer backup do banco antes de executar!
-- ⚠️ ATENÇÃO: Esta migration REMOVE o campo CVV permanentemente!

BEGIN;

-- ============================================================
-- STEP 1: REMOVER CVV (má prática PCI-DSS)
-- ============================================================

-- AVISO: CVV NUNCA deve ser armazenado após a transação!
ALTER TABLE pagamentos
DROP COLUMN IF EXISTS cartao_cvv;

-- ============================================================
-- STEP 2: Adicionar campo para token do cartão
-- ============================================================

-- Token gerado pela Cielo ou outro gateway
ALTER TABLE pagamentos
ADD COLUMN IF NOT EXISTS cartao_token VARCHAR(255);

-- Índice para busca rápida por token
CREATE INDEX IF NOT EXISTS idx_pagamentos_cartao_token 
ON pagamentos(cartao_token);

-- ============================================================
-- STEP 3: Adicionar flag de dados sensíveis mascarados
-- ============================================================

ALTER TABLE pagamentos
ADD COLUMN IF NOT EXISTS dados_mascarados BOOLEAN DEFAULT false;

-- ============================================================
-- STEP 4: Mascarar números de cartão existentes
-- ============================================================

-- Manter apenas últimos 4 dígitos
-- Exemplo: 1234567890123456 → •••• 3456
UPDATE pagamentos
SET 
    cartao_numero = '•••• ' || RIGHT(cartao_numero, 4),
    dados_mascarados = true
WHERE cartao_numero IS NOT NULL 
  AND cartao_numero NOT LIKE '••••%'
  AND LENGTH(cartao_numero) >= 4;

-- ============================================================
-- STEP 5: Adicionar comentários de segurança
-- ============================================================

COMMENT ON COLUMN pagamentos.cartao_numero IS 
'Últimos 4 dígitos do cartão (formato: •••• 1234). NUNCA armazenar número completo.';

COMMENT ON COLUMN pagamentos.cartao_token IS 
'Token seguro do cartão gerado pelo gateway de pagamento.';

-- ============================================================
-- STEP 6: Validação
-- ============================================================

DO $$
DECLARE
    count_pagamentos INTEGER;
    count_com_cvv INTEGER;
    count_mascarados INTEGER;
BEGIN
    -- Contar total de pagamentos
    SELECT COUNT(*) INTO count_pagamentos FROM pagamentos;
    
    -- Verificar se ainda existe coluna CVV (não deveria)
    SELECT COUNT(*) INTO count_com_cvv
    FROM information_schema.columns
    WHERE table_name = 'pagamentos' 
      AND column_name = 'cartao_cvv';
    
    -- Contar pagamentos mascarados
    SELECT COUNT(*) INTO count_mascarados
    FROM pagamentos
    WHERE dados_mascarados = true;
    
    IF count_com_cvv > 0 THEN
        RAISE EXCEPTION 'ERRO: Coluna CVV ainda existe!';
    END IF;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION DE SEGURANÇA CONCLUÍDA!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total de pagamentos: %', count_pagamentos;
    RAISE NOTICE 'Coluna CVV removida: OK';
    RAISE NOTICE 'Pagamentos mascarados: %', count_mascarados;
    RAISE NOTICE 'Campo token adicionado: OK';
    RAISE NOTICE '========================================';
    RAISE NOTICE '⚠️  IMPORTANTE: Atualizar código para:';
    RAISE NOTICE '   1. Não solicitar CVV após primeira transação';
    RAISE NOTICE '   2. Usar tokens para transações recorrentes';
    RAISE NOTICE '   3. Nunca exibir número completo do cartão';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- ============================================================
-- ROLLBACK (NÃO RECOMENDADO - CVV não deve voltar!)
-- ============================================================
-- Se absolutamente necessário (CUIDADO!):
-- 
-- BEGIN;
-- ALTER TABLE pagamentos DROP COLUMN IF EXISTS cartao_token;
-- ALTER TABLE pagamentos DROP COLUMN IF EXISTS dados_mascarados;
-- -- NÃO restaurar CVV - violação de segurança!
-- COMMIT;

