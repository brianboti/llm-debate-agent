import { PropsWithChildren } from "react";
import { cn } from "@/lib/cn";

export function Card({ className, children }: PropsWithChildren<{ className?: string }>) {
  return (
    <section className={cn("surface rounded-2xl", className)}>
      {children}
    </section>
  );
}

export function CardHeader({ className, children }: PropsWithChildren<{ className?: string }>) {
  return <div className={cn("px-5 pt-5", className)}>{children}</div>;
}

export function CardTitle({ className, children }: PropsWithChildren<{ className?: string }>) {
  return <h2 className={cn("text-[15px] font-semibold tracking-tight text-primary", className)}>{children}</h2>;
}

export function CardSubtitle({ className, children }: PropsWithChildren<{ className?: string }>) {
  return <p className={cn("mt-1 text-sm text-muted", className)}>{children}</p>;
}

export function CardBody({ className, children }: PropsWithChildren<{ className?: string }>) {
  return <div className={cn("px-5 pb-5 pt-4", className)}>{children}</div>;
}

