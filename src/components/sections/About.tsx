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
        <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
          <FadeIn>
            <SectionHeading
              eyebrow="About"
              title="AI engineering with a product mindset."
              description="I’m building toward a career in AI engineering, with a practical focus on RAG, agentic systems and full-stack products that solve real operational problems."
            />
          </FadeIn>

          <div className="grid gap-4 sm:grid-cols-3 lg:pt-16">
            {cards.map((card, index) => (
              <FadeIn key={card.title} delay={index * 0.08}>
                <article className="h-full rounded-[28px] border border-[var(--line)] bg-[var(--panel)] p-6 transition hover:border-[var(--line-strong)] hover:bg-[var(--panel-strong)]">
                  <div className="mb-10 grid h-11 w-11 place-items-center rounded-2xl border border-[var(--line)] bg-[var(--surface)] text-[var(--accent)]">
                    <card.icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-semibold tracking-[-0.02em] text-[var(--foreground)]">{card.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{card.text}</p>
                </article>
              </FadeIn>
            ))}
          </div>
        </div>
      </Container>
    </section>
  );
}
