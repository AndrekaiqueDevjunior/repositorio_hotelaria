export const formatCPF = (value) => {
  const numbers = (value || '').replace(/\D/g, '').substring(0, 11)
  if (numbers.length <= 3) return numbers
  if (numbers.length <= 6) return `${numbers.slice(0, 3)}.${numbers.slice(3)}`
  if (numbers.length <= 9) return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6)}`
  return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6, 9)}-${numbers.slice(9)}`
}

export const formatTelefone = (value) => {
  const numbers = (value || '').replace(/\D/g, '').substring(0, 11)
  if (numbers.length <= 2) return numbers
  if (numbers.length <= 7) return `(${numbers.slice(0, 2)}) ${numbers.slice(2)}`
  return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(7)}`
}

export const formatCurrency = (value) => {
  return `R$ ${Number(value || 0).toFixed(2)}`
}

export const onlyDigits = (value) => {
  return (value || '').replace(/\D/g, '')
}
