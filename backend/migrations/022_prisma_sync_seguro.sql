-- Sincroniza schema com prisma migrate diff, excluindo partes destrutivas
-- (DROP TABLE clientes_rp/premios_rp, DROP COLUMN em tarifas_suites/reservas)
-- que tem dados reais e ficam para decisao separada.
-- Tabelas vazias (historico_rp, resgates_rp, tarifas) sao removidas aqui
-- pois nao ha risco de perda de dados.

-- ===== Tabelas legadas vazias (0 linhas confirmado) =====
DROP VIEW IF EXISTS vw_historico_rp_detalhado;
DROP VIEW IF EXISTS vw_estatisticas_rp;
DROP TABLE IF EXISTS historico_rp;
DROP TABLE IF EXISTS resgates_rp;
DROP TABLE IF EXISTS tarifas;

-- ===== Ampliacao de tipos e NOT NULL (sem nulos existentes, confirmado) =====
ALTER TABLE auditorias
    ALTER COLUMN entidade SET DATA TYPE TEXT,
    ALTER COLUMN entidade_id SET DATA TYPE TEXT,
    ALTER COLUMN acao SET DATA TYPE TEXT,
    ALTER COLUMN ip_address SET DATA TYPE TEXT,
    ALTER COLUMN user_agent SET DATA TYPE TEXT,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN updated_at SET NOT NULL,
    ALTER COLUMN updated_at DROP DEFAULT,
    ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3);

ALTER TABLE beneficios_nivel
    ALTER COLUMN titulo SET DATA TYPE TEXT,
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN updated_at DROP DEFAULT,
    ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3);

ALTER TABLE categorias_premios
    ALTER COLUMN nome SET DATA TYPE TEXT,
    ALTER COLUMN slug SET DATA TYPE TEXT,
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN updated_at DROP DEFAULT,
    ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3);

ALTER TABLE checkin_cash_approvals
    ALTER COLUMN expira_em SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN aprovado_em SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN updated_at DROP DEFAULT,
    ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3);

ALTER TABLE codigos_resgate
    ALTER COLUMN codigo SET DATA TYPE TEXT,
    ALTER COLUMN status SET DATA TYPE TEXT,
    ALTER COLUMN valido_ate SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN utilizado_em SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN updated_at DROP DEFAULT,
    ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3);

ALTER TABLE comprovantes_pagamento
    ALTER COLUMN tipo_comprovante SET DATA TYPE TEXT,
    ALTER COLUMN nome_arquivo SET DATA TYPE TEXT,
    ALTER COLUMN caminho_arquivo SET DATA TYPE TEXT,
    ALTER COLUMN status_validacao SET NOT NULL,
    ALTER COLUMN status_validacao SET DATA TYPE TEXT,
    ALTER COLUMN data_upload SET NOT NULL,
    ALTER COLUMN data_upload SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN data_validacao SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN updated_at SET NOT NULL,
    ALTER COLUMN updated_at DROP DEFAULT,
    ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3);

ALTER TABLE configuracoes_jornada
    ALTER COLUMN chave SET DATA TYPE TEXT,
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN updated_at DROP DEFAULT,
    ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3);

ALTER TABLE cupons
    ALTER COLUMN updated_at DROP DEFAULT;

ALTER TABLE cupons_usos
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3);

ALTER TABLE funcionarios
    ALTER COLUMN primeiro_acesso SET NOT NULL;

ALTER TABLE hospedagens
    ALTER COLUMN status_hospedagem SET NOT NULL,
    ALTER COLUMN status_hospedagem SET DATA TYPE TEXT,
    ALTER COLUMN checkin_realizado_em SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN checkout_realizado_em SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN placa_veiculo SET DATA TYPE TEXT,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN updated_at SET NOT NULL,
    ALTER COLUMN updated_at DROP DEFAULT,
    ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3);

-- Em bancos ja sincronizados, repetir SET DATA TYPE TEXT em indicacoes.status
-- falha porque a view vw_friend_referral_rewards depende dessa coluna. Execute
-- o bloco apenas na primeira conversao (antes de a view existir).
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
          FROM information_schema.columns
         WHERE table_schema = 'public'
           AND table_name = 'indicacoes'
           AND column_name = 'status'
           AND data_type <> 'text'
    ) THEN
        ALTER TABLE indicacoes
            ALTER COLUMN status SET DATA TYPE TEXT,
            ALTER COLUMN data_envio SET DATA TYPE TIMESTAMP(3),
            ALTER COLUMN data_reserva SET DATA TYPE TIMESTAMP(3),
            ALTER COLUMN data_checkin SET DATA TYPE TIMESTAMP(3),
            ALTER COLUMN data_checkout SET DATA TYPE TIMESTAMP(3),
            ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
            ALTER COLUMN updated_at DROP DEFAULT,
            ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3);
    END IF;
END $$;

ALTER TABLE logs_jornada
    ALTER COLUMN acao SET DATA TYPE TEXT,
    ALTER COLUMN ip SET DATA TYPE TEXT,
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3);

ALTER TABLE niveis_fidelidade
    ALTER COLUMN nome SET DATA TYPE TEXT,
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN updated_at DROP DEFAULT,
    ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3);

ALTER TABLE otp_verificacoes
    ALTER COLUMN expira_em SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN validado_em SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN ultimo_envio_em SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN updated_at DROP DEFAULT,
    ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3);

ALTER TABLE pagamentos
    ALTER COLUMN dados_mascarados SET NOT NULL,
    ALTER COLUMN status_pagamento SET NOT NULL;

ALTER TABLE premios
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN updated_at DROP DEFAULT,
    ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3);

ALTER TABLE reservas
    ALTER COLUMN forma_pagamento SET DATA TYPE TEXT,
    ALTER COLUMN telefone_contato SET DATA TYPE TEXT,
    ALTER COLUMN email_contato SET DATA TYPE TEXT;

ALTER TABLE resgates_premios
    ALTER COLUMN created_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN updated_at DROP DEFAULT,
    ALTER COLUMN updated_at SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN codigo_resgate SET DATA TYPE TEXT,
    ALTER COLUMN codigo_status SET DATA TYPE TEXT,
    ALTER COLUMN usado_em SET DATA TYPE TIMESTAMP(3),
    ALTER COLUMN expira_em SET DATA TYPE TIMESTAMP(3);

ALTER TABLE transacoes_pontos
    ALTER COLUMN saldo_anterior SET NOT NULL,
    ALTER COLUMN saldo_anterior SET DEFAULT 0,
    ALTER COLUMN saldo_posterior SET NOT NULL,
    ALTER COLUMN saldo_posterior SET DEFAULT 0,
    ALTER COLUMN status SET DATA TYPE TEXT,
    ALTER COLUMN liberar_em SET DATA TYPE TIMESTAMP(3);

-- ===== Enums legados, sem uso apos conversao das colunas para TEXT acima =====
DROP TYPE IF EXISTS "OrigemTransacaoPontos";
DROP TYPE IF EXISTS "TipoTransacaoPontos";

-- ===== Indices novos =====
CREATE UNIQUE INDEX IF NOT EXISTS resgates_premios_codigo_resgate_key ON resgates_premios(codigo_resgate);
CREATE INDEX IF NOT EXISTS transacoes_pontos_reserva_id_origem_idx ON transacoes_pontos(reserva_id, origem);

-- ===== Foreign keys faltantes (adiciona, ignora se ja existir com outro nome) =====
DO $$
BEGIN
    BEGIN
        ALTER TABLE comprovantes_pagamento ADD CONSTRAINT comprovantes_pagamento_pagamento_id_fkey
            FOREIGN KEY (pagamento_id) REFERENCES pagamentos(id) ON DELETE RESTRICT ON UPDATE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    BEGIN
        ALTER TABLE hospedagens ADD CONSTRAINT hospedagens_reserva_id_fkey
            FOREIGN KEY (reserva_id) REFERENCES reservas(id) ON DELETE RESTRICT ON UPDATE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    BEGIN
        ALTER TABLE transacoes_pontos ADD CONSTRAINT transacoes_pontos_cliente_id_fkey
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT ON UPDATE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    BEGIN
        ALTER TABLE transacoes_pontos ADD CONSTRAINT transacoes_pontos_funcionario_id_fkey
            FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id) ON DELETE SET NULL ON UPDATE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    BEGIN
        ALTER TABLE indicacoes ADD CONSTRAINT indicacoes_cliente_indicador_id_fkey
            FOREIGN KEY (cliente_indicador_id) REFERENCES clientes(id) ON DELETE RESTRICT ON UPDATE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    BEGIN
        ALTER TABLE indicacoes ADD CONSTRAINT indicacoes_cliente_indicado_id_fkey
            FOREIGN KEY (cliente_indicado_id) REFERENCES clientes(id) ON DELETE SET NULL ON UPDATE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    BEGIN
        ALTER TABLE indicacoes ADD CONSTRAINT indicacoes_reserva_id_fkey
            FOREIGN KEY (reserva_id) REFERENCES reservas(id) ON DELETE SET NULL ON UPDATE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    BEGIN
        ALTER TABLE indicacoes ADD CONSTRAINT indicacoes_transacao_pontos_id_fkey
            FOREIGN KEY (transacao_pontos_id) REFERENCES transacoes_pontos(id) ON DELETE SET NULL ON UPDATE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    BEGIN
        ALTER TABLE beneficios_nivel ADD CONSTRAINT beneficios_nivel_nivel_id_fkey
            FOREIGN KEY (nivel_id) REFERENCES niveis_fidelidade(id) ON DELETE RESTRICT ON UPDATE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    BEGIN
        ALTER TABLE premios ADD CONSTRAINT premios_categoria_id_fkey
            FOREIGN KEY (categoria_id) REFERENCES categorias_premios(id) ON DELETE SET NULL ON UPDATE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    BEGIN
        ALTER TABLE logs_jornada ADD CONSTRAINT logs_jornada_cliente_id_fkey
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL ON UPDATE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    BEGIN
        ALTER TABLE otp_verificacoes ADD CONSTRAINT otp_verificacoes_cliente_id_fkey
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL ON UPDATE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
END $$;

-- ===== Renomeacoes de indices/constraints (cosmetico, sem risco) =====
DO $$
BEGIN
    BEGIN ALTER INDEX idx_auditorias_acao RENAME TO auditorias_acao_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_auditorias_created_at RENAME TO auditorias_created_at_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_auditorias_entidade RENAME TO auditorias_entidade_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_auditorias_entidade_id RENAME TO auditorias_entidade_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_auditorias_funcionario_id RENAME TO auditorias_funcionario_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_beneficios_nivel_nivel_ativo RENAME TO beneficios_nivel_nivel_id_ativo_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_categorias_premios_ativo_ordem RENAME TO categorias_premios_ativo_ordem_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_checkin_cash_approvals_expira_em RENAME TO checkin_cash_approvals_expira_em_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_checkin_cash_approvals_reserva_id RENAME TO checkin_cash_approvals_reserva_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_checkin_cash_approvals_status RENAME TO checkin_cash_approvals_status_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_codigos_resgate_resgate_id RENAME TO codigos_resgate_resgate_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_codigos_resgate_status RENAME TO codigos_resgate_status_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_codigos_resgate_valido_ate RENAME TO codigos_resgate_valido_ate_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_comprovantes_data_upload RENAME TO comprovantes_pagamento_data_upload_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_comprovantes_pagamento_pagamento_id RENAME TO comprovantes_pagamento_pagamento_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_comprovantes_status_validacao RENAME TO comprovantes_pagamento_status_validacao_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_configuracoes_jornada_ativo RENAME TO configuracoes_jornada_ativo_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_cupons_ativo RENAME TO cupons_ativo_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_cupons_cliente_indicador_id RENAME TO cupons_cliente_indicador_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_cupons_codigo RENAME TO cupons_codigo_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_cupons_data_inicio_fim RENAME TO cupons_data_inicio_data_fim_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_cupons_status RENAME TO cupons_status_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_cupons_tipo_campanha RENAME TO cupons_tipo_campanha_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_cupons_usos_cliente_id RENAME TO cupons_usos_cliente_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_cupons_usos_created_at RENAME TO cupons_usos_created_at_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_cupons_usos_cupom_id RENAME TO cupons_usos_cupom_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_hospedagens_reserva RENAME TO hospedagens_reserva_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_hospedagens_status RENAME TO hospedagens_status_hospedagem_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_indicacoes_indicado_cliente RENAME TO indicacoes_cliente_indicado_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_indicacoes_indicador RENAME TO indicacoes_cliente_indicador_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_indicacoes_pontos_creditados RENAME TO indicacoes_pontos_creditados_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_indicacoes_status RENAME TO indicacoes_status_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX indicacoes_cpf_indicado_unique RENAME TO indicacoes_cpf_indicado_key; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX indicacoes_reserva_unique RENAME TO indicacoes_reserva_id_key; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX indicacoes_transacao_unique RENAME TO indicacoes_transacao_pontos_id_key; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_logs_jornada_acao RENAME TO logs_jornada_acao_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_logs_jornada_cliente RENAME TO logs_jornada_cliente_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_logs_jornada_created_at RENAME TO logs_jornada_created_at_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_niveis_fidelidade_ativo_pontos RENAME TO niveis_fidelidade_ativo_pontos_minimos_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_otp_verificacoes_cliente_id RENAME TO otp_verificacoes_cliente_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_otp_verificacoes_documento RENAME TO otp_verificacoes_documento_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_otp_verificacoes_expira_em RENAME TO otp_verificacoes_expira_em_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_otp_verificacoes_status RENAME TO otp_verificacoes_status_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_otp_verificacoes_telefone RENAME TO otp_verificacoes_telefone_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_otp_verificacoes_ultimo_envio RENAME TO otp_verificacoes_ultimo_envio_em_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_premios_ativo RENAME TO premios_ativo_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_premios_categoria RENAME TO premios_categoria_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_premios_categoria_id RENAME TO premios_categoria_id_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_resgates_premios_codigo_status RENAME TO resgates_premios_codigo_status_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER INDEX idx_transacoes_pontos_status_liberar_em RENAME TO transacoes_pontos_status_liberar_em_idx; EXCEPTION WHEN undefined_object OR undefined_table OR duplicate_table OR duplicate_object THEN NULL; END;
    BEGIN ALTER TABLE historico_pontos RENAME CONSTRAINT historico_pontos_usuario_id_fkey TO historico_pontos_usuario_pontos_id_fkey; EXCEPTION WHEN undefined_object THEN NULL; END;
    BEGIN ALTER TABLE transacoes_pontos RENAME CONSTRAINT transacoes_pontos_usuario_id_fkey TO transacoes_pontos_usuario_pontos_id_fkey; EXCEPTION WHEN undefined_object THEN NULL; END;
END $$;
