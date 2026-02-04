/**
 * Painel de Controle de Acessibilidade
 * Permite aos usuários ajustar as configurações de acessibilidade
 */

'use client'

import { useEffect, useState } from 'react'
import { Eye, EyeOff, Keyboard, Monitor, Type, Volume2, VolumeX, Check, X } from 'lucide-react'

const AccessibilityPanel = ({ isOpen, onClose, onSettingsChange }) => {
  const [settings, setSettings] = useState({
    screenReader: false,
    highContrast: false,
    reducedMotion: false,
    largeText: false,
    keyboardNavigation: false,
    showFocusIndicators: true,
    announcements: true,
    autoSkipLinks: true
  })

  const handleSettingChange = (key, value) => {
    const newSettings = { ...settings, [key]: value }
    setSettings(newSettings)
    onSettingsChange?.(newSettings)
    
    // Aplicar configurações imediatamente
    applySettings(newSettings)
  }

  const applySettings = (currentSettings) => {
    // Alto contraste
    document.body.classList.toggle('high-contrast', currentSettings.highContrast)
    
    // Movimento reduzido
    document.body.classList.toggle('reduced-motion', currentSettings.reducedMotion)
    
    // Texto grande
    document.body.classList.toggle('large-text', currentSettings.largeText)
    
    // Indicadores de foco
    document.body.classList.toggle('show-focus', currentSettings.showFocusIndicators)
    
    // Skip links
    const skipLinks = document.querySelector('.skip-links')
    if (skipLinks) {
      skipLinks.style.display = currentSettings.autoSkipLinks ? 'block' : 'none'
    }
  }

  const resetSettings = () => {
    const defaultSettings = {
      screenReader: false,
      highContrast: false,
      reducedMotion: false,
      largeText: false,
      keyboardNavigation: false,
      showFocusIndicators: true,
      announcements: true,
      autoSkipLinks: true
    }
    
    setSettings(defaultSettings)
    onSettingsChange?.(defaultSettings)
    applySettings(defaultSettings)
  }

  const SettingToggle = ({ icon, label, description, settingKey, settingValue }) => (
    <div className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors">
      <div className="flex items-center space-x-3">
        <div className="text-gray-600">
          {icon}
        </div>
        <div>
          <div className="font-medium text-gray-900">{label}</div>
          <div className="text-sm text-gray-500">{description}</div>
        </div>
      </div>
      <button
        onClick={() => handleSettingChange(settingKey, !settingValue)}
        className={`
          relative inline-flex h-6 w-11 items-center rounded-full transition-colors
          ${settingValue ? 'bg-blue-600' : 'bg-gray-200'}
        `}
        role="switch"
        aria-checked={settingValue}
        aria-label={`${label} ${settingValue ? 'ativado' : 'desativado'}`}
      >
        <span
          className={`
            inline-block h-4 w-4 transform rounded-full bg-white transition-transform
            ${settingValue ? 'translate-x-6' : 'translate-x-1'}
          `}
        />
      </button>
    </div>
  )

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Acessibilidade</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Fechar painel de acessibilidade"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Leitor de Tela */}
          <SettingToggle
            icon={<Volume2 className="w-5 h-5" />}
            label="Leitor de Tela"
            description="Anúncios de navegação e mudanças de estado"
            settingKey="screenReader"
            settingValue={settings.screenReader}
          />

          {/* Alto Contraste */}
          <SettingToggle
            icon={<Monitor className="w-5 h-5" />}
            label="Alto Contraste"
            description="Cores com alto contraste para melhor visibilidade"
            settingKey="highContrast"
            settingValue={settings.highContrast}
          />

          {/* Movimento Reduzido */}
          <SettingToggle
            icon={<Eye className="w-5 h-5" />}
            label="Movimento Reduzido"
            description="Reduz animações e transições"
            settingKey="reducedMotion"
            settingValue={settings.reducedMotion}
          />

          {/* Texto Grande */}
          <SettingToggle
            icon={<Type className="w-5 h-5" />}
            label="Texto Grande"
            description="Aumenta o tamanho do texto para melhor legibilidade"
            settingKey="largeText"
            settingValue={settings.largeText}
          />

          {/* Navegação por Teclado */}
          <SettingToggle
            icon={<Keyboard className="w-5 h-5" />}
            label="Navegação por Teclado"
            description="Atalhos e navegação otimizada para teclado"
            settingKey="keyboardNavigation"
            settingValue={settings.keyboardNavigation}
          />

          {/* Indicadores de Foco */}
          <SettingToggle
            icon={<Eye className="w-5 h-5" />}
            label="Indicadores de Foco"
            description="Mostra claramente qual elemento está focado"
            settingKey="showFocusIndicators"
            settingValue={settings.showFocusIndicators}
          />

          {/* Anúncios */}
          <SettingToggle
            icon={<Volume2 className="w-5 h-5" />}
            label="Anúncios"
            description="Anúncios de mudanças e navegação"
            settingKey="announcements"
            settingValue={settings.announcements}
          />

          {/* Skip Links */}
          <SettingToggle
            icon={<Keyboard className="w-5 h-5" />}
            label="Links de Pulo"
            description="Atalhos para pular para conteúdo principal"
            settingKey="autoSkipLinks"
            settingValue={settings.autoSkipLinks}
          />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <button
            onClick={resetSettings}
            className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
          >
            Restaurar Padrão
          </button>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Aplicar
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Botão Flutuante de Acessibilidade
export const AccessibilityButton = ({ onClick }) => (
  <button
    onClick={onClick}
    className="fixed bottom-4 right-4 z-40 p-3 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-all hover:scale-110 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
    aria-label="Abrir configurações de acessibilidade"
    title="Configurações de Acessibilidade"
  >
    <Keyboard className="w-6 h-6" />
  </button>
)

// Componente Principal
const AccessibilityManager = ({ children }) => {
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const [currentSettings, setCurrentSettings] = useState({})

  const handleSettingsChange = (newSettings) => {
    setCurrentSettings(newSettings)
    
    // Salvar preferências no localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('accessibility-settings', JSON.stringify(newSettings))
    }
  }

  // Carregar preferências salvas
  useEffect(() => {
    if (typeof window === 'undefined') return
    const savedSettings = localStorage.getItem('accessibility-settings')
    if (savedSettings) {
      const settings = JSON.parse(savedSettings)
      setCurrentSettings(settings)
      applySettings(settings)
    }
  }, [])

  const applySettings = (settings) => {
    if (typeof window === 'undefined') return
    // Aplicar configurações ao body
    document.body.classList.toggle('high-contrast', settings.highContrast)
    document.body.classList.toggle('reduced-motion', settings.reducedMotion)
    document.body.classList.toggle('large-text', settings.largeText)
    document.body.classList.toggle('show-focus', settings.showFocusIndicators)
  }

  return (
    <>
      {children}
      <AccessibilityButton onClick={() => setIsPanelOpen(true)} />
      <AccessibilityPanel
        isOpen={isPanelOpen}
        onClose={() => setIsPanelOpen(false)}
        onSettingsChange={handleSettingsChange}
      />
    </>
  )
}

export default AccessibilityManager
