import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "DataLine - 多源异类数据采集汇聚系统",
  description: "可视化管理采集配置、采集结果和日志",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className={`${inter.variable} h-full`}>
      <body className={`${inter.className} min-h-full flex flex-col`}>
        <TooltipProvider>
          <SidebarProvider>
            <AppSidebar />
            <div className="flex min-h-0 min-w-0 flex-1 flex-col">
              <header className="sticky top-0 z-50 border-b border-border/80 bg-background/75 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
                <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-3 px-4 sm:px-6">
                  <SidebarTrigger className="shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-semibold tracking-tight text-foreground">
                      DataLine
                    </p>
                    <p className="text-xs text-muted-foreground">
                      多源异类数据采集汇聚
                    </p>
                  </div>
                </div>
              </header>
              <main className="flex min-h-0 min-w-0 flex-1 flex-col">{children}</main>
            </div>
          </SidebarProvider>
        </TooltipProvider>
      </body>
    </html>
  );
}
