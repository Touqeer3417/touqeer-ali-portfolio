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
      <Container>
        <FadeIn>
          <SectionHeading
            eyebrow="Services"
            title="From AI prototypes to client-ready digital products."
            description="Services are deliberately focused around the areas where AI engineering and modern web development create measurable business value."
          />
        </FadeIn>

        <div className="mt-12 border-t border-[var(--line)] lg:mt-16">
          {services.map((service, index) => (
            <FadeIn
              key={service.number}
              delay={Math.min(index * 0.04, 0.15)}
            >
              <article className="service-row group grid gap-4 border-b border-[var(--line)] py-7 transition sm:grid-cols-[80px_1fr_auto] sm:items-center sm:py-9">
                <span className="font-mono text-xs tracking-[0.2em] text-[var(--accent)]">
                  {service.number}
                </span>

                <div>
                  <h3 className="text-xl font-semibold tracking-[-0.03em] text-[var(--foreground)] sm:text-2xl">
                    {service.title}
                  </h3>

                  <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--body-copy)] sm:text-base">
                    {service.description}
                  </p>
                </div>

                <ArrowUpRight className="hidden h-5 w-5 text-[var(--muted)] transition duration-300 group-hover:-translate-y-1 group-hover:translate-x-1 group-hover:text-[var(--foreground)] sm:block" />
              </article>
            </FadeIn>
          ))}
        </div>
      </Container>
    </section>
  );
}