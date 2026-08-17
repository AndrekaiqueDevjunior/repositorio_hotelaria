'use client'

import { ArrowLeft, KeyRound } from 'lucide-react'
import { getSuiteDescription, getSuiteImage } from '../utils/suites'

const formatBRL = (valor) =>
  Number(valor || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const formatData = (valor) => {
  if (!valor) return ''
  const data = new Date(valor)
  return Number.isNaN(data.getTime()) ? '' : data.toLocaleDateString('pt-BR')
}

export default function StepQuarto({
  searchData,
  tiposDisponiveis,
  numDiarias,
  onSelecionarQuarto,
  onVoltar
}) {
  return (
    <div>
      {/* período escolhido */}
      <div className="jr-periodo">
        <div>
          <span className="jr-periodo__rotulo">Período</span>
          <span className="jr-periodo__valor">
            {formatData(searchData.data_checkin)} — {formatData(searchData.data_checkout)}
          </span>
        </div>

        <div>
          <span className="jr-periodo__rotulo">Estadia</span>
          <span className="jr-periodo__valor jr-periodo__valor--ouro">
            {numDiarias} {numDiarias === 1 ? 'diária' : 'diárias'}
          </span>
        </div>

        <button type="button" onClick={onVoltar} className="jr-btn jr-btn--contorno jr-btn--pequeno">
          <ArrowLeft size={15} strokeWidth={2} aria-hidden="true" />
          <span style={{ marginLeft: 8 }}>Trocar datas</span>
        </button>
      </div>

      {tiposDisponiveis.length === 0 ? (
        <div className="jr-sem-quarto" style={{ marginTop: 28 }}>
          <p className="jr-lede">
            Nenhuma suíte livre nesse período. Ajuste as datas e a corte volta a receber.
          </p>
          <button type="button" onClick={onVoltar} className="jr-btn">
            Escolher outras datas
          </button>
        </div>
      ) : (
        <ol className="jr-suites">
          {tiposDisponiveis.map((tipo) => {
            const info = getSuiteDescription(tipo.tipo)
            const imagem = getSuiteImage(tipo.tipo)
            const quartos = Array.isArray(tipo.quartos) ? tipo.quartos : []

            return (
              <li className="jr-suite" key={tipo.tipo}>
                <figure className="jr-suite__foto">
                  <img src={imagem} alt={info.titulo} loading="lazy" />
                  <span className="jr-suite__veu" aria-hidden="true" />
                  <figcaption className="jr-suite__nome-foto">{info.titulo}</figcaption>
                </figure>

                <div className="jr-suite__corpo">
                  <div className="jr-suite__topo">
                    <div>
                      <h3 className="jr-suite__titulo jr-ouro-metal">{info.titulo}</h3>
                      <p className="jr-suite__descricao">{info.descricao}</p>
                    </div>

                    <p className="jr-suite__preco">
                      <span className="jr-suite__preco-rotulo">A partir de</span>
                      <strong className="jr-suite__preco-valor jr-ouro-metal">
                        {formatBRL(tipo.preco_diaria)}
                      </strong>
                      <span className="jr-suite__preco-nota">por noite</span>
                    </p>
                  </div>

                  <ul className="jr-suite__amenidades">
                    {info.amenidades.map((amenidade) => (
                      <li key={amenidade}>{amenidade}</li>
                    ))}
                  </ul>

                  <div className="jr-suite__rodape">
                    <p className="jr-suite__total">
                      {numDiarias} {numDiarias === 1 ? 'diária' : 'diárias'}
                      <strong>{formatBRL(tipo.preco_total)}</strong>
                    </p>

                    <div className="jr-suite__escolha">
                      {/*
                       * O hóspede escolhe a categoria, não o número do quarto:
                       * são 52 suítes no hotel, listar cada uma seria uma
                       * parede de botões. A recepção designa o quarto na
                       * chegada — aqui só reservamos a primeira livre da
                       * categoria para manter o contrato do backend.
                       */}
                      <span className="jr-suite__disponibilidade">
                        {tipo.quantidade_disponivel === 1
                          ? 'Última disponível'
                          : `${tipo.quantidade_disponivel} disponíveis`}
                      </span>

                      <button
                        type="button"
                        className="jr-btn"
                        disabled={quartos.length === 0}
                        onClick={() => onSelecionarQuarto(tipo, quartos[0])}
                      >
                        <KeyRound size={16} strokeWidth={1.9} aria-hidden="true" />
                        <span>Escolher esta suíte</span>
                      </button>
                    </div>
                  </div>
                </div>
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
