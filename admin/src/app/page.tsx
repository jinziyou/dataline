import Link from "next/link";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { PageHeader, PageShell } from "@/components/layout/page-frame";
import { Database, BarChart3, ScrollText } from "lucide-react";

const CARDS = [
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

export default function HomePage() {
  return (
    <PageShell>
      <PageHeader
        eyebrow="DataLine"
        title="控制台"
        description="多源异类数据采集汇聚系统 — 统一接入、配置驱动、可视化管理"
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {CARDS.map((card) => (
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
