import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Container({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "mx-auto w-full max-w-[87.5rem] px-5 sm:px-8 lg:px-6 2xl:px-0",
        className,
      )}
    >
      {children}
    </div>
  );
}
