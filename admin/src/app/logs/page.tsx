"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
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
import type { CrawlerLog } from "@/types";
import { listLogs } from "@/lib/api";

const LEVEL_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  INFO: "secondary",
  WARNING: "outline",
  ERROR: "destructive",
  DEBUG: "outline",
};

export default function LogsPage() {
  const [logs, setLogs] = useState<CrawlerLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listLogs({ limit: 100 })
      .then(setLogs)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">运行日志</h1>
        <p className="text-muted-foreground">
          查看 Crawler 采集过程中的运行日志
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>日志列表</CardTitle>
          <CardDescription>最近的采集运行日志</CardDescription>
        </CardHeader>
        <CardContent>
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
    </div>
  );
}
