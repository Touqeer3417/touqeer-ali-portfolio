import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const API = process.env.RAG_API_URL;
const SECRET = process.env.RAG_API_SECRET ?? "";

// Hard cap for the whole upstream exchange, including the streamed body.
const UPSTREAM_TIMEOUT_MS = 55_000;

// GET = wake-up ping (free-tier backends sleep). Called when the chat opens.
export async function GET() {
  try {
    await fetch(`${API}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
  } catch {}
  return new Response("ok");
}

export async function POST(req: NextRequest) {
  if (!API) return new Response("server_not_configured", { status: 500 });
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "unknown";

  // Abort the upstream request when EITHER the browser disconnects (Stop button,
  // tab closed, navigation) OR the timeout fires. Without req.signal the backend
  // would keep generating (and paying for) tokens nobody is reading.
  const signal = AbortSignal.any([req.signal, AbortSignal.timeout(UPSTREAM_TIMEOUT_MS)]);

  let upstream: Response;
  try {
    upstream = await fetch(`${API}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": SECRET,
        "x-client-ip": ip,
      },
      body: await req.text(),
      cache: "no-store",
      signal,
    });
  } catch {
    // Client already left: nobody is listening, just end quietly.
    if (req.signal.aborted) return new Response(null, { status: 499 });
    return new Response("upstream_unreachable", { status: 502 });
  }

  if (!upstream.ok || !upstream.body) {
    // Release the upstream connection instead of leaving the body unread.
    await upstream.body?.cancel().catch(() => {});
    return new Response("upstream_error", {
      status: upstream.status === 429 ? 429 : 502,
    });
  }

  const headers: Record<string, string> = {
    "Content-Type": "text/plain; charset=utf-8",
    // no-transform + X-Accel-Buffering stop proxies/CDNs from buffering tokens.
    "Cache-Control": "no-store, no-transform",
    "X-Accel-Buffering": "no",
  };
  const requestId = upstream.headers.get("x-request-id");
  if (requestId) headers["X-Request-ID"] = requestId;

  // Pass the body through untouched: it stays a live stream, and cancelling the
  // client response cancels the upstream body (closing the connection to FastAPI).
  return new Response(upstream.body, { headers });
}
