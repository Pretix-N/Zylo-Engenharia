import React, { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'

const AreaInterna = lazy(() => import('./pages/AreaInterna'))

function Carregando() {
  return (
    <div className="flex h-screen items-center justify-center bg-[#0f0f0f]">
      <div className="flex h-10 w-10 animate-pulse items-center justify-center rounded-xl bg-amber-500">
        <span className="text-lg font-black text-black">Z</span>
      </div>
    </div>
  )
}

const interna = (modo) => (
  <Suspense fallback={<Carregando />}>
    <AreaInterna modo={modo} />
  </Suspense>
)

export default function App() {
  return (
    <Router>
      <Routes>
        {/* Site público: rota leve, sem Firebase no bundle inicial. */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={interna('login')} />
        <Route path="/app/*" element={interna('app')} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}
