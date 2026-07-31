export type Dataset = {
  id: string;
  name: string;
  rows: number;
  columns: number;
  preview: Record<string, unknown>[];
};

export type Profile = {
  dataset_id: string;
  rows: number;
  columns: number;
  duplicate_rows: number;
  columns_profile: {
    name: string;
    dtype: string;
    null_percentage: number;
    unique_values: number;
  }[];
  numeric_summary: Record<string, Record<string, number | null>>;
};

export type Analysis = {
  answer: string;
  reasoning: string;
  confidence: number;
  assumptions: string[];
  limitations: string[];
  generated_sql?: string | null;
  generated_pandas?: string | null;
  chart?: {
    data: unknown[];
    layout: object;
  } | null;
  insights: string[];
  anomalies: Record<string, unknown>[];
  metadata: Record<string, unknown>;
};
