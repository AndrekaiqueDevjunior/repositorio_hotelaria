'use client'

import Link from 'next/link'

/*
 * Barra de navegação inferior das telas do hóspede.
 *
 * Os destinos são exatamente os do mapa de clicáveis do projeto: mudar um
 * href aqui muda a navegação de todas as telas. O CPF, quando existe na URL,
 * viaja junto — é assim que /consultar-pontos e /resgate_dos_premios se
 * encontram sem pedir o documento de novo.
 *
 * O estilo vive em app/jornada-real.css (.jr-nav*), junto com o resto da
 * linguagem visual.
 */
const ITENS = [
  { label: 'Início', href: '/', comCpf: false },
  { label: 'Minha Jornada', href: '/consultar-pontos', comCpf: true },
  { label: 'Prêmios', href: '/resgate_dos_premios', comCpf: true },
  { label: 'Perfil', href: '/entrar-jornada-real', comCpf: false },
]

export default function JornadaNav({ atual = '/', cpf = '' }) {
  const montarHref = (item) => {
    if (!item.comCpf || !cpf) return item.href
    return `${item.href}?cpf=${encodeURIComponent(cpf)}`
  }

  return (
    <nav className="jr-nav" aria-label="Navegação da Jornada Real">
      <ul className="jr-nav__lista">
        {ITENS.map((item) => {
          const ativo = item.href === atual
          return (
            <li key={item.href} className="jr-nav__item">
              <Link
                href={montarHref(item)}
                className="jr-nav__link"
                data-ativo={ativo ? 'sim' : 'nao'}
                aria-current={ativo ? 'page' : undefined}
              >
                <span className="jr-nav__marca" aria-hidden="true" />
                {item.label}
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
