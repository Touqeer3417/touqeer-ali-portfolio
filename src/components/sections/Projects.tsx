import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { ProjectShowcase } from "@/components/projects/ProjectShowcase";
import { projects } from "@/data/projects";

export function Projects() {
  return (
    <section id="work" className="section-space border-t border-[var(--line)]">
      <Container>
        <div className="mb-12 flex flex-col gap-8 lg:mb-16 lg:flex-row lg:items-end lg:justify-between">
          <SectionHeading
            eyebrow="Selected work"
            title="Projects built as case studies, not logo collections."
            description="Each project explains the problem, engineering decisions, architecture and outcome — because the proof is in how the system works."
          />
          <div className="max-w-sm font-mono text-[10px] uppercase leading-5 tracking-[0.16em] text-[var(--muted)]">
            03 featured builds · RAG · agents · automation · full-stack
          </div>
        </div>
        <ProjectShowcase projects={projects.filter((project) => project.featured)} />
      </Container>
    </section>
  );
}
