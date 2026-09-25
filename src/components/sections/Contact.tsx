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
      className="section-space border-t border-(--line)"
    >
      <Container>
        <FadeIn>
          <div className="contact-panel relative overflow-hidden rounded-[36px] border border-(--line) px-6 py-12 sm:px-10 sm:py-16 lg:px-16 lg:py-20">

            {/* Background Glow */}
            <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-(--accent) opacity-[0.08] blur-3xl" />

            <div className="relative z-10 max-w-4xl">

              {/* Small Label */}
              <div className="mb-5 font-mono text-[10px] uppercase tracking-[0.2em] text-(--accent)">
                Have a project in mind?
              </div>

              {/* Heading */}
              <h2 className="text-balance text-4xl font-semibold leading-[0.98] tracking-tighter text-(--foreground) sm:text-6xl lg:text-7xl">
                Let&apos;s build something useful, fast and genuinely
                intelligent.
              </h2>

              {/* Description */}
              <p className="mt-7 max-w-2xl font-medium text-base leading-7 text-(--body-copy) sm:text-lg">
                Available for AI/RAG freelance projects, AI chatbot
                integrations, full-stack builds and opportunities.
              </p>

              {/* Buttons */}
              <div className="mt-9 flex flex-wrap gap-3">

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