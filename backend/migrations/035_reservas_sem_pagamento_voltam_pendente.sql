-- Corrige reservas promovidas para CONFIRMADA antes da quitacao.
-- O voucher permanece emitido; apenas o estado operacional da reserva volta
-- para PENDENTE. A consulta e idempotente e preserva qualquer reserva que ja
-- possua ao menos um pagamento aprovado.

UPDATE reservas AS r
SET status_reserva = 'PENDENTE',
    updated_at = NOW()
WHERE r.status_reserva = 'CONFIRMADA'
  AND EXISTS (
      SELECT 1
      FROM pagamentos AS p
      WHERE p.reserva_id = r.id
        AND p.status_pagamento = 'PENDENTE'
  )
  AND NOT EXISTS (
      SELECT 1
      FROM pagamentos AS p
      WHERE p.reserva_id = r.id
        AND UPPER(p.status_pagamento) IN (
            'PAGO',
            'APROVADO',
            'CONFIRMADO',
            'APPROVED',
            'CAPTURED',
            'AUTHORIZED'
        )
  );
