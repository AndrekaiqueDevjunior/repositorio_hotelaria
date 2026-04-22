/**
 * Componente de Tabela Acessível
 * Segue WCAG 2.1 AA com suporte a screen readers e navegação por teclado
 */

import { forwardRef } from 'react'
import { ChevronUp, ChevronDown, ChevronUpDown } from 'lucide-react'

const AccessibleTable = forwardRef(({
  columns,
  data,
  caption,
  sortBy,
  sortOrder,
  onSort,
  loading = false,
  emptyMessage = 'Nenhum registro encontrado',
  className = '',
  ...props
}, ref) => {
  const handleSort = (column) => {
    if (!column.sortable) return

    const newOrder = sortBy === column.key && sortOrder === 'asc' ? 'desc' : 'asc'
    onSort?.(column.key, newOrder)
  }

  const getSortIcon = (column) => {
    if (!column.sortable) return null

    if (sortBy !== column.key) {
      return <ChevronUpDown className="w-4 h-4 text-gray-400" />
    }

    return sortOrder === 'asc' 
      ? <ChevronUp className="w-4 h-4 text-blue-600" />
      : <ChevronDown className="w-4 h-4 text-blue-600" />
  }

  const getSortDirection = (column) => {
    if (!column.sortable) return 'none'
    if (sortBy !== column.key) return 'none'
    return sortOrder
  }

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table
        ref={ref}
        className="min-w-full divide-y divide-gray-200"
        role="table"
        aria-label={caption}
        aria-rowcount={data.length + 1}
        aria-colcount={columns.length}
        {...props}
      >
        {/* Caption */}
        {caption && (
          <caption className="sr-only">
            {caption}
          </caption>
        )}

        {/* Header */}
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column, index) => (
              <th
                key={column.key}
                scope="col"
                className={`
                  px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider
                  ${column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''}
                `}
                aria-sort={getSortDirection(column)}
                onClick={() => handleSort(column)}
                onKeyDown={(e) => {
                  if ((e.key === 'Enter' || e.key === ' ') && column.sortable) {
                    e.preventDefault()
                    handleSort(column)
                  }
                }}
                tabIndex={column.sortable ? 0 : -1}
              >
                <div className="flex items-center space-x-2">
                  <span>{column.title}</span>
                  {column.sortable && (
                    <span className="inline-flex items-center" aria-hidden="true">
                      {getSortIcon(column)}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>

        {/* Body */}
        <tbody className="bg-white divide-y divide-gray-200">
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="px-6 py-12 text-center">
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-gray-500">Carregando...</span>
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-6 py-12 text-center">
                <div className="text-gray-500">
                  <div className="text-4xl mb-2">📋</div>
                  <p>{emptyMessage}</p>
                </div>
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr
                key={row.id || rowIndex}
                className="hover:bg-gray-50 transition-colors"
                role="row"
                aria-rowindex={rowIndex + 1}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                    role="gridcell"
                  >
                    {column.render ? column.render(row[column.key], row) : row[column.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>

        {/* Footer (opcional) */}
        {data.length > 0 && (
          <tfoot className="bg-gray-50">
            <tr>
              <td colSpan={columns.length} className="px-6 py-3 text-sm text-gray-500">
                Total: {data.length} registro{data.length !== 1 ? 's' : ''}
              </td>
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  )
})

AccessibleTable.displayName = 'AccessibleTable'

export default AccessibleTable
