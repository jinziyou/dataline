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

export default function ResultsPage() {
  const [tasks, setTasks] = useState<CrawlerTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listTasks({ limit: 50 })
      .then(setTasks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">采集结果</h1>
        <p className="text-muted-foreground">
          查看采集任务的执行状态与结果统计
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>任务列表</CardTitle>
          <CardDescription>最近的采集任务及执行状态</CardDescription>
        </CardHeader>
        <CardContent>
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
                  <TableRow key={task.id}>
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
    </div>
  );
}
