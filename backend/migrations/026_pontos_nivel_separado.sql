-- 026_pontos_nivel_separado.sql
-- Separa "Pontos N" (nivel, cumulativo, nunca decresce) de "Pontos R" (saldo
-- resgatavel, ja existente na coluna usuarios_pontos.saldo). Ate aqui o nivel
-- de fidelidade era calculado em cima do proprio saldo resgatavel, entao um
-- resgate podia derrubar o cliente de nivel. Agora pontos_nivel e uma coluna
-- separada, so incrementada em creditos, nunca tocada pelo resgate.
--
-- Idempotente: ADD COLUMN IF NOT EXISTS + backfill so preenche quando a
-- coluna acabou de ser criada (WHERE pontos_nivel = 0), seguro para rodar
-- de novo sem duplicar valores.

ALTER TABLE usuarios_pontos ADD COLUMN IF NOT EXISTS pontos_nivel INTEGER NOT NULL DEFAULT 0;

UPDATE usuarios_pontos up
SET pontos_nivel = COALESCE((
    SELECT SUM(tp.pontos)
    FROM transacoes_pontos tp
    WHERE tp.cliente_id = up.cliente_id
      AND tp.pontos > 0
      AND COALESCE(tp.status, 'liberado') NOT IN ('pendente', 'bloqueado', 'expirado')
), 0)
WHERE up.pontos_nivel = 0;
