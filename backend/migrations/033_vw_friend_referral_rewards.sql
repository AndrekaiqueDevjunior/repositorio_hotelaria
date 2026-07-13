-- 033: View de acompanhamento do Cupom Amigo (somente consulta, nao credita).
-- Arquitetura do modulo (equivalencias com o desenho de referencia):
--   * referral_uses      -> indicacoes (+ cupons_usos para o desconto)
--   * points_ledger      -> transacoes_pontos (idempotencia: indice unico
--                           parcial da migration 031 por reserva/origem)
--   * fn_credit_...      -> IndicacaoService.processar_credito_indicacao_
--                           apos_checkout (db.tx + FOR UPDATE + autocura
--                           derivando do cupom quando o vinculo faltar)
--   * sp_complete_..._checkout -> fluxo oficial de checkout (reserva_repo/
--                           hospedagem_repo), que sempre chama o credito
-- Trigger defensiva: NAO adotada por decisao — todo caminho de checkout
-- passa pelo servico oficial; se um dia surgir UPDATE direto de status
-- fora dele, reavaliar (a idempotencia do credito ja protege duplicidade).

CREATE OR REPLACE VIEW vw_friend_referral_rewards AS
SELECT
    cu.id                    AS cupom_uso_id,
    c.codigo                 AS coupon_code,
    cu.reserva_id,
    r.codigo_reserva         AS reservation_code,
    r.status_reserva         AS reservation_status,
    r.checkout_real          AS checked_out_at,

    c.cliente_indicador_id   AS referrer_customer_id,
    referrer."nomeCompleto"  AS referrer_name,
    referrer.documento       AS referrer_document,

    cu.cliente_id            AS referred_customer_id,
    referred."nomeCompleto"  AS referred_name,
    referred.documento       AS referred_document,

    cu.valor_original        AS gross_amount,
    cu.valor_desconto        AS discount_amount,
    cu.valor_final           AS net_amount,

    i.id                     AS indicacao_id,
    i.status                 AS indicacao_status,
    i.pontos_creditados,

    tp.id                    AS points_ledger_id,
    tp.pontos                AS reward_points,
    tp.created_at            AS points_credited_at,

    CASE
        WHEN tp.id IS NOT NULL THEN 'REWARDED'
        WHEN r.status_reserva IN ('CANCELADO', 'CANCELADA', 'NO_SHOW') THEN 'CANCELLED'
        WHEN COALESCE(c.cliente_indicador_id, 0) = COALESCE(cu.cliente_id, -1) THEN 'BLOCKED'
        WHEN r.checkout_real IS NOT NULL
             OR r.status_reserva IN ('CHECKED_OUT', 'CHECKOUT_REALIZADO', 'FINALIZADA') THEN 'ELIGIBLE'
        ELSE 'PENDING'
    END AS reward_status

FROM cupons_usos cu
JOIN cupons c
    ON c.id = cu.cupom_id
   AND UPPER(COALESCE(c.tipo_campanha, '')) = 'CUPOM_AMIGO'
JOIN reservas r
    ON r.id = cu.reserva_id
LEFT JOIN clientes referrer
    ON referrer.id = c.cliente_indicador_id
LEFT JOIN clientes referred
    ON referred.id = cu.cliente_id
LEFT JOIN indicacoes i
    ON i.reserva_id = cu.reserva_id
LEFT JOIN transacoes_pontos tp
    ON tp.reserva_id = cu.reserva_id
   AND tp.tipo = 'CREDITO'
   AND tp.origem IN ('FRIEND_REFERRAL', 'CONVITE_REAL');
