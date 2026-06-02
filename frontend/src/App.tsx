import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppShell from '@/components/layout/AppShell'
import ExperimentsPage from '@/pages/ExperimentsPage'
import ResultsPage from '@/pages/ResultsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/experiments" replace />} />
          <Route path="experiments" element={<ExperimentsPage />} />
          <Route path="experiments/:id/results" element={<ResultsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
