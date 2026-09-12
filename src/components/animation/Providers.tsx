"use client";

import type { ReactNode } from "react";
import { ThemeProvider } from "next-themes";
import { SmoothScroll } from "@/components/animation/SmoothScroll";
import { CursorGlow } from "@/components/animation/CursorGlow";
import { ScrollProgress } from "@/components/animation/ScrollProgress";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <SmoothScroll />
      <ScrollProgress />
      <CursorGlow />
      {children}
    </ThemeProvider>
  );
}
