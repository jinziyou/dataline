"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Database, ScrollText } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

const NAV_ITEMS = [
  { title: "数据源管理", href: "/sources", icon: Database },
  { title: "采集结果", href: "/results", icon: BarChart3 },
  { title: "运行日志", href: "/logs", icon: ScrollText },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <Sidebar>
      <SidebarHeader className="border-b border-border/80 px-5 py-4">
        <Link href="/" className="flex flex-col gap-0.5">
          <span className="text-lg font-semibold tracking-tight text-foreground">
            DataLine
          </span>
          <span className="text-xs text-muted-foreground">
            多源异类数据采集汇聚系统
          </span>
        </Link>
      </SidebarHeader>
      <SidebarContent className="px-2 pt-2">
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            管理
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1">
              {NAV_ITEMS.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    render={<Link href={item.href} />}
                    isActive={
                      pathname === item.href ||
                      pathname.startsWith(`${item.href}/`)
                    }
                  >
                    <item.icon className="opacity-80" />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
