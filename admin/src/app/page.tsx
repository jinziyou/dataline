"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PageHeader, PageShell } from "@/components/layout/page-frame";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Database,
  BarChart3,
  ScrollText,
  CheckCircle,
  XCircle,
  Loader2,
  FileStack,
} from "lucide-react";
import type { StatsOverview } from "@/types";
import { getStats } from "@/lib/api";

const NAV_CARDS = [
  {
    title: "数据源管理",
    description: "管理数据源配置与数据通道，支持五大类数据源接入",
    href: "/sources",
    icon: Database,
  },
  {
    title: "采集结果",
    description: "查看采集任务执行状态与已采集的数据",
    href: "/results",
    icon: BarChart3,
  },
  {
    title: "运行日志",
    description: "查看 Crawler 采集过程中的运行日志",
    href: "/logs",
    icon: ScrollText,
  },
];

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

export default function HomePage() {
  const [stats, setStats] = useState<StatsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    getStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <PageShell>
      <PageHeader
        eyebrow="DataLine"
        title="控制台"
        description="多源异类数据采集汇聚系统 — 统一接入、配置驱动、可视化管理"
      />

      {/* Stat cards */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Database}
          label="数据源"
          value={stats?.source_count}
          sub={stats ? `${stats.enabled_source_count} 个启用` : undefined}
          loading={loading}
        />
        <StatCard
          icon={BarChart3}
          label="采集任务"
          value={stats?.task_count}
          sub={stats ? `${stats.task_status_counts.running} 个运行中` : undefined}
          loading={loading}
        />
        <StatCard
          icon={FileStack}
          label="已采集数据"
          value={stats?.total_collected_items}
          loading={loading}
        />
        <StatCard
          icon={ScrollText}
          label="日志条数"
          value={stats?.log_count}
          loading={loading}
        />
      </div>

      {/* Task status breakdown */}
      {stats && (
        <div className="mb-8 grid gap-4 sm:grid-cols-4">
          <MiniStat icon={Loader2} label="等待中" value={stats.task_status_counts.pending} className="text-muted-foreground" />
          <MiniStat icon={Loader2} label="运行中" value={stats.task_status_counts.running} className="text-blue-500" spin />
          <MiniStat icon={CheckCircle} label="成功" value={stats.task_status_counts.success} className="text-green-500" />
          <MiniStat icon={XCircle} label="失败" value={stats.task_status_counts.failed} className="text-destructive" />
        </div>
      )}

      {/* Recent tasks */}
      {stats && stats.recent_tasks.length > 0 && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>最近任务</CardTitle>
            <CardDescription>最近 5 个采集任务</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>任务 ID</TableHead>
                  <TableHead>数据源</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">采集数</TableHead>
                  <TableHead>时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.recent_tasks.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell>
                      <Link href={`/results/${t.id}`} className="font-mono text-xs text-primary hover:underline">
                        {t.id}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Link href={`/sources/${t.source_id}`} className="hover:underline">
                        {t.source_name}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[t.status] || "outline"}>
                        {STATUS_LABEL[t.status] || t.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono">{t.total_items}</TableCell>
                    <TableCell className="text-muted-foreground whitespace-nowrap">
                      {new Date(t.created_at).toLocaleString("zh-CN")}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Quick nav */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {NAV_CARDS.map((card) => (
          <Link key={card.href} href={card.href} className="block">
            <Card className="h-full cursor-pointer transition-[transform,box-shadow] duration-200 hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-lg dark:hover:shadow-black/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <card.icon className="h-5 w-5 shrink-0 text-primary opacity-90" />
                  {card.title}
                </CardTitle>
                <CardDescription>{card.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <span className="text-sm font-medium text-primary">
                  进入管理 &rarr;
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </PageShell>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  loading,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value?: number;
  sub?: string;
  loading: boolean;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        <div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-primary/10">
          <Icon className="size-5 text-primary" />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-medium text-muted-foreground">{label}</p>
          {loading ? (
            <Skeleton className="mt-1 h-7 w-16" />
          ) : (
            <p className="text-2xl font-bold tracking-tight">{value?.toLocaleString() ?? 0}</p>
          )}
          {sub && !loading && (
            <p className="text-xs text-muted-foreground">{sub}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function MiniStat({
  icon: Icon,
  label,
  value,
  className,
  spin,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
  className?: string;
  spin?: boolean;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <Icon className={`size-4 ${spin ? "animate-spin" : ""} ${className ?? ""}`} />
        <div>
          <p className="text-lg font-bold">{value}</p>
          <p className="text-xs text-muted-foreground">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}
