import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTelegram } from '../hooks/useTelegram'
import { api } from '../api/client'

const CATEGORIES = {
  expense: ['Продукты', 'Транспорт', 'Развлечения', 'Здоровье', 'Одежда', 'Рестораны', 'Связь', 'Другое'],
  income: ['Зарплата', 'Подработка', 'Подарок', 'Возврат', 'Другое']
}

function AddTransaction() {
  const navigate = useNavigate()
  const { showBackButton, hideBackButton, hapticFeedback } = useTelegram()

  const [type, setType] = useState('expense')
  const [amount, setAmount] = useState('')
  const [category, setCategory] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    showBackButton(() => {
      navigate('/')
    })
    return () => hideBackButton()
  }, [])

  useEffect(() => {
    setCategory(CATEGORIES[type][0])
  }, [type])

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!amount || parseFloat(amount) <= 0) {
      setError('Введите сумму')
      hapticFeedback('notification', 'error')
      return
    }

    try {
      setLoading(true)
      setError(null)

      await api.createTransaction({
        type,
        amount: parseFloat(amount),
        currency: 'RUB',
        category,
        description: description || null
      })

      hapticFeedback('notification', 'success')
      navigate('/')
    } catch (err) {
      setError(err.message)
      hapticFeedback('notification', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '24px' }}>
        Новая операция
      </h1>

      <form onSubmit={handleSubmit}>
        {/* Тип операции */}
        <div className="form-group">
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className={`btn ${type === 'expense' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setType('expense')}
              style={{ flex: 1 }}
            >
              Расход
            </button>
            <button
              type="button"
              className={`btn ${type === 'income' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setType('income')}
              style={{ flex: 1 }}
            >
              Доход
            </button>
          </div>
        </div>

        {/* Сумма */}
        <div className="form-group">
          <label className="label">Сумма</label>
          <input
            type="number"
            className="input"
            placeholder="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            inputMode="decimal"
            style={{ fontSize: '24px', fontWeight: '600' }}
          />
        </div>

        {/* Категория */}
        <div className="form-group">
          <label className="label">Категория</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {CATEGORIES[type].map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategory(cat)}
                style={{
                  padding: '8px 16px',
                  borderRadius: '20px',
                  border: 'none',
                  background: category === cat
                    ? 'var(--tg-theme-button-color)'
                    : 'var(--tg-theme-secondary-bg-color)',
                  color: category === cat
                    ? 'var(--tg-theme-button-text-color)'
                    : 'var(--tg-theme-text-color)',
                  fontSize: '14px',
                  cursor: 'pointer'
                }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Описание */}
        <div className="form-group">
          <label className="label">Описание (опционально)</label>
          <input
            type="text"
            className="input"
            placeholder="Комментарий"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        {error && (
          <p style={{ color: '#ff3b30', marginBottom: '16px' }}>{error}</p>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
          style={{ marginTop: '8px' }}
        >
          {loading ? 'Сохранение...' : 'Сохранить'}
        </button>
      </form>
    </div>
  )
}

export default AddTransaction
