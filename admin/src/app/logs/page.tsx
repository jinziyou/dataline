"use client";

import { useEffect, useState, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PageHeader, PageShell } from "@/components/layout/page-frame";
import type { CrawlerLog } from "@/types";
import { listLogs } from "@/lib/api";

const LEVEL_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  INFO: "secondary",
  WARNING: "outline",
  ERROR: "destructive",
  DEBUG: "outline",
};

const LEVEL_OPTIONS = [
  { value: "", label: "全部级别" },
  { value: "DEBUG", label: "DEBUG" },
  { value: "INFO", label: "INFO" },
  { value: "WARNING", label: "WARNING" },
  { value: "ERROR", label: "ERROR" },
];

export default function LogsPage() {
  const [logs, setLogs] = useState<CrawlerLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filterSource, setFilterSource] = useState("");
  const [filterTask, setFilterTask] = useState("");
  const [filterLevel, setFilterLevel] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    listLogs({
      source_id: filterSource || undefined,
      task_id: filterTask || undefined,
      level: filterLevel || undefined,
      limit: 100,
    })
      .then(setLogs)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [filterSource, filterTask, filterLevel]);

  useEffect(() => { load(); }, [load]);

  return (
    <PageShell>
      <PageHeader
        eyebrow="管理"
        title="运行日志"
        description="查看 Crawler 采集过程中的运行日志"
      />

      <Card>
        <CardHeader>
          <CardTitle>日志列表</CardTitle>
          <CardDescription>最近的采集运行日志</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex flex-wrap gap-3">
            <Input
              placeholder="按数据源 ID 筛选"
              value={filterSource}
              onChange={(e) => setFilterSource(e.target.value)}
              className="max-w-[200px]"
            />
            <Input
              placeholder="按任务 ID 筛选"
              value={filterTask}
              onChange={(e) => setFilterTask(e.target.value)}
              className="max-w-[200px]"
            />
            <select
              value={filterLevel}
              onChange={(e) => setFilterLevel(e.target.value)}
              className="h-9 rounded-xl border border-border/60 bg-muted/30 px-3 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              {LEVEL_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {loading ? (
            <p className="text-muted-foreground py-8 text-center">加载中...</p>
          ) : error ? (
            <p className="text-destructive py-8 text-center">{error}</p>
          ) : logs.length === 0 ? (
            <p className="text-muted-foreground py-8 text-center">
              暂无日志记录
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[80px]">级别</TableHead>
                  <TableHead>消息</TableHead>
                  <TableHead>任务 ID</TableHead>
                  <TableHead>数据源</TableHead>
                  <TableHead>时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>
                      <Badge variant={LEVEL_VARIANT[log.level] || "outline"}>
                        {log.level}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[400px] truncate">
                      {log.message}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {log.task_id}
                    </TableCell>
                    <TableCell>{log.source_id}</TableCell>
                    <TableCell className="text-muted-foreground whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString("zh-CN")}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </PageShell>
  );
}
