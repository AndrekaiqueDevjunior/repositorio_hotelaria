-- 029_indices_fk_faltantes.sql
-- Adiciona indices em colunas de chave estrangeira que o schema.prisma
-- declara via @relation mas que nunca tinham indice real no banco (o
-- schema.prisma sozinho nao cria nada em producao -- so migrations SQL
-- fazem isso aqui, ja que "prisma migrate deploy" e no-op sem a pasta
-- prisma/migrations). Sem indice, toda consulta por essas colunas faz
-- sequential scan (ex.: checar reserva aberta do cliente a cada tentativa
-- de reserva publica, listar pagamentos/antifraude por cliente).

CREATE INDEX IF NOT EXISTS idx_reservas_cliente_id ON reservas(cliente_id);

CREATE INDEX IF NOT EXISTS idx_pagamentos_cliente_id ON pagamentos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pagamentos_reserva_id ON pagamentos(reserva_id);

CREATE INDEX IF NOT EXISTS idx_operacoes_antifraude_cliente_id ON operacoes_antifraude(cliente_id);
CREATE INDEX IF NOT EXISTS idx_operacoes_antifraude_pagamento_id ON operacoes_antifraude(pagamento_id);

CREATE INDEX IF NOT EXISTS idx_resgates_premios_funcionario_id ON resgates_premios(funcionario_id);
CREATE INDEX IF NOT EXISTS idx_resgates_premios_funcionario_entrega_id ON resgates_premios(funcionario_entrega_id);

CREATE INDEX IF NOT EXISTS idx_codigos_resgate_funcionario_id ON codigos_resgate(funcionario_id);
