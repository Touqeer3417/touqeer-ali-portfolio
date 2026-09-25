"use client";

import dynamic from "next/dynamic";
import { useLayoutEffect, useRef } from "react";
import { ArrowDown } from "lucide-react";

import { GitHubIcon } from "@/components/icons/BrandIcons";
import { Container } from "@/components/ui/Container";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { MagneticButton } from "@/components/animation/MagneticButton";
import { TextReveal } from "@/components/animation/TextReveal";
import { gsap } from "@/lib/gsap";
import { siteConfig } from "@/lib/site";

const HeroThreeScene = dynamic(
  () =>
    import("@/components/three/HeroThreeScene").then(
      (module) => module.HeroThreeScene,
    ),
  {
    ssr: false,
    loading: () => (
      <div
        className="absolute inset-0 grid place-items-center"
        aria-hidden="true"
      >
        <div className="h-36 w-36 rounded-full border border-(--line-strong) bg-(--accent-soft) shadow-[0_0_90px_var(--accent-soft)]" />
      </div>
    ),
  },
);

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

    const mm = gsap.matchMedia();

    const ctx = gsap.context(() => {
      // -----------------------------------------
      // HERO INTRO
      // -----------------------------------------
      const intro = gsap.timeline({
        defaults: {
          ease: "power3.out",
        },
      });

      // Three.js visual entrance
      intro.fromTo(
        "[data-hero-visual]",
        {
          opacity: 0,
          scale: 0.96,
          rotateY: -4,
        },
        {
          opacity: 1,
          scale: 1,
          rotateY: 0,
          duration: 1.05,
        },
        0.05,
      );

      // Text / metadata / CTA entrance
      intro.fromTo(
        "[data-hero-fade]",
        {
          opacity: 0,
          y: 18,
        },
        {
          opacity: 1,
          y: 0,
          duration: 0.76,
          stagger: 0.07,
        },
        0.38,
      );

      // -----------------------------------------
      // DESKTOP PARALLAX
      // -----------------------------------------
      mm.add(
        "(min-width: 1024px) and (prefers-reduced-motion: no-preference)",
        () => {
          if (!visual.current || !root.current) {
            return;
          }

          gsap.to(visual.current, {
            yPercent: 9,
            rotate: 1.1,
            scale: 0.992,
            ease: "none",
            scrollTrigger: {
              trigger: root.current,
              start: "top top",
              end: "bottom top",
              scrub: 0.9,
            },
          });
        },
      );

      // -----------------------------------------
      // TABLET + MOBILE PARALLAX
      // -----------------------------------------
      mm.add(
        "(max-width: 1023px) and (prefers-reduced-motion: no-preference)",
        () => {
          if (!visual.current || !root.current) {
            return;
          }

          gsap.to(visual.current, {
            yPercent: 4,
            rotate: 0.4,
            ease: "none",
            scrollTrigger: {
              trigger: root.current,
              start: "top top",
              end: "bottom top",
              scrub: 0.7,
            },
          });
        },
      );
    }, root);

    return () => {
      mm.revert();
      ctx.revert();
    };
  }, []);

  return (
    <section
      ref={root}
      id="top"
      className="relative min-h-screen overflow-hidden pt-28 sm:pt-32"
    >
      {/* -----------------------------------------
          BACKGROUND
      ------------------------------------------ */}
      <div className="hero-grid absolute inset-0 -z-20" />
      <div className="hero-vignette absolute inset-0 -z-10" />

      {/* Static atmospheric halo */}
      <div
        className="pointer-events-none absolute right-[-12rem] top-[8%] -z-10 h-[34rem] w-[34rem] rounded-full bg-(--accent-soft) opacity-60 blur-[120px]"
        aria-hidden="true"
      />

      <Container className="relative flex min-h-[calc(100vh-7rem)] flex-col justify-between pb-8 sm:pb-12">
        <div className="grid flex-1 items-center gap-8 py-10 lg:grid-cols-[1.12fr_0.88fr] lg:gap-4 lg:py-16">
          {/* =====================================
              LEFT CONTENT
          ====================================== */}
          <div className="relative z-20 max-w-5xl">
            {/* Availability Badge */}
            <div
              data-hero-fade
              className="mb-7 inline-flex items-center gap-2 rounded-full border border-(--line) bg-(--panel) px-3.5 py-2 font-mono text-[10px] uppercase tracking-[0.16em] text-(--body-copy) backdrop-blur"
            >
              <span className="relative flex h-2 w-2">
                <span
                  className="relative inline-flex h-2 w-2 rounded-full bg-(--accent)"
                  aria-hidden="true"
                />
              </span>

              {siteConfig.availability}
            </div>

            {/* Name + Role */}
            <p
              data-hero-fade
              className="mb-4 font-mono text-xs uppercase tracking-[0.22em] text-(--body-copy)"
            >
              {siteConfig.name} · {siteConfig.role}
            </p>

            {/* Main Heading */}
            <h1 className="max-w-245 text-[clamp(3.25rem,8.5vw,8.6rem)] font-semibold leading-[0.88] tracking-[-0.065em] text-(--foreground)">
              <TextReveal text="BUILDING" delay={0.1} />

              <br />

              <span className="text-(--muted-strong)">
                <TextReveal text="INTELLIGENT" delay={0.2} />
              </span>

              <br />

              <TextReveal text="SYSTEMS." delay={0.3} />
            </h1>

            {/* Description + Buttons */}
            <div className="mt-8 grid max-w-3xl gap-6 sm:grid-cols-[1fr_auto] sm:items-end">
              <p
                data-hero-fade
                className="max-w-2xl text-base font-medium leading-7 text-(--body-copy) sm:text-lg"
              >
                I build AI agents, RAG systems, business automation and
                polished full-stack products that move from prototype to
                usable software.
              </p>

              <div data-hero-fade className="flex flex-wrap gap-3">
                <MagneticButton>
                  <ButtonLink href="#work">View my work</ButtonLink>
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
                  <ButtonLink href="#contact" variant="ghost">
                    Hire me
                  </ButtonLink>
                </MagneticButton>
              </div>
            </div>

            {/* Technologies */}
            <div
              data-hero-fade
              className="mt-8 flex flex-wrap gap-x-5 gap-y-2 font-mono text-[10px] uppercase tracking-[0.16em] text-(--body-copy)"
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

          {/* =====================================
              RIGHT THREE.JS VISUAL
          ====================================== */}
          <div
            ref={visual}
            data-hero-visual
            className="relative mx-auto min-h-[320px] w-full max-w-155 sm:min-h-[420px] lg:aspect-square lg:min-h-0"
            style={{ perspective: "1200px" }}
          >
            {/* WebGL frame */}
            <div className="absolute inset-[2%] overflow-hidden rounded-[2.25rem] border border-(--line) bg-(--panel) shadow-[0_30px_120px_rgba(0,0,0,0.16)] backdrop-blur-sm">
              {/* Accent glow */}
              <div
                className="pointer-events-none absolute inset-0 z-10 bg-[radial-gradient(circle_at_50%_45%,var(--accent-soft),transparent_38%)]"
                aria-hidden="true"
              />

              <HeroThreeScene />

              {/* Scanline treatment */}
              <div
                className="pointer-events-none absolute inset-0 z-10 opacity-25 [background-image:linear-gradient(to_bottom,transparent_49%,var(--line)_50%,transparent_51%)] [background-size:100%_9px]"
                aria-hidden="true"
              />
            </div>

            {/* Structural rings */}
            <div
              className="pointer-events-none absolute inset-[9%] rounded-full border border-(--line)"
              aria-hidden="true"
            />

            <div
              className="pointer-events-none absolute inset-[17%] rounded-full border border-dashed border-(--line-strong) opacity-60"
              aria-hidden="true"
            />

            {/* HUD */}
            <div className="pointer-events-none absolute inset-x-[6%] top-[6%] z-20 flex items-center justify-between gap-4 font-mono text-[9px] uppercase tracking-[0.18em] text-(--body-copy) sm:text-[10px]">
              <span className="rounded-full border border-(--line) bg-(--nav) px-3 py-1.5 backdrop-blur">
                Live system graph
              </span>

              <span className="hidden sm:inline">
                RAG · Agents · Tools · API
              </span>
            </div>

            {/* Bottom HUD */}
            <div className="pointer-events-none absolute bottom-[7%] left-1/2 z-20 -translate-x-1/2 whitespace-nowrap rounded-full border border-(--line) bg-(--nav) px-4 py-2 font-mono text-[9px] uppercase tracking-[0.18em] text-(--body-copy) backdrop-blur sm:text-[10px]">
              Query → Retrieve → Reason → Act
            </div>
          </div>
        </div>

        {/* =====================================
            SCROLL INDICATOR
        ====================================== */}
        <div
          data-hero-fade
          className="flex items-center justify-between border-t border-(--line) pt-5 text-xs text-(--body-copy)"
        >
          <span className="font-mono uppercase tracking-[0.18em]">
            Scroll to explore
          </span>

          <ArrowDown
            className="h-4 w-4 transition-transform duration-300 hover:translate-y-1"
            aria-hidden="true"
          />
        </div>
      </Container>
    </section>
  );
}