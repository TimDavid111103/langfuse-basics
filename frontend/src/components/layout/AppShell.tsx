import { Outlet } from 'react-router-dom'
import TopNav from './TopNav'

export default function AppShell() {
  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <TopNav />
      <main className="max-w-5xl mx-auto px-6 py-10">
        <Outlet />
      </main>
    </div>
  )
}
