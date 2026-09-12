import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";

export function ButtonLink({
  href,
  children,
  variant = "primary",
  external = false,
  className,
}: {
  href: string;
  children: ReactNode;
  variant?: "primary" | "ghost";
  external?: boolean;
  className?: string;
}) {
  const styles = cn(
    "group inline-flex min-h-12 items-center justify-center gap-2 rounded-full border px-5 text-sm font-medium transition duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--background)]",
    variant === "primary"
      ? "border-[var(--foreground)] bg-[var(--foreground)] text-[var(--background)] hover:-translate-y-0.5 hover:shadow-[0_14px_45px_rgba(117,245,181,0.15)]"
      : "border-[var(--line)] bg-[var(--panel)] text-[var(--foreground)] hover:border-[var(--line-strong)] hover:bg-[var(--panel-strong)]",
    className,
  );

  if (external) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className={styles}>
        {children}
        <ArrowUpRight className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
      </a>
    );
  }

  return (
    <Link href={href} className={styles}>
      {children}
      <ArrowUpRight className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
    </Link>
  );
}
