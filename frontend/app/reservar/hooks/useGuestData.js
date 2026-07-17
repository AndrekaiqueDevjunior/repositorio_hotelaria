import { useState } from 'react'

const initialGuestData = {
  nome_completo: '',
  documento: '',
  email: '',
  telefone: '',
  num_hospedes: 1,
  num_criancas: 0,
  observacoes: ''
}

export const useGuestData = () => {
  const [hospedeData, setHospedeData] = useState(initialGuestData)

  const updateField = (field, value) => {
    setHospedeData((current) => ({
      ...current,
      [field]: value
    }))
  }

  const resetarDados = () => {
    setHospedeData(initialGuestData)
  }

  const applyCustomerData = (customer) => {
    setHospedeData((current) => ({
      ...current,
      nome_completo: customer?.nome_completo || current.nome_completo,
      documento: customer?.documento || current.documento,
      email: customer?.email || current.email,
      telefone: customer?.telefone || current.telefone,
    }))
  }

  return {
    hospedeData,
    setHospedeData,
    updateField,
    resetarDados,
    applyCustomerData
  }
}
