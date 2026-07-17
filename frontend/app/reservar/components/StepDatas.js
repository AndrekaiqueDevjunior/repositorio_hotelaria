'use client'

import { CalendarDays, ChevronDown, Crown, Gift, Search, ShieldCheck, Star, User } from 'lucide-react'
import { toast } from 'react-toastify'

export default function StepDatas({
  searchData,
  onSearchDataChange,
  onBuscar,
  loading,
  today
}) {
  const handleBuscar = () => {
    if (!searchData.data_checkin || !searchData.data_checkout) {
      toast.warning('Selecione as datas de check-in e check-out')
      return
    }

    if (searchData.data_checkout <= searchData.data_checkin) {
      toast.warning('Data de check-out deve ser posterior ao check-in')
      return
    }

    onBuscar()
  }

  return (
    <div className="overflow-hidden rounded-[22px] border border-[#8b651c]/70 bg-black/64 shadow-[0_0_36px_rgba(0,0,0,0.62),inset_0_0_28px_rgba(229,184,74,0.06)] backdrop-blur-[2px]">
      <div className="px-5 pb-5 pt-8 text-center sm:px-9 sm:pt-9">
        <h2 className="font-serif text-[2rem] font-bold uppercase leading-none tracking-wide text-[#e5b84a] drop-shadow-[0_0_10px_rgba(229,184,74,0.35)] sm:text-[2.4rem]">
          Encontre Sua Data Ideal
        </h2>
        <div className="mx-auto mt-5 flex w-[78%] items-center justify-center gap-2 text-[#d7a52c]">
          <span className="h-px flex-1 bg-gradient-to-r from-transparent via-[#8e651b] to-[#d7a52c]" />
          <span className="h-2 w-2 rotate-45 border border-[#d7a52c]" />
          <span className="h-px flex-1 bg-gradient-to-l from-transparent via-[#8e651b] to-[#d7a52c]" />
        </div>
        <p className="mt-5 text-xl text-[#f4ead2] sm:text-2xl">Escolha as datas da sua estadia</p>
      </div>

      <div className="mx-4 rounded-[24px] border border-white/10 bg-[#120d09]/72 p-5 shadow-[inset_0_0_18px_rgba(255,255,255,0.03)] sm:mx-9 sm:p-7">
        <div className="grid gap-6">
          {/* Check-in */}
          <label className="grid grid-cols-[74px_1fr] items-center gap-4 border-b border-white/10 pb-6">
            <span className="grid h-14 w-14 place-items-center rounded-full border border-[#9f721f]/65 bg-black/30 text-[#e5b84a] shadow-[0_0_14px_rgba(229,184,74,0.22)]">
              <CalendarDays size={30} strokeWidth={1.7} />
            </span>
            <span className="min-w-0">
              <span className="block font-serif text-xl font-bold uppercase text-[#f4ead2]">Check-in</span>
              <span className="relative mt-2 block">
                <input
                  type="date"
                  min={today}
                  value={searchData.data_checkin}
                  onChange={(e) => onSearchDataChange('data_checkin', e.target.value)}
                  className="royal-date-input peer w-full border-0 border-b border-white/10 bg-transparent py-2 pr-12 text-2xl uppercase text-[#f4ead2] outline-none [color-scheme:dark] focus:border-[#e5b84a]"
                />
              </span>
              <span className="mt-3 block text-lg text-[#c7b99b]">A partir das <strong className="text-[#e5b84a]">12:00</strong></span>
            </span>
          </label>

          {/* Check-out */}
          <label className="grid grid-cols-[74px_1fr] items-center gap-4 border-b border-white/10 pb-6">
            <span className="grid h-14 w-14 place-items-center rounded-full border border-[#9f721f]/65 bg-black/30 text-[#e5b84a] shadow-[0_0_14px_rgba(229,184,74,0.22)]">
              <CalendarDays size={30} strokeWidth={1.7} />
            </span>
            <span className="min-w-0">
              <span className="block font-serif text-xl font-bold uppercase text-[#f4ead2]">Check-out</span>
              <span className="relative mt-2 block">
                <input
                  type="date"
                  min={searchData.data_checkin || today}
                  value={searchData.data_checkout}
                  onChange={(e) => onSearchDataChange('data_checkout', e.target.value)}
                  className="royal-date-input w-full border-0 border-b border-white/10 bg-transparent py-2 pr-12 text-2xl uppercase text-[#f4ead2] outline-none [color-scheme:dark] focus:border-[#e5b84a]"
                />
              </span>
              <span className="mt-3 block text-lg text-[#c7b99b]">Até as <strong className="text-[#e5b84a]">11:00</strong></span>
            </span>
          </label>

          {/* Hóspedes */}
          <label className="grid grid-cols-[74px_1fr] items-center gap-4">
            <span className="grid h-14 w-14 place-items-center rounded-full border border-[#9f721f]/65 bg-black/30 text-[#e5b84a] shadow-[0_0_14px_rgba(229,184,74,0.22)]">
              <User size={30} strokeWidth={1.7} />
            </span>
            <span className="min-w-0">
              <span className="block font-serif text-xl font-bold uppercase text-[#f4ead2]">Hóspedes</span>
              <span className="relative mt-3 block">
                <select
                  value={searchData.num_hospedes}
                  onChange={(e) => onSearchDataChange('num_hospedes', parseInt(e.target.value))}
                  className="w-full appearance-none rounded-xl border border-white/12 bg-[#080604] px-5 py-4 text-2xl text-[#f4ead2] outline-none [color-scheme:dark] focus:border-[#e5b84a]"
                >
                  {[1, 2, 3, 4, 5, 6].map(n => (
                    <option key={n} value={n}>{n} {n === 1 ? 'hóspede' : 'hóspedes'}</option>
                  ))}
                </select>
                <ChevronDown className="pointer-events-none absolute right-5 top-1/2 -translate-y-1/2 text-white/70" size={28} />
              </span>
            </span>
          </label>
        </div>

        {/* Botão Buscar */}
        <button
          onClick={handleBuscar}
          disabled={loading}
          className="mt-7 grid min-h-[76px] w-full grid-cols-[46px_minmax(0,1fr)_42px] items-center gap-2 rounded-[28px] border border-[#fff0ad]/65 bg-[linear-gradient(180deg,#fff0ad_0%,#e7b943_48%,#a86608_100%)] px-4 font-serif text-[0.78rem] font-bold uppercase tracking-wide text-[#160d04] shadow-[0_14px_28px_rgba(0,0,0,0.48),0_0_28px_rgba(229,184,74,0.4),inset_0_1px_0_rgba(255,255,255,0.5)] transition hover:scale-[1.01] disabled:opacity-55 sm:grid-cols-[58px_minmax(0,1fr)_48px] sm:gap-4 sm:px-5 sm:text-[1.45rem]"
        >
          <span className="grid h-11 w-11 place-items-center justify-self-start rounded-full border-2 border-[#1d1205]/70 sm:h-14 sm:w-14">
            <Search size={27} strokeWidth={1.8} />
          </span>
          <span className="min-w-0 text-center leading-tight">{loading ? 'Buscando...' : 'Verificar Disponibilidade'}</span>
          <img className="jr-button-crest justify-self-end" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
        </button>
      </div>

      {/* Benefícios */}
      <div className="mt-5 border-t border-[#8b651c]/45 px-5 py-5 sm:px-7">
        <div className="grid grid-cols-3 divide-x divide-white/12 rounded-[20px] border border-white/10 bg-black/22 py-4 text-center">
          {[
            { icon: ShieldCheck, title: 'Reserva Segura', text: 'Ambiente 100% protegido' },
            { icon: Gift, title: 'Melhor Preço', text: 'Condições exclusivas para você' },
            { icon: Star, title: 'Acumule Pontos', text: 'Ganhe pontos na Jornada Real' },
          ].map((item) => {
            const Icon = item.icon
            return (
              <div key={item.title} className="px-2">
                <Icon className="mx-auto mb-2 text-[#d7a52c]" size={30} strokeWidth={1.7} />
                <strong className="block font-serif text-[0.75rem] uppercase text-[#e5b84a] sm:text-[0.95rem]">{item.title}</strong>
                <span className="mt-2 block text-[0.72rem] leading-snug text-[#f4ead2] sm:text-[0.9rem]">{item.text}</span>
              </div>
            )
          })}
        </div>

        <p className="mx-auto mt-5 flex w-fit items-center justify-center gap-3 rounded-full border border-[#8b651c]/55 bg-black/30 px-6 py-3 text-center text-[#f4ead2]">
          <Crown size={26} className="text-[#e5b84a]" />
          <span>Sua reserva é garantida e seus pontos também!</span>
        </p>
      </div>
    </div>
  )
}
