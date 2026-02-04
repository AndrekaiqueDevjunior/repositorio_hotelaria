import Link from 'next/link'
import { notFound } from 'next/navigation'
import { cookies } from 'next/headers'

async function getReservaById(id) {
  const backendUrl = (process.env.BACKEND_URL || 'http://backend:8000').replace(/\/+$/, '')
  const url = `${backendUrl}/api/v1/reservas/${id}`

  const cookieHeader = cookies().toString()

  const res = await fetch(url, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      Cookie: cookieHeader,
      'ngrok-skip-browser-warning': 'true'
    },
    cache: 'no-store'
  })

  if (res.status === 404) return null
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`Falha ao buscar reserva ${id}: ${res.status} ${text}`)
  }

  return await res.json()
}

function formatDateTime(value) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleString('pt-BR')
}

function formatCurrency(value) {
  if (value === null || value === undefined) return '—'
  const num = Number(value)
  if (Number.isNaN(num)) return String(value)
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(num)
}

export default async function ReservaDetalhePage({ params }) {
  const id = params?.id
  const reserva = await getReservaById(id)

  if (!reserva) notFound()

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Reserva #{reserva.id}</h1>
        <Link
          href="/reservas"
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
        >
          Voltar
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="text-sm text-gray-500">Código</div>
            <div className="text-lg font-semibold">{reserva.codigo_reserva || '—'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Status</div>
            <div className="text-lg font-semibold">{reserva.status || '—'}</div>
          </div>

          <div>
            <div className="text-sm text-gray-500">Cliente</div>
            <div className="text-lg font-semibold">{reserva.cliente_nome || `#${reserva.cliente_id}`}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Quarto</div>
            <div className="text-lg font-semibold">{reserva.quarto_numero || '—'}</div>
          </div>

          <div>
            <div className="text-sm text-gray-500">Tipo suíte</div>
            <div className="text-lg font-semibold">{reserva.tipo_suite || '—'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Valor total</div>
            <div className="text-lg font-semibold">{formatCurrency(reserva.valor_total)}</div>
          </div>

          <div>
            <div className="text-sm text-gray-500">Check-in previsto</div>
            <div className="text-lg font-semibold">{formatDateTime(reserva.checkin_previsto)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Check-out previsto</div>
            <div className="text-lg font-semibold">{formatDateTime(reserva.checkout_previsto)}</div>
          </div>

          <div>
            <div className="text-sm text-gray-500">Check-in realizado</div>
            <div className="text-lg font-semibold">{formatDateTime(reserva.checkin_realizado)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Check-out realizado</div>
            <div className="text-lg font-semibold">{formatDateTime(reserva.checkout_realizado)}</div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        <h2 className="text-xl font-bold mb-4">Pagamentos</h2>

        {!reserva.pagamentos || reserva.pagamentos.length === 0 ? (
          <div className="text-gray-500">Nenhum pagamento vinculado.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2 pr-4">ID</th>
                  <th className="py-2 pr-4">Método</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Valor</th>
                </tr>
              </thead>
              <tbody>
                {reserva.pagamentos.map((p) => (
                  <tr key={p.id || `${p.metodo}-${p.valor}`} className="border-b">
                    <td className="py-2 pr-4">{p.id ?? '—'}</td>
                    <td className="py-2 pr-4">{p.metodo ?? p.forma ?? '—'}</td>
                    <td className="py-2 pr-4">{p.statusPagamento ?? p.status ?? '—'}</td>
                    <td className="py-2 pr-4">{formatCurrency(p.valor)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
