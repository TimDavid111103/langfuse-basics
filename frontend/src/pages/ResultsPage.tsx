import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useExperiment } from '@/hooks/useExperiments'
import { useEvaluationSummary } from '@/hooks/useEvaluation'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Legend } from 'recharts'
import { clsx } from 'clsx'
import { Winner, EvalDimension, RunSummary, QuestionEvaluationResult } from '@/types/evaluation'

const DIMENSION_LABELS: Record<EvalDimension, string> = {
  concept_coverage: 'Concept Coverage',
  factual_accuracy: 'Factual Accuracy',
  specificity: 'Specificity',
  subject_matter_depth: 'Depth',
}

const WINNER_LABEL: Record<Winner, string> = {
  rag: 'RAG wins',
  no_rag: 'No-RAG wins',
  tie: 'Tie',
}

function WinnerPill({ winner }: { winner: Winner }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center text-xs px-2.5 py-1 rounded-full font-medium border',
        winner === 'rag'
          ? 'bg-[var(--color-primary-light)] text-[var(--color-primary)] border-orange-200'
          : winner === 'no_rag'
          ? 'bg-stone-100 text-stone-600 border-stone-200'
          : 'bg-amber-50 text-amber-700 border-amber-200',
      )}
    >
      {WINNER_LABEL[winner]}
    </span>
  )
}

function QuestionRow({ result }: { result: QuestionEvaluationResult }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-[var(--color-border)] last:border-0">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-5 py-3 text-left hover:bg-[var(--color-bg)] transition-colors"
      >
        <span className="text-xs font-medium text-[var(--color-text-secondary)] w-24 shrink-0">
          Q{result.questionIndex + 1}
        </span>
        <span className="flex-1 text-sm text-[var(--color-text-primary)] truncate">
          {result.questionText}
        </span>
        <div className="flex items-center gap-3 shrink-0">
          {result.dimensionScores.map((d) => (
            <div key={d.dimension} className="text-xs text-right hidden sm:block">
              <div className="text-[var(--color-text-secondary)]">{DIMENSION_LABELS[d.dimension].split(' ')[0]}</div>
              <div>
                <span className="text-[var(--color-text-secondary)]">{d.rubricNoRagScore.toFixed(1)}</span>
                <span className="text-[var(--color-border)] mx-0.5">/</span>
                <span className={d.rubricRagScore > d.rubricNoRagScore ? 'text-[var(--color-primary)] font-semibold' : ''}>
                  {d.rubricRagScore.toFixed(1)}
                </span>
              </div>
            </div>
          ))}
          <WinnerPill winner={result.winner} />
          <svg
            width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            className={clsx('text-[var(--color-text-secondary)] transition-transform shrink-0', open && 'rotate-180')}
          >
            <path d="M6 9l6 6 6-6" />
          </svg>
        </div>
      </button>

      {open && (
        <div className="px-5 pb-4 pt-1 bg-[var(--color-bg)]">
          <div className="text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
            Judge Reasoning
          </div>
          <div className="block-quote text-sm text-[var(--color-text-secondary)] leading-relaxed mb-4">
            {result.judgeReasoning}
          </div>
          <div className="grid grid-cols-2 gap-3">
            {result.dimensionScores.map((d) => (
              <div
                key={d.dimension}
                className="bg-[var(--color-surface)] rounded-lg p-3"
                style={{ boxShadow: 'var(--shadow-card)' }}
              >
                <div className="text-xs font-semibold text-[var(--color-text-primary)] mb-1">
                  {DIMENSION_LABELS[d.dimension]}
                </div>
                <div className="flex items-center gap-2 mb-1">
                  <div className="flex-1 h-1.5 bg-[var(--color-border)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-stone-400 rounded-full"
                      style={{ width: `${(d.rubricNoRagScore / 10) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium w-8 text-right">{d.rubricNoRagScore.toFixed(1)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-[var(--color-border)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[var(--color-primary)] rounded-full"
                      style={{ width: `${(d.rubricRagScore / 10) * 100}%` }}
                    />
                  </div>
                  <span className={clsx('text-xs font-medium w-8 text-right', d.rubricRagScore > d.rubricNoRagScore && 'text-[var(--color-primary)]')}>
                    {d.rubricRagScore.toFixed(1)}
                  </span>
                </div>
                <div className="flex justify-between text-[10px] text-[var(--color-text-secondary)] mt-1">
                  <span>No-RAG</span><span>RAG</span>
                </div>
                <div className="text-xs text-[var(--color-text-secondary)] mt-2 leading-relaxed">{d.reasoning}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function RunCard({ run, isOnly }: { run: RunSummary; isOnly: boolean }) {
  const [collapsed, setCollapsed] = useState(!isOnly)
  return (
    <div
      className="bg-[var(--color-surface)] rounded-[var(--radius-card)] overflow-hidden"
      style={{ boxShadow: 'var(--shadow-card)' }}
    >
      <button
        onClick={() => setCollapsed((v) => !v)}
        className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-[var(--color-bg)] transition-colors"
      >
        <span className="text-sm font-semibold text-[var(--color-text-primary)]">
          Run {run.runIndex + 1}
        </span>
        <div className="flex items-center gap-4 text-sm text-[var(--color-text-secondary)]">
          <span>No-RAG <span className="font-semibold text-[var(--color-text-primary)]">{run.noRagAvg.toFixed(2)}</span></span>
          <span>RAG <span className={clsx('font-semibold', run.winner === 'rag' ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-primary)]')}>{run.ragAvg.toFixed(2)}</span></span>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <WinnerPill winner={run.winner} />
          <svg
            width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            className={clsx('text-[var(--color-text-secondary)] transition-transform', !collapsed && 'rotate-180')}
          >
            <path d="M6 9l6 6 6-6" />
          </svg>
        </div>
      </button>

      {!collapsed && (
        <div className="border-t border-[var(--color-border)]">
          <div className="px-5 py-2 flex gap-6 text-xs text-[var(--color-text-secondary)] border-b border-[var(--color-border)]">
            <span>No-RAG</span>
            {DIMENSION_LABELS && Object.values(DIMENSION_LABELS).map((l) => (
              <span key={l} className="hidden sm:inline">{l.split(' ')[0]}</span>
            ))}
            <span className="ml-auto">RAG</span>
            <span>Winner</span>
          </div>
          {run.perQuestionResults.map((r) => (
            <QuestionRow key={r.questionIndex} result={r} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const experimentId = Number(id)
  const { data: experiment } = useExperiment(experimentId)
  const { data: summary, isLoading } = useEvaluationSummary(experimentId)

  if (isLoading || !summary) {
    return (
      <div className="max-w-4xl">
        <BackButton onClick={() => navigate('/experiments')} />
        <p className="text-[var(--color-text-secondary)] text-sm mt-6">
          {isLoading ? 'Loading results…' : 'No results available yet.'}
        </p>
      </div>
    )
  }

  const radarData = (Object.keys(DIMENSION_LABELS) as EvalDimension[]).map((dim) => ({
    dimension: DIMENSION_LABELS[dim],
    'No-RAG': summary.dimensionAverages[dim]?.no_rag ?? 0,
    RAG: summary.dimensionAverages[dim]?.rag ?? 0,
  }))

  return (
    <div className="max-w-4xl">
      <BackButton onClick={() => navigate('/experiments')} />

      <div className="mb-6 mt-2">
        <h1 className="text-2xl font-semibold tracking-tight">{experiment?.name ?? 'Results'}</h1>
        <p className="text-sm text-[var(--color-text-secondary)] mt-1">{summary.judgeSummary}</p>
      </div>

      {/* Aggregate header */}
      <div
        className="rounded-[var(--radius-card)] px-6 py-5 flex flex-col sm:flex-row sm:items-center gap-4 mb-6"
        style={{ background: 'var(--color-primary)', color: '#fff' }}
      >
        <div className="flex-1">
          <div className="text-xs uppercase tracking-widest opacity-70 mb-1 font-medium">
            Overall Winner · {summary.numRuns} run{summary.numRuns !== 1 ? 's' : ''}
          </div>
          <div className="text-2xl font-semibold tracking-tight">{WINNER_LABEL[summary.overallWinner]}</div>
        </div>
        <div className="flex gap-6 text-sm">
          <div className="text-center">
            <div className="opacity-70 text-xs mb-0.5">No-RAG avg</div>
            <div className="font-semibold text-lg">{summary.overallNoRagScore.toFixed(2)}</div>
          </div>
          <div className="text-center">
            <div className="opacity-70 text-xs mb-0.5">RAG avg</div>
            <div className="font-semibold text-lg">{summary.overallRagScore.toFixed(2)}</div>
          </div>
          {summary.numRuns > 1 && (
            <div className="text-center">
              <div className="opacity-70 text-xs mb-0.5">RAG run wins</div>
              <div className="font-semibold text-lg">
                {summary.runs.filter((r) => r.winner === 'rag').length}/{summary.numRuns}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Aggregate radar */}
      <div
        className="bg-[var(--color-surface)] rounded-[var(--radius-card)] p-6 mb-6"
        style={{ boxShadow: 'var(--shadow-card)' }}
      >
        <h2 className="text-sm font-semibold mb-4">
          Dimension Averages{summary.numRuns > 1 ? ` (across ${summary.numRuns} runs)` : ''}
        </h2>
        <ResponsiveContainer width="100%" height={240}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#e5e0da" />
            <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 12, fill: '#78716c' }} />
            <Radar name="No-RAG" dataKey="No-RAG" stroke="#78716c" fill="#78716c" fillOpacity={0.12} />
            <Radar name="RAG" dataKey="RAG" stroke="#c9572a" fill="#c9572a" fillOpacity={0.18} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Per-run cards */}
      <h2 className="text-sm font-semibold mb-3 text-[var(--color-text-secondary)] uppercase tracking-wide">
        Runs
      </h2>
      <div className="space-y-3 mb-20">
        {summary.runs.map((run) => (
          <RunCard key={run.runIndex} run={run} isOnly={summary.numRuns === 1} />
        ))}
      </div>

      {/* Fixed bottom bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-[var(--color-primary)] text-white px-8 py-4 flex items-center gap-4">
        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 5v14M5 12l7 7 7-7" />
          </svg>
        </div>
        <div>
          <div className="text-sm font-semibold">Experiment Complete · {summary.numRuns} run{summary.numRuns !== 1 ? 's' : ''}</div>
          <div className="text-xs opacity-70">Traces in Langfuse · ID: {experimentId}</div>
        </div>
      </div>
    </div>
  )
}

function BackButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] flex items-center gap-1.5 transition-colors"
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M19 12H5M12 5l-7 7 7 7" />
      </svg>
      Experiments
    </button>
  )
}
