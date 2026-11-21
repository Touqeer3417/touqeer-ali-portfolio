import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { FadeIn } from "@/components/animation/FadeIn";
import { skillGroups } from "@/data/skills";

export function Skills() {
  return (
    <section
      id="stack"
      className="section-space border-t border-[var(--line)]"
    >
      <Container>
        <div className="grid gap-11 lg:grid-cols-[0.75fr_1.25fr] lg:gap-[4.5rem]">
          <FadeIn>
            <SectionHeading
              eyebrow="AI engineering stack"
              title="A focused stack for retrieval, agents and product delivery."
              description="I group technologies by the problems they solve instead of presenting a wall of logos."
            />
          </FadeIn>

          <div className="grid gap-[0.9rem] sm:grid-cols-2">
            {skillGroups.map((group, index) => (
              <FadeIn key={group.title} delay={index * 0.06}>
                <div className="h-full rounded-[1.575rem] border border-[var(--line)] bg-[var(--panel)] p-[1.35rem] sm:p-[1.575rem]">
                  <div className="mb-[1.35rem] font-mono text-[0.6875rem] uppercase tracking-[0.18em] text-[var(--accent)]">
                    {group.title}
                  </div>

                  <div className="flex flex-wrap gap-[0.5625rem]">
                    {group.items.map((item) => (
                      <span
                        key={item}
                        className="rounded-full border border-[var(--line)] bg-[var(--surface)] px-[0.7875rem] py-[0.45rem] text-[0.8rem] text-[var(--foreground)]"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </Container>
    </section>
  );
}