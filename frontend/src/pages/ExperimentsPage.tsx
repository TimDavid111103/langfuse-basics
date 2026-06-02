import { useNavigate } from 'react-router-dom'
import { useExperiments } from '@/hooks/useExperiments'
import { clsx } from 'clsx'

const STATUS_STYLES: Record<string, string> = {
  created: 'bg-[#f5f3ef] text-[var(--color-text-secondary)] border border-[var(--color-border)]',
  running: 'bg-amber-50 text-amber-700 border border-amber-200',
  complete: 'bg-[var(--color-primary-light)] text-[var(--color-primary)] border border-orange-200',
  failed: 'bg-red-50 text-red-600 border border-red-200',
}

function StatusDot({ status }: { status: string }) {
  const dotColor =
    status === 'running' ? 'bg-amber-500' :
    status === 'complete' ? 'bg-[var(--color-primary)]' :
    status === 'failed' ? 'bg-red-500' :
    'bg-[var(--color-text-secondary)]'
  return <span className={clsx('inline-block w-1.5 h-1.5 rounded-full mr-1.5', dotColor)} />
}

export default function ExperimentsPage() {
  const navigate = useNavigate()
  const { data: experiments, isLoading } = useExperiments()

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)] tracking-tight">Experiments</h1>
        <p className="text-sm text-[var(--color-text-secondary)] mt-1">
          RAG vs No-RAG rubric evaluation runs
        </p>
      </div>

      {isLoading ? (
        <div className="text-sm text-[var(--color-text-secondary)]">Loading…</div>
      ) : !experiments?.length ? (
        <div
          className="rounded-[var(--radius-card)] border border-dashed border-[var(--color-border)] px-8 py-16 text-center"
          style={{ background: 'var(--color-surface)' }}
        >
          <div className="text-[var(--color-text-secondary)] text-sm">No experiments yet.</div>
          <div className="text-[var(--color-text-secondary)] text-xs mt-1 opacity-70">
            Run a backend script to create and start an experiment.
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {experiments.map((e) => (
            <div
              key={e.id}
              className="bg-[var(--color-surface)] rounded-[var(--radius-card)] px-5 py-4 flex items-center gap-4"
              style={{ boxShadow: 'var(--shadow-card)' }}
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-[var(--color-text-primary)] truncate">{e.name}</div>
                <div className="text-xs text-[var(--color-text-secondary)] mt-0.5">
                  {new Date(e.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                </div>
              </div>

              <span className={clsx('inline-flex items-center text-xs px-2.5 py-1 rounded-[var(--radius-pill)] font-medium', STATUS_STYLES[e.status])}>
                <StatusDot status={e.status} />
                {e.status}
              </span>

              {e.status === 'complete' && (
                <button
                  onClick={() => navigate(`/experiments/${e.id}/results`)}
                  className="text-xs px-3.5 py-1.5 rounded-[var(--radius-pill)] bg-[var(--color-primary)] text-white font-medium hover:bg-[var(--color-primary-dark)] transition-colors"
                >
                  View Results
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
