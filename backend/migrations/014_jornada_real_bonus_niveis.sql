-- Jornada Real: garante bonus de pontos por nivel em bancos ja migrados.

INSERT INTO niveis_fidelidade (
    codigo, nome, pontos_minimos, bonus_percentual, beneficios, ordem, ativo, created_at, updated_at
)
VALUES
    (0, 'ESSENCIA', 0, 0, '{"descricao": "Entrada na Jornada Real"}', 0, TRUE, NOW(), NOW()),
    (1, 'EXPERIENCIA', 50, 20, '{"descricao": "Beneficios de evolucao da Jornada Real", "pontos_por_reserva": "+20%"}', 1, TRUE, NOW(), NOW()),
    (2, 'REAL', 90, 40, '{"descricao": "Nivel maximo da Jornada Real", "pontos_por_reserva": "+40%"}', 2, TRUE, NOW(), NOW())
ON CONFLICT (codigo) DO UPDATE
SET nome = EXCLUDED.nome,
    pontos_minimos = EXCLUDED.pontos_minimos,
    bonus_percentual = EXCLUDED.bonus_percentual,
    beneficios = EXCLUDED.beneficios,
    ordem = EXCLUDED.ordem,
    ativo = EXCLUDED.ativo,
    updated_at = NOW();
