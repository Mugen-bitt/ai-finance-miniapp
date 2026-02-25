import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTelegram } from '../hooks/useTelegram'
import { api } from '../api/client'

function History() {
  const navigate = useNavigate()
  const { showBackButton, hideBackButton, hapticFeedback } = useTelegram()

  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    showBackButton(() => navigate('/'))
    loadTransactions()
    return () => hideBackButton()
  }, [])

  const loadTransactions = async () => {
    try {
      setLoading(true)
      const data = await api.getTransactions({ limit: 50 })
      setTransactions(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Удалить операцию?')) return

    try {
      await api.deleteTransaction(id)
      hapticFeedback('notification', 'success')
      setTransactions(transactions.filter((t) => t.id !== id))
    } catch (err) {
      hapticFeedback('notification', 'error')
      alert('Ошибка удаления')
    }
  }

  const formatMoney = (amount) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'decimal',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short'
    })
  }

  const groupByDate = (items) => {
    const groups = {}
    items.forEach((item) => {
      const date = item.transaction_date
      if (!groups[date]) {
        groups[date] = []
      }
      groups[date].push(item)
    })
    return groups
  }

  const grouped = groupByDate(transactions)

  return (
    <div className="container">
      <h1 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '24px' }}>
        История операций
      </h1>

      {loading && (
        <div className="card text-center">
          <p className="text-hint">Загрузка...</p>
        </div>
      )}

      {error && (
        <div className="card">
          <p style={{ color: '#ff3b30' }}>{error}</p>
        </div>
      )}

      {!loading && transactions.length === 0 && (
        <div className="card text-center">
          <p className="text-hint">Пока нет операций</p>
          <button
            className="btn btn-primary mt-16"
            onClick={() => navigate('/add')}
          >
            Добавить первую
          </button>
        </div>
      )}

      {Object.entries(grouped).map(([date, items]) => (
        <div key={date} style={{ marginBottom: '16px' }}>
          <p className="text-hint" style={{ fontSize: '12px', marginBottom: '8px' }}>
            {formatDate(date)}
          </p>
          {items.map((tx) => (
            <div
              key={tx.id}
              className="card"
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '8px'
              }}
              onClick={() => handleDelete(tx.id)}
            >
              <div>
                <p style={{ fontWeight: '500' }}>{tx.category}</p>
                {tx.description && (
                  <p className="text-hint" style={{ fontSize: '12px' }}>
                    {tx.description}
                  </p>
                )}
              </div>
              <p style={{
                fontWeight: '600',
                color: tx.type === 'income' ? '#34c759' : '#ff3b30'
              }}>
                {tx.type === 'income' ? '+' : '-'}{formatMoney(tx.amount)} р.
              </p>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

export default History
