-- 032: indicacoes.updated_at era NOT NULL SEM default. Os INSERTs crus do
-- indicacao_repo nao enviavam updated_at, entao TODA criacao de indicacao
-- falhava com violacao de NOT NULL (e o cupom_service engolia o erro).
-- Resultado: cupons amigo usados sem vinculo criado e indicador sem os
-- 5 pontos apos o checkout do indicado. Default now() blinda qualquer
-- INSERT cru futuro; o fix do INSERT em si esta no codigo.

ALTER TABLE indicacoes ALTER COLUMN updated_at SET DEFAULT now();
