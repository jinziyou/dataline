"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader, PageShell } from "@/components/layout/page-frame";
import type { Source, SourceType } from "@/types";
import { listSources, createSource } from "@/lib/api";

const TYPE_LABELS: Record<string, string> = {
  website: "公开网站",
  api: "API 接口",
  file: "文件系统",
  stream: "消息流",
  external: "外部系统",
};

const SOURCE_TYPES: { value: SourceType; label: string }[] = [
  { value: "website", label: "公开网站" },
  { value: "api", label: "API 接口" },
  { value: "file", label: "文件系统" },
  { value: "stream", label: "消息流" },
  { value: "external", label: "外部系统" },
];

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 64);
}

export default function SourcesPage() {
  const router = useRouter();
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [formName, setFormName] = useState("");
  const [formId, setFormId] = useState("");
  const [formIdTouched, setFormIdTouched] = useState(false);
  const [formType, setFormType] = useState<SourceType>("website");
  const [formUrl, setFormUrl] = useState("");
  const [formDesc, setFormDesc] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    listSources()
      .then(setSources)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  function resetForm() {
    setFormName("");
    setFormId("");
    setFormIdTouched(false);
    setFormType("website");
    setFormUrl("");
    setFormDesc("");
    setFormError(null);
  }

  async function handleCreate() {
    const id = formId || slugify(formName);
    if (!id || !formName) {
      setFormError("名称和 ID 不能为空");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      await createSource({
        id,
        name: formName,
        type: formType,
        url: formUrl || undefined,
        description: formDesc || undefined,
      });
      setSheetOpen(false);
      resetForm();
      load();
    } catch (e: unknown) {
      setFormError(e instanceof Error ? e.message : "创建失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageShell>
      <PageHeader
        eyebrow="管理"
        title="数据源管理"
        description="管理数据源配置与数据通道"
        actions={
          <Sheet open={sheetOpen} onOpenChange={(open) => { setSheetOpen(open); if (!open) resetForm(); }}>
            <SheetTrigger
              render={
                <Button>
                  <Plus data-icon="inline-start" />
                  新增数据源
                </Button>
              }
            />
            <SheetContent side="right" className="sm:max-w-md">
              <SheetHeader>
                <SheetTitle>新增数据源</SheetTitle>
                <SheetDescription>填写数据源基本信息，创建后可添加数据通道</SheetDescription>
              </SheetHeader>
              <div className="flex flex-col gap-4 overflow-y-auto px-4">
                <div className="grid gap-1.5">
                  <Label htmlFor="source-name">名称 *</Label>
                  <Input
                    id="source-name"
                    placeholder="如：人民日报"
                    value={formName}
                    onChange={(e) => {
                      setFormName(e.target.value);
                      if (!formIdTouched) setFormId(slugify(e.target.value));
                    }}
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="source-id">ID *</Label>
                  <Input
                    id="source-id"
                    placeholder="自动生成，可手动修改"
                    value={formId}
                    onChange={(e) => { setFormId(e.target.value); setFormIdTouched(true); }}
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="source-type">类型</Label>
                  <select
                    id="source-type"
                    value={formType}
                    onChange={(e) => setFormType(e.target.value as SourceType)}
                    className="h-9 w-full rounded-xl border border-border/60 bg-muted/30 px-3 py-2 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                  >
                    {SOURCE_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="source-url">地址</Label>
                  <Input
                    id="source-url"
                    type="url"
                    placeholder="https://example.com"
                    value={formUrl}
                    onChange={(e) => setFormUrl(e.target.value)}
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="source-desc">描述</Label>
                  <Textarea
                    id="source-desc"
                    placeholder="可选的数据源描述"
                    value={formDesc}
                    onChange={(e) => setFormDesc(e.target.value)}
                  />
                </div>
                {formError && (
                  <p className="text-sm text-destructive">{formError}</p>
                )}
              </div>
              <SheetFooter>
                <Button onClick={handleCreate} disabled={submitting}>
                  {submitting ? "创建中..." : "创建数据源"}
                </Button>
              </SheetFooter>
            </SheetContent>
          </Sheet>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>数据源列表</CardTitle>
          <CardDescription>当前系统中已配置的所有数据源</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3 py-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
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
                  <TableHead className="text-center">通道数</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>更新时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sources.map((source) => (
                  <TableRow
                    key={source.id}
                    className="cursor-pointer"
                    onClick={() => router.push(`/sources/${source.id}`)}
                  >
                    <TableCell className="font-medium">{source.name}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">
                        {TYPE_LABELS[source.type] || source.type}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[300px] truncate text-muted-foreground">
                      {source.url || "-"}
                    </TableCell>
                    <TableCell className="text-center font-mono">
                      {source.line_count}
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
