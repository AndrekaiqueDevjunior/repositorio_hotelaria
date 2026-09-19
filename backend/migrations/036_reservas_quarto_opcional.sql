-- Reservas passam a ser feitas por categoria de suite.
-- O quarto fisico pode ser designado posteriormente pela recepcao.

ALTER TABLE reservas
    ALTER COLUMN quarto_id DROP NOT NULL,
    ALTER COLUMN quarto_numero DROP NOT NULL;

COMMENT ON COLUMN reservas.quarto_id IS
    'Quarto designado pela recepcao; pode permanecer nulo ate antes do check-in.';

COMMENT ON COLUMN reservas.quarto_numero IS
    'Numero do quarto designado; pode permanecer nulo ate antes do check-in.';
