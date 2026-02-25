import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { initTelegram } from './hooks/useTelegram'
import Dashboard from './pages/Dashboard'
import AddTransaction from './pages/AddTransaction'
import History from './pages/History'

function App() {
  useEffect(() => {
    initTelegram()
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/add" element={<AddTransaction />} />
        <Route path="/history" element={<History />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
