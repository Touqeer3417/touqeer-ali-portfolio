"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { motion } from "motion/react";
import type { MouseEvent } from "react";
import type { Project } from "@/types/project";
import { Badge } from "@/components/ui/Badge";

export function ProjectCard({ project }: { project: Project }) {
  const handleMouseMove = (event: MouseEvent<HTMLElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    event.currentTarget.style.setProperty("--mouse-x", `${event.clientX - rect.left}px`);
    event.currentTarget.style.setProperty("--mouse-y", `${event.clientY - rect.top}px`);
  };

  return (
    <motion.article
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-8%" }}
      transition={{ duration: 0.72, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -6 }}
      onMouseMove={handleMouseMove}
      className="project-card group relative overflow-hidden rounded-[32px] border border-[var(--line)] bg-[var(--panel)]"
    >
      <div className="project-card-glow" aria-hidden />
      <Link href={`/projects/${project.slug}`} className="relative z-10 block">
        <div className="relative aspect-[16/10] overflow-hidden border-b border-[var(--line)] bg-[var(--surface)]">
          <Image
            src={project.image}
            alt={`${project.title} project preview`}
            fill
            sizes="(max-width: 768px) 100vw, 50vw"
            className="object-cover transition duration-700 ease-out group-hover:scale-[1.035]"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent" />
          <span className="absolute left-5 top-5 rounded-full border border-white/15 bg-black/30 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.18em] text-white/80 backdrop-blur-md">
            {project.eyebrow}
          </span>
        </div>

        <div className="p-6 sm:p-8">
          <div className="mb-5 flex items-center justify-between gap-4">
            <span className="font-mono text-xs tracking-[0.2em] text-[var(--accent)]">{project.index}</span>
            <ArrowUpRight className="h-5 w-5 text-[var(--muted)] transition duration-300 group-hover:-translate-y-1 group-hover:translate-x-1 group-hover:rotate-6 group-hover:text-[var(--foreground)]" />
          </div>

          <h3 className="text-3xl font-semibold tracking-[-0.04em] text-[var(--foreground)] sm:text-4xl">
            {project.title}
          </h3>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-[var(--muted)] sm:text-base sm:leading-7">
            {project.summary}
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            {project.stack.slice(0, 5).map((tech) => (
              <Badge key={tech}>{tech}</Badge>
            ))}
          </div>
        </div>
      </Link>
    </motion.article>
  );
}
