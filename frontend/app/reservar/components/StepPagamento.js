'use client'

import { ArrowLeft, Check, Crown, CreditCard, Info } from 'lucide-react'
import { formatCurrency } from '../utils/formatters'
import { getSuiteDescription } from '../utils/suites'

const formatData = (valor) => {
  if (!valor) return ''
  const d = new Date(valor)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('pt-BR')
}

export default function StepPagamento({
  hospedeData,
  quartoSelecionado,
  searchData,
  numDiarias,
  valoresReserva,
  pontosEstimados,
  cupomCodigo,
  cupomValidacao,
  cupomLoading,
  onCupomCodigoChange,
  onValidarCupom,
  onVoltar,
  onConfirmarReserva,
  loading
}) {
  const suite = getSuiteDescription(quartoSelecionado.tipo)
  const rotuloDiarias = `${numDiarias} ${numDiarias === 1 ? 'diária' : 'diárias'}`

  return (
    <div>
      {/* resumo da reserva */}
      <div className="jr-resumo">
        <div>
          <span className="jr-periodo__rotulo">{hospedeData.nome_completo || 'Hóspede'}</span>
          <span className="jr-resumo__valor">{suite.titulo}</span>
          <span className="jr-campo__dica" style={{ display: 'block', marginTop: 4 }}>
            {formatData(searchData.data_checkin)} — {formatData(searchData.data_checkout)} · {rotuloDiarias}
          </span>
        </div>

        <div style={{ textAlign: 'right' }}>
          <span className="jr-periodo__rotulo">Total</span>
          <span className="jr-resumo__total">{formatCurrency(valoresReserva.total)}</span>
        </div>
      </div>

      {/* ------------------------------------------------------- cupom */}
      <section className="jr-bloco">
        <div className="jr-bloco__cabeca">
          <div>
            <h2 className="jr-bloco__titulo jr-ouro-metal">Tem um convite?</h2>
            <p className="jr-bloco__sub">
              Cupom de desconto ou Convite Real de quem já é da corte.
            </p>
          </div>
        </div>

        <div className="jr-campo-acao">
          <label className="jr-campo">
            <span className="jr-campo__rotulo">Código</span>
            <input
              type="text"
              value={cupomCodigo}
              onChange={(e) => onCupomCodigoChange(e.target.value)}
              placeholder="AMIGO_XXXXXX"
              maxLength={50}
              style={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}
            />
          </label>

          <button
            type="button"
            onClick={onValidarCupom}
            disabled={cupomLoading || !cupomCodigo}
            className="jr-btn jr-btn--contorno"
          >
            {cupomLoading ? 'Validando...' : 'Aplicar'}
          </button>
        </div>

        {cupomValidacao && (
          <div
            className={`jr-aviso ${cupomValidacao.valido ? 'jr-aviso--ok' : ''}`}
            style={{ marginTop: 18 }}
          >
            {cupomValidacao.valido ? (
              <Check size={17} strokeWidth={2.2} aria-hidden="true" />
            ) : (
              <Info size={17} strokeWidth={1.9} aria-hidden="true" />
            )}
            <p>
              {cupomValidacao.mensagem}
              {cupomValidacao.valido && valoresReserva.desconto > 0 && (
                <>
                  <br />
                  Economia de <strong>{formatCurrency(valoresReserva.desconto)}</strong> nesta estadia.
                </>
              )}
            </p>
          </div>
        )}

        {pontosEstimados && (
          <div className="jr-pontos-previsao" style={{ marginTop: 18 }}>
            <p className="jr-pontos-previsao__titulo">
              <Crown size={14} strokeWidth={1.9} aria-hidden="true" />
              O que esta estadia rende
            </p>
            <div className="jr-pontos-previsao__grade">
              <span>
                <b>{pontosEstimados.pontosN}</b> pontos de nível
              </span>
              <span>
                <b>{pontosEstimados.pontosR}</b> pontos de resgate
              </span>
              {pontosEstimados.multiplicador > 1 && (
                <span>
                  Nível {pontosEstimados.nivelNome || ''} rende <b>{pontosEstimados.multiplicador}x</b>
                </span>
              )}
            </div>
          </div>
        )}
      </section>

      {/* ---------------------------------------------------- pagamento */}
      <section className="jr-bloco">
        <div className="jr-bloco__cabeca">
          <div>
            <h2 className="jr-bloco__titulo jr-ouro-metal">Como você paga</h2>
            <p className="jr-bloco__sub">
              Nada é cobrado agora. O pagamento acontece na recepção, no check-in.
            </p>
          </div>
        </div>

        <div className="jr-forma-pgto">
          <CreditCard size={20} strokeWidth={1.8} aria-hidden="true" />
          <div>
            <p className="jr-forma-pgto__nome">Na recepção, pela maquininha</p>
            <p className="jr-forma-pgto__nota">
              Cartão de crédito, débito ou PIX no momento da chegada.
            </p>
          </div>
          <Check className="jr-forma-pgto__marca" size={19} strokeWidth={2.2} aria-hidden="true" />
        </div>

        <div className="jr-aviso" style={{ marginTop: 16 }}>
          <Info size={17} strokeWidth={1.9} aria-hidden="true" />
          <p>
            Sua suíte fica <strong>guardada no seu nome</strong> desde já. Cancelamentos até 24h
            antes do check-in não têm custo nenhum.
          </p>
        </div>

        {/* --------------------------------------------------- conta */}
        <div className="jr-conta" style={{ marginTop: 26 }}>
          <div className="jr-conta__linha">
            <span>Diárias ({rotuloDiarias})</span>
            <b>{formatCurrency(valoresReserva.subtotal)}</b>
          </div>

          {valoresReserva.desconto > 0 && (
            <div className="jr-conta__linha jr-conta__linha--desconto">
              <span>
                Desconto
                {valoresReserva.percentualCupom ? ` (${valoresReserva.percentualCupom}%)` : ''}
              </span>
              <b>−{formatCurrency(valoresReserva.desconto)}</b>
            </div>
          )}

          <div className="jr-conta__total">
            <span>A pagar no check-in</span>
            <b className="jr-ouro-metal">{formatCurrency(valoresReserva.total)}</b>
          </div>
        </div>

        <div className="jr-acoes-passo">
          <button type="button" onClick={onVoltar} className="jr-btn jr-btn--contorno">
            <ArrowLeft size={17} strokeWidth={1.9} aria-hidden="true" />
            <span>Voltar</span>
          </button>

          <button
            type="button"
            onClick={onConfirmarReserva}
            disabled={loading}
            className="jr-btn"
          >
            <Crown size={18} strokeWidth={1.8} aria-hidden="true" />
            <span>{loading ? 'Confirmando...' : 'Confirmar minha reserva'}</span>
          </button>
        </div>
      </section>
    </div>
  )
}
