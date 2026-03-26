import Link from "next/link";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";

const CARDS = [
  {
    title: "数据源管理",
    description: "管理数据源配置与数据通道，支持五大类数据源接入",
    href: "/sources",
    icon: "🗄",
  },
  {
    title: "采集结果",
    description: "查看采集任务执行状态与已采集的数据",
    href: "/results",
    icon: "📊",
  },
  {
    title: "运行日志",
    description: "查看 Crawler 采集过程中的运行日志",
    href: "/logs",
    icon: "📋",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">DataLine</h1>
        <p className="text-muted-foreground mt-2">
          多源异类数据采集汇聚系统 — 统一接入、配置驱动、可视化管理
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {CARDS.map((card) => (
          <Link key={card.href} href={card.href}>
            <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="text-2xl">{card.icon}</span>
                  {card.title}
                </CardTitle>
                <CardDescription>{card.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <span className="text-sm text-primary">
                  进入管理 &rarr;
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
