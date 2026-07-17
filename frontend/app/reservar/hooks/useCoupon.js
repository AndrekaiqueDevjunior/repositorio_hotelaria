import { useState, useMemo } from 'react'

export const useCoupon = (quartoSelecionado) => {
  const [cupomCodigo, setCupomCodigo] = useState('')
  const [cupomValidacao, setCupomValidacao] = useState(null)
  const [cupomLoading, setCupomLoading] = useState(false)

  const aplicarDesconto = (validacao) => {
    setCupomValidacao(validacao)
  }

  const limparCupom = () => {
    setCupomCodigo('')
    setCupomValidacao(null)
  }

  const reset = () => {
    setCupomCodigo('')
    setCupomValidacao(null)
    setCupomLoading(false)
  }

  return {
    cupomCodigo,
    setCupomCodigo,
    cupomValidacao,
    setCupomValidacao,
    cupomLoading,
    setCupomLoading,
    aplicarDesconto,
    limparCupom,
    reset
  }
}
