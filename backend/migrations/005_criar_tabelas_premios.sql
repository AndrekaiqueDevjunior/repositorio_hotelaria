CREATE TABLE IF NOT EXISTS public.premios (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT NULL,
    preco_em_pontos INT NOT NULL,
    preco_em_rp INT NOT NULL DEFAULT 0,
    categoria TEXT NOT NULL DEFAULT 'GERAL',
    estoque INT NULL,
    imagem_url TEXT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_premios_ativo ON public.premios (ativo);
CREATE INDEX IF NOT EXISTS idx_premios_categoria ON public.premios (categoria);

CREATE TABLE IF NOT EXISTS public.resgates_premios (
    id SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL,
    premio_id INT NOT NULL,
    pontos_usados INT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDENTE',
    funcionario_id INT NULL,
    funcionario_entrega_id INT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_resgates_premios_cliente FOREIGN KEY (cliente_id) REFERENCES public.clientes(id) ON DELETE CASCADE,
    CONSTRAINT fk_resgates_premios_premio FOREIGN KEY (premio_id) REFERENCES public.premios(id) ON DELETE RESTRICT,
    CONSTRAINT fk_resgates_premios_funcionario FOREIGN KEY (funcionario_id) REFERENCES public.funcionarios(id) ON DELETE SET NULL,
    CONSTRAINT fk_resgates_premios_funcionario_entrega FOREIGN KEY (funcionario_entrega_id) REFERENCES public.funcionarios(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_resgates_premios_cliente ON public.resgates_premios (cliente_id);
CREATE INDEX IF NOT EXISTS idx_resgates_premios_premio ON public.resgates_premios (premio_id);
CREATE INDEX IF NOT EXISTS idx_resgates_premios_status ON public.resgates_premios (status);
