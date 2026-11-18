import { Mail } from "lucide-react";

import {
  GitHubIcon,
  LinkedInIcon,
} from "@/components/icons/BrandIcons";

import { Container } from "@/components/ui/Container";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { FadeIn } from "@/components/animation/FadeIn";

import { siteConfig } from "@/lib/site";

export function Contact() {
  return (
    <section
      id="contact"
      className="section-space section-zoom-90 border-t border-(--line)"
    >
      <Container>
        <FadeIn>
          <div className="contact-panel relative overflow-hidden rounded-[2.025rem] border border-(--line) px-[1.35rem] py-[2.7rem] sm:px-[2.25rem] sm:py-[3.6rem] lg:px-[3.6rem] lg:py-[4.5rem]">

            {/* Background Glow */}
            <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-(--accent) opacity-[0.08] blur-3xl" />

            <div className="relative z-10 max-w-4xl">

              {/* Small Label */}
              <div className="mb-[1.125rem] font-mono text-[9px] uppercase tracking-[0.2em] text-(--accent)">
                Have a project in mind?
              </div>

              {/* Heading */}
              <h2 className="text-balance text-[2.025rem] font-semibold leading-[0.98] tracking-tighter text-(--foreground) sm:text-[3.375rem] lg:text-[4.05rem]">
                Let&apos;s build something useful, fast and genuinely
                intelligent.
              </h2>

              {/* Description */}
              <p className="mt-[1.575rem] max-w-2xl font-medium text-[0.9rem] leading-[1.6] text-(--body-copy) sm:text-base">
                Available for AI/RAG freelance projects, AI chatbot
                integrations, full-stack builds and opportunities.
              </p>

              {/* Buttons */}
              <div className="mt-[2.025rem] flex flex-wrap gap-[0.675rem]">

                {/* Email */}
                <ButtonLink
                  href={`mailto:${siteConfig.email}`}
                >
                  <Mail className="h-4 w-4" />

                  Email me
                </ButtonLink>

                {/* LinkedIn */}
                <ButtonLink
                  href={siteConfig.linkedin}
                  external
                  variant="ghost"
                >
                  <LinkedInIcon className="h-4 w-4" />

                  LinkedIn
                </ButtonLink>

                {/* GitHub */}
                <ButtonLink
                  href={siteConfig.github}
                  external
                  variant="ghost"
                >
                  <GitHubIcon className="h-4 w-4" />

                  GitHub
                </ButtonLink>
              </div>

            

            </div>
          </div>
        </FadeIn>
      </Container>
    </section>
  );
}