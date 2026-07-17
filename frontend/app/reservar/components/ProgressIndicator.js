'use client'

const reservationSteps = [
  { num: 1, label: 'Datas' },
  { num: 2, label: 'Quarto' },
  { num: 3, label: 'Dados' },
  { num: 4, label: 'Pagamento' },
  { num: 5, label: 'Confirmação' },
]

export default function ProgressIndicator({ currentStep }) {
  return (
    <div className="relative z-40 mx-auto w-full max-w-[820px] px-4 py-5 sm:px-8">
      <div className="grid grid-cols-5 gap-2 border-b border-[#b9821b]/25 pb-5">
        {reservationSteps.map((s) => (
          <div key={s.num} className="flex flex-col items-center gap-2">
            <div className={`grid h-14 w-14 place-items-center rounded-full border font-serif text-2xl font-bold transition-all sm:h-[72px] sm:w-[72px] sm:text-3xl ${
              currentStep >= s.num
                ? 'border-[#fff0ad] bg-[radial-gradient(circle_at_30%_22%,#fff3b4,#d79b22_58%,#8c5706)] text-[#1e1004] shadow-[0_0_22px_rgba(235,190,75,0.7)]'
                : 'border-[#9f721f]/38 bg-black/28 text-white/38'
            }`}>
              {currentStep > s.num ? '✓' : s.num}
            </div>
            <span className={`font-serif text-[0.52rem] font-bold uppercase leading-none sm:text-[1rem] ${
              currentStep >= s.num ? 'text-[#e5b84a]' : 'text-white/78'
            }`}>
              {s.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
