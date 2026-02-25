import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTelegram } from '../hooks/useTelegram'
import { api } from '../api/client'

function Dashboard() {
  const navigate = useNavigate()
  const { user, hapticFeedback } = useTelegram()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1

  useEffect(() => {
    loadReport()
  }, [])

  const loadReport = async () => {
    try {
      setLoading(true)
      const data = await api.getMonthlyReport(year, month)
      setReport(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAddClick = () => {
    hapticFeedback('impact', 'light')
    navigate('/add')
  }

  const handleHistoryClick = () => {
    hapticFeedback('impact', 'light')
    navigate('/history')
  }

  const formatMoney = (amount) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'decimal',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  const monthNames = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
  ]

  return (
    <div className="container">
      <div className="mb-16">
        <h1 style={{ fontSize: '24px', fontWeight: '600' }}>
          {user?.first_name ? `Привет, ${user.first_name}!` : 'AI Finance'}
        </h1>
        <p className="text-hint" style={{ marginTop: '4px' }}>
          {monthNames[month - 1]} {year}
        </p>
      </div>

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

      {report && !loading && (
        <>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div>
                <p className="text-hint" style={{ fontSize: '12px' }}>Доходы</p>
                <p style={{ fontSize: '20px', fontWeight: '600', color: '#34c759' }}>
                  +{formatMoney(report.total_income)} р.
                </p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <p className="text-hint" style={{ fontSize: '12px' }}>Расходы</p>
                <p style={{ fontSize: '20px', fontWeight: '600', color: '#ff3b30' }}>
                  -{formatMoney(report.total_expense)} р.
                </p>
              </div>
            </div>
            <div style={{
              borderTop: '1px solid var(--tg-theme-hint-color)',
              paddingTop: '12px',
              opacity: 0.3
            }} />
            <div style={{ textAlign: 'center' }}>
              <p className="text-hint" style={{ fontSize: '12px' }}>Баланс</p>
              <p style={{
                fontSize: '28px',
                fontWeight: '700',
                color: report.savings >= 0 ? '#34c759' : '#ff3b30'
              }}>
                {report.savings >= 0 ? '+' : ''}{formatMoney(report.savings)} р.
              </p>
            </div>
          </div>

          {report.expenses_by_category.length > 0 && (
            <div className="card">
              <p style={{ fontWeight: '600', marginBottom: '12px' }}>Расходы по категориям</p>
              {report.expenses_by_category.map((cat) => (
                <div
                  key={cat.category}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px 0',
                    borderBottom: '1px solid var(--tg-theme-secondary-bg-color)'
                  }}
                >
                  <span>{cat.category}</span>
                  <span style={{ fontWeight: '500' }}>{formatMoney(cat.total)} р.</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
        <button className="btn btn-primary" onClick={handleAddClick}>
          + Добавить
        </button>
        <button className="btn btn-secondary" onClick={handleHistoryClick}>
          История
        </button>
      </div>
    </div>
  )
}

export default Dashboard
