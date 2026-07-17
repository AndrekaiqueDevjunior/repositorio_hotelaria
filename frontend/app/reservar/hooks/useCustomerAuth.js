import { useState } from 'react'

const initialState = {
  status: 'idle',
  customer: null,
  otpId: '',
  otpCode: '',
  accessToken: '',
  expiresInSeconds: 0,
}

export const useCustomerAuth = () => {
  const [customerAuth, setCustomerAuth] = useState(initialState)
  const [authLoading, setAuthLoading] = useState(false)

  const reset = () => {
    setCustomerAuth(initialState)
  }

  const setCustomer = (customer, status = 'found') => {
    setCustomerAuth((current) => ({
      ...current,
      status,
      customer
    }))
  }

  const setOtpSent = (otpId, expiresInSeconds = 300) => {
    setCustomerAuth((current) => ({
      ...current,
      status: 'otp_sent',
      otpId,
      otpCode: '',
      accessToken: '',
      expiresInSeconds
    }))
  }

  const updateOtpCode = (code) => {
    setCustomerAuth((current) => ({
      ...current,
      otpCode: code
    }))
  }

  const setVerified = (customer, accessToken) => {
    setCustomerAuth((current) => ({
      ...current,
      status: 'verified',
      customer,
      accessToken,
      otpCode: '',
      otpId: ''
    }))
  }

  const setNotFound = () => {
    setCustomerAuth((current) => ({
      ...current,
      status: 'not_found'
    }))
  }

  const resetOtp = () => {
    setCustomerAuth((current) => ({
      ...current,
      otpId: '',
      otpCode: '',
      accessToken: ''
    }))
  }

  const isAuthenticated = Boolean(customerAuth.accessToken && customerAuth.customer)

  return {
    customerAuth,
    setCustomerAuth,
    authLoading,
    setAuthLoading,
    reset,
    setCustomer,
    setOtpSent,
    updateOtpCode,
    setVerified,
    setNotFound,
    resetOtp,
    isAuthenticated
  }
}
