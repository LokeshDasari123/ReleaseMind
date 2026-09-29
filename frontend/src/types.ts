export interface HistoricalExperience {
  id: string;
  title: string;
  description: string;
  category: string;
  source: string;
  source_url: string;
  triggering_change?: string | null;
  retrieval_score?: number | null;
  root_cause?: string | null;
  remediation?: string | null;
  severity?: string | null;
  date?: string | null;
  services_affected: string[];
  is_synthetic: boolean;
}

export interface RiskAssessment {
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_score: number;
  summary: string;
  key_risks: string[];
  recommended_safeguards: string[];
  evidence_citations: string[];
  model_reasoning: string;
  confidence_notes: string;
}

export interface AssessmentResponse {
  baseline_assessment: RiskAssessment;
  memory_assessment: RiskAssessment;
  retrieved_experiences: HistoricalExperience[];
  metadata: {
    memory_provider: string;
    llm_model: string;
    evidence_count: number;
    assessment_scope: string;
    [key: string]: unknown;
  };
}

export interface MemoryStats {
  total_experiences: number;
  categories: Record<string, number>;
  sources: Record<string, number>;
  provider: string;
  persistence: string;
}

export interface ServiceHealth {
  status: string;
  llm_configured: boolean;
  llm_model: string;
  memory_provider: string;
  memory_items: number;
}
