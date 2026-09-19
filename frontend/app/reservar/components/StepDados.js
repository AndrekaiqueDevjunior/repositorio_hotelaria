'use client'

import { useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, Check, Info, MessageCircle, ShieldCheck } from 'lucide-react'
import { demoAtivo } from '@/lib/demo-mock'
import { formatCPF, formatTelefone, onlyDigits } from '../utils/formatters'
import { getSuiteDescription } from '../utils/suites'

const formatBRL = (valor) =>
  Number(valor || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

// Estado da autenticação → selo. Usa o mesmo .jr-chip do resto da Jornada,
// em vez de pílulas coloridas de sistema (azul/âmbar/roxo/verde).
const SELO_AUTH = {
  idle: { texto: 'Aguardando CPF', estado: 'pendente' },
  not_found: { texto: 'Novo cadastro', estado: 'used' },
  found: { texto: 'Cadastro localizado', estado: 'used' },
  otp_sent: { texto: 'Código enviado', estado: 'used' },
  verified: { texto: 'Autenticado', estado: 'active' },
}

export default function StepDados({
  hospedeData,
  onUpdateField,
  onUpdateOtpCode,
  quartoSelecionado,
  numDiarias,
  customerAuth,
  onBuscarCpf,
  onCriarCadastro,
  onEnviarOtp,
  onValidarOtp,
  authLoading,
  isAuthenticated,
  onVoltar,
  onContinuar
}) {
  // lido só depois da montagem: demoAtivo() olha a URL do navegador e
  // avaliá-lo no servidor faria o HTML divergir do cliente
  const [emDemo, setEmDemo] = useState(false)
  useEffect(() => setEmDemo(demoAtivo()), [])

  const podeEditarDados = customerAuth.status === 'idle' || customerAuth.status === 'not_found'
  const selo = SELO_AUTH[customerAuth.status] || SELO_AUTH.idle
  const suite = getSuiteDescription(quartoSelecionado?.tipo)

  return (
    <div>
      {/* resumo da escolha */}
      <div className="jr-resumo">
        <div>
          <span className="jr-periodo__rotulo">Sua escolha</span>
          {/* sem número de quarto: o hóspede escolheu a categoria, a
              recepção designa a suíte na chegada */}
          <span className="jr-resumo__valor">{suite.titulo}</span>
        </div>

        <div style={{ textAlign: 'right' }}>
          <span className="jr-periodo__rotulo">
            {numDiarias} {numDiarias === 1 ? 'diária' : 'diárias'}
          </span>
          <span className="jr-resumo__total">{formatBRL(quartoSelecionado.preco_total)}</span>
        </div>
      </div>

      {/* ---------------------------------------------------- autenticação */}
      <section className="jr-bloco">
        <div className="jr-bloco__cabeca">
          <div>
            <h2 className="jr-bloco__titulo jr-ouro-metal">Quem se hospeda</h2>
            <p className="jr-bloco__sub">
              Confirmamos sua identidade por um código no WhatsApp. É o que garante que a
              reserva e os pontos fiquem no seu nome.
            </p>
          </div>
          <span className="jr-chip" data-estado={selo.estado}>{selo.texto}</span>
        </div>

        <div className="jr-campo-acao">
          <label className="jr-campo">
            <span className="jr-campo__rotulo">CPF</span>
            <input
              type="text"
              placeholder="000.000.000-00"
              value={hospedeData.documento}
              onChange={(e) => onUpdateField('documento', formatCPF(e.target.value))}
              disabled={!podeEditarDados}
              maxLength={14}
            />
          </label>

          <button
            type="button"
            onClick={onBuscarCpf}
            disabled={authLoading || customerAuth.status !== 'idle'}
            className="jr-btn jr-btn--contorno"
          >
            {authLoading && customerAuth.status === 'idle' ? 'Consultando...' : 'Consultar'}
          </button>
        </div>

        {/* CPF sem cadastro */}
        {customerAuth.status === 'not_found' && (
          <div style={{ marginTop: 22 }}>
            <div className="jr-aviso jr-aviso--atencao">
              <Info size={17} strokeWidth={1.9} aria-hidden="true" />
              <p>
                Primeira vez conosco. Preencha nome, e-mail e telefone abaixo — criamos seu
                cadastro e enviamos o código em seguida.
              </p>
            </div>

            <button
              type="button"
              onClick={onCriarCadastro}
              disabled={authLoading}
              className="jr-btn"
              style={{ marginTop: 14 }}
            >
              {authLoading ? 'Criando cadastro...' : 'Criar meu cadastro'}
            </button>
          </div>
        )}

        {/* cadastro localizado → envio e validação do código */}
        {customerAuth.customer && customerAuth.status !== 'verified' && (
          <div style={{ marginTop: 22 }}>
            <div className="jr-aviso">
              <MessageCircle size={17} strokeWidth={1.9} aria-hidden="true" />
              <p>
                <strong>{customerAuth.customer.nome_completo}</strong>
                <br />
                WhatsApp {formatTelefone(customerAuth.customer.telefone || '') || 'não cadastrado'}
              </p>
            </div>

            <button
              type="button"
              onClick={onEnviarOtp}
              disabled={authLoading}
              className="jr-btn jr-btn--contorno"
              style={{ marginTop: 14 }}
            >
              {customerAuth.status === 'otp_sent' ? 'Reenviar código' : 'Enviar código no WhatsApp'}
            </button>

            {customerAuth.status === 'otp_sent' && (
              <div style={{ marginTop: 22 }}>
                <span className="jr-campo__rotulo" style={{ display: 'block', marginBottom: 10 }}>
                  Código de 6 dígitos
                </span>

                {emDemo && (
                  <div className="jr-aviso jr-aviso--atencao" style={{ marginBottom: 14 }}>
                    <Info size={17} strokeWidth={1.9} aria-hidden="true" />
                    <p>
                      <strong>Modo demonstração:</strong> nenhum WhatsApp é enviado. Digite{' '}
                      <strong>qualquer 6 dígitos</strong> — por exemplo <strong>123456</strong>.
                    </p>
                  </div>
                )}

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
                  <input
                    type="text"
                    inputMode="numeric"
                    placeholder="000000"
                    className="jr-codigo-otp"
                    value={customerAuth.otpCode}
                    /*
                     * O código do OTP mora em customerAuth, não em
                     * hospedeData: precisa do setter próprio. Usar
                     * onUpdateField aqui gravava num campo inexistente e o
                     * código digitado nunca chegava na validação.
                     */
                    onChange={(e) => onUpdateOtpCode(onlyDigits(e.target.value).slice(0, 6))}
                    maxLength={6}
                  />

                  <button
                    type="button"
                    onClick={onValidarOtp}
                    disabled={authLoading}
                    className="jr-btn"
                  >
                    {authLoading ? 'Validando...' : 'Validar'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {isAuthenticated && (
          <div className="jr-aviso jr-aviso--ok" style={{ marginTop: 22 }}>
            <Check size={17} strokeWidth={2.2} aria-hidden="true" />
            <p>Identidade confirmada. A reserva já está vinculada ao seu CPF.</p>
          </div>
        )}
      </section>

      {/* ------------------------------------------------------- dados */}
      <section className="jr-bloco">
        <div className="jr-bloco__cabeca">
          <h2 className="jr-bloco__titulo jr-ouro-metal">Dados da estadia</h2>
        </div>

        <div className="jr-campos jr-campos--duplo">
          <label className="jr-campo">
            <span className="jr-campo__rotulo">Nome completo</span>
            <input
              type="text"
              placeholder="Como está no documento"
              value={hospedeData.nome_completo}
              onChange={(e) => onUpdateField('nome_completo', e.target.value)}
              disabled={!podeEditarDados}
            />
          </label>

          <label className="jr-campo">
            <span className="jr-campo__rotulo">E-mail</span>
            <input
              type="email"
              placeholder="seu@email.com"
              value={hospedeData.email}
              onChange={(e) => onUpdateField('email', e.target.value)}
              disabled={!podeEditarDados}
            />
            <span className="jr-campo__dica">A confirmação da reserva chega aqui</span>
          </label>

          <label className="jr-campo">
            <span className="jr-campo__rotulo">Telefone</span>
            <input
              type="text"
              placeholder="(00) 00000-0000"
              value={hospedeData.telefone}
              onChange={(e) => onUpdateField('telefone', formatTelefone(e.target.value))}
              disabled={!podeEditarDados}
              maxLength={15}
            />
          </label>

          <div className="jr-campos jr-campos--duplo" style={{ gap: 16 }}>
            <label className="jr-campo">
              <span className="jr-campo__rotulo">Adultos</span>
              <select
                value={hospedeData.num_hospedes}
                onChange={(e) => onUpdateField('num_hospedes', parseInt(e.target.value))}
              >
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </label>

            <label className="jr-campo">
              <span className="jr-campo__rotulo">Crianças</span>
              <select
                value={hospedeData.num_criancas}
                onChange={(e) => onUpdateField('num_criancas', parseInt(e.target.value))}
              >
                {[0, 1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
              <span className="jr-campo__dica">Até 12 anos</span>
            </label>
          </div>

          <label className="jr-campo jr-campo--largo">
            <span className="jr-campo__rotulo">Recados para a recepção</span>
            <textarea
              placeholder="Chegada tarde da noite, andar alto, restrição alimentar, comemoração..."
              value={hospedeData.observacoes}
              onChange={(e) => onUpdateField('observacoes', e.target.value)}
              rows={3}
            />
            <span className="jr-campo__dica">Opcional — fazemos o possível para atender</span>
          </label>
        </div>

        <div className="jr-acoes-passo">
          <button type="button" onClick={onVoltar} className="jr-btn jr-btn--contorno">
            <ArrowLeft size={17} strokeWidth={1.9} aria-hidden="true" />
            <span>Voltar</span>
          </button>

          <button
            type="button"
            onClick={onContinuar}
            disabled={!isAuthenticated}
            className="jr-btn"
          >
            <ShieldCheck size={17} strokeWidth={1.9} aria-hidden="true" />
            <span>{isAuthenticated ? 'Ir para o pagamento' : 'Confirme sua identidade'}</span>
            {isAuthenticated && <ArrowRight size={17} strokeWidth={1.9} aria-hidden="true" />}
          </button>
        </div>
      </section>
    </div>
  )
}
