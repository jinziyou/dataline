"use client";

import { Fragment, useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import type { CrawlerTask, CollectedData } from "@/types";
import { getTask, getTaskData } from "@/lib/api";

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

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [task, setTask] = useState<CrawlerTask | null>(null);
  const [data, setData] = useState<CollectedData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [t, d] = await Promise.all([
        getTask(id),
        getTaskData(id, { limit: 200 }),
      ]);
      setTask(t);
      setData(d);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const autoRefreshRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    if (task && (task.status === "running" || task.status === "pending")) {
      autoRefreshRef.current = setInterval(() => load(), 5000);
    }
    return () => {
      if (autoRefreshRef.current) clearInterval(autoRefreshRef.current);
    };
  }, [task, load]);

  if (loading) {
    return (
      <PageShell>
        <p className="text-muted-foreground py-20 text-center">加载中...</p>
      </PageShell>
    );
  }

  if (error && !task) {
    return (
      <PageShell>
        <p className="text-destructive py-20 text-center">{error}</p>
      </PageShell>
    );
  }

  if (!task) return null;

  const duration =
    task.started_at && task.finished_at
      ? `${((new Date(task.finished_at).getTime() - new Date(task.started_at).getTime()) / 1000).toFixed(1)}s`
      : task.started_at
        ? "运行中..."
        : "-";

  return (
    <PageShell>
      <PageHeader
        eyebrow="任务详情"
        title={task.id}
        description={
          <>
            数据源:{" "}
            <Link href={`/sources/${task.source_id}`} className="text-primary hover:underline">
              {task.source_name || task.source_id}
            </Link>
          </>
        }
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => router.push("/results")}>
              <ArrowLeft data-icon="inline-start" />
              返回列表
            </Button>
            {(task.status === "running" || task.status === "pending") && (
              <Badge variant="secondary" className="animate-pulse">自动刷新中</Badge>
            )}
          </div>
        }
      />

      {/* Task summary */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>任务概览</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <dt className="text-muted-foreground">状态</dt>
              <dd className="mt-1">
                <Badge variant={STATUS_VARIANT[task.status] || "outline"}>
                  {STATUS_LABEL[task.status] || task.status}
                </Badge>
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">采集数量</dt>
              <dd className="mt-1 font-mono">{task.total_items}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">成功 / 失败</dt>
              <dd className="mt-1 font-mono">
                <span className="text-green-600">{task.success_count}</span>
                {" / "}
                <span className="text-destructive">{task.failed_count}</span>
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">耗时</dt>
              <dd className="mt-1 font-mono">{duration}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">开始时间</dt>
              <dd className="mt-1">
                {task.started_at ? new Date(task.started_at).toLocaleString("zh-CN") : "-"}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">结束时间</dt>
              <dd className="mt-1">
                {task.finished_at ? new Date(task.finished_at).toLocaleString("zh-CN") : "-"}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">创建时间</dt>
              <dd className="mt-1">{new Date(task.created_at).toLocaleString("zh-CN")}</dd>
            </div>
            {task.error && (
              <div className="sm:col-span-2 lg:col-span-4">
                <dt className="text-muted-foreground">错误信息</dt>
                <dd className="mt-1 text-destructive">{task.error}</dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      {/* Collected data */}
      <Card>
        <CardHeader>
          <CardTitle>采集数据 ({data.length})</CardTitle>
          <CardDescription>本次任务采集到的数据条目</CardDescription>
        </CardHeader>
        <CardContent>
          {data.length === 0 ? (
            <p className="text-muted-foreground py-8 text-center">
              {task.status === "running" ? "任务运行中，暂无数据" : "暂无采集数据"}
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>标题</TableHead>
                  <TableHead>通道</TableHead>
                  <TableHead>来源地址</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>采集时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((item) => (
                  <Fragment key={item.id}>
                    <TableRow
                      className="cursor-pointer"
                      onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                    >
                      <TableCell className="max-w-[250px] truncate font-medium">
                        {item.title || "(无标题)"}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-xs">
                        {item.line_id}
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate text-muted-foreground">
                        {item.url ? (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 hover:text-foreground"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {(() => { try { return new URL(item.url).pathname.slice(0, 40); } catch { return item.url.slice(0, 40); } })()}
                            <ExternalLink className="size-3" />
                          </a>
                        ) : "-"}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{item.content_type}</Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground whitespace-nowrap">
                        {new Date(item.collected_at).toLocaleString("zh-CN")}
                      </TableCell>
                    </TableRow>
                    {expandedId === item.id && (
                      <TableRow>
                        <TableCell colSpan={5} className="bg-muted/30">
                          <div className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-lg bg-background p-4 text-sm">
                            {item.content || "(无内容)"}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </Fragment>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </PageShell>
  );
}
