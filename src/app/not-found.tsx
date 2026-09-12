import Link from "next/link";
import { Container } from "@/components/ui/Container";

export default function NotFound() {
  return (
    <Container className="grid min-h-screen place-items-center py-32">
      <div className="max-w-xl text-center">
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-[var(--accent)]">404 · Signal lost</div>
        <h1 className="mt-5 text-5xl font-semibold tracking-[-0.05em] text-[var(--foreground)] sm:text-7xl">This route doesn&apos;t exist.</h1>
        <p className="mt-5 text-[var(--muted)]">The page may have moved, or the URL may be incorrect.</p>
        <Link href="/" className="mt-8 inline-flex rounded-full bg-[var(--foreground)] px-5 py-3 text-sm font-medium text-[var(--background)]">Return home</Link>
      </div>
    </Container>
  );
}
