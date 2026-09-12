import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { FadeIn } from "@/components/animation/FadeIn";
import { currentlyExploring, experience } from "@/data/experience";

export function Experience() {
  return (
    <section className="section-space border-t border-[var(--line)]">
      <Container>
        <div className="grid gap-14 lg:grid-cols-[1fr_0.7fr] lg:gap-20">
          <div>
            <SectionHeading eyebrow="Journey" title="Learning by shipping increasingly complex systems." />
            <div className="mt-10 border-t border-[var(--line)]">
              {experience.map((item, index) => (
                <FadeIn key={item.title} delay={index * 0.08}>
                  <div className="grid gap-4 border-b border-[var(--line)] py-7 sm:grid-cols-[150px_1fr]">
                    <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[var(--muted)]">{item.period}</div>
                    <div>
                      <h3 className="text-xl font-semibold tracking-[-0.03em] text-[var(--foreground)]">{item.title}</h3>
                      <div className="mt-1 text-sm text-[var(--accent)]">{item.organization}</div>
                      <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">{item.description}</p>
                    </div>
                  </div>
                </FadeIn>
              ))}
            </div>
          </div>

          <FadeIn className="lg:pt-24">
            <aside className="rounded-[32px] border border-[var(--line)] bg-[var(--panel)] p-7 sm:p-8">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--accent)]">Currently exploring</div>
              <div className="mt-8 space-y-5">
                {currentlyExploring.map((item, index) => (
                  <div key={item} className="flex items-center gap-4 border-b border-[var(--line)] pb-5 last:border-b-0 last:pb-0">
                    <span className="font-mono text-[10px] text-[var(--muted)]">0{index + 1}</span>
                    <span className="text-base text-[var(--foreground)]">{item}</span>
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
