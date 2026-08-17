'use client'

import { CalendarDays, ChevronDown, Search, User } from 'lucide-react'
import { toast } from 'react-toastify'
import { Fleurao, Selo } from '@/components/jornada/Ornamentos'

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
    <div className="jr-vidro overflow-hidden rounded-[4px]">
      <div className="px-5 pb-6 pt-9 text-center sm:px-9">
        <h2 className="font-['Playfair_Display',Georgia,serif] text-[2.1rem] font-normal leading-[1.06] text-[#f0d68f] sm:text-[2.6rem]">
          Encontre Sua Data Ideal
        </h2>
        <Fleurao largura={240} className="mx-auto mt-3 block" />
        <p className="mx-auto mt-4 max-w-[42ch] text-[1.02rem] leading-relaxed text-[#efe6d2]/70">
          Escolha as datas da sua estadia
        </p>
      </div>

      <div className="jr-vidro-interno mx-4 rounded-[4px] p-5 sm:mx-9 sm:p-7">
        <div className="grid gap-0">
          {/* Check-in */}
          <label className="grid grid-cols-[56px_1fr] items-center gap-4 border-b border-[#cd9b40]/22 py-6 first:pt-0">
            <span className="grid h-14 w-14 place-items-center rounded-full border border-[#cd9b40]/58 bg-black/30 text-[#cd9b40]">
              <CalendarDays size={26} strokeWidth={1.7} />
            </span>
            <span className="min-w-0">
              <span className="block font-['Cinzel',serif] text-[0.75rem] font-semibold uppercase tracking-[0.12em] text-[#f0d68f]">Check-in</span>
              <span className="relative mt-2 block">
                <input
                  type="date"
                  min={today}
                  value={searchData.data_checkin}
                  onChange={(e) => onSearchDataChange('data_checkin', e.target.value)}
                  className="royal-date-input peer w-full border-0 border-b border-[#efe6d2]/16 bg-transparent py-1.5 pr-12 text-xl text-[#efe6d2] outline-none [color-scheme:dark] focus:border-[#cd9b40]"
                />
              </span>
              <span className="mt-2 block text-sm text-[#efe6d2]/56">A partir das <strong className="text-[#f0d68f]">12:00</strong></span>
            </span>
          </label>

          {/* Check-out */}
          <label className="grid grid-cols-[56px_1fr] items-center gap-4 border-b border-[#cd9b40]/22 py-6">
            <span className="grid h-14 w-14 place-items-center rounded-full border border-[#cd9b40]/58 bg-black/30 text-[#cd9b40]">
              <CalendarDays size={26} strokeWidth={1.7} />
            </span>
            <span className="min-w-0">
              <span className="block font-['Cinzel',serif] text-[0.75rem] font-semibold uppercase tracking-[0.12em] text-[#f0d68f]">Check-out</span>
              <span className="relative mt-2 block">
                <input
                  type="date"
                  min={searchData.data_checkin || today}
                  value={searchData.data_checkout}
                  onChange={(e) => onSearchDataChange('data_checkout', e.target.value)}
                  className="royal-date-input w-full border-0 border-b border-[#efe6d2]/16 bg-transparent py-1.5 pr-12 text-xl text-[#efe6d2] outline-none [color-scheme:dark] focus:border-[#cd9b40]"
                />
              </span>
              <span className="mt-2 block text-sm text-[#efe6d2]/56">Até as <strong className="text-[#f0d68f]">11:00</strong></span>
            </span>
          </label>

          {/* Hóspedes */}
          <label className="grid grid-cols-[56px_1fr] items-center gap-4 py-6 last:pb-0">
            <span className="grid h-14 w-14 place-items-center rounded-full border border-[#cd9b40]/58 bg-black/30 text-[#cd9b40]">
              <User size={26} strokeWidth={1.7} />
            </span>
            <span className="min-w-0">
              <span className="block font-['Cinzel',serif] text-[0.75rem] font-semibold uppercase tracking-[0.12em] text-[#f0d68f]">Hóspedes</span>
              <span className="relative mt-2.5 block">
                <select
                  value={searchData.num_hospedes}
                  onChange={(e) => onSearchDataChange('num_hospedes', parseInt(e.target.value))}
                  className="w-full appearance-none border border-[#efe6d2]/14 bg-black/40 px-4 py-3 text-lg text-[#efe6d2] outline-none [color-scheme:dark] focus:border-[#cd9b40]"
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => (
                    <option key={n} value={n}>{n} {n === 1 ? 'hóspede' : 'hóspedes'}</option>
                  ))}
                </select>
                <ChevronDown className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[#efe6d2]/56" size={22} />
              </span>
            </span>
          </label>
        </div>

        {/* Botão Buscar */}
        <button
          onClick={handleBuscar}
          disabled={loading}
          className="mt-7 flex min-h-[58px] w-full items-center justify-center gap-3 rounded-full border border-transparent bg-[linear-gradient(135deg,#f3dda6_0%,#d8a94f_42%,#a97c2c_100%)] px-8 font-['Inter',sans-serif] text-[0.75rem] font-semibold uppercase tracking-[0.14em] text-[#160f04] shadow-[0_0_0_1px_rgba(205,155,64,0.35),0_12px_40px_-14px_rgba(205,155,64,0.75)] transition hover:brightness-[1.08] disabled:cursor-not-allowed disabled:opacity-55"
        >
          <Search size={19} strokeWidth={1.9} aria-hidden="true" />
          <span>{loading ? 'Buscando...' : 'Verificar Disponibilidade'}</span>
        </button>
      </div>

      {/* Selo da reserva */}
      <div className="jr-selo-reserva">
        <Selo className="jr-selo-reserva__lacre" tamanho={76} />

        <div>
          <p className="jr-selo-reserva__titulo">Reserva selada pelo Hotel Real</p>
          <p className="jr-selo-reserva__texto">
            Confirmação no ato e tarifa direta do hotel, sem intermediário. Os pontos da{' '}
            <b>Jornada Real</b> já entram contados nesta estadia.
          </p>
        </div>
      </div>
    </div>
  )
}
