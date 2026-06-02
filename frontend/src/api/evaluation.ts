import { ExperimentEvaluationSummary } from '@/types/evaluation'
import client from './client'

export async function getEvaluationSummary(experimentId: number): Promise<ExperimentEvaluationSummary> {
  const res = await client.get<ExperimentEvaluationSummary>(`/evaluation/${experimentId}/summary`)
  return res.data
}
