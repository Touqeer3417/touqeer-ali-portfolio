"use client";

import { useLayoutEffect, useRef } from "react";
import { ArrowDown, Sparkles } from "lucide-react";

import { GitHubIcon } from "@/components/icons/BrandIcons";
import { Container } from "@/components/ui/Container";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { MagneticButton } from "@/components/animation/MagneticButton";
import { TextReveal } from "@/components/animation/TextReveal";

import { gsap } from "@/lib/gsap";
import { siteConfig } from "@/lib/site";

const nodes = [
  { x: 46, y: 52, label: "LLM" },
  { x: 23, y: 24, label: "RAG" },
  { x: 77, y: 24, label: "TOOLS" },
  { x: 81, y: 72, label: "API" },
  { x: 19, y: 75, label: "DATA" },
];

export function Hero() {
  const root = useRef<HTMLElement>(null);
  const visual = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (
      !root.current ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return;
    }

    const ctx = gsap.context(() => {
      gsap.fromTo(
        "[data-hero-fade]",
        {
          opacity: 0,
          y: 18,
        },
        {
          opacity: 1,
          y: 0,
          duration: 0.9,
          delay: 0.75,
          stagger: 0.08,
          ease: "power3.out",
        }
      );

      if (visual.current) {
        gsap.to(visual.current, {
          yPercent: 12,
          rotate: 1.8,
          ease: "none",
          scrollTrigger: {
            trigger: root.current,
            start: "top top",
            end: "bottom top",
            scrub: 1,
          },
        });
      }

      gsap.to("[data-orbit]", {
        rotate: 360,
        transformOrigin: "50% 50%",
        duration: 22,
        ease: "none",
        repeat: -1,
      });
    }, root);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={root}
      id="top"
      className="relative min-h-screen overflow-hidden pt-28 sm:pt-32"
    >
      {/* Background Grid */}
      <div className="hero-grid absolute inset-0 -z-20" />

      {/* Background Vignette */}
      <div className="hero-vignette absolute inset-0 -z-10" />

      <Container className="relative flex min-h-[calc(100vh-7rem)] flex-col justify-between pb-8 sm:pb-12">
        <div className="grid flex-1 items-center gap-12 py-10 lg:grid-cols-[1.15fr_0.85fr] lg:py-16">

          {/* =========================
              LEFT CONTENT
          ========================== */}
          <div className="max-w-5xl">

            {/* Availability Badge */}
            <div
              data-hero-fade
              className="mb-7 inline-flex items-center gap-2 rounded-full border border-(--line) bg-(--panel) px-3.5 py-2 font-mono text-[10px] uppercase tracking-[0.16em] text-(--muted) backdrop-blur"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-(--accent) opacity-50" />

                <span className="relative inline-flex h-2 w-2 rounded-full bg-(--accent)" />
              </span>

              {siteConfig.availability}
            </div>

            {/* Name */}
            <p
              data-hero-fade
              className="mb-4 font-mono text-xs uppercase tracking-[0.22em] text-(--muted)"
            >
              {siteConfig.name} · {siteConfig.role}
            </p>

            {/* Main Heading */}
            <h1 className="max-w-245 text-[clamp(3.25rem,8.5vw,8.6rem)] font-semibold leading-[0.88] tracking-[-0.065em] text-(--foreground)">
              <TextReveal
                text="BUILDING"
                delay={0.1}
              />

              <br />

              <span className="text-(--muted-strong)">
                <TextReveal
                  text="INTELLIGENT"
                  delay={0.2}
                />
              </span>

              <br />

              <TextReveal
                text="SYSTEMS."
                delay={0.3}
              />
            </h1>

            {/* Description + Buttons */}
            <div className="mt-8 grid max-w-3xl gap-6 sm:grid-cols-[1fr_auto] sm:items-end">

              <p
                data-hero-fade
                className="max-w-2xl text-base leading-7 text-(--muted) sm:text-lg"
              >
                I build AI agents, RAG systems, business automation and
                polished full-stack products that move from prototype to
                usable software.
              </p>

              <div
                data-hero-fade
                className="flex flex-wrap gap-3"
              >
                <MagneticButton>
                  <ButtonLink href="#work">
                    View my work
                  </ButtonLink>
                </MagneticButton>

                <MagneticButton>
                  <ButtonLink
                    href={siteConfig.github}
                    external
                    variant="ghost"
                  >
                    <GitHubIcon className="h-4 w-4" />
                    GitHub
                  </ButtonLink>
                </MagneticButton>

                <MagneticButton>
                  <ButtonLink
                    href="#contact"
                    variant="ghost"
                  >
                    Hire me
                  </ButtonLink>
                </MagneticButton>
              </div>
            </div>

            {/* Technologies */}
            <div
              data-hero-fade
              className="mt-8 flex flex-wrap gap-x-5 gap-y-2 font-mono text-[10px] uppercase tracking-[0.16em] text-(--muted)"
            >
              <span>RAG</span>
              <span>•</span>
              <span>AGENTIC AI</span>
              <span>•</span>
              <span>LANGGRAPH</span>
              <span>•</span>
              <span>FASTAPI</span>
              <span>•</span>
              <span>NEXT.JS</span>
            </div>
          </div>

          {/* =========================
              RIGHT AI VISUAL
          ========================== */}
          <div
            ref={visual}
            className="relative mx-auto hidden aspect-square w-full max-w-140 lg:block"
          >
            {/* Outer Background */}
            <div className="absolute inset-[7%] rounded-full border border-(--line) bg-[radial-gradient(circle_at_50%_50%,rgba(117,245,181,0.07),transparent_62%)]" />

            {/* Rotating Orbit */}
            <div
              data-orbit
              className="absolute inset-[14%] rounded-full border border-dashed border-(--line-strong) opacity-70"
            />

            {/* Inner Circle */}
            <div className="absolute inset-[25%] rounded-full border border-(--line) bg-(--panel) shadow-[0_0_100px_rgba(117,245,181,0.08)] backdrop-blur-xl" />

            {/* Connecting Lines */}
            <svg
              className="absolute inset-0 h-full w-full"
              viewBox="0 0 100 100"
              aria-hidden="true"
            >
              {nodes.slice(1).map((node, index) => (
                <line
                  key={index}
                  x1="46"
                  y1="52"
                  x2={node.x}
                  y2={node.y}
                  stroke="currentColor"
                  strokeWidth="0.22"
                  className="text-(--line-strong)"
                />
              ))}
            </svg>

            {/* AI Nodes */}
            {nodes.map((node, index) => (
              <div
                key={node.label}
                className="absolute -translate-x-1/2 -translate-y-1/2"
                style={{
                  left: `${node.x}%`,
                  top: `${node.y}%`,
                }}
              >
                <div
                  className={
                    index === 0
                      ? "hero-node hero-node-main"
                      : "hero-node"
                  }
                >
                  {index === 0 ? (
                    <Sparkles className="mb-2 h-5 w-5" />
                  ) : null}

                  <span>{node.label}</span>
                </div>
              </div>
            ))}

            {/* Workflow Label */}
            <div className="absolute bottom-[7%] left-1/2 -translate-x-1/2 rounded-full border border-(--line) bg-(--nav) px-4 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-(--muted) backdrop-blur">
              Query → Retrieve → Reason → Act
            </div>
          </div>
        </div>

        {/* =========================
            SCROLL INDICATOR
        ========================== */}
        <div
          data-hero-fade
          className="flex items-center justify-between border-t border-(--line) pt-5 text-xs text-(--muted)"
        >
          <span className="font-mono uppercase tracking-[0.18em]">
            Scroll to explore
          </span>

          <ArrowDown className="h-4 w-4 animate-bounce" />
        </div>
      </Container>
    </section>
  );
}