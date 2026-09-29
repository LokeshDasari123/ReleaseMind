import axios from 'axios';
import { AssessmentResponse, MemoryStats, ServiceHealth } from './types';

const client = axios.create({ baseURL: '' });

export async function submitChange(changeDescription: string, context?: string): Promise<AssessmentResponse> {
  const { data } = await client.post<AssessmentResponse>('/api/assess', {
    change_description: changeDescription,
    context: context || undefined,
  });
  return data;
}

export async function getHealth(): Promise<ServiceHealth> {
  const { data } = await client.get<ServiceHealth>('/api/health');
  return data;
}

export async function getMemoryStats(): Promise<MemoryStats> {
  const { data } = await client.get<MemoryStats>('/api/memory/stats');
  return data;
}

export async function importDataset(file: File): Promise<{ imported: number; skipped: number; memory_provider: string; message: string }> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await client.post('/api/memory/import', form);
  return data;
}
