import { Experiment, ExperimentResult } from '@/types/experiment'
import client from './client'

export async function listExperiments(): Promise<Experiment[]> {
  const res = await client.get<Experiment[]>('/experiments')
  return res.data
}

export async function getExperiment(id: number): Promise<Experiment> {
  const res = await client.get<Experiment>(`/experiments/${id}`)
  return res.data
}

export async function getExperimentResults(id: number): Promise<ExperimentResult[]> {
  const res = await client.get<ExperimentResult[]>(`/experiments/${id}/results`)
  return res.data
}
