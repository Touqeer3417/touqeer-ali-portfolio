import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const API = process.env.RAG_API_URL;
const SECRET = process.env.RAG_API_SECRET ?? "";

// GET = wake-up ping (free-tier backends sleep). Called when the chat opens.
export async function GET() {
  try {
    await fetch(`${API}/health`, { cache: "no-store" });
  } catch {}
  return new Response("ok");
}

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "unknown";

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
    });
  } catch {
    return new Response("upstream_unreachable", { status: 502 });
  }

  if (!upstream.ok || !upstream.body) {
    return new Response("upstream_error", {
      status: upstream.status === 429 ? 429 : 502,
    });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}
