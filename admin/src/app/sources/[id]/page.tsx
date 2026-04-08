"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Play,
  Plus,
  Trash2,
  Pencil,
  Save,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
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
} from "@/components/ui/sheet";
import { PageHeader, PageShell } from "@/components/layout/page-frame";
import type { Source, Line } from "@/types";
import {
  getSource,
  updateSource,
  deleteSource,
  listLines,
  createLine,
  deleteLine,
  triggerTask,
} from "@/lib/api";

const TYPE_LABELS: Record<string, string> = {
  website: "公开网站",
  api: "API 接口",
  file: "文件系统",
  stream: "消息流",
  external: "外部系统",
};

export default function SourceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [source, setSource] = useState<Source | null>(null);
  const [lines, setLines] = useState<Line[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // edit mode
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editUrl, setEditUrl] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editEnabled, setEditEnabled] = useState(true);
  const [saving, setSaving] = useState(false);

  // add line sheet
  const [lineSheetOpen, setLineSheetOpen] = useState(false);
  const [lineName, setLineName] = useState("");
  const [lineId, setLineId] = useState("");
  const [lineUrl, setLineUrl] = useState("");
  const [lineDesc, setLineDesc] = useState("");
  const [lineSubmitting, setLineSubmitting] = useState(false);
  const [lineError, setLineError] = useState<string | null>(null);

  // trigger
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null);

  // delete
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, l] = await Promise.all([getSource(id), listLines(id)]);
      setSource(s);
      setLines(l);
      setEditName(s.name);
      setEditUrl(s.url ?? "");
      setEditDesc(s.description);
      setEditEnabled(s.enabled);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await updateSource(id, {
        name: editName,
        url: editUrl || undefined,
        description: editDesc || undefined,
        enabled: editEnabled,
      });
      setSource(updated);
      setEditing(false);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm("确认删除该数据源？此操作不可恢复。")) return;
    setDeleting(true);
    try {
      await deleteSource(id);
      router.push("/sources");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "删除失败");
      setDeleting(false);
    }
  }

  async function handleTrigger() {
    setTriggering(true);
    setTriggerMsg(null);
    try {
      const task = await triggerTask({ source_id: id });
      setTriggerMsg(`任务已创建: ${task.id}`);
    } catch (e: unknown) {
      setTriggerMsg(e instanceof Error ? e.message : "触发失败");
    } finally {
      setTriggering(false);
    }
  }

  async function handleCreateLine() {
    const lid = lineId || `${id}-${lineName.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 30)}`;
    if (!lineName) { setLineError("名称不能为空"); return; }
    setLineSubmitting(true);
    setLineError(null);
    try {
      await createLine(id, {
        id: lid,
        source_id: id,
        name: lineName,
        url: lineUrl || undefined,
        description: lineDesc || undefined,
      });
      setLineSheetOpen(false);
      setLineName(""); setLineId(""); setLineUrl(""); setLineDesc("");
      const l = await listLines(id);
      setLines(l);
    } catch (e: unknown) {
      setLineError(e instanceof Error ? e.message : "创建失败");
    } finally {
      setLineSubmitting(false);
    }
  }

  async function handleDeleteLine(lineId: string) {
    if (!confirm("确认删除该数据通道？")) return;
    try {
      await deleteLine(lineId);
      setLines((prev) => prev.filter((l) => l.id !== lineId));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "删除失败");
    }
  }

  if (loading) {
    return (
      <PageShell>
        <p className="text-muted-foreground py-20 text-center">加载中...</p>
      </PageShell>
    );
  }

  if (error && !source) {
    return (
      <PageShell>
        <p className="text-destructive py-20 text-center">{error}</p>
      </PageShell>
    );
  }

  if (!source) return null;

  return (
    <PageShell>
      <PageHeader
        eyebrow="数据源详情"
        title={source.name}
        description={`${TYPE_LABELS[source.type] || source.type} · ${source.id}`}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => router.push("/sources")}>
              <ArrowLeft data-icon="inline-start" />
              返回列表
            </Button>
            {!editing ? (
              <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                <Pencil data-icon="inline-start" />
                编辑
              </Button>
            ) : (
              <>
                <Button variant="outline" size="sm" onClick={() => setEditing(false)}>
                  <X data-icon="inline-start" />
                  取消
                </Button>
                <Button size="sm" onClick={handleSave} disabled={saving}>
                  <Save data-icon="inline-start" />
                  {saving ? "保存中..." : "保存"}
                </Button>
              </>
            )}
            <Button
              variant="destructive"
              size="sm"
              onClick={handleDelete}
              disabled={deleting}
            >
              <Trash2 data-icon="inline-start" />
              删除
            </Button>
          </div>
        }
      />

      {error && <p className="mb-4 text-sm text-destructive">{error}</p>}

      {/* Source Info Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent>
          {editing ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-1.5">
                <Label htmlFor="edit-name">名称</Label>
                <Input id="edit-name" value={editName} onChange={(e) => setEditName(e.target.value)} />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="edit-url">地址</Label>
                <Input id="edit-url" value={editUrl} onChange={(e) => setEditUrl(e.target.value)} />
              </div>
              <div className="grid gap-1.5 sm:col-span-2">
                <Label htmlFor="edit-desc">描述</Label>
                <Textarea id="edit-desc" value={editDesc} onChange={(e) => setEditDesc(e.target.value)} />
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={editEnabled} onCheckedChange={setEditEnabled} />
                <Label>{editEnabled ? "启用" : "停用"}</Label>
              </div>
            </div>
          ) : (
            <dl className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <dt className="text-muted-foreground">类型</dt>
                <dd className="mt-1">
                  <Badge variant="secondary">{TYPE_LABELS[source.type] || source.type}</Badge>
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">地址</dt>
                <dd className="mt-1 truncate">{source.url || "-"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">状态</dt>
                <dd className="mt-1">
                  <Badge variant={source.enabled ? "default" : "outline"}>
                    {source.enabled ? "启用" : "停用"}
                  </Badge>
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">更新时间</dt>
                <dd className="mt-1">{new Date(source.updated_at).toLocaleString("zh-CN")}</dd>
              </div>
              {source.description && (
                <div className="sm:col-span-2 lg:col-span-4">
                  <dt className="text-muted-foreground">描述</dt>
                  <dd className="mt-1">{source.description}</dd>
                </div>
              )}
            </dl>
          )}
        </CardContent>
      </Card>

      {/* Trigger Crawl */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>采集操作</CardTitle>
          <CardDescription>触发一次采集任务，将对所有启用的数据通道执行采集</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Button onClick={handleTrigger} disabled={triggering || lines.filter((l) => l.enabled).length === 0}>
              <Play data-icon="inline-start" />
              {triggering ? "触发中..." : "触发采集"}
            </Button>
            {lines.filter((l) => l.enabled).length === 0 && (
              <span className="text-sm text-muted-foreground">请先添加并启用数据通道</span>
            )}
            {triggerMsg && (
              <span className="text-sm text-muted-foreground">{triggerMsg}</span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Lines Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>数据通道 ({lines.length})</CardTitle>
            <CardDescription>此数据源下的采集通道列表</CardDescription>
          </div>
          <Sheet open={lineSheetOpen} onOpenChange={(open) => { setLineSheetOpen(open); if (!open) { setLineName(""); setLineId(""); setLineUrl(""); setLineDesc(""); setLineError(null); } }}>
            <Button size="sm" onClick={() => setLineSheetOpen(true)}>
              <Plus data-icon="inline-start" />
              添加通道
            </Button>
            <SheetContent side="right" className="sm:max-w-md">
              <SheetHeader>
                <SheetTitle>添加数据通道</SheetTitle>
                <SheetDescription>为数据源 &ldquo;{source.name}&rdquo; 添加新的采集通道</SheetDescription>
              </SheetHeader>
              <div className="flex flex-col gap-4 overflow-y-auto px-4">
                <div className="grid gap-1.5">
                  <Label htmlFor="line-name">名称 *</Label>
                  <Input
                    id="line-name"
                    placeholder="如：科技新闻"
                    value={lineName}
                    onChange={(e) => setLineName(e.target.value)}
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="line-id">ID</Label>
                  <Input
                    id="line-id"
                    placeholder="自动生成"
                    value={lineId}
                    onChange={(e) => setLineId(e.target.value)}
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="line-url">采集地址</Label>
                  <Input
                    id="line-url"
                    type="url"
                    placeholder="https://example.com/category"
                    value={lineUrl}
                    onChange={(e) => setLineUrl(e.target.value)}
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="line-desc">描述</Label>
                  <Textarea
                    id="line-desc"
                    placeholder="可选的通道描述"
                    value={lineDesc}
                    onChange={(e) => setLineDesc(e.target.value)}
                  />
                </div>
                {lineError && <p className="text-sm text-destructive">{lineError}</p>}
              </div>
              <SheetFooter>
                <Button onClick={handleCreateLine} disabled={lineSubmitting}>
                  {lineSubmitting ? "创建中..." : "添加通道"}
                </Button>
              </SheetFooter>
            </SheetContent>
          </Sheet>
        </CardHeader>
        <CardContent>
          {lines.length === 0 ? (
            <p className="text-muted-foreground py-8 text-center">
              暂无数据通道，请点击&ldquo;添加通道&rdquo;
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>名称</TableHead>
                  <TableHead>地址</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>更新时间</TableHead>
                  <TableHead className="w-[60px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {lines.map((line) => (
                  <TableRow key={line.id}>
                    <TableCell className="font-medium">{line.name}</TableCell>
                    <TableCell className="max-w-[300px] truncate text-muted-foreground">
                      {line.url || "-"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={line.enabled ? "default" : "outline"}>
                        {line.enabled ? "启用" : "停用"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(line.updated_at).toLocaleString("zh-CN")}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => handleDeleteLine(line.id)}
                      >
                        <Trash2 className="size-3.5 text-destructive" />
                      </Button>
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
