"use client";

import { useLayoutEffect, useRef } from "react";
import { gsap } from "@/lib/gsap";
import { cn } from "@/lib/utils";

export function TextReveal({
  text,
  className,
  delay = 0,
}: {
  text: string;
  className?: string;
  delay?: number;
}) {
  const root = useRef<HTMLSpanElement>(null);

  useLayoutEffect(() => {
    const el = root.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        el.querySelectorAll("[data-word]"),
        { yPercent: 120, opacity: 0 },
        {
          yPercent: 0,
          opacity: 1,
          duration: 1.05,
          delay,
          stagger: 0.045,
          ease: "power4.out",
        },
      );
    }, el);

    return () => ctx.revert();
  }, [delay]);

  return (
    <span ref={root} className={cn("inline-flex flex-wrap", className)}>
      {text.split(" ").map((word, index) => (
        <span key={`${word}-${index}`} className="overflow-hidden pr-[0.24em] pb-[0.08em]">
          <span data-word className="inline-block will-change-transform">
            {word}
          </span>
        </span>
      ))}
    </span>
  );
}
