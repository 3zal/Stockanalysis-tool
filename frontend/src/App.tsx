import { Routes, Route } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import MainLayout from '@/components/layout/MainLayout'
import Home from '@/pages/Home'
import StockPage from '@/pages/StockPage'
import Toast from '@/components/common/Toast'

export default function App() {
  return (
    <>
      <AnimatePresence mode="wait">
        <Routes>
          <Route element={<MainLayout />}>
            <Route path="/" element={<Home />} />
            <Route path="/stock/:ticker" element={<StockPage />} />
          </Route>
        </Routes>
      </AnimatePresence>
      <Toast />
    </>
  )
}
