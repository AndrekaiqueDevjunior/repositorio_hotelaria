-- Corrige bloqueio de criacao de tarifas: colunas legadas "nome" e
-- "valor_diaria" em tarifas_suites ainda exigiam NOT NULL, mas o modelo
-- TarifaSuite atual (schema.prisma) nao preenche esses campos ao criar,
-- causando falha em POST /api/v1/tarifas. Torna ambas opcionais sem
-- apagar nada -- os registros legados existentes mantem seus valores.

ALTER TABLE tarifas_suites ALTER COLUMN nome DROP NOT NULL;
ALTER TABLE tarifas_suites ALTER COLUMN valor_diaria DROP NOT NULL;
