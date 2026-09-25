import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { siteConfig } from "@/lib/site";

export function Footer() {
  return (
    <footer className="border-t border-[var(--line)] py-8 sm:py-10">
      <Container className="flex flex-col gap-6 text-sm text-[var(--body-copy)] sm:flex-row sm:items-center sm:justify-between">
        <div>
          © {new Date().getFullYear()} {siteConfig.name}
        </div>
        <div className="flex flex-wrap items-center gap-5">
          <a href={siteConfig.github} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 hover:text-[var(--foreground)]">
            GitHub <ArrowUpRight className="h-3.5 w-3.5" />
          </a>
          <a href={siteConfig.linkedin} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 hover:text-[var(--foreground)]">
            LinkedIn <ArrowUpRight className="h-3.5 w-3.5" />
          </a>
          <Link href="#top" className="hover:text-[var(--foreground)]">Back to top ↑</Link>
        </div>
      </Container>
    </footer>
  );
}
