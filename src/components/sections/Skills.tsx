import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { FadeIn } from "@/components/animation/FadeIn";
import { skillGroups } from "@/data/skills";

export function Skills() {
  return (
    <section id="stack" className="section-space border-t border-[var(--line)]">
      <Container>
        <div className="grid gap-12 lg:grid-cols-[0.75fr_1.25fr] lg:gap-20">
          <SectionHeading
            eyebrow="AI engineering stack"
            title="A focused stack for retrieval, agents and product delivery."
            description="I group technologies by the problems they solve instead of presenting a wall of logos."
          />

          <div className="grid gap-4 sm:grid-cols-2">
            {skillGroups.map((group, index) => (
              <FadeIn key={group.title} delay={index * 0.06}>
                <div className="h-full rounded-[28px] border border-[var(--line)] bg-[var(--panel)] p-6 sm:p-7">
                  <div className="mb-6 font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--accent)]">{group.title}</div>
                  <div className="flex flex-wrap gap-2.5">
                    {group.items.map((item) => (
                      <span key={item} className="rounded-full border border-[var(--line)] bg-[var(--surface)] px-3.5 py-2 text-sm text-[var(--foreground)]">
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
