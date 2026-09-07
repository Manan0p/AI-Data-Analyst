// Auto-Analysis Intelligence Report types
// Mirrors backend app/schemas/contracts.py AutoAnalysisResponse

export type InsightType = 'stat' | 'trend' | 'anomaly' | 'distribution' | 'correlation';

export interface InsightCard {
  title: string;
  body: string;
  metric?: string | null;
  type: InsightType;
  chart?: Record<string, unknown> | null;
  importance: number;
}

export interface NullColumnInfo {
  name: string;
  null_pct: number;
}

export interface DataQualityReport {
  total_rows: number;
  total_columns: number;
  duplicate_rows: number;
  null_columns: NullColumnInfo[];
  healthy_columns: number;
  health_score: number;
}

export interface AutoAnalysisChart {
  title: string;
  data?: unknown[];
  layout?: object;
  figure?: {
    data: unknown[];
    layout: object;
  };
}

export interface AutoAnalysis {
  dataset_id: string;
  executive_summary: string;
  trend_story?: string | null;
  insights: InsightCard[];
  charts: AutoAnalysisChart[];
  recommendations: string[];
  data_quality: DataQualityReport;
  anomaly_note?: string | null;
  generated_at: string;
  gemini_used: boolean;
  groq_used: boolean;
  status: 'completed' | 'processing' | 'not_found' | 'failed';
}
