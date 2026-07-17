'use client'

export default function Footer() {
  return (
    <footer className="relative z-30 mt-auto border-t border-[#d4af37]/15 bg-[#090504]/70 py-8 text-white/80 backdrop-blur-sm">
      <div className="max-w-6xl mx-auto px-4 text-center">
        <div className="flex items-center justify-center gap-3 mb-4">
          <span className="text-3xl">🏨</span>
          <div>
            <h3 className="text-xl font-bold text-white">Hotel Real Cabo Frio</h3>
            <p className="text-sm text-yellow-400">O melhor da região</p>
          </div>
        </div>
        <p className="text-sm">Rua enfermeiro Ricardo Sanches 22, RJ</p>
        <p className="text-sm mt-1">📞 (22) 2648-5900 | 📧 contato@hotelrealcabofrio.com.br</p>
        <p className="text-xs mt-4 opacity-60">© 2024 Hotel Real Cabo Frio. Todos os direitos reservados.</p>
      </div>
    </footer>
  )
}
