"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { useLayoutEffect, useRef } from "react";
import type { MouseEvent } from "react";

import { Badge } from "@/components/ui/Badge";
import type { Project } from "@/types/project";
import { gsap } from "@/lib/gsap";

export function ProjectCard({ project }: { project: Project }) {
  const root = useRef<HTMLElement>(null);
  const image = useRef<HTMLImageElement>(null);

  const handleMouseMove = (event: MouseEvent<HTMLElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();

    event.currentTarget.style.setProperty(
      "--mouse-x",
      `${event.clientX - rect.left}px`,
    );

    event.currentTarget.style.setProperty(
      "--mouse-y",
      `${event.clientY - rect.top}px`,
    );
  };

  useLayoutEffect(() => {
    if (!root.current) {
      return;
    }

    const mm = gsap.matchMedia();

    mm.add(
      "(min-width: 1024px) and (prefers-reduced-motion: no-preference)",
      () => {
        if (!root.current || !image.current) {
          return;
        }

        gsap.fromTo(
          root.current,
          {
            opacity: 0,
            y: 34,
          },
          {
            opacity: 1,
            y: 0,
            duration: 0.78,
            ease: "power3.out",
            clearProps: "transform,opacity",
            scrollTrigger: {
              trigger: root.current,
              start: "top 86%",
              once: true,
              toggleActions: "play none none none",
            },
          },
        );

        gsap.fromTo(
          image.current,
          {
            scale: 1.04,
          },
          {
            scale: 1,
            ease: "none",
            scrollTrigger: {
              trigger: root.current,
              start: "top 88%",
              end: "bottom 20%",
              scrub: 0.7,
            },
          },
        );
      },
    );

    mm.add(
      "(max-width: 1023px) and (prefers-reduced-motion: no-preference)",
      () => {
        if (!root.current) {
          return;
        }

        gsap.fromTo(
          root.current,
          {
            opacity: 0,
            y: 24,
          },
          {
            opacity: 1,
            y: 0,
            duration: 0.7,
            ease: "power3.out",
            clearProps: "transform,opacity",
            scrollTrigger: {
              trigger: root.current,
              start: "top 90%",
              once: true,
              toggleActions: "play none none none",
            },
          },
        );
      },
    );

    return () => mm.revert();
  }, []);

  return (
    <article
      ref={root}
      onMouseMove={handleMouseMove}
      className="project-card relative"
    >
      <div className="group relative overflow-hidden rounded-[1.8rem] border border-[var(--line)] bg-[var(--panel)] transition duration-500 ease-out hover:-translate-y-1 hover:border-[var(--line-strong)]">
        <div className="project-card-glow" aria-hidden />

        <Link
          href={`/projects/${project.slug}`}
          className="relative z-10 block"
        >
          <div className="relative aspect-[16/10] overflow-hidden border-b border-[var(--line)] bg-[var(--surface)]">
            <div className="absolute inset-0 transition-transform duration-700 ease-out group-hover:scale-[1.015]">
              <Image
                ref={image}
                src={project.image}
                alt={`${project.title} project preview`}
                fill
                sizes="(max-width: 768px) 100vw, 50vw"
                className="object-cover"
              />
            </div>

            <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent" />

            <span className="absolute left-[1.125rem] top-[1.125rem] rounded-full border border-white/15 bg-black/30 px-3 py-1.5 font-mono text-[12px] uppercase tracking-[0.18em] text-white/80 backdrop-blur-md">
              {project.eyebrow}
            </span>
          </div>

          <div className="p-[1.35rem] sm:p-[1.8rem]">
            <div className="mb-[1.125rem] flex items-center justify-between gap-4">
              <span className="font-mono text-xs tracking-[0.2em] text-[var(--accent)]">
                {project.index}
              </span>

              <ArrowUpRight className="h-[1.125rem] w-[1.125rem] text-[var(--muted)] transition duration-300 group-hover:-translate-y-1 group-hover:translate-x-1 group-hover:rotate-6 group-hover:text-[var(--foreground)]" />
            </div>

            <h3 className="text-[1.6875rem] font-semibold tracking-[-0.04em] text-[var(--foreground)] sm:text-[2.025rem]">
              {project.title}
            </h3>

            <p className="mt-[0.9rem] max-w-2xl text-[0.8rem] leading-[1.55] text-[var(--body-copy)] sm:text-[0.9rem] sm:leading-[1.6]">
              {project.summary}
            </p>

            <div className="mt-[1.35rem] flex flex-wrap gap-[0.45rem]">
              {project.stack.slice(0, 5).map((tech) => (
                <Badge key={tech}>{tech}</Badge>
              ))}
            </div>
          </div>
        </Link>
      </div>
    </article>
  );
}