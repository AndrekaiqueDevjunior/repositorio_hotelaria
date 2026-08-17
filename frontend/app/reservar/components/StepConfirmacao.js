'use client'

import Link from 'next/link'
import { Clock3, Crown, Phone, Printer, ShieldCheck } from 'lucide-react'
import { getSuiteDescription } from '../utils/suites'

const formatBRL = (valor) =>
  Number(valor || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const formatData = (valor) => {
  if (!valor) return ''
  const d = new Date(valor)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('pt-BR')
}

export default function StepConfirmacao({ reservaConfirmada, onNovaReserva }) {
  if (!reservaConfirmada) return null

  const { reserva, instrucoes } = reservaConfirmada
  const temDesconto = Number(reserva.valor_desconto || 0) > 0
  const total = Number(reserva.valor_total_com_desconto || reserva.valor_total || 0)

  return (
    <section className="jr-bloco jr-confirmado">
      <div className="jr-confirmado__selo">
        {/* brasão limpo, sem a cera vermelha: o carmim brigava com o azul
            e o dourado da marca nesta tela */}
        <img
          src="/images/jornada/marcas/brasao-hr.png"
          alt=""
          aria-hidden="true"
          className="jr-confirmado__brasao"
        />
      </div>

      <h2 className="jr-confirmado__titulo jr-ouro-metal">Sua suíte está guardada</h2>
      <p className="jr-lede jr-confirmado__lede">
        A reserva foi registrada no nome de {reserva.cliente}. Enviamos os detalhes por e-mail —
        na chegada, basta apresentar o código abaixo na recepção.
      </p>

      {/* o código é o objeto que o hóspede leva consigo */}
      <div className="jr-codigo-reserva">
        <span className="jr-codigo-reserva__rotulo">Código da reserva</span>
        <strong className="jr-codigo-reserva__valor">{reserva.codigo}</strong>
        <p className="jr-codigo-reserva__nota">
          Guarde este código para consultar ou alterar sua reserva
        </p>
      </div>

      <dl className="jr-ficha">
        <div>
          <dt>Hóspede</dt>
          <dd>{reserva.cliente}</dd>
        </div>

        <div>
          <dt>Acomodação</dt>
          <dd>
            {/* nome de vitrine, não o código do sistema ("LUXO") */}
            {getSuiteDescription(reserva.tipo_suite).titulo}
            <small>Quarto {reserva.quarto}</small>
          </dd>
        </div>

        <div>
          <dt>Check-in</dt>
          <dd>
            {formatData(reserva.checkin)}
            <small>a partir das {instrucoes?.checkin_horario || '12:00'}</small>
          </dd>
        </div>

        <div>
          <dt>Check-out</dt>
          <dd>
            {formatData(reserva.checkout)}
            <small>até as {instrucoes?.checkout_horario || '11:00'}</small>
          </dd>
        </div>

        <div>
          <dt>Estadia</dt>
          <dd>{reserva.num_diarias} {reserva.num_diarias === 1 ? 'diária' : 'diárias'}</dd>
        </div>

        <div>
          <dt>A pagar no check-in</dt>
          <dd>
            {formatBRL(total)}
            {temDesconto && <small>desconto de {formatBRL(reserva.valor_desconto)} aplicado</small>}
          </dd>
        </div>
      </dl>

      <ul className="jr-instrucoes">
        <li>
          <ShieldCheck size={16} strokeWidth={1.8} aria-hidden="true" />
          <span>{instrucoes?.documentos || 'Traga documento de identificação com foto'}</span>
        </li>
        <li>
          <Clock3 size={16} strokeWidth={1.8} aria-hidden="true" />
          <span>
            Chegando fora do horário? Avise a recepção que organizamos sua entrada.
          </span>
        </li>
        <li>
          <Phone size={16} strokeWidth={1.8} aria-hidden="true" />
          <span>Qualquer coisa, fale conosco: {instrucoes?.contato || '(22) 2648-5900'}</span>
        </li>
      </ul>

      <div className="jr-acoes-passo">
        <button type="button" onClick={() => window.print()} className="jr-btn jr-btn--contorno">
          <Printer size={17} strokeWidth={1.9} aria-hidden="true" />
          <span>Imprimir</span>
        </button>

        <Link href="/consultar-pontos" className="jr-btn">
          <Crown size={18} strokeWidth={1.8} aria-hidden="true" />
          <span>Ver minha Jornada Real</span>
        </Link>
      </div>

      <button
        type="button"
        onClick={onNovaReserva}
        className="jr-link"
        style={{ marginTop: 22, background: 'none', border: 0, cursor: 'pointer', fontSize: '0.844rem' }}
      >
        Fazer outra reserva
      </button>
    </section>
  )
}
