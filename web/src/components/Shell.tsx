import { PropsWithChildren, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Moon, Sparkles, SunMedium, Zap } from "lucide-react";
import { cn } from "@/lib/cn";

type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  const saved = localStorage.getItem("theme");
  if (saved === "light" || saved === "dark") return saved;
  return "light";
}

export default function Shell({ children }: PropsWithChildren) {
  const [theme, setTheme] = useState<Theme>(() => getInitialTheme());

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggle = () => setTheme((t) => (t === "light" ? "dark" : "light"));
  const themeLabel = useMemo(() => (theme === "light" ? "Light" : "Dark"), [theme]);

  return (
    <div className={cn("bg-app min-h-screen")}>
      <div className="mx-auto max-w-6xl px-5 py-10">
        <motion.header
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-[rgba(79,70,229,0.10)] ring-1 ring-[rgba(79,70,229,0.16)] grid place-items-center">
              <Sparkles className="h-5 w-5 text-[color:var(--brand)]" />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-tight text-primary">LLM Debate</h1>
              <p className="text-sm text-muted">Premium debate + judge viewer</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-2 text-xs">
              <span className="rounded-full bg-[rgba(15,23,42,0.06)] px-3 py-1 text-primary ring-1 ring-[rgba(15,23,42,0.10)]">
                React + Vite
              </span>
              <span className="rounded-full bg-[rgba(15,23,42,0.06)] px-3 py-1 text-primary ring-1 ring-[rgba(15,23,42,0.10)]">
                FastAPI
              </span>
              <span className="rounded-full bg-[rgba(15,23,42,0.06)] px-3 py-1 text-primary ring-1 ring-[rgba(15,23,42,0.10)] inline-flex items-center gap-1">
                <Zap className="h-3.5 w-3.5 text-[color:var(--brand)]" /> OpenAI
              </span>
            </div>

            <button
              onClick={toggle}
              className="inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-2 text-xs text-primary ring-1 ring-[rgba(15,23,42,0.10)] shadow-[0_10px_30px_rgba(2,6,23,0.10)] hover:bg-white"
              title="Toggle theme"
            >
              {theme === "light" ? <SunMedium className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              {themeLabel}
            </button>
          </div>
        </motion.header>

        <main className="mt-8">{children}</main>

        <footer className="mt-10 text-xs text-muted">
          Tip: set <code className="font-mono text-primary">VITE_API_BASE_URL</code> in{" "}
          <code className="font-mono text-primary">web/.env</code>.
        </footer>
      </div>
    </div>
  );
}

