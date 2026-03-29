"use client";

import { useEffect, useState } from "react";
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
import type { Source } from "@/types";
import { listSources } from "@/lib/api";

const TYPE_LABELS: Record<string, string> = {
  website: "公开网站",
  api: "API 接口",
  file: "文件系统",
  stream: "消息流",
  external: "外部系统",
};

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSources()
      .then(setSources)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PageShell>
      <PageHeader
        eyebrow="管理"
        title="数据源管理"
        description="管理数据源配置与数据通道"
        actions={<Button>新增数据源</Button>}
      />

      <Card>
        <CardHeader>
          <CardTitle>数据源列表</CardTitle>
          <CardDescription>当前系统中已配置的所有数据源</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-muted-foreground py-8 text-center">加载中...</p>
          ) : error ? (
            <p className="text-destructive py-8 text-center">{error}</p>
          ) : sources.length === 0 ? (
            <p className="text-muted-foreground py-8 text-center">
              暂无数据源，请点击&ldquo;新增数据源&rdquo;添加
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>名称</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>地址</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>更新时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sources.map((source) => (
                  <TableRow key={source.id}>
                    <TableCell className="font-medium">{source.name}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">
                        {TYPE_LABELS[source.type] || source.type}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[300px] truncate text-muted-foreground">
                      {source.url || "-"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={source.enabled ? "default" : "outline"}>
                        {source.enabled ? "启用" : "停用"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(source.updated_at).toLocaleString("zh-CN")}
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
