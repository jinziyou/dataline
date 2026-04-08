export type SourceType = "website" | "api" | "file" | "stream" | "external";

export interface Source {
  id: string;
  name: string;
  type: SourceType;
  url: string | null;
  description: string;
  enabled: boolean;
  meta: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  line_count: number;
}

export interface Line {
  id: string;
  source_id: string;
  name: string;
  url: string | null;
  description: string;
  enabled: boolean;
  meta: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CrawlerTask {
  id: string;
  source_id: string;
  source_name: string;
  status: "pending" | "running" | "success" | "failed";
  config: Record<string, unknown>;
  total_items: number;
  success_count: number;
  failed_count: number;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface CollectedData {
  id: string;
  task_id: string;
  source_id: string;
  line_id: string;
  url: string | null;
  title: string;
  content: string;
  content_type: string;
  raw: Record<string, unknown>;
  meta: Record<string, unknown>;
  collected_at: string;
}

export interface CrawlerLog {
  id: number;
  task_id: string;
  source_id: string;
  level: string;
  message: string;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface TaskStatusCounts {
  pending: number;
  running: number;
  success: number;
  failed: number;
}

export interface StatsOverview {
  source_count: number;
  enabled_source_count: number;
  task_count: number;
  task_status_counts: TaskStatusCounts;
  total_collected_items: number;
  log_count: number;
  recent_tasks: {
    id: string;
    source_id: string;
    source_name: string;
    status: string;
    total_items: number;
    created_at: string;
  }[];
}
