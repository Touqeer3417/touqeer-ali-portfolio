import { cn } from "@/lib/utils";

export function SectionHeading({
  eyebrow,
  title,
  description,
  className,
  descriptionClassName,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  className?: string;
  descriptionClassName?: string;
}) {
  return (
    <div className={cn("max-w-[42rem]", className)}>
      <div className="mb-[1.125rem] flex items-center gap-[0.675rem] font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--body-copy)]">
        <span className="h-px w-[2.025rem] bg-[var(--accent)]" />
        {eyebrow}
      </div>
      <h2 className="text-balance text-[clamp(2rem,3vw,3.375rem)] font-semibold leading-[1.04] tracking-[-0.04em] text-[var(--foreground)]">
        {title}
      </h2>
      {description ? (
        <p
          className={cn(
            "mt-[1.35rem] max-w-[38rem] text-[0.9rem] font-medium leading-[1.6] text-[var(--body-copy)] sm:text-base",
            descriptionClassName,
          )}
        >
          {description}
        </p>
      ) : null}
    </div>
  );
}