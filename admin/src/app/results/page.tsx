"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
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
import type { CrawlerTask } from "@/types";
import { listTasks } from "@/lib/api";

const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  pending: "outline",
  running: "secondary",
  success: "default",
  failed: "destructive",
};

const STATUS_LABEL: Record<string, string> = {
  pending: "等待中",
  running: "运行中",
  success: "成功",
  failed: "失败",
};

const STATUS_OPTIONS = [
  { value: "", label: "全部状态" },
  { value: "pending", label: "等待中" },
  { value: "running", label: "运行中" },
  { value: "success", label: "成功" },
  { value: "failed", label: "失败" },
];

export default function ResultsPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<CrawlerTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filterSource, setFilterSource] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    listTasks({
      source_id: filterSource || undefined,
      status: filterStatus || undefined,
      limit: 50,
    })
      .then(setTasks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [filterSource, filterStatus]);

  useEffect(() => { load(); }, [load]);

  return (
    <PageShell>
      <PageHeader
        eyebrow="管理"
        title="采集结果"
        description="查看采集任务的执行状态与结果统计"
      />

      <Card>
        <CardHeader>
          <CardTitle>任务列表</CardTitle>
          <CardDescription>最近的采集任务及执行状态，点击行查看详情</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex flex-wrap gap-3">
            <Input
              placeholder="按数据源 ID 筛选"
              value={filterSource}
              onChange={(e) => setFilterSource(e.target.value)}
              className="max-w-[200px]"
            />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="h-9 rounded-xl border border-border/60 bg-muted/30 px-3 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              {STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {loading ? (
            <p className="text-muted-foreground py-8 text-center">加载中...</p>
          ) : error ? (
            <p className="text-destructive py-8 text-center">{error}</p>
          ) : tasks.length === 0 ? (
            <p className="text-muted-foreground py-8 text-center">
              暂无采集任务
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>任务 ID</TableHead>
                  <TableHead>数据源</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">采集数</TableHead>
                  <TableHead className="text-right">成功</TableHead>
                  <TableHead className="text-right">失败</TableHead>
                  <TableHead>开始时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tasks.map((task) => (
                  <TableRow
                    key={task.id}
                    className="cursor-pointer"
                    onClick={() => router.push(`/results/${task.id}`)}
                  >
                    <TableCell className="font-mono text-xs">
                      {task.id}
                    </TableCell>
                    <TableCell>{task.source_id}</TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[task.status] || "outline"}>
                        {STATUS_LABEL[task.status] || task.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {task.total_items}
                    </TableCell>
                    <TableCell className="text-right">
                      {task.success_count}
                    </TableCell>
                    <TableCell className="text-right">
                      {task.failed_count}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {task.started_at
                        ? new Date(task.started_at).toLocaleString("zh-CN")
                        : "-"}
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
