import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import {
  PAGE_MAX_W_CLASS,
  PAGE_READING_MAX_CLASS,
  pagePaddingX,
  pagePaddingY,
  pagePaddingYHero,
  detailStackClass,
  listStackClass,
} from "@/lib/page-layout";

type ShellVariant = "default" | "reading" | "hero";

const shellMax: Record<ShellVariant, string> = {
  default: PAGE_MAX_W_CLASS,
  reading: PAGE_READING_MAX_CLASS,
  hero: PAGE_MAX_W_CLASS,
};

const shellY: Record<ShellVariant, string> = {
  default: pagePaddingY,
  reading: pagePaddingY,
  hero: pagePaddingYHero,
};

export function PageShell({
  children,
  className,
  variant = "default",
}: {
  children: ReactNode;
  className?: string;
  variant?: ShellVariant;
}) {
  return (
    <div
      className={cn(
        "mx-auto w-full",
        shellMax[variant],
        pagePaddingX,
        shellY[variant],
        className,
      )}
    >
      {children}
    </div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <header
      className={cn(
        "mb-8 flex flex-col gap-4 sm:flex-row sm:justify-between",
        actions ? "sm:items-center" : "sm:items-start",
      )}
    >
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-widest text-primary/90">
          {eyebrow}
        </p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-foreground md:text-3xl">
          {title}
        </h1>
        {description ? (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex shrink-0 flex-col gap-2 sm:flex-row sm:items-center">
          {actions}
        </div>
      ) : null}
    </header>
  );
}

export function PageList({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cn(listStackClass, className)}>{children}</div>;
}

export function PageStack({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cn(detailStackClass, className)}>{children}</div>;
}
