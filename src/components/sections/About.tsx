import { BrainCircuit, Code2, Layers3 } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { FadeIn } from "@/components/animation/FadeIn";

const cards = [
  {
    icon: BrainCircuit,
    title: "AI that does useful work",
    text: "I focus on grounded retrieval, tool use and workflow automation — not chat demos that stop at a nice response.",
  },
  {
    icon: Layers3,
    title: "Systems over snippets",
    text: "I like connecting retrieval, APIs, databases, auth, orchestration and frontend UX into complete products.",
  },
  {
    icon: Code2,
    title: "Engineering + presentation",
    text: "Strong architecture matters, but so does the experience around it: clear UX, responsive design and production-minded code.",
  },
];

export function About() {
  return (
    <section id="about" className="section-space border-t border-[var(--line)]">
      <Container>
        <div className="grid gap-11 lg:grid-cols-[0.8fr_1.2fr] lg:gap-[4.5rem]>
          <FadeIn>
            <SectionHeading
              eyebrow="About"
              title="AI engineering with a product mindset."
              description="I’m building toward a career in AI engineering, with a practical focus on RAG, agentic systems and full-stack products that solve real operational problems."
              descriptionClassName="font-medium text-[var(--body-copy)]"
            />
          </FadeIn>

          <div className="grid gap-[0.9rem] sm:grid-cols-3 lg:pt-[3.6rem]">
            {cards.map((card, index) => (
              <FadeIn key={card.title} delay={index * 0.08}>
                <article className="h-full rounded-[1.575rem] border border-[var(--line)] bg-[var(--panel)] p-[1.35rem] transition hover:border-[var(--line-strong)] hover:bg-[var(--panel-strong)]">
                  <div className="mb-9 grid h-10 w-10 place-items-center rounded-2xl border border-[var(--line)] bg-[var(--surface)] text-[var(--accent)]">
                    <card.icon className="h-[1.125rem] w-[1.125rem]" />
                  </div>
                  <h3 className="text-[1.0125rem] font-semibold tracking-[-0.02em] text-[var(--foreground)]">{card.title}</h3>
                  <p className="mt-[0.675rem] text-[0.8rem] leading-[1.55] text-[var(--body-copy)]">{card.text}</p>
                </article>
              </FadeIn>
            ))}
          </div>
        </div>
      </Container>
    </section>
  );
}
