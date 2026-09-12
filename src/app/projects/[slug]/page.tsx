import type { Metadata } from "next";

import Image from "next/image";
import Link from "next/link";

import { notFound } from "next/navigation";

import {
  ArrowLeft,
  ArrowUpRight,
} from "lucide-react";

import { GitHubIcon } from "@/components/icons/BrandIcons";

import { Container } from "@/components/ui/Container";
import { Badge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/ButtonLink";

import {
  projects,
  getProject,
} from "@/data/projects";

export function generateStaticParams() {
  return projects.map((project) => ({
    slug: project.slug,
  }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{
    slug: string;
  }>;
}): Promise<Metadata> {
  const { slug } = await params;

  const project = getProject(slug);

  if (!project) {
    return {};
  }

  return {
    title: project.title,
    description: project.summary,

    openGraph: {
      title: project.title,
      description: project.summary,

      images: [
        {
          url: project.image,
        },
      ],
    },
  };
}

export default async function ProjectPage({
  params,
}: {
  params: Promise<{
    slug: string;
  }>;
}) {
  const { slug } = await params;

  const project = getProject(slug);

  if (!project) {
    notFound();
  }

  return (
    <article className="pb-20 pt-32 sm:pt-36">
      <Container>

        {/* Back Button */}
        <Link
          href="/#work"
          className="mb-10 inline-flex items-center gap-2 text-sm text-(--muted) transition hover:text-(--foreground)"
        >
          <ArrowLeft className="h-4 w-4" />

          Back to selected work
        </Link>

        {/* Hero */}
        <div className="grid gap-10 lg:grid-cols-[1fr_0.65fr] lg:items-end">

          {/* Left Side */}
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-(--accent)">
              {project.index} · {project.eyebrow} · {project.year}
            </div>

            <h1 className="mt-5 max-w-5xl text-5xl font-semibold leading-[0.95] tracking-[-0.055em] text-(--foreground) sm:text-7xl lg:text-8xl">
              {project.title}
            </h1>
          </div>

          {/* Right Side */}
          <div>
            <p className="text-base leading-7 text-(--muted) sm:text-lg">
              {project.description}
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              {project.links.map((link) => (
                <ButtonLink
                  key={link.href}
                  href={link.href}
                  external
                  variant={
                    link.type === "github"
                      ? "ghost"
                      : "primary"
                  }
                >
                  {link.type === "github" ? (
                    <GitHubIcon className="h-4 w-4" />
                  ) : null}

                  {link.label}
                </ButtonLink>
              ))}
            </div>
          </div>
        </div>

        {/* Main Project Image */}
        <div className="relative mt-12 aspect-16/8.5 overflow-hidden rounded-4xl border border-(--line) bg-(--panel) sm:mt-16">
          <Image
            src={project.image}
            alt={`${project.title} case study visual`}
            fill
            priority
            className="object-cover"
            sizes="100vw"
          />
        </div>

        {/* Tech Stack */}
        <div className="mt-10 flex flex-wrap gap-2 sm:mt-12">
          {project.stack.map((tech) => (
            <Badge key={tech}>
              {tech}
            </Badge>
          ))}
        </div>

        {/* Problem / Solution / Outcome */}
        <section className="mt-20 grid gap-5 lg:grid-cols-3">
          {[
            ["Problem", project.problem],
            ["Solution", project.solution],
            ["Outcome", project.outcome],
          ].map(([title, text]) => (
            <div
              key={title}
              className="rounded-[28px] border border-(--line) bg-(--panel) p-7"
            >
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-(--accent)">
                {title}
              </div>

              <p className="mt-5 text-sm leading-7 text-(--muted) sm:text-base">
                {text}
              </p>
            </div>
          ))}
        </section>

        {/* Architecture */}
        <section className="mt-20 grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">

          {/* Left */}
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-(--accent)">
              Architecture
            </div>

            <h2 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-(--foreground) sm:text-5xl">
              How the system flows.
            </h2>
          </div>

          {/* Right */}
          <div className="rounded-4xl border border-(--line) bg-(--panel) p-6 sm:p-8">

            <div className="space-y-3">
              {project.architecture.map(
                (step, index) => (
                  <div
                    key={step}
                    className="flex items-center gap-4 rounded-2xl border border-(--line) bg-(--surface) p-4"
                  >
                    {/* Number */}
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-(--foreground) font-mono text-[10px] text-(--background)">
                      {String(index + 1).padStart(
                        2,
                        "0"
                      )}
                    </span>

                    {/* Step */}
                    <span className="text-sm text-(--foreground) sm:text-base">
                      {step}
                    </span>

                    {/* Arrow */}
                    {index !==
                    project.architecture.length - 1 ? (
                      <ArrowUpRight className="ml-auto h-4 w-4 rotate-45 text-(--muted)" />
                    ) : null}
                  </div>
                )
              )}
            </div>

          </div>
        </section>

        {/* Engineering */}
        <section className="mt-20 grid gap-8 lg:grid-cols-2">

          {/* Highlights */}
          <div className="rounded-4xl border border-(--line) bg-(--panel) p-7 sm:p-8">

            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-(--accent)">
              Engineering highlights
            </div>

            <div className="mt-7 space-y-5">
              {project.highlights.map(
                (item, index) => (
                  <div
                    key={item}
                    className="flex gap-4 border-b border-(--line) pb-5 last:border-0 last:pb-0"
                  >
                    <span className="font-mono text-[10px] text-(--muted)">
                      {String(index + 1).padStart(
                        2,
                        "0"
                      )}
                    </span>

                    <p className="text-sm leading-6 text-(--foreground) sm:text-base">
                      {item}
                    </p>
                  </div>
                )
              )}
            </div>
          </div>

          {/* Metrics */}
          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
            {project.metrics.map((metric) => (
              <div
                key={metric.label}
                className="rounded-[28px] border border-(--line) bg-(--panel) p-6"
              >
                <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-(--muted)">
                  {metric.label}
                </div>

                <div className="mt-3 text-2xl font-semibold tracking-[-0.03em] text-(--foreground)">
                  {metric.value}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <section className="mt-20 rounded-[36px] border border-(--line) bg-(--panel) p-8 sm:p-12">
          <div className="max-w-3xl">

            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-(--accent)">
              Next project
            </div>

            <h2 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-(--foreground) sm:text-5xl">
              Need a system like this for your business?
            </h2>

            <p className="mt-5 text-base leading-7 text-(--muted)">
              I&apos;m available for RAG, AI agents,
              website chatbot integration and full-stack
              AI work.
            </p>

            <div className="mt-7">
              <ButtonLink href="/#contact">
                Start a conversation
              </ButtonLink>
            </div>

          </div>
        </section>

      </Container>
    </article>
  );
}