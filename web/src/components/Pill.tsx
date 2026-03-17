import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export default function Pill({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "good" | "bad" | "info";
}) {
  const styles =
    tone === "good"
      ? "bg-[rgba(16,185,129,0.12)] text-[color:var(--ok)] ring-[rgba(16,185,129,0.25)]"
      : tone === "bad"
        ? "bg-[rgba(239,68,68,0.10)] text-[color:var(--bad)] ring-[rgba(239,68,68,0.22)]"
        : tone === "info"
          ? "bg-[rgba(79,70,229,0.10)] text-[color:var(--brand)] ring-[rgba(79,70,229,0.22)]"
          : "bg-[rgba(15,23,42,0.06)] text-primary ring-[rgba(15,23,42,0.10)]";

  return <span className={cn("inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs ring-1", styles)}>{children}</span>;
}
