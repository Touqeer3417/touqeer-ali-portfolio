"use client";

import { useRef } from "react";
import { motion, useMotionValue, useSpring } from "motion/react";
import type { ReactNode, MouseEvent } from "react";

export function MagneticButton({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useSpring(useMotionValue(0), { stiffness: 220, damping: 18, mass: 0.25 });
  const y = useSpring(useMotionValue(0), { stiffness: 220, damping: 18, mass: 0.25 });

  const move = (event: MouseEvent<HTMLDivElement>) => {
    if (!ref.current || window.innerWidth < 900) return;
    const rect = ref.current.getBoundingClientRect();
    x.set((event.clientX - rect.left - rect.width / 2) * 0.16);
    y.set((event.clientY - rect.top - rect.height / 2) * 0.16);
  };

  const reset = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div ref={ref} style={{ x, y }} onMouseMove={move} onMouseLeave={reset}>
      {children}
    </motion.div>
  );
}
