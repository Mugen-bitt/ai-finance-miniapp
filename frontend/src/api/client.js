const API_URL = import.meta.env.VITE_API_URL || '/api'

const tg = window.Telegram?.WebApp

async function request(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  }

  // Добавляем Telegram initData для авторизации
  if (tg?.initData) {
    headers['X-Telegram-Init-Data'] = tg.initData
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'Request failed')
  }

  return response.json()
}

export const api = {
  // Transactions
  getTransactions: (params = {}) => {
    const query = new URLSearchParams(params).toString()
    return request(`/transactions/${query ? `?${query}` : ''}`)
  },

  getTransaction: (id) => {
    return request(`/transactions/${id}`)
  },

  createTransaction: (data) => {
    return request('/transactions/', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  },

  deleteTransaction: (id) => {
    return request(`/transactions/${id}`, {
      method: 'DELETE'
    })
  },

  // Reports
  getMonthlyReport: (year, month) => {
    return request(`/transactions/report/monthly?year=${year}&month=${month}`)
  },

  // Categories
  getCategories: () => {
    return request('/transactions/categories/list')
  }
}
