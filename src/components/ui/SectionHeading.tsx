import { cn } from "@/lib/utils";

export function SectionHeading({
  eyebrow,
  title,
  description,
  className,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  className?: string;
}) {
  return (
    <div className={cn("max-w-3xl", className)}>
      <div className="mb-5 flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.24em] text-[var(--muted)]">
        <span className="h-px w-9 bg-[var(--accent)]" />
        {eyebrow}
      </div>
      <h2 className="text-balance text-4xl font-semibold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl lg:text-6xl">
        {title}
      </h2>
      {description ? (
        <p className="mt-6 max-w-2xl text-base leading-7 text-[var(--muted)] sm:text-lg">
          {description}
        </p>
      ) : null}
    </div>
  );
}
