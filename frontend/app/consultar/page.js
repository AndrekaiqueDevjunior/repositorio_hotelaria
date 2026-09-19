'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowLeft, ArrowRight, LockKeyhole, User } from 'lucide-react'
import '../jornada-real.css'
import Reveal from '@/components/jornada/Reveal'
import LuzPonteiro from '@/components/jornada/LuzPonteiro'
import BotaoSom from '@/components/jornada/BotaoSom'
import { CantoMoldura, Fleurao } from '@/components/jornada/Ornamentos'

export default function ConsultarJornadaReal() {
  const router = useRouter()
  const [cpf, setCpf] = useState('')
  const [erro, setErro] = useState('')

  const formatarCPF = (valor) => {
    const numeros = valor.replace(/\D/g, '').slice(0, 11)

    if (numeros.length <= 3) return numeros
    if (numeros.length <= 6) return `${numeros.slice(0, 3)}.${numeros.slice(3)}`
    if (numeros.length <= 9) {
      return `${numeros.slice(0, 3)}.${numeros.slice(3, 6)}.${numeros.slice(6)}`
    }

    return `${numeros.slice(0, 3)}.${numeros.slice(3, 6)}.${numeros.slice(6, 9)}-${numeros.slice(9)}`
  }

  const handleSubmit = (event) => {
    event.preventDefault()

    const cpfLimpo = cpf.replace(/\D/g, '')
    if (cpfLimpo.length !== 11) {
      setErro('Digite um CPF válido.')
      return
    }

    setErro('')
    router.push(`/consultar-pontos?cpf=${cpfLimpo}`)
  }

  return (
    <main className="jr jr-porta-pagina">
      <LuzPonteiro densidade={2} />

      <header className="jr-barra">
        <div className="jr-shell jr-barra__interno">
          <div className="jr-barra__grupo">
            <Link href="/" className="jr-barra__voltar" aria-label="Voltar ao início">
              <ArrowLeft size={18} strokeWidth={1.9} />
            </Link>
            <Link href="/" className="jr-barra__marca" aria-label="Jornada Real — Hotel Real Cabo Frio">
              <img src="/images/logo-jornada-real.png" alt="Jornada Real" />
            </Link>
          </div>

          <div className="jr-barra__acoes">
            <BotaoSom />
          </div>
        </div>
      </header>

      <section className="jr-cena jr-porta" aria-labelledby="jr-porta-titulo">
        <div className="jr-feixe jr-porta__feixe" aria-hidden="true" />
        <div className="jr-poeira jr-porta__poeira" aria-hidden="true" />

        <div className="jr-shell jr-shell--estreito">
          <Reveal className="jr-cena__cabeca">
            <h1 id="jr-porta-titulo" className="jr-cena__titulo jr-ouro-metal">
              Consulte sua
              <br />
              Jornada Real
            </h1>
            <Fleurao largura={260} />
            <p className="jr-lede jr-porta__lede">
              Digite seu CPF e descubra o quanto você já avançou na sua jornada.
            </p>
          </Reveal>

          <Reveal delay={100} className="jr-porta__cartao">
            <CantoMoldura className="jr-porta__canto jr-porta__canto--se" tamanho={40} />
            <CantoMoldura className="jr-porta__canto jr-porta__canto--sd" tamanho={40} rotacao={90} />
            <CantoMoldura className="jr-porta__canto jr-porta__canto--id" tamanho={40} rotacao={180} />
            <CantoMoldura className="jr-porta__canto jr-porta__canto--ie" tamanho={40} rotacao={270} />

            <div className="jr-carta__palco jr-porta__chave-palco">
              <span className="jr-carta__foco" aria-hidden="true" />
              <span className="jr-carta__chao" aria-hidden="true" />
              <img
                src="/images/jornada/objetos/chave.png"
                alt=""
                aria-hidden="true"
                className="jr-objeto jr-carta__objeto jr-carta__objeto--chave"
              />
            </div>

            <form onSubmit={handleSubmit}>
              <label htmlFor="cpf" className="jr-porta__rotulo">
                Digite seu CPF para continuar
              </label>

              <div className="jr-porta__campo">
                <User size={19} strokeWidth={1.7} aria-hidden="true" />
                <input
                  id="cpf"
                  type="text"
                  inputMode="numeric"
                  autoComplete="off"
                  value={cpf}
                  onChange={(event) => {
                    setCpf(formatarCPF(event.target.value))
                    setErro('')
                  }}
                  placeholder="000.000.000-00"
                  maxLength={14}
                  aria-invalid={Boolean(erro)}
                />
              </div>

              {erro && <p className="jr-porta__erro">{erro}</p>}

              <button type="submit" className="jr-btn jr-porta__botao">
                <span>Ver minha jornada</span>
                <ArrowRight size={18} strokeWidth={2} />
              </button>

              <p className="jr-porta__privacidade">
                <LockKeyhole size={13} strokeWidth={2} aria-hidden="true" />
                Seus dados estão protegidos conosco.
              </p>
            </form>
          </Reveal>
        </div>
      </section>
    </main>
  )
}

