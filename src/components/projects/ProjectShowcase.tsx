import { ProjectCard } from "@/components/projects/ProjectCard";
import type { Project } from "@/types/project";

export function ProjectShowcase({ projects }: { projects: Project[] }) {
  return (
    <div className="grid gap-5 lg:grid-cols-2 lg:gap-6">
      {projects.map((project, index) => (
        <div key={project.slug} className={index === 0 ? "lg:col-span-2" : ""}>
          <ProjectCard project={project} />
        </div>
      ))}
    </div>
  );
}
