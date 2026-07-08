-- 030_reservas_fk_operacionais.sql
-- Adiciona FKs operacionais na tabela reservas:
--   * criado_por_funcionario_id -> funcionarios(id): quem criou a reserva no
--     painel admin (reservas do site/cliente ficam NULL). Base para auditoria
--     e relatorios de produtividade por funcionario.
--   * tarifa_suite_id -> tarifas_suites(id): qual tarifa vigente foi aplicada
--     no momento da criacao. Preserva a origem do preco mesmo que a tarifa
--     seja editada depois (o valor_diaria continua congelado na reserva).
-- Ambas NULL-aveis com ON DELETE SET NULL: apagar funcionario/tarifa nao pode
-- apagar nem travar a reserva (registro financeiro/historico).

ALTER TABLE reservas ADD COLUMN IF NOT EXISTS criado_por_funcionario_id INTEGER;
ALTER TABLE reservas ADD COLUMN IF NOT EXISTS tarifa_suite_id INTEGER;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='reservas_criado_por_funcionario_id_fkey') THEN
    ALTER TABLE reservas ADD CONSTRAINT reservas_criado_por_funcionario_id_fkey
      FOREIGN KEY (criado_por_funcionario_id) REFERENCES funcionarios(id)
      ON UPDATE CASCADE ON DELETE SET NULL;
  END IF;
EXCEPTION WHEN duplicate_object OR undefined_table OR undefined_column OR foreign_key_violation THEN NULL; END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='reservas_tarifa_suite_id_fkey') THEN
    ALTER TABLE reservas ADD CONSTRAINT reservas_tarifa_suite_id_fkey
      FOREIGN KEY (tarifa_suite_id) REFERENCES tarifas_suites(id)
      ON UPDATE CASCADE ON DELETE SET NULL;
  END IF;
EXCEPTION WHEN duplicate_object OR undefined_table OR undefined_column OR foreign_key_violation THEN NULL; END $$;

CREATE INDEX IF NOT EXISTS idx_reservas_criado_por_funcionario_id ON reservas(criado_por_funcionario_id);
CREATE INDEX IF NOT EXISTS idx_reservas_tarifa_suite_id ON reservas(tarifa_suite_id);
