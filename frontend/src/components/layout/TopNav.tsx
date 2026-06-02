import { NavLink } from 'react-router-dom'
import { clsx } from 'clsx'

function StarburstIcon({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" aria-hidden="true">
      {Array.from({ length: 8 }, (_, i) => {
        const angle = (i * 45 * Math.PI) / 180
        const x = 50 + 44 * Math.sin(angle)
        const y = 50 - 44 * Math.cos(angle)
        return (
          <line
            key={i}
            x1="50"
            y1="50"
            x2={x}
            y2={y}
            stroke="currentColor"
            strokeWidth="9"
            strokeLinecap="round"
          />
        )
      })}
    </svg>
  )
}

const NAV_ITEMS = [{ to: '/experiments', label: 'Experiments' }]

export default function TopNav() {
  return (
    <header
      className="bg-[var(--color-surface)] px-6 h-14 flex items-center justify-between"
      style={{ boxShadow: 'var(--shadow-nav)' }}
    >
      <div className="flex items-center gap-2.5 text-[var(--color-primary)]">
        <StarburstIcon size={18} />
        <span className="text-[var(--color-text-primary)] font-semibold tracking-tight text-[15px]">
          Pensive
        </span>
      </div>

      <nav className="flex items-center gap-1">
        {NAV_ITEMS.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-[var(--color-primary-light)] text-[var(--color-primary)]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-black/5',
              )
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="w-[72px] flex justify-end">
        <div className="w-8 h-8 rounded-full bg-[var(--color-border)] flex items-center justify-center text-[var(--color-text-secondary)]">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </div>
      </div>
    </header>
  )
}
