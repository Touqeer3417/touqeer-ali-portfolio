"use client";

import { useLayoutEffect, useRef } from "react";

import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { FadeIn } from "@/components/animation/FadeIn";
import { gsap } from "@/lib/gsap";
import { currentlyExploring, experience } from "@/data/experience";

export function Experience() {
  const root = useRef<HTMLElement>(null);
  const timeline = useRef<HTMLDivElement>(null);
  const progress = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (
      !root.current ||
      !timeline.current ||
      !progress.current ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return;
    }

    const ctx = gsap.context(() => {
      gsap.fromTo(
        progress.current,
        {
          scaleY: 0,
        },
        {
          scaleY: 1,
          ease: "none",
          scrollTrigger: {
            trigger: timeline.current,
            start: "top 75%",
            end: "bottom 25%",
            scrub: 0.5,
          },
        },
      );
    }, root);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={root}
      className="section-space border-t border-[var(--line)]"
    >
      <Container>
        <div className="grid gap-14 lg:grid-cols-[1fr_0.7fr] lg:gap-20">
          <div>
            <FadeIn>
              <SectionHeading
                eyebrow="Journey"
                title="Learning by shipping increasingly complex systems."
              />
            </FadeIn>

            <div
              ref={timeline}
              className="relative mt-10 border-t border-[var(--line)]"
            >
              <div
                ref={progress}
                className="pointer-events-none absolute bottom-0 left-[3px] top-0 w-px origin-top bg-[var(--accent)]"
                aria-hidden="true"
              />

              {experience.map((item, index) => (
                <FadeIn key={item.title} delay={index * 0.08}>
                  <div className="relative grid gap-4 border-b border-[var(--line)] py-7 pl-7 sm:grid-cols-[150px_1fr] sm:pl-7">
                    <span
                      className="absolute left-0 top-8 h-2 w-2 rounded-full border border-[var(--background)] bg-[var(--accent)] shadow-[0_0_12px_var(--accent-soft)]"
                      aria-hidden="true"
                    />

                    <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[var(--body-copy)]">
                      {item.period}
                    </div>

                    <div>
                      <h3 className="text-xl font-semibold tracking-[-0.03em] text-[var(--foreground)]">
                        {item.title}
                      </h3>

                      <div className="mt-1 text-sm text-[var(--accent)]">
                        {item.organization}
                      </div>

                      <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--body-copy)]">
                        {item.description}
                      </p>
                    </div>
                  </div>
                </FadeIn>
              ))}
            </div>
          </div>

          <FadeIn className="lg:pt-24">
            <aside className="rounded-[32px] border border-[var(--line)] bg-[var(--panel)] p-7 sm:p-8">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--accent)]">
                Currently exploring
              </div>

              <div className="mt-8 space-y-5">
                {currentlyExploring.map((item, index) => (
                  <div
                    key={item}
                    className="flex items-center gap-4 border-b border-[var(--line)] pb-5 last:border-b-0 last:pb-0"
                  >
                    <span className="font-mono text-[10px] text-[var(--body-copy)]">
                      0{index + 1}
                    </span>

                    <span className="text-base text-[var(--foreground)]">
                      {item}
                    </span>
                  </div>
                ))}
              </div>
            </aside>
          </FadeIn>
        </div>
      </Container>
    </section>
  );
}