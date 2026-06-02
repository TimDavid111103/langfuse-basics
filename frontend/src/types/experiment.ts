export type ExperimentStatus = 'created' | 'running' | 'complete' | 'failed'
export type Winner = 'no_rag' | 'rag' | 'tie'

export interface Experiment {
  id: number
  name: string
  questionnaireId: number
  questionnaireVersion: number
  sourceMaterialId: number
  status: ExperimentStatus
  langfuseTraceId: string | null
  errorMessage: string | null
  createdAt: string
  completedAt: string | null
}

export interface ExperimentResult {
  id: number
  experimentId: number
  questionIndex: number
  questionText: string
  rubricNoRag: string
  rubricRag: string
  retrievedChunksJson: string
  evaluationJson: string | null
  winner: Winner | null
  createdAt: string
}
