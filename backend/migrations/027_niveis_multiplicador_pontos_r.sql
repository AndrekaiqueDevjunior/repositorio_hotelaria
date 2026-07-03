-- 027_niveis_multiplicador_pontos_r.sql
-- Nova regra de fidelidade: Pontos N (nivel) nunca recebem multiplicador;
-- somente Pontos R (resgate) sao multiplicados conforme o nivel do cliente.
-- Substitui o antigo bonus de +20%/+40% (aplicado sobre o total) por um
-- multiplicador de 2x/4x aplicado apenas aos Pontos R:
--   Nivel 1 (0-49N):  1x
--   Nivel 2 (50-89N): 2x  (bonus_percentual = 100)
--   Nivel 3 (90N+):   4x  (bonus_percentual = 300)
-- O calculo de multiplicador (1 + bonus_percentual/100) ja existe no codigo
-- (programa_pontos_service.py), so os valores da tabela precisam mudar.

UPDATE niveis_fidelidade SET bonus_percentual = 0, updated_at = NOW() WHERE codigo = 0;
UPDATE niveis_fidelidade SET bonus_percentual = 100, updated_at = NOW() WHERE codigo = 1;
UPDATE niveis_fidelidade SET bonus_percentual = 300, updated_at = NOW() WHERE codigo = 2;
