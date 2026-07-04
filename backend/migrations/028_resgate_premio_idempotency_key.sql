-- 028_resgate_premio_idempotency_key.sql
-- Resgate de premio (debito de Pontos R) nao tinha nenhuma chave de
-- idempotencia: um duplo-clique ou retry de rede no POST /premios/{id}/resgatar
-- criava dois resgates de verdade (debitava pontos duas vezes, consumia dois
-- estoques, emitia dois codigos). Segue o mesmo padrao ja usado em
-- pagamentos.idempotency_key: coluna unica opcional, checada antes do INSERT
-- e usada como fallback caso a constraint pegue uma corrida.
--
-- Idempotente: ADD COLUMN IF NOT EXISTS + CREATE UNIQUE INDEX IF NOT EXISTS.

ALTER TABLE resgates_premios ADD COLUMN IF NOT EXISTS idempotency_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS resgates_premios_idempotency_key_key
    ON resgates_premios(idempotency_key);
