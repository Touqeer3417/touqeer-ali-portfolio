import { ArrowUpRight } from "lucide-react";

import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { FadeIn } from "@/components/animation/FadeIn";
import { services } from "@/data/skills";

export function Services() {
  return (
    <section
      id="services"
      className="section-space border-t border-[var(--line)]"
    >
      <div
        className="mx-auto w-full px-5 sm:px-8 lg:px-6 2xl:px-0"
        style={{ maxWidth: "1400px" }}
      >
        <FadeIn>
          <SectionHeading
            eyebrow="Services"
            title="From AI prototypes to client-ready digital products."
            description="Services are deliberately focused around the areas where AI engineering and modern web development create measurable business value."
          />
        </FadeIn>

        <div className="mt-[2.7rem] border-t border-[var(--line)] lg:mt-[3.6rem]">
          {services.map((service, index) => (
            <FadeIn
              key={service.number}
              delay={Math.min(index * 0.04, 0.15)}
            >
              <article className="service-row group grid gap-[0.9rem] border-b border-[var(--line)] py-[1.575rem] transition sm:grid-cols-[72px_1fr_auto] sm:items-center sm:py-[2.025rem]">
                <span className="font-mono text-xs tracking-[0.2em] text-[var(--accent)]">
                  {service.number}
                </span>

                <div>
                  <h3 className="text-[1.125rem] font-semibold tracking-[-0.03em] text-[var(--foreground)] sm:text-[1.35rem]">
                    {service.title}
                  </h3>

                  <p className="mt-[0.45rem] max-w-2xl text-[0.8rem] leading-[1.55] text-[var(--body-copy)] sm:text-[0.9rem]">
                    {service.description}
                  </p>
                </div>

                <ArrowUpRight className="hidden h-[1.125rem] w-[1.125rem] text-[var(--muted)] transition duration-300 group-hover:-translate-y-1 group-hover:translate-x-1 group-hover:text-[var(--foreground)] sm:block" />
              </article>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}