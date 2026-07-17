import { useState, useEffect } from 'react'

const initialSearchData = {
  data_checkin: '',
  data_checkout: '',
  num_hospedes: 1
}

export const useReservationForm = () => {
  const [searchData, setSearchData] = useState(initialSearchData)
  const [tiposDisponiveis, setTiposDisponiveis] = useState([])
  const [numDiarias, setNumDiarias] = useState(0)
  const [quartoSelecionado, setQuartoSelecionado] = useState(null)
  const [loading, setLoading] = useState(false)

  const today = new Date().toISOString().split('T')[0]

  const handleSearchDataChange = (field, value) => {
    setSearchData((current) => ({ ...current, [field]: value }))
    if (field === 'data_checkin' || field === 'data_checkout') {
      setQuartoSelecionado(null)
      setTiposDisponiveis([])
    }
  }

  const selecionarQuarto = (tipo, quarto) => {
    setQuartoSelecionado({
      numero: quarto.numero,
      tipo: tipo.tipo,
      preco_diaria: tipo.preco_diaria,
      preco_total: tipo.preco_total
    })
  }

  const resetarBusca = () => {
    setSearchData(initialSearchData)
    setTiposDisponiveis([])
    setNumDiarias(0)
    setQuartoSelecionado(null)
  }

  return {
    searchData,
    setSearchData,
    handleSearchDataChange,
    tiposDisponiveis,
    setTiposDisponiveis,
    numDiarias,
    setNumDiarias,
    quartoSelecionado,
    setQuartoSelecionado,
    selecionarQuarto,
    loading,
    setLoading,
    today,
    resetarBusca
  }
}
