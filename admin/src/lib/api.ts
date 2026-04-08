import type {
  CollectedData,
  CrawlerLog,
  CrawlerTask,
  Line,
  PaginatedResponse,
  Source,
  SourceType,
  StatsOverview,
} from "@/types";

function apiBase(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
  return raw.replace(/\/$/, "");
}

function qs(params: Record<string, string | number | boolean | null | undefined>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v != null && v !== "") q.set(k, String(v));
  }
  const s = q.toString();
  return s ? `?${s}` : "";
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

async function fetchVoid(path: string, init?: RequestInit): Promise<void> {
  const url = `${apiBase()}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `${res.status} ${res.statusText}`);
  }
}

const jsonBody = (data: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});

const jsonPatch = (data: unknown): RequestInit => ({
  method: "PATCH",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});

// ── Sources ──

export function listSources(params?: { enabled?: boolean }): Promise<Source[]> {
  return fetchJson<Source[]>(`/sources${qs(params ?? {})}`);
}

export function getSource(id: string): Promise<Source> {
  return fetchJson<Source>(`/sources/${id}`);
}

export function createSource(body: {
  id: string;
  name: string;
  type: SourceType;
  url?: string;
  description?: string;
  enabled?: boolean;
}): Promise<Source> {
  return fetchJson<Source>("/sources", jsonBody(body));
}

export function updateSource(
  id: string,
  body: { name?: string; url?: string; description?: string; enabled?: boolean },
): Promise<Source> {
  return fetchJson<Source>(`/sources/${id}`, jsonPatch(body));
}

export function deleteSource(id: string): Promise<void> {
  return fetchVoid(`/sources/${id}`, { method: "DELETE" });
}

// ── Lines ──

export function listLines(sourceId: string): Promise<Line[]> {
  return fetchJson<Line[]>(`/sources/${sourceId}/lines`);
}

export function createLine(
  sourceId: string,
  body: { id: string; source_id: string; name: string; url?: string; description?: string },
): Promise<Line> {
  return fetchJson<Line>(`/sources/${sourceId}/lines`, jsonBody(body));
}

export function updateLine(
  lineId: string,
  body: { name?: string; url?: string; description?: string; enabled?: boolean },
): Promise<Line> {
  return fetchJson<Line>(`/sources/lines/${lineId}`, jsonPatch(body));
}

export function deleteLine(lineId: string): Promise<void> {
  return fetchVoid(`/sources/lines/${lineId}`, { method: "DELETE" });
}

// ── Tasks ──

export function listTasks(params?: {
  source_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<CrawlerTask>> {
  return fetchJson<PaginatedResponse<CrawlerTask>>(`/tasks${qs(params ?? {})}`);
}

export function getTask(id: string): Promise<CrawlerTask> {
  return fetchJson<CrawlerTask>(`/tasks/${id}`);
}

export function triggerTask(body: {
  source_id: string;
  overrides?: Record<string, unknown>;
}): Promise<CrawlerTask> {
  return fetchJson<CrawlerTask>("/tasks", jsonBody(body));
}

export function getTaskData(
  taskId: string,
  params?: { limit?: number; offset?: number },
): Promise<CollectedData[]> {
  return fetchJson<CollectedData[]>(`/tasks/${taskId}/data${qs(params ?? {})}`);
}

// ── Logs ──

export function listLogs(params?: {
  task_id?: string;
  source_id?: string;
  level?: string;
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<CrawlerLog>> {
  return fetchJson<PaginatedResponse<CrawlerLog>>(`/logs${qs(params ?? {})}`);
}

// ── Stats ──

export function getStats(): Promise<StatsOverview> {
  return fetchJson<StatsOverview>("/stats");
}
