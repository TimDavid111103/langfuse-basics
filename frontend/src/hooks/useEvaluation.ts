import { useQuery } from '@tanstack/react-query'
import { getEvaluationSummary } from '@/api/evaluation'

export function useEvaluationSummary(experimentId: number) {
  return useQuery({
    queryKey: ['evaluation', experimentId],
    queryFn: () => getEvaluationSummary(experimentId),
    enabled: experimentId > 0,
  })
}
