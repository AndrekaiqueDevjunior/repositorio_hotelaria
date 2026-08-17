'use client'

import { Check } from 'lucide-react'

const ETAPAS = [
  { numeral: 'I', label: 'Datas' },
  { numeral: 'II', label: 'Quarto' },
  { numeral: 'III', label: 'Dados' },
  { numeral: 'IV', label: 'Pagamento' },
  { numeral: 'V', label: 'Confirmação' },
]

export default function ProgressIndicator({ currentStep }) {
  return (
    <nav className="jr-shell jr-shell--estreito" aria-label="Etapas da reserva">
      <ol className="jr-passos">
        {ETAPAS.map((etapa, indice) => {
          const numero = indice + 1
          const estado = currentStep > numero ? 'feito' : currentStep === numero ? 'atual' : 'pendente'

          return (
            <li key={etapa.label} className="jr-passo" data-estado={estado}>
              <span className="jr-passo__marca" aria-hidden="true">
                {estado === 'feito' ? <Check size={17} strokeWidth={2.4} /> : etapa.numeral}
              </span>
              <span className="jr-passo__rotulo">{etapa.label}</span>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
