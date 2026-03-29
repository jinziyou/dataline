import type { CrawlerLog, CrawlerTask, Source } from "@/types";

function apiBase(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
  return raw.replace(/\/$/, "");
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${apiBase()}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function listSources(): Promise<Source[]> {
  return fetchJson<Source[]>("/sources");
}

export function listTasks(params?: {
  source_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<CrawlerTask[]> {
  const q = new URLSearchParams();
  if (params?.source_id) q.set("source_id", params.source_id);
  if (params?.status) q.set("status", params.status);
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  const qs = q.toString();
  return fetchJson<CrawlerTask[]>(`/tasks${qs ? `?${qs}` : ""}`);
}

export function listLogs(params?: {
  task_id?: string;
  source_id?: string;
  level?: string;
  limit?: number;
  offset?: number;
}): Promise<CrawlerLog[]> {
  const q = new URLSearchParams();
  if (params?.task_id) q.set("task_id", params.task_id);
  if (params?.source_id) q.set("source_id", params.source_id);
  if (params?.level) q.set("level", params.level);
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  const qs = q.toString();
  return fetchJson<CrawlerLog[]>(`/logs${qs ? `?${qs}` : ""}`);
}
