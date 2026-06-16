-- Jornada Real: impede sobreposicao de reservas que bloqueiam disponibilidade.
-- Permite checkout e novo check-in no mesmo instante usando intervalo [).

CREATE EXTENSION IF NOT EXISTS btree_gist;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'reservas_quarto_periodo_no_overlap'
    ) THEN
        ALTER TABLE reservas
        ADD CONSTRAINT reservas_quarto_periodo_no_overlap
        EXCLUDE USING gist (
            quarto_numero WITH =,
            tsrange(checkin_previsto, checkout_previsto, '[)') WITH &&
        )
        WHERE (
            status_reserva IN (
                'PENDENTE',
                'PENDENTE_PAGAMENTO',
                'AGUARDANDO_PAGAMENTO',
                'AGUARDANDO_COMPROVANTE',
                'EM_ANALISE',
                'CONFIRMADA',
                'PAGA_APROVADA',
                'CHECKIN_LIBERADO',
                'CHECKIN_REALIZADO',
                'HOSPEDADO',
                'CHECKED_IN'
            )
        );
    END IF;
END $$;
