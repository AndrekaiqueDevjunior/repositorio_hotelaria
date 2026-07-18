-- 034: Vincula checkin_cash_approvals ao sistema de pontos (transacoes_pontos).
--
-- As FKs reserva_id, aprovado_por e pagamento_id ja existiam no banco desde a
-- migration 019, mas nunca foram modeladas em schema.prisma (o model so tinha
-- os Int soltos, sem @relation) -- ficavam sem integridade referencial visivel
-- pro Prisma Client e sem possibilidade de include(). Corrigido no schema, sem
-- necessidade de SQL porque a constraint ja existe fisicamente no banco.
--
-- O que falta de fato criar aqui: transacao_pontos_id, ligando cada aprovacao
-- de check-in em dinheiro a transacao de pontos (se houver) originada dela.
-- Mesmo padrao ja usado em indicacoes.transacao_pontos_id (migration 008):
-- FK nullable + indice unico (1 aprovacao -> no maximo 1 transacao de pontos).
--
-- Efeito no comportamento: NENHUM. Nenhuma linha existente e alterada e
-- nenhum codigo passa a escrever nessa coluna automaticamente; e apenas a
-- coluna/constraint ficando disponivel para uso futuro (ex.: o servico de
-- checkout passar a gravar o vinculo ao creditar pontos de uma reserva que
-- teve check-in em dinheiro aprovado).

ALTER TABLE checkin_cash_approvals
    ADD COLUMN IF NOT EXISTS transacao_pontos_id INTEGER NULL
        REFERENCES transacoes_pontos(id);

CREATE UNIQUE INDEX IF NOT EXISTS checkin_cash_approvals_transacao_pontos_id_key
    ON checkin_cash_approvals(transacao_pontos_id);
