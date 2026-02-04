/**
 * Adapter para integração com FullCalendar
 * Transforma dados da API para o formato esperado pelo FullCalendar
 */

export const agendaAdapter = {
  /**
   * Transforma eventos da API para formato FullCalendar
   * @param {Array} events - Eventos da API
   * @returns {Array} Eventos formatados para FullCalendar
   */
  transformEvents(events = []) {
    return events.map(event => ({
      id: event.id || String(event.codigo),
      title: event.title || event.nome || 'Reserva',
      start: event.start || event.data_checkin || event.data_inicio,
      end: event.end || event.data_checkout || event.data_fim,
      backgroundColor: event.backgroundColor || event.color || '#3b82f6',
      borderColor: event.borderColor || event.color || '#1e40af',
      extendedProps: {
        ...event,
        tipo: event.tipo || 'reserva',
        status: event.status || 'confirmada',
        cliente: event.cliente || {},
        quarto: event.quarto || {}
      }
    }));
  },

  /**
   * Prepara dados para criar novo evento
   * @param {Object} eventData - Dados do evento do FullCalendar
   * @returns {Object} Dados formatados para API
   */
  prepareCreateEvent(eventData) {
    const { start, end, title, extendedProps } = eventData;
    
    return {
      titulo: title,
      data_inicio: start,
      data_fim: end,
      tipo: extendedProps.tipo || 'bloqueio',
      descricao: extendedProps.descricao || '',
      quarto_id: extendedProps.quarto_id,
      cliente_id: extendedProps.cliente_id,
      status: extendedProps.status || 'pendente'
    };
  },

  /**
   * Prepara dados para atualizar evento
   * @param {string} eventId - ID do evento
   * @param {Object} eventData - Dados do evento do FullCalendar
   * @returns {Object} Dados formatados para API
   */
  prepareUpdateEvent(eventId, eventData) {
    const { start, end, title, extendedProps } = eventData;
    
    return {
      id: eventId,
      titulo: title,
      data_inicio: start,
      data_fim: end,
      tipo: extendedProps.tipo || 'bloqueio',
      descricao: extendedProps.descricao || '',
      quarto_id: extendedProps.quarto_id,
      cliente_id: extendedProps.cliente_id,
      status: extendedProps.status || 'pendente'
    };
  },

  /**
   * Valida evento antes de enviar para API
   * @param {Object} eventData - Dados do evento
   * @returns {Object} { valid: boolean, errors: Array }
   */
  validateEvent(eventData) {
    const errors = [];
    
    if (!eventData.start) {
      errors.push('Data de início é obrigatória');
    }
    
    if (!eventData.end) {
      errors.push('Data de fim é obrigatória');
    }
    
    if (!eventData.title || eventData.title.trim() === '') {
      errors.push('Título é obrigatório');
    }
    
    if (eventData.start && eventData.end && new Date(eventData.start) >= new Date(eventData.end)) {
      errors.push('Data de fim deve ser posterior à data de início');
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  },

  /**
   * Gera cor baseada no tipo/status do evento
   * @param {string} tipo - Tipo do evento
   * @param {string} status - Status do evento
   * @returns {string} Cor em formato hexadecimal
   */
  getEventColor(tipo, status) {
    const colors = {
      reserva: {
        confirmada: '#10b981',
        pendente: '#f59e0b',
        cancelada: '#ef4444',
        checkin: '#3b82f6',
        checkout: '#8b5cf6'
      },
      bloqueio: {
        ativo: '#6b7280',
        inativo: '#d1d5db'
      },
      manutencao: {
        agendada: '#f97316',
        em_andamento: '#dc2626',
        concluida: '#22c55e'
      }
    };
    
    return colors[tipo]?.[status] || '#3b82f6';
  }
};
