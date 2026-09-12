"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Menu, Moon, Sun, X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { useTheme } from "next-themes";
import { Container } from "@/components/ui/Container";
import { siteConfig } from "@/lib/site";

const navItems = [
  { label: "About", href: "#about" },
  { label: "Work", href: "#work" },
  { label: "Services", href: "#services" },
  { label: "Stack", href: "#stack" },
  { label: "Contact", href: "#contact" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { resolvedTheme, setTheme } = useTheme();

  useEffect(() => setMounted(true), []);

  return (
    <header className="fixed inset-x-0 top-0 z-50 pt-4 sm:pt-5">
      <Container>
        <div className="flex h-16 items-center justify-between rounded-full border border-[var(--line)] bg-[var(--nav)] px-3 shadow-[0_12px_50px_rgba(0,0,0,0.14)] backdrop-blur-xl sm:px-4">
          <Link
            href="#top"
            className="group flex items-center gap-3 rounded-full px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
            aria-label={`${siteConfig.name} home`}
          >
            <span className="grid h-9 w-9 place-items-center rounded-full border border-[var(--line-strong)] bg-[var(--foreground)] font-mono text-[11px] font-semibold text-[var(--background)]">
              {siteConfig.shortName}
            </span>
            <span className="hidden text-sm font-semibold tracking-[-0.02em] text-[var(--foreground)] sm:block">
              {siteConfig.name}
            </span>
          </Link>

          <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary navigation">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-full px-4 py-2 text-sm text-[var(--muted)] transition hover:bg-[var(--panel)] hover:text-[var(--foreground)]"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
              className="grid h-10 w-10 place-items-center rounded-full border border-[var(--line)] bg-[var(--panel)] text-[var(--foreground)] transition hover:border-[var(--line-strong)]"
              aria-label="Toggle color theme"
            >
              {mounted && resolvedTheme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>

            <Link
              href="#contact"
              className="hidden rounded-full bg-[var(--foreground)] px-5 py-2.5 text-sm font-medium text-[var(--background)] transition hover:-translate-y-0.5 sm:inline-flex"
            >
              Let&apos;s talk
            </Link>

            <button
              type="button"
              onClick={() => setOpen((value) => !value)}
              className="grid h-10 w-10 place-items-center rounded-full border border-[var(--line)] bg-[var(--panel)] text-[var(--foreground)] lg:hidden"
              aria-label="Toggle navigation menu"
              aria-expanded={open}
            >
              {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </Container>

      <AnimatePresence>
        {open ? (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.22 }}
            className="lg:hidden"
          >
            <Container className="mt-2">
              <div className="overflow-hidden rounded-[28px] border border-[var(--line)] bg-[var(--nav)] p-3 shadow-2xl backdrop-blur-xl">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className="block rounded-2xl px-4 py-3.5 text-base text-[var(--foreground)] transition hover:bg-[var(--panel)]"
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            </Container>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </header>
  );
}
