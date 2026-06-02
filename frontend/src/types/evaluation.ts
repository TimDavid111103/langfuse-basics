export type Condition = 'no_rag' | 'rag'
export type Winner = 'no_rag' | 'rag' | 'tie'
export type EvalDimension =
  | 'concept_coverage'
  | 'factual_accuracy'
  | 'specificity'
  | 'subject_matter_depth'

export interface DimensionScore {
  dimension: EvalDimension
  rubricNoRagScore: number
  rubricRagScore: number
  reasoning: string
}

export interface QuestionEvaluationResult {
  runIndex: number
  questionIndex: number
  questionText: string
  dimensionScores: DimensionScore[]
  noRagTotal: number
  ragTotal: number
  winner: Winner
  judgeReasoning: string
  judgeModel: string
  langfuseSpanId: string
}

export interface RunSummary {
  runIndex: number
  perQuestionResults: QuestionEvaluationResult[]
  noRagAvg: number
  ragAvg: number
  winner: Winner
}

export interface ExperimentEvaluationSummary {
  experimentId: number
  numRuns: number
  runs: RunSummary[]
  overallNoRagScore: number
  overallRagScore: number
  overallWinner: Winner
  dimensionAverages: Record<EvalDimension, Record<Condition, number>>
  judgeSummary: string
}
