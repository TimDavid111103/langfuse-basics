import { useQuery } from '@tanstack/react-query'
import { listExperiments, getExperiment, getExperimentResults } from '@/api/experiments'

export function useExperiments() {
  return useQuery({ queryKey: ['experiments'], queryFn: listExperiments })
}

export function useExperiment(id: number) {
  return useQuery({ queryKey: ['experiments', id], queryFn: () => getExperiment(id) })
}

export function useExperimentResults(id: number) {
  return useQuery({
    queryKey: ['experiments', id, 'results'],
    queryFn: () => getExperimentResults(id),
  })
}
