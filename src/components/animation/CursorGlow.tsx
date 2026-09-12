"use client";

import { useEffect, useRef } from "react";

export function CursorGlow() {
  const glow = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = glow.current;
    if (!el || window.matchMedia("(pointer: coarse)").matches) return;

    let raf = 0;
    let x = window.innerWidth / 2;
    let y = window.innerHeight / 2;

    const render = () => {
      el.style.transform = `translate3d(${x - 220}px, ${y - 220}px, 0)`;
      raf = 0;
    };

    const move = (event: PointerEvent) => {
      x = event.clientX;
      y = event.clientY;
      if (!raf) raf = requestAnimationFrame(render);
    };

    window.addEventListener("pointermove", move, { passive: true });
    return () => {
      window.removeEventListener("pointermove", move);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return <div ref={glow} aria-hidden className="cursor-glow hidden lg:block" />;
}
