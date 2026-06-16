-- Jornada Real JR-09: campos admin para cupons rastreados/influencer.

ALTER TABLE cupons
    ADD COLUMN IF NOT EXISTS influencer_nome VARCHAR(180);

ALTER TABLE cupons
    ADD COLUMN IF NOT EXISTS commission_percentual NUMERIC(5, 2);

CREATE INDEX IF NOT EXISTS idx_cupons_influencer_nome
    ON cupons(influencer_nome);
