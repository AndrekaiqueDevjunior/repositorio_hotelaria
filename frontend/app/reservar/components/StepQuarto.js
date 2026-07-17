'use client'

import { getSuiteDescription, getSuiteImage } from '../utils/suites'

export default function StepQuarto({
  searchData,
  tiposDisponiveis,
  numDiarias,
  onSelecionarQuarto,
  onVoltar
}) {
  return (
    <div className="space-y-6">
      {/* Resumo do período */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 text-white flex items-center justify-between">
        <div>
          <p className="text-sm opacity-80">Período selecionado</p>
          <p className="font-bold">
            {new Date(searchData.data_checkin).toLocaleDateString('pt-BR')} → {new Date(searchData.data_checkout).toLocaleDateString('pt-BR')}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm opacity-80">Duração</p>
          <p className="font-bold text-yellow-400">{numDiarias} {numDiarias === 1 ? 'diária' : 'diárias'}</p>
        </div>
        <button
          onClick={onVoltar}
          className="px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-all"
        >
          ✏️ Alterar
        </button>
      </div>

      <h2 className="text-2xl font-bold text-white text-center">🛏️ Escolha sua Suíte</h2>

      {tiposDisponiveis.length === 0 ? (
        <div className="bg-white rounded-xl p-8 text-center text-gray-900">
          <p className="text-gray-600">Não há quartos disponíveis para as datas selecionadas.</p>
          <button
            onClick={onVoltar}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg"
          >
            Tentar outras datas
          </button>
        </div>
      ) : (
        <div className="grid gap-6">
          {tiposDisponiveis.map((tipo) => {
            const info = getSuiteDescription(tipo.tipo)
            const image = getSuiteImage(tipo.tipo)

            return (
              <div key={tipo.tipo} className="bg-white rounded-2xl shadow-xl overflow-hidden text-gray-900">
                <div className="md:flex">
                  {/* Imagem */}
                  <div className="md:w-1/3 relative h-48 md:h-auto">
                    <img
                      src={image}
                      alt={info.titulo}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                    <div className="absolute bottom-4 left-4 text-white">
                      <span className="text-2xl font-bold">{info.titulo}</span>
                    </div>
                  </div>

                  {/* Detalhes */}
                  <div className="md:w-2/3 p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-xl font-bold text-gray-800">{info.titulo}</h3>
                        <p className="text-gray-600">{info.descricao}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-500">a partir de</p>
                        <p className="text-2xl font-bold text-green-600">
                          R$ {tipo.preco_diaria.toFixed(2)}
                        </p>
                        <p className="text-sm text-gray-500">por noite</p>
                      </div>
                    </div>

                    {/* Amenidades */}
                    <div className="flex flex-wrap gap-2 mb-4">
                      {info.amenidades.map((amenidade, i) => (
                        <span key={i} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                          {amenidade}
                        </span>
                      ))}
                    </div>

                    {/* Quartos disponíveis */}
                    <div className="border-t pt-4">
                      <p className="text-sm text-gray-600 mb-2">
                        {tipo.quantidade_disponivel} {tipo.quantidade_disponivel === 1 ? 'quarto disponível' : 'quartos disponíveis'}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {tipo.quartos.slice(0, 5).map((quarto) => (
                          <button
                            key={quarto.numero}
                            onClick={() => onSelecionarQuarto(tipo, quarto)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all flex items-center gap-2"
                          >
                            Quarto {quarto.numero}
                            <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
                          </button>
                        ))}
                        {tipo.quartos.length > 5 && (
                          <span className="px-4 py-2 text-gray-500">+{tipo.quartos.length - 5} mais</span>
                        )}
                      </div>
                    </div>

                    {/* Total */}
                    <div className="mt-4 p-3 bg-yellow-50 rounded-lg flex justify-between items-center">
                      <span className="text-gray-700">Total para {numDiarias} {numDiarias === 1 ? 'diária' : 'diárias'}:</span>
                      <span className="text-xl font-bold text-green-600">R$ {tipo.preco_total.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
