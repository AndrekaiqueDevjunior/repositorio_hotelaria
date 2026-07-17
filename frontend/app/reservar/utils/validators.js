import { onlyDigits } from './formatters'

export const isValidCPF = (value) => {
  const cpf = onlyDigits(value)
  if (cpf.length !== 11 || cpf === cpf[0]?.repeat(11)) return false

  const calcDigit = (base) => {
    const sum = base
      .split('')
      .reduce((total, digit, index) => total + Number(digit) * (base.length + 1 - index), 0)
    const rest = (sum * 10) % 11
    return rest === 10 ? '0' : String(rest)
  }

  return cpf.slice(9) === `${calcDigit(cpf.slice(0, 9))}${calcDigit(cpf.slice(0, 10))}`
}

export const isValidEmail = (email) => {
  return email?.includes('@') || false
}

export const isValidTelefone = (telefone) => {
  const digits = onlyDigits(telefone)
  return digits.length >= 10
}

export const normalizeCouponCode = (value) => {
  return String(value || '')
    .toUpperCase()
    .replace(/[^A-Z0-9_-]/g, '')
    .slice(0, 50)
}
