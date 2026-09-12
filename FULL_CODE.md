# Full Source Code
This file contains the complete source of the generated portfolio project.

## `.env.example`
```text
# Optional. Used by metadata and social sharing.
NEXT_PUBLIC_SITE_URL=https://your-domain.com

```

## `.gitignore`
```text
# dependencies
/node_modules
/.pnp
.pnp.*

# next.js
/.next/
/out/

# production
/build

# local env files
.env*
!.env.example

# misc
.DS_Store
*.pem
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts

```

## `README.md`
```md
# Touqeer Ali — Premium AI Engineer Portfolio

A production-oriented personal portfolio built with **Next.js 16, React 19, TypeScript, Tailwind CSS 4, GSAP + ScrollTrigger, Motion, Lenis, next-themes and Lucide React**.

The site is deliberately designed around strong project case studies instead of a crowded project gallery. It positions you for AI/RAG freelance work, AI engineering internships, full-stack work and landing-page projects.

## Included

- Premium dark/light visual system
- Cinematic hero reveal
- GSAP ScrollTrigger parallax
- Lenis smooth scrolling synchronized with GSAP
- Motion-based card/section/page transitions
- Mouse-following glow on desktop
- Responsive navbar + mobile menu
- Selected project case studies
- Dynamic `/projects/[slug]` pages
- Problem → Solution → Outcome storytelling
- Services section
- Focused AI engineering tech stack
- Education / learning journey
- Contact CTA
- `prefers-reduced-motion` support
- SEO metadata, sitemap and robots
- Custom project preview SVG assets
- Vercel-ready project structure

## 1. Requirements

Use Node.js 20.9+ (Node 22 LTS/current is also fine).

## 2. Install

```bash
npm install
```

## 3. Run locally

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

## 4. Before deploying — edit these first

Open:

```text
src/lib/site.ts
```

Replace:

- `your-email@example.com`
- `https://www.linkedin.com/in/your-linkedin`

Optionally update your GitHub URL, role, headline and location there too.

Then put your PDF resume here:

```text
public/resume/touqeer-ali-resume.pdf
```

## 5. Replace project visuals

Current visuals are custom placeholder/mockup SVGs created for the portfolio. Replace them later with your real screenshots if you want:

```text
public/projects/lifeops-ai.svg
public/projects/corrective-rag.svg
public/projects/document-rag.svg
public/projects/business-agent.svg
```

Then update image paths in:

```text
src/data/projects.ts
```

## 6. Edit projects

All project content lives in:

```text
src/data/projects.ts
```

Every project supports:

- title
- summary
- full description
- tech stack
- GitHub/live links
- problem
- solution
- outcome
- architecture flow
- engineering highlights
- metrics

Adding a new object automatically gives it a case-study page at:

```text
/projects/your-project-slug
```

## 7. Edit services and skills

```text
src/data/skills.ts
```

The current services are:

1. AI Agent & Business Automation
2. Custom RAG Chatbots
3. AI Chatbot Integration
4. Full-Stack Web Applications
5. Landing Pages

## 8. Environment

Copy `.env.example` to `.env.local` and set your production URL:

```bash
NEXT_PUBLIC_SITE_URL=https://your-domain.com
```

## 9. Production build

```bash
npm run build
npm run start
```

## 10. Deploy to Vercel

1. Push this folder to a GitHub repository.
2. Import the repository into Vercel.
3. Add `NEXT_PUBLIC_SITE_URL` in Vercel environment variables.
4. Deploy.
5. Attach your custom domain.

## Folder structure

```text
touqeer-portfolio/
├── public/
│   ├── projects/
│   │   ├── business-agent.svg
│   │   ├── corrective-rag.svg
│   │   ├── document-rag.svg
│   │   └── lifeops-ai.svg
│   └── resume/
│       └── README.txt
├── src/
│   ├── app/
│   │   ├── projects/[slug]/page.tsx
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   ├── not-found.tsx
│   │   ├── page.tsx
│   │   ├── robots.ts
│   │   └── sitemap.ts
│   ├── components/
│   │   ├── animation/
│   │   ├── layout/
│   │   ├── projects/
│   │   ├── sections/
│   │   └── ui/
│   ├── data/
│   ├── hooks/
│   ├── lib/
│   └── types/
├── .env.example
├── .gitignore
├── eslint.config.mjs
├── next.config.ts
├── package.json
├── postcss.config.mjs
└── tsconfig.json
```

## Design philosophy

This portfolio intentionally avoids Three.js in V1. The premium feel comes from typography, composition, restrained gradients, spacing, Motion micro-interactions, GSAP choreography and excellent project storytelling rather than visual overload.

```

## `components.json`
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "css": "src/app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide"
}

```

## `eslint.config.mjs`
```js
import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
]);

```

## `next.config.ts`
```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
};

export default nextConfig;

```

## `package.json`
```json
{
  "name": "touqeer-ali-portfolio",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint ."
  },
  "dependencies": {
    "clsx": "^2.1.1",
    "gsap": "^3.15.0",
    "lenis": "^1.3.26",
    "lucide-react": "^1.45.0",
    "motion": "^13.2.0",
    "next": "16.3.4",
    "next-themes": "^0.4.6",
    "react": "19.3.0",
    "react-dom": "19.3.0",
    "tailwind-merge": "^3.3.1",
    "@radix-ui/react-slot": "^1.2.3",
    "class-variance-authority": "^0.7.1"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4.3.3",
    "@types/node": "^24.5.2",
    "@types/react": "^19.1.16",
    "@types/react-dom": "^19.1.9",
    "eslint": "^9.35.0",
    "eslint-config-next": "16.3.4",
    "postcss": "^8.5.6",
    "tailwindcss": "^4.3.3",
    "typescript": "^5.9.2"
  }
}

```

## `postcss.config.mjs`
```js
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;

```

## `public/projects/business-agent.svg`
```xml
<svg width="1600" height="1000" viewBox="0 0 1600 1000" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="1600" height="1000" fill="#090C0F"/><circle cx="1260" cy="260" r="500" fill="#75F5B5" fill-opacity=".1"/>
<text x="120" y="145" fill="#EAF4EE" font-family="Arial" font-size="46" font-weight="700">Business AI Agent</text><text x="120" y="190" fill="#75877F" font-family="monospace" font-size="16">ANSWER · QUALIFY · AUTOMATE · HAND OFF</text>
<rect x="120" y="260" width="860" height="610" rx="36" fill="#0F1518" stroke="#fff" stroke-opacity=".1"/><rect x="160" y="305" width="780" height="92" rx="22" fill="#121B1D"/><text x="195" y="346" fill="#EAF4EE" font-family="Arial" font-size="20">Visitor: Can you integrate an AI assistant into our website?</text><text x="195" y="375" fill="#71837B" font-family="Arial" font-size="15">Intent detected: sales inquiry · high confidence</text>
<rect x="160" y="430" width="780" height="170" rx="24" fill="#11211C" stroke="#75F5B5" stroke-opacity=".25"/><text x="195" y="474" fill="#75F5B5" font-family="monospace" font-size="13">AI ASSISTANT</text><text x="195" y="518" fill="#EAF4EE" font-family="Arial" font-size="19">Yes. I can answer from your website + docs, qualify leads,</text><text x="195" y="550" fill="#EAF4EE" font-family="Arial" font-size="19">and send serious inquiries to your CRM or email workflow.</text>
<rect x="160" y="636" width="360" height="176" rx="24" fill="#121B1D"/><text x="195" y="680" fill="#778A82" font-family="monospace" font-size="13">LEAD CAPTURE</text><text x="195" y="724" fill="#EAF4EE" font-family="Arial" font-size="18">Name · Email · Project</text><rect x="195" y="754" width="180" height="34" rx="17" fill="#75F5B5"/><text x="225" y="777" fill="#07100C" font-family="Arial" font-size="14" font-weight="700">QUALIFIED ✓</text>
<rect x="548" y="636" width="392" height="176" rx="24" fill="#121B1D"/><text x="583" y="680" fill="#778A82" font-family="monospace" font-size="13">WORKFLOW</text><text x="583" y="724" fill="#EAF4EE" font-family="Arial" font-size="18">Chat → Lead → CRM → Follow-up</text><text x="583" y="762" fill="#75F5B5" font-family="monospace" font-size="14">AUTOMATION READY</text>
<g font-family="monospace"><rect x="1040" y="260" width="440" height="610" rx="36" fill="#0F1518" stroke="#fff" stroke-opacity=".1"/><text x="1090" y="320" fill="#75F5B5" font-size="14">AGENT FLOW</text><text x="1090" y="390" fill="#EAF4EE" font-size="20">01  Understand intent</text><text x="1090" y="455" fill="#EAF4EE" font-size="20">02  Retrieve business data</text><text x="1090" y="520" fill="#EAF4EE" font-size="20">03  Answer accurately</text><text x="1090" y="585" fill="#EAF4EE" font-size="20">04  Capture lead</text><text x="1090" y="650" fill="#EAF4EE" font-size="20">05  Trigger workflow</text><path d="M1100 710H1410" stroke="#75F5B5" stroke-opacity=".35"/><text x="1090" y="765" fill="#7D9087" font-size="14">NEXT.JS · FASTAPI · RAG</text><text x="1090" y="800" fill="#7D9087" font-size="14">LANGGRAPH · WEBHOOKS</text></g>
</svg>

```

## `public/projects/corrective-rag.svg`
```xml
<svg width="1600" height="1000" viewBox="0 0 1600 1000" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="a" x1="0" y1="0" x2="1600" y2="1000"><stop stop-color="#07100F"/><stop offset="1" stop-color="#12131B"/></linearGradient><radialGradient id="b"><stop stop-color="#75F5B5" stop-opacity=".24"/><stop offset="1" stop-color="#75F5B5" stop-opacity="0"/></radialGradient></defs>
<rect width="1600" height="1000" fill="url(#a)"/><circle cx="1190" cy="270" r="560" fill="url(#b)"/>
<text x="120" y="135" fill="#75F5B5" font-family="monospace" font-size="18">CORRECTIVE RETRIEVAL GRAPH</text><text x="120" y="195" fill="#EAF4EE" font-family="Arial" font-weight="700" font-size="46">Retrieve. Grade. Correct. Answer.</text>
<g stroke="#75F5B5" stroke-opacity=".35" stroke-width="3"><path d="M330 390H570"/><path d="M740 390H980"/><path d="M1150 390V560H980"/><path d="M810 560H570"/><path d="M450 560V720H690"/></g>
<g font-family="Arial"><rect x="120" y="320" width="210" height="138" rx="28" fill="#10191A" stroke="#fff" stroke-opacity=".12"/><text x="155" y="368" fill="#7D9188" font-family="monospace" font-size="14">01</text><text x="155" y="411" fill="#EAF4EE" font-size="24">Query</text>
<rect x="570" y="320" width="240" height="138" rx="28" fill="#10191A" stroke="#fff" stroke-opacity=".12"/><text x="605" y="368" fill="#7D9188" font-family="monospace" font-size="14">02</text><text x="605" y="411" fill="#EAF4EE" font-size="24">Hybrid Retrieval</text>
<rect x="980" y="320" width="260" height="138" rx="28" fill="#11211C" stroke="#75F5B5" stroke-opacity=".35"/><text x="1015" y="368" fill="#75F5B5" font-family="monospace" font-size="14">03</text><text x="1015" y="411" fill="#EAF4EE" font-size="24">Grade Context</text>
<rect x="760" y="510" width="220" height="110" rx="26" fill="#161520" stroke="#fff" stroke-opacity=".12"/><text x="795" y="555" fill="#9B91BC" font-family="monospace" font-size="14">WEAK?</text><text x="795" y="592" fill="#EAF4EE" font-size="22">Rewrite query</text>
<rect x="450" y="510" width="220" height="110" rx="26" fill="#10191A" stroke="#fff" stroke-opacity=".12"/><text x="485" y="555" fill="#7D9188" font-family="monospace" font-size="14">CORRECT</text><text x="485" y="592" fill="#EAF4EE" font-size="22">Search again</text>
<rect x="690" y="680" width="280" height="130" rx="28" fill="#11211C" stroke="#75F5B5" stroke-opacity=".45"/><text x="725" y="728" fill="#75F5B5" font-family="monospace" font-size="14">FINAL</text><text x="725" y="775" fill="#EAF4EE" font-size="26">Grounded answer ✓</text></g>
<g font-family="monospace" font-size="15" fill="#7D9188"><text x="1260" y="355">BM25</text><text x="1260" y="390">QDRANT</text><text x="1260" y="425">RERANKER</text><text x="1260" y="460">LANGGRAPH</text></g>
</svg>

```

## `public/projects/document-rag.svg`
```xml
<svg width="1600" height="1000" viewBox="0 0 1600 1000" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="1600" height="1000" fill="#0A0D10"/><circle cx="360" cy="200" r="460" fill="#4BC3FF" fill-opacity=".08"/><circle cx="1280" cy="720" r="500" fill="#75F5B5" fill-opacity=".08"/>
<rect x="100" y="100" width="1400" height="800" rx="42" fill="#0E1316" stroke="#fff" stroke-opacity=".1"/>
<text x="150" y="175" fill="#EAF4EE" font-family="Arial" font-size="34" font-weight="700">Document Search RAG</text><text x="150" y="214" fill="#72847D" font-family="monospace" font-size="15">SEMANTIC RETRIEVAL · GROUNDED ANSWERS</text>
<rect x="150" y="270" width="420" height="555" rx="28" fill="#12191C"/><text x="185" y="320" fill="#75F5B5" font-family="monospace" font-size="14">KNOWLEDGE BASE</text>
<g font-family="Arial"><rect x="185" y="355" width="350" height="85" rx="20" fill="#0C1214"/><text x="215" y="392" fill="#EAF4EE" font-size="19">research-paper.pdf</text><text x="215" y="418" fill="#75877F" font-size="14">42 chunks · indexed</text><rect x="185" y="460" width="350" height="85" rx="20" fill="#0C1214"/><text x="215" y="497" fill="#EAF4EE" font-size="19">project-notes.pdf</text><text x="215" y="523" fill="#75877F" font-size="14">18 chunks · indexed</text></g>
<rect x="615" y="270" width="835" height="555" rx="28" fill="#10171A"/><text x="655" y="326" fill="#7A8A84" font-family="monospace" font-size="14">QUESTION</text><text x="655" y="374" fill="#EAF4EE" font-family="Arial" font-size="27">How does the proposed retrieval method work?</text>
<rect x="655" y="420" width="755" height="140" rx="24" fill="#0C1214" stroke="#75F5B5" stroke-opacity=".22"/><text x="690" y="462" fill="#75F5B5" font-family="monospace" font-size="13">TOP CONTEXT · SCORE 0.91</text><text x="690" y="506" fill="#B7C6BF" font-family="Arial" font-size="18">The system embeds each chunk, performs vector similarity search,</text><text x="690" y="536" fill="#B7C6BF" font-family="Arial" font-size="18">then supplies the most relevant passages to the language model…</text>
<rect x="655" y="600" width="755" height="170" rx="24" fill="#11211C"/><text x="690" y="644" fill="#75F5B5" font-family="monospace" font-size="13">ANSWER</text><text x="690" y="690" fill="#EAF4EE" font-family="Arial" font-size="20">The pipeline uses semantic embeddings + FAISS retrieval before</text><text x="690" y="722" fill="#EAF4EE" font-family="Arial" font-size="20">generation, keeping the response tied to source passages.</text><text x="690" y="752" fill="#82958C" font-family="Arial" font-size="15">Source: research-paper.pdf · p. 7</text>
</svg>

```

## `public/projects/lifeops-ai.svg`
```xml
<svg width="1600" height="1000" viewBox="0 0 1600 1000" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1600" y2="1000"><stop stop-color="#08110F"/><stop offset="1" stop-color="#0D1719"/></linearGradient>
    <radialGradient id="glow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(1190 180) rotate(125) scale(620 520)"><stop stop-color="#75F5B5" stop-opacity=".24"/><stop offset="1" stop-color="#75F5B5" stop-opacity="0"/></radialGradient>
  </defs>
  <rect width="1600" height="1000" fill="url(#bg)"/><rect width="1600" height="1000" fill="url(#glow)"/>
  <g opacity=".16" stroke="#DDF8E7"><path d="M0 120H1600M0 240H1600M0 360H1600M0 480H1600M0 600H1600M0 720H1600M0 840H1600"/><path d="M160 0V1000M320 0V1000M480 0V1000M640 0V1000M800 0V1000M960 0V1000M1120 0V1000M1280 0V1000M1440 0V1000"/></g>
  <rect x="120" y="110" width="1360" height="780" rx="40" fill="#0B1214" stroke="#FFFFFF" stroke-opacity=".14"/>
  <rect x="160" y="152" width="1280" height="68" rx="20" fill="#111C1D"/><circle cx="204" cy="186" r="8" fill="#75F5B5"/><text x="236" y="194" fill="#EAF4EE" font-family="Arial" font-size="24" font-weight="700">LifeOps AI</text><text x="1250" y="194" fill="#7C9188" font-family="monospace" font-size="18">AGENT ONLINE</text>
  <rect x="160" y="252" width="286" height="594" rx="28" fill="#0F181A" stroke="#FFFFFF" stroke-opacity=".08"/><text x="194" y="304" fill="#75F5B5" font-family="monospace" font-size="16">WORKSPACE</text>
  <g font-family="Arial" font-size="22" fill="#B9C8C1"><text x="194" y="365">Overview</text><text x="194" y="420">Calendar Agent</text><text x="194" y="475">Gmail Intelligence</text><text x="194" y="530">Knowledge Base</text><text x="194" y="585">Automations</text></g>
  <rect x="486" y="252" width="954" height="594" rx="28" fill="#0D1517" stroke="#FFFFFF" stroke-opacity=".08"/>
  <text x="530" y="310" fill="#EAF4EE" font-family="Arial" font-size="32" font-weight="700">Good afternoon, Touqeer.</text><text x="530" y="350" fill="#81948B" font-family="Arial" font-size="20">What should I handle for you?</text>
  <rect x="530" y="394" width="820" height="98" rx="24" fill="#111D1E" stroke="#75F5B5" stroke-opacity=".26"/><text x="566" y="435" fill="#DDEBE4" font-family="Arial" font-size="20">Move tomorrow's AI project review to 4:30 PM</text><text x="566" y="468" fill="#75F5B5" font-family="monospace" font-size="14">CALENDAR TOOL · CONTEXT VERIFIED</text>
  <path d="M785 534H1070" stroke="#75F5B5" stroke-opacity=".55" stroke-width="2" stroke-dasharray="8 10"/>
  <g><rect x="530" y="574" width="220" height="124" rx="22" fill="#111D1E"/><text x="558" y="615" fill="#7F9389" font-family="monospace" font-size="13">01 · INTENT</text><text x="558" y="660" fill="#EAF4EE" font-family="Arial" font-size="22">Reschedule</text></g>
  <g><rect x="780" y="574" width="220" height="124" rx="22" fill="#111D1E"/><text x="808" y="615" fill="#7F9389" font-family="monospace" font-size="13">02 · CONTEXT</text><text x="808" y="660" fill="#EAF4EE" font-family="Arial" font-size="22">Event found</text></g>
  <g><rect x="1030" y="574" width="320" height="124" rx="22" fill="#11211C" stroke="#75F5B5" stroke-opacity=".28"/><text x="1058" y="615" fill="#75F5B5" font-family="monospace" font-size="13">03 · ACTION</text><text x="1058" y="660" fill="#EAF4EE" font-family="Arial" font-size="22">Calendar updated ✓</text></g>
  <rect x="530" y="736" width="820" height="70" rx="20" fill="#0A1113" stroke="#FFFFFF" stroke-opacity=".1"/><text x="560" y="780" fill="#748780" font-family="Arial" font-size="18">Ask LifeOps anything…</text><circle cx="1315" cy="771" r="20" fill="#75F5B5"/>
</svg>

```

## `public/resume/README.txt`
```text
Place your final PDF resume in this folder and name it:

touqeer-ali-resume.pdf

The path is already configured in src/lib/site.ts.

```

## `src/app/globals.css`
```css
@import "tailwindcss";

:root {
  --background: #f4f5f1;
  --foreground: #0c1111;
  --muted: #626b68;
  --muted-strong: #777f7d;
  --surface: #eceee9;
  --panel: rgba(255, 255, 255, 0.55);
  --panel-strong: rgba(255, 255, 255, 0.82);
  --nav: rgba(244, 245, 241, 0.82);
  --line: rgba(11, 17, 17, 0.10);
  --line-strong: rgba(11, 17, 17, 0.22);
  --accent: #0b8c58;
  --accent-soft: rgba(11, 140, 88, 0.12);
}

.dark {
  --background: #080b0d;
  --foreground: #eef4ef;
  --muted: #89938f;
  --muted-strong: #66716d;
  --surface: #0d1214;
  --panel: rgba(16, 22, 23, 0.66);
  --panel-strong: rgba(22, 30, 30, 0.85);
  --nav: rgba(8, 11, 13, 0.76);
  --line: rgba(232, 242, 235, 0.095);
  --line-strong: rgba(232, 242, 235, 0.19);
  --accent: #75f5b5;
  --accent-soft: rgba(117, 245, 181, 0.10);
}

* {
  box-sizing: border-box;
}

html {
  scroll-padding-top: 100px;
  background: var(--background);
}

body {
  margin: 0;
  min-width: 320px;
  overflow-x: hidden;
  background: var(--background);
  color: var(--foreground);
  font-family: var(--font-geist-sans), Arial, Helvetica, sans-serif;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
}

::selection {
  background: var(--accent);
  color: var(--background);
}

::-webkit-scrollbar {
  width: 10px;
}

::-webkit-scrollbar-track {
  background: var(--background);
}

::-webkit-scrollbar-thumb {
  border: 3px solid var(--background);
  border-radius: 999px;
  background: var(--line-strong);
}

button,
a {
  -webkit-tap-highlight-color: transparent;
}

code,
.font-mono {
  font-family: var(--font-geist-mono), monospace;
}

.section-space {
  padding-block: clamp(5.5rem, 10vw, 9rem);
}

.hero-grid {
  background-image:
    linear-gradient(to right, var(--line) 1px, transparent 1px),
    linear-gradient(to bottom, var(--line) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: linear-gradient(to bottom, black 0%, black 58%, transparent 100%);
  opacity: 0.52;
}

.hero-vignette {
  background:
    radial-gradient(circle at 74% 35%, var(--accent-soft), transparent 24%),
    radial-gradient(circle at 18% 10%, var(--accent-soft), transparent 22%),
    linear-gradient(to bottom, transparent 45%, var(--background) 98%);
}

.cursor-glow {
  pointer-events: none;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 2;
  width: 440px;
  height: 440px;
  border-radius: 999px;
  background: radial-gradient(circle, var(--accent-soft) 0%, transparent 67%);
  opacity: 0.8;
  will-change: transform;
}

.hero-node {
  display: grid;
  min-width: 74px;
  min-height: 74px;
  place-items: center;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  background: var(--nav);
  color: var(--muted);
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.12);
  backdrop-filter: blur(16px);
  font-family: var(--font-geist-mono), monospace;
  font-size: 9px;
  letter-spacing: 0.15em;
}

.hero-node-main {
  min-width: 128px;
  min-height: 128px;
  color: var(--foreground);
  border-color: var(--accent);
  box-shadow: 0 0 90px var(--accent-soft);
}

.project-card {
  --mouse-x: 50%;
  --mouse-y: 50%;
  isolation: isolate;
}

.project-card-glow {
  pointer-events: none;
  position: absolute;
  inset: 0;
  z-index: 0;
  opacity: 0;
  transition: opacity 300ms ease;
  background: radial-gradient(
    600px circle at var(--mouse-x) var(--mouse-y),
    var(--accent-soft),
    transparent 40%
  );
}

.project-card:hover .project-card-glow {
  opacity: 1;
}

.service-row:hover {
  background: linear-gradient(to right, transparent, var(--accent-soft), transparent);
}

.contact-panel {
  background:
    linear-gradient(125deg, var(--panel-strong), transparent),
    radial-gradient(circle at 85% 10%, var(--accent-soft), transparent 34%),
    var(--surface);
}

@media (max-width: 1023px) {
  .hero-grid {
    background-size: 48px 48px;
    opacity: 0.35;
  }
}

@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto !important;
  }

  *,
  *::before,
  *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.001ms !important;
  }
}

```

## `src/app/layout.tsx`
```tsx
import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/animation/Providers";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { PageTransition } from "@/components/animation/PageTransition";
import { siteConfig } from "@/lib/site";

const geist = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://example.com";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: `${siteConfig.name} — AI Engineer`,
    template: `%s — ${siteConfig.name}`,
  },
  description: siteConfig.description,
  keywords: [
    "Touqeer Ali",
    "AI Engineer",
    "RAG Developer",
    "Agentic AI Developer",
    "AI Agent Developer",
    "LangGraph",
    "FastAPI",
    "Next.js",
  ],
  authors: [{ name: siteConfig.name }],
  creator: siteConfig.name,
  openGraph: {
    type: "website",
    title: `${siteConfig.name} — AI Engineer`,
    description: siteConfig.description,
    url: siteUrl,
    siteName: siteConfig.name,
  },
  twitter: {
    card: "summary_large_image",
    title: `${siteConfig.name} — AI Engineer`,
    description: siteConfig.description,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#080b0d" },
    { media: "(prefers-color-scheme: light)", color: "#f4f5f1" },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geist.variable} ${geistMono.variable}`}>
        <Providers>
          <Navbar />
          <main><PageTransition>{children}</PageTransition></main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}

```

## `src/app/not-found.tsx`
```tsx
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

```

## `src/app/page.tsx`
```tsx
import { Hero } from "@/components/sections/Hero";
import { About } from "@/components/sections/About";
import { Projects } from "@/components/sections/Projects";
import { Services } from "@/components/sections/Services";
import { Skills } from "@/components/sections/Skills";
import { Experience } from "@/components/sections/Experience";
import { Contact } from "@/components/sections/Contact";

export default function Home() {
  return (
    <>
      <Hero />
      <About />
      <Projects />
      <Services />
      <Skills />
      <Experience />
      <Contact />
    </>
  );
}

```

## `src/app/projects/[slug]/page.tsx`
```tsx
import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ArrowUpRight, Github } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { Badge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { projects, getProject } from "@/data/projects";

export function generateStaticParams() {
  return projects.map((project) => ({ slug: project.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const project = getProject(slug);

  if (!project) return {};

  return {
    title: project.title,
    description: project.summary,
    openGraph: {
      title: project.title,
      description: project.summary,
      images: [{ url: project.image }],
    },
  };
}

export default async function ProjectPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const project = getProject(slug);

  if (!project) notFound();

  return (
    <article className="pb-20 pt-32 sm:pt-36">
      <Container>
        <Link
          href="/#work"
          className="mb-10 inline-flex items-center gap-2 text-sm text-[var(--muted)] transition hover:text-[var(--foreground)]"
        >
          <ArrowLeft className="h-4 w-4" /> Back to selected work
        </Link>

        <div className="grid gap-10 lg:grid-cols-[1fr_0.65fr] lg:items-end">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--accent)]">
              {project.index} · {project.eyebrow} · {project.year}
            </div>
            <h1 className="mt-5 max-w-5xl text-5xl font-semibold leading-[0.95] tracking-[-0.055em] text-[var(--foreground)] sm:text-7xl lg:text-8xl">
              {project.title}
            </h1>
          </div>
          <div>
            <p className="text-base leading-7 text-[var(--muted)] sm:text-lg">{project.description}</p>
            <div className="mt-6 flex flex-wrap gap-3">
              {project.links.map((link) => (
                <ButtonLink key={link.href} href={link.href} external variant={link.type === "github" ? "ghost" : "primary"}>
                  {link.type === "github" ? <Github className="h-4 w-4" /> : null}
                  {link.label}
                </ButtonLink>
              ))}
            </div>
          </div>
        </div>

        <div className="relative mt-12 aspect-[16/8.5] overflow-hidden rounded-[32px] border border-[var(--line)] bg-[var(--panel)] sm:mt-16">
          <Image src={project.image} alt={`${project.title} case study visual`} fill priority className="object-cover" sizes="100vw" />
        </div>

        <div className="mt-10 flex flex-wrap gap-2 sm:mt-12">
          {project.stack.map((tech) => <Badge key={tech}>{tech}</Badge>)}
        </div>

        <section className="mt-20 grid gap-5 lg:grid-cols-3">
          {[
            ["Problem", project.problem],
            ["Solution", project.solution],
            ["Outcome", project.outcome],
          ].map(([title, text]) => (
            <div key={title} className="rounded-[28px] border border-[var(--line)] bg-[var(--panel)] p-7">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--accent)]">{title}</div>
              <p className="mt-5 text-sm leading-7 text-[var(--muted)] sm:text-base">{text}</p>
            </div>
          ))}
        </section>

        <section className="mt-20 grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--accent)]">Architecture</div>
            <h2 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">
              How the system flows.
            </h2>
          </div>
          <div className="rounded-[32px] border border-[var(--line)] bg-[var(--panel)] p-6 sm:p-8">
            <div className="space-y-3">
              {project.architecture.map((step, index) => (
                <div key={step} className="flex items-center gap-4 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-4">
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[var(--foreground)] font-mono text-[10px] text-[var(--background)]">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="text-sm text-[var(--foreground)] sm:text-base">{step}</span>
                  {index !== project.architecture.length - 1 ? <ArrowUpRight className="ml-auto h-4 w-4 rotate-45 text-[var(--muted)]" /> : null}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-20 grid gap-8 lg:grid-cols-2">
          <div className="rounded-[32px] border border-[var(--line)] bg-[var(--panel)] p-7 sm:p-8">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--accent)]">Engineering highlights</div>
            <div className="mt-7 space-y-5">
              {project.highlights.map((item, index) => (
                <div key={item} className="flex gap-4 border-b border-[var(--line)] pb-5 last:border-0 last:pb-0">
                  <span className="font-mono text-[10px] text-[var(--muted)]">0{index + 1}</span>
                  <p className="text-sm leading-6 text-[var(--foreground)] sm:text-base">{item}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
            {project.metrics.map((metric) => (
              <div key={metric.label} className="rounded-[28px] border border-[var(--line)] bg-[var(--panel)] p-6">
                <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[var(--muted)]">{metric.label}</div>
                <div className="mt-3 text-2xl font-semibold tracking-[-0.03em] text-[var(--foreground)]">{metric.value}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-20 rounded-[36px] border border-[var(--line)] bg-[var(--panel)] p-8 sm:p-12">
          <div className="max-w-3xl">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--accent)]">Next project</div>
            <h2 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">Need a system like this for your business?</h2>
            <p className="mt-5 text-base leading-7 text-[var(--muted)]">I’m available for RAG, AI agents, website chatbot integration and full-stack AI work.</p>
            <div className="mt-7"><ButtonLink href="/#contact">Start a conversation</ButtonLink></div>
          </div>
        </section>
      </Container>
    </article>
  );
}

```

## `src/app/robots.ts`
```ts
import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://example.com";
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}

```

## `src/app/sitemap.ts`
```ts
import type { MetadataRoute } from "next";
import { projects } from "@/data/projects";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://example.com";
  return [
    { url: baseUrl, lastModified: new Date(), changeFrequency: "monthly", priority: 1 },
    ...projects.map((project) => ({
      url: `${baseUrl}/projects/${project.slug}`,
      lastModified: new Date(),
      changeFrequency: "monthly" as const,
      priority: 0.8,
    })),
  ];
}

```

## `src/components/animation/CursorGlow.tsx`
```tsx
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

```

## `src/components/animation/FadeIn.tsx`
```tsx
"use client";

import { motion } from "motion/react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function FadeIn({
  children,
  className,
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-8%" }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
      className={cn(className)}
    >
      {children}
    </motion.div>
  );
}

```

## `src/components/animation/MagneticButton.tsx`
```tsx
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

```

## `src/components/animation/PageTransition.tsx`
```tsx
"use client";

import { AnimatePresence, motion } from "motion/react";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

export function PageTransition({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.34, ease: [0.22, 1, 0.36, 1] }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

```

## `src/components/animation/Providers.tsx`
```tsx
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

```

## `src/components/animation/ScrollProgress.tsx`
```tsx
"use client";

import { motion, useScroll, useSpring } from "motion/react";

export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 100, damping: 30, restDelta: 0.001 });

  return (
    <motion.div
      style={{ scaleX }}
      className="fixed inset-x-0 top-0 z-[100] h-[2px] origin-left bg-[var(--accent)]"
    />
  );
}

```

## `src/components/animation/SmoothScroll.tsx`
```tsx
"use client";

import { useEffect } from "react";
import Lenis from "lenis";
import "lenis/dist/lenis.css";
import { gsap, ScrollTrigger } from "@/lib/gsap";

export function SmoothScroll() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const lenis = new Lenis({
      lerp: 0.085,
      smoothWheel: true,
      wheelMultiplier: 0.9,
    });

    const onScroll = () => ScrollTrigger.update();
    lenis.on("scroll", onScroll);

    const tick = (time: number) => {
      lenis.raf(time * 1000);
    };

    gsap.ticker.add(tick);
    gsap.ticker.lagSmoothing(0);

    return () => {
      lenis.off("scroll", onScroll);
      gsap.ticker.remove(tick);
      lenis.destroy();
    };
  }, []);

  return null;
}

```

## `src/components/animation/TextReveal.tsx`
```tsx
"use client";

import { useLayoutEffect, useRef } from "react";
import { gsap } from "@/lib/gsap";
import { cn } from "@/lib/utils";

export function TextReveal({
  text,
  className,
  delay = 0,
}: {
  text: string;
  className?: string;
  delay?: number;
}) {
  const root = useRef<HTMLSpanElement>(null);

  useLayoutEffect(() => {
    const el = root.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        el.querySelectorAll("[data-word]"),
        { yPercent: 120, opacity: 0 },
        {
          yPercent: 0,
          opacity: 1,
          duration: 1.05,
          delay,
          stagger: 0.045,
          ease: "power4.out",
        },
      );
    }, el);

    return () => ctx.revert();
  }, [delay]);

  return (
    <span ref={root} className={cn("inline-flex flex-wrap", className)}>
      {text.split(" ").map((word, index) => (
        <span key={`${word}-${index}`} className="overflow-hidden pr-[0.24em] pb-[0.08em]">
          <span data-word className="inline-block will-change-transform">
            {word}
          </span>
        </span>
      ))}
    </span>
  );
}

```

## `src/components/layout/Footer.tsx`
```tsx
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { siteConfig } from "@/lib/site";

export function Footer() {
  return (
    <footer className="border-t border-[var(--line)] py-8 sm:py-10">
      <Container className="flex flex-col gap-6 text-sm text-[var(--muted)] sm:flex-row sm:items-center sm:justify-between">
        <div>
          © {new Date().getFullYear()} {siteConfig.name}. Built with Next.js, GSAP & Motion.
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

```

## `src/components/layout/Navbar.tsx`
```tsx
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

```

## `src/components/projects/ProjectCard.tsx`
```tsx
"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { motion } from "motion/react";
import type { MouseEvent } from "react";
import type { Project } from "@/types/project";
import { Badge } from "@/components/ui/Badge";

export function ProjectCard({ project }: { project: Project }) {
  const handleMouseMove = (event: MouseEvent<HTMLElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    event.currentTarget.style.setProperty("--mouse-x", `${event.clientX - rect.left}px`);
    event.currentTarget.style.setProperty("--mouse-y", `${event.clientY - rect.top}px`);
  };

  return (
    <motion.article
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-8%" }}
      transition={{ duration: 0.72, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -6 }}
      onMouseMove={handleMouseMove}
      className="project-card group relative overflow-hidden rounded-[32px] border border-[var(--line)] bg-[var(--panel)]"
    >
      <div className="project-card-glow" aria-hidden />
      <Link href={`/projects/${project.slug}`} className="relative z-10 block">
        <div className="relative aspect-[16/10] overflow-hidden border-b border-[var(--line)] bg-[var(--surface)]">
          <Image
            src={project.image}
            alt={`${project.title} project preview`}
            fill
            sizes="(max-width: 768px) 100vw, 50vw"
            className="object-cover transition duration-700 ease-out group-hover:scale-[1.035]"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent" />
          <span className="absolute left-5 top-5 rounded-full border border-white/15 bg-black/30 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.18em] text-white/80 backdrop-blur-md">
            {project.eyebrow}
          </span>
        </div>

        <div className="p-6 sm:p-8">
          <div className="mb-5 flex items-center justify-between gap-4">
            <span className="font-mono text-xs tracking-[0.2em] text-[var(--accent)]">{project.index}</span>
            <ArrowUpRight className="h-5 w-5 text-[var(--muted)] transition duration-300 group-hover:-translate-y-1 group-hover:translate-x-1 group-hover:rotate-6 group-hover:text-[var(--foreground)]" />
          </div>

          <h3 className="text-3xl font-semibold tracking-[-0.04em] text-[var(--foreground)] sm:text-4xl">
            {project.title}
          </h3>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-[var(--muted)] sm:text-base sm:leading-7">
            {project.summary}
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            {project.stack.slice(0, 5).map((tech) => (
              <Badge key={tech}>{tech}</Badge>
            ))}
          </div>
        </div>
      </Link>
    </motion.article>
  );
}

```

## `src/components/projects/ProjectShowcase.tsx`
```tsx
import { ProjectCard } from "@/components/projects/ProjectCard";
import type { Project } from "@/types/project";

export function ProjectShowcase({ projects }: { projects: Project[] }) {
  return (
    <div className="grid gap-5 lg:grid-cols-2 lg:gap-6">
      {projects.map((project, index) => (
        <div key={project.slug} className={index === 0 ? "lg:col-span-2" : ""}>
          <ProjectCard project={project} />
        </div>
      ))}
    </div>
  );
}

```

## `src/components/sections/About.tsx`
```tsx
import { BrainCircuit, Code2, Layers3 } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { FadeIn } from "@/components/animation/FadeIn";

const cards = [
  {
    icon: BrainCircuit,
    title: "AI that does useful work",
    text: "I focus on grounded retrieval, tool use and workflow automation — not chat demos that stop at a nice response.",
  },
  {
    icon: Layers3,
    title: "Systems over snippets",
    text: "I like connecting retrieval, APIs, databases, auth, orchestration and frontend UX into complete products.",
  },
  {
    icon: Code2,
    title: "Engineering + presentation",
    text: "Strong architecture matters, but so does the experience around it: clear UX, responsive design and production-minded code.",
  },
];

export function About() {
  return (
    <section id="about" className="section-space border-t border-[var(--line)]">
      <Container>
        <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
          <FadeIn>
            <SectionHeading
              eyebrow="About"
              title="AI engineering with a product mindset."
              description="I’m building toward a career in AI engineering, with a practical focus on RAG, agentic systems and full-stack products that solve real operational problems."
            />
          </FadeIn>

          <div className="grid gap-4 sm:grid-cols-3 lg:pt-16">
            {cards.map((card, index) => (
              <FadeIn key={card.title} delay={index * 0.08}>
                <article className="h-full rounded-[28px] border border-[var(--line)] bg-[var(--panel)] p-6 transition hover:border-[var(--line-strong)] hover:bg-[var(--panel-strong)]">
                  <div className="mb-10 grid h-11 w-11 place-items-center rounded-2xl border border-[var(--line)] bg-[var(--surface)] text-[var(--accent)]">
                    <card.icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-semibold tracking-[-0.02em] text-[var(--foreground)]">{card.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{card.text}</p>
                </article>
              </FadeIn>
            ))}
          </div>
        </div>
      </Container>
    </section>
  );
}

```

## `src/components/sections/Contact.tsx`
```tsx
import { Github, Linkedin, Mail } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { FadeIn } from "@/components/animation/FadeIn";
import { siteConfig } from "@/lib/site";

export function Contact() {
  return (
    <section id="contact" className="section-space border-t border-[var(--line)]">
      <Container>
        <FadeIn>
          <div className="contact-panel relative overflow-hidden rounded-[36px] border border-[var(--line)] px-6 py-12 sm:px-10 sm:py-16 lg:px-16 lg:py-20">
            <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-[var(--accent)] opacity-[0.08] blur-3xl" />
            <div className="relative z-10 max-w-4xl">
              <div className="mb-5 font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--accent)]">Have a project in mind?</div>
              <h2 className="text-balance text-4xl font-semibold leading-[0.98] tracking-[-0.05em] text-[var(--foreground)] sm:text-6xl lg:text-7xl">
                Let&apos;s build something useful, fast and genuinely intelligent.
              </h2>
              <p className="mt-7 max-w-2xl text-base leading-7 text-[var(--muted)] sm:text-lg">
                Available for AI/RAG freelance projects, AI chatbot integrations, full-stack builds and internship opportunities.
              </p>
              <div className="mt-9 flex flex-wrap gap-3">
                <ButtonLink href={`mailto:${siteConfig.email}`}>
                  <Mail className="h-4 w-4" /> Email me
                </ButtonLink>
                <ButtonLink href={siteConfig.linkedin} external variant="ghost">
                  <Linkedin className="h-4 w-4" /> LinkedIn
                </ButtonLink>
                <ButtonLink href={siteConfig.github} external variant="ghost">
                  <Github className="h-4 w-4" /> GitHub
                </ButtonLink>
              </div>
              <p className="mt-6 text-xs text-[var(--muted)]">
                Replace the placeholder email and LinkedIn URL in <code className="font-mono text-[var(--foreground)]">src/lib/site.ts</code> before deployment.
              </p>
            </div>
          </div>
        </FadeIn>
      </Container>
    </section>
  );
}

```

## `src/components/sections/Experience.tsx`
```tsx
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { FadeIn } from "@/components/animation/FadeIn";
import { currentlyExploring, experience } from "@/data/experience";

export function Experience() {
  return (
    <section className="section-space border-t border-[var(--line)]">
      <Container>
        <div className="grid gap-14 lg:grid-cols-[1fr_0.7fr] lg:gap-20">
          <div>
            <SectionHeading eyebrow="Journey" title="Learning by shipping increasingly complex systems." />
            <div className="mt-10 border-t border-[var(--line)]">
              {experience.map((item, index) => (
                <FadeIn key={item.title} delay={index * 0.08}>
                  <div className="grid gap-4 border-b border-[var(--line)] py-7 sm:grid-cols-[150px_1fr]">
                    <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[var(--muted)]">{item.period}</div>
                    <div>
                      <h3 className="text-xl font-semibold tracking-[-0.03em] text-[var(--foreground)]">{item.title}</h3>
                      <div className="mt-1 text-sm text-[var(--accent)]">{item.organization}</div>
                      <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">{item.description}</p>
                    </div>
                  </div>
                </FadeIn>
              ))}
            </div>
          </div>

          <FadeIn className="lg:pt-24">
            <aside className="rounded-[32px] border border-[var(--line)] bg-[var(--panel)] p-7 sm:p-8">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--accent)]">Currently exploring</div>
              <div className="mt-8 space-y-5">
                {currentlyExploring.map((item, index) => (
                  <div key={item} className="flex items-center gap-4 border-b border-[var(--line)] pb-5 last:border-b-0 last:pb-0">
                    <span className="font-mono text-[10px] text-[var(--muted)]">0{index + 1}</span>
                    <span className="text-base text-[var(--foreground)]">{item}</span>
                  </div>
                ))}
              </div>
            </aside>
          </FadeIn>
        </div>
      </Container>
    </section>
  );
}

```

## `src/components/sections/Hero.tsx`
```tsx
"use client";

import { useLayoutEffect, useRef } from "react";
import { ArrowDown, Github, Sparkles } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { MagneticButton } from "@/components/animation/MagneticButton";
import { TextReveal } from "@/components/animation/TextReveal";
import { gsap } from "@/lib/gsap";
import { siteConfig } from "@/lib/site";

const nodes = [
  { x: 46, y: 52, label: "LLM" },
  { x: 23, y: 24, label: "RAG" },
  { x: 77, y: 24, label: "TOOLS" },
  { x: 81, y: 72, label: "API" },
  { x: 19, y: 75, label: "DATA" },
];

export function Hero() {
  const root = useRef<HTMLElement>(null);
  const visual = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (!root.current || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        "[data-hero-fade]",
        { opacity: 0, y: 18 },
        { opacity: 1, y: 0, duration: 0.9, delay: 0.75, stagger: 0.08, ease: "power3.out" },
      );

      if (visual.current) {
        gsap.to(visual.current, {
          yPercent: 12,
          rotate: 1.8,
          ease: "none",
          scrollTrigger: {
            trigger: root.current,
            start: "top top",
            end: "bottom top",
            scrub: 1,
          },
        });
      }

      gsap.to("[data-orbit]", {
        rotate: 360,
        transformOrigin: "50% 50%",
        duration: 22,
        ease: "none",
        repeat: -1,
      });
    }, root);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={root} id="top" className="relative min-h-screen overflow-hidden pt-28 sm:pt-32">
      <div className="hero-grid absolute inset-0 -z-20" />
      <div className="hero-vignette absolute inset-0 -z-10" />

      <Container className="relative flex min-h-[calc(100vh-7rem)] flex-col justify-between pb-8 sm:pb-12">
        <div className="grid flex-1 items-center gap-12 py-10 lg:grid-cols-[1.15fr_0.85fr] lg:py-16">
          <div className="max-w-5xl">
            <div
              data-hero-fade
              className="mb-7 inline-flex items-center gap-2 rounded-full border border-[var(--line)] bg-[var(--panel)] px-3.5 py-2 font-mono text-[10px] uppercase tracking-[0.16em] text-[var(--muted)] backdrop-blur"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--accent)] opacity-50" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--accent)]" />
              </span>
              {siteConfig.availability}
            </div>

            <p data-hero-fade className="mb-4 font-mono text-xs uppercase tracking-[0.22em] text-[var(--muted)]">
              {siteConfig.name} · {siteConfig.role}
            </p>

            <h1 className="max-w-[980px] text-[clamp(3.25rem,8.5vw,8.6rem)] font-semibold leading-[0.88] tracking-[-0.065em] text-[var(--foreground)]">
              <TextReveal text="BUILDING" delay={0.1} />
              <br />
              <span className="text-[var(--muted-strong)]">
                <TextReveal text="INTELLIGENT" delay={0.2} />
              </span>
              <br />
              <TextReveal text="SYSTEMS." delay={0.3} />
            </h1>

            <div className="mt-8 grid max-w-3xl gap-6 sm:grid-cols-[1fr_auto] sm:items-end">
              <p data-hero-fade className="max-w-2xl text-base leading-7 text-[var(--muted)] sm:text-lg">
                I build AI agents, RAG systems, business automation and polished full-stack products that move from prototype to usable software.
              </p>
              <div data-hero-fade className="flex flex-wrap gap-3">
                <MagneticButton>
                  <ButtonLink href="#work">View my work</ButtonLink>
                </MagneticButton>
                <MagneticButton>
                  <ButtonLink href={siteConfig.github} external variant="ghost">
                    <Github className="h-4 w-4" /> GitHub
                  </ButtonLink>
                </MagneticButton>
                <MagneticButton>
                  <ButtonLink href="#contact" variant="ghost">Hire me</ButtonLink>
                </MagneticButton>
              </div>
            </div>

            <div data-hero-fade className="mt-8 flex flex-wrap gap-x-5 gap-y-2 font-mono text-[10px] uppercase tracking-[0.16em] text-[var(--muted)]">
              <span>RAG</span><span>•</span><span>AGENTIC AI</span><span>•</span><span>LANGGRAPH</span><span>•</span><span>FASTAPI</span><span>•</span><span>NEXT.JS</span>
            </div>
          </div>

          <div ref={visual} className="relative mx-auto hidden aspect-square w-full max-w-[560px] lg:block">
            <div className="absolute inset-[7%] rounded-full border border-[var(--line)] bg-[radial-gradient(circle_at_50%_50%,rgba(117,245,181,0.07),transparent_62%)]" />
            <div data-orbit className="absolute inset-[14%] rounded-full border border-dashed border-[var(--line-strong)] opacity-70" />
            <div className="absolute inset-[25%] rounded-full border border-[var(--line)] bg-[var(--panel)] shadow-[0_0_100px_rgba(117,245,181,0.08)] backdrop-blur-xl" />

            <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" aria-hidden>
              {nodes.slice(1).map((node, index) => (
                <line key={index} x1="46" y1="52" x2={node.x} y2={node.y} stroke="currentColor" strokeWidth="0.22" className="text-[var(--line-strong)]" />
              ))}
            </svg>

            {nodes.map((node, index) => (
              <div
                key={node.label}
                className="absolute -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${node.x}%`, top: `${node.y}%` }}
              >
                <div className={index === 0 ? "hero-node hero-node-main" : "hero-node"}>
                  {index === 0 ? <Sparkles className="mb-2 h-5 w-5" /> : null}
                  <span>{node.label}</span>
                </div>
              </div>
            ))}

            <div className="absolute bottom-[7%] left-1/2 -translate-x-1/2 rounded-full border border-[var(--line)] bg-[var(--nav)] px-4 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--muted)] backdrop-blur">
              Query → Retrieve → Reason → Act
            </div>
          </div>
        </div>

        <div data-hero-fade className="flex items-center justify-between border-t border-[var(--line)] pt-5 text-xs text-[var(--muted)]">
          <span className="font-mono uppercase tracking-[0.18em]">Scroll to explore</span>
          <ArrowDown className="h-4 w-4 animate-bounce" />
        </div>
      </Container>
    </section>
  );
}

```

## `src/components/sections/Projects.tsx`
```tsx
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { ProjectShowcase } from "@/components/projects/ProjectShowcase";
import { projects } from "@/data/projects";

export function Projects() {
  return (
    <section id="work" className="section-space border-t border-[var(--line)]">
      <Container>
        <div className="mb-12 flex flex-col gap-8 lg:mb-16 lg:flex-row lg:items-end lg:justify-between">
          <SectionHeading
            eyebrow="Selected work"
            title="Projects built as case studies, not logo collections."
            description="Each project explains the problem, engineering decisions, architecture and outcome — because the proof is in how the system works."
          />
          <div className="max-w-sm font-mono text-[10px] uppercase leading-5 tracking-[0.16em] text-[var(--muted)]">
            03 featured builds · RAG · agents · automation · full-stack
          </div>
        </div>
        <ProjectShowcase projects={projects.filter((project) => project.featured)} />
      </Container>
    </section>
  );
}

```

## `src/components/sections/Services.tsx`
```tsx
import { ArrowUpRight } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { FadeIn } from "@/components/animation/FadeIn";
import { services } from "@/data/skills";

export function Services() {
  return (
    <section id="services" className="section-space border-t border-[var(--line)]">
      <Container>
        <SectionHeading
          eyebrow="Services"
          title="From AI prototypes to client-ready digital products."
          description="Services are deliberately focused around the areas where AI engineering and modern web development create measurable business value."
        />

        <div className="mt-12 border-t border-[var(--line)] lg:mt-16">
          {services.map((service, index) => (
            <FadeIn key={service.number} delay={Math.min(index * 0.04, 0.15)}>
              <article className="service-row group grid gap-4 border-b border-[var(--line)] py-7 transition sm:grid-cols-[80px_1fr_auto] sm:items-center sm:py-9">
                <span className="font-mono text-xs tracking-[0.2em] text-[var(--accent)]">{service.number}</span>
                <div>
                  <h3 className="text-xl font-semibold tracking-[-0.03em] text-[var(--foreground)] sm:text-2xl">{service.title}</h3>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--muted)] sm:text-base">{service.description}</p>
                </div>
                <ArrowUpRight className="hidden h-5 w-5 text-[var(--muted)] transition duration-300 group-hover:-translate-y-1 group-hover:translate-x-1 group-hover:text-[var(--foreground)] sm:block" />
              </article>
            </FadeIn>
          ))}
        </div>
      </Container>
    </section>
  );
}

```

## `src/components/sections/Skills.tsx`
```tsx
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { FadeIn } from "@/components/animation/FadeIn";
import { skillGroups } from "@/data/skills";

export function Skills() {
  return (
    <section id="stack" className="section-space border-t border-[var(--line)]">
      <Container>
        <div className="grid gap-12 lg:grid-cols-[0.75fr_1.25fr] lg:gap-20">
          <SectionHeading
            eyebrow="AI engineering stack"
            title="A focused stack for retrieval, agents and product delivery."
            description="I group technologies by the problems they solve instead of presenting a wall of logos."
          />

          <div className="grid gap-4 sm:grid-cols-2">
            {skillGroups.map((group, index) => (
              <FadeIn key={group.title} delay={index * 0.06}>
                <div className="h-full rounded-[28px] border border-[var(--line)] bg-[var(--panel)] p-6 sm:p-7">
                  <div className="mb-6 font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--accent)]">{group.title}</div>
                  <div className="flex flex-wrap gap-2.5">
                    {group.items.map((item) => (
                      <span key={item} className="rounded-full border border-[var(--line)] bg-[var(--surface)] px-3.5 py-2 text-sm text-[var(--foreground)]">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </Container>
    </section>
  );
}

```

## `src/components/ui/Badge.tsx`
```tsx
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Badge({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-[var(--line)] bg-[var(--panel)] px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-[var(--muted)] backdrop-blur",
        className,
      )}
    >
      {children}
    </span>
  );
}

```

## `src/components/ui/ButtonLink.tsx`
```tsx
import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";

export function ButtonLink({
  href,
  children,
  variant = "primary",
  external = false,
  className,
}: {
  href: string;
  children: ReactNode;
  variant?: "primary" | "ghost";
  external?: boolean;
  className?: string;
}) {
  const styles = cn(
    "group inline-flex min-h-12 items-center justify-center gap-2 rounded-full border px-5 text-sm font-medium transition duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--background)]",
    variant === "primary"
      ? "border-[var(--foreground)] bg-[var(--foreground)] text-[var(--background)] hover:-translate-y-0.5 hover:shadow-[0_14px_45px_rgba(117,245,181,0.15)]"
      : "border-[var(--line)] bg-[var(--panel)] text-[var(--foreground)] hover:border-[var(--line-strong)] hover:bg-[var(--panel-strong)]",
    className,
  );

  if (external) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className={styles}>
        {children}
        <ArrowUpRight className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
      </a>
    );
  }

  return (
    <Link href={href} className={styles}>
      {children}
      <ArrowUpRight className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
    </Link>
  );
}

```

## `src/components/ui/Container.tsx`
```tsx
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Container({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mx-auto w-full max-w-[1380px] px-5 sm:px-8 lg:px-12", className)}>
      {children}
    </div>
  );
}

```

## `src/components/ui/SectionHeading.tsx`
```tsx
import { cn } from "@/lib/utils";

export function SectionHeading({
  eyebrow,
  title,
  description,
  className,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  className?: string;
}) {
  return (
    <div className={cn("max-w-3xl", className)}>
      <div className="mb-5 flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.24em] text-[var(--muted)]">
        <span className="h-px w-9 bg-[var(--accent)]" />
        {eyebrow}
      </div>
      <h2 className="text-balance text-4xl font-semibold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl lg:text-6xl">
        {title}
      </h2>
      {description ? (
        <p className="mt-6 max-w-2xl text-base leading-7 text-[var(--muted)] sm:text-lg">
          {description}
        </p>
      ) : null}
    </div>
  );
}

```

## `src/components/ui/button.tsx`
```tsx
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-[var(--foreground)] text-[var(--background)] hover:-translate-y-0.5",
        outline: "border border-[var(--line)] bg-[var(--panel)] text-[var(--foreground)] hover:border-[var(--line-strong)]",
        ghost: "text-[var(--foreground)] hover:bg-[var(--panel)]",
      },
      size: {
        default: "h-12 px-5",
        sm: "h-9 px-4 text-xs",
        lg: "h-14 px-6 text-base",
        icon: "size-10",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> & VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}

export { Button, buttonVariants };

```

## `src/data/experience.ts`
```ts
export const experience = [
  {
    period: "2025 — Present",
    title: "AI Engineering Projects",
    organization: "Independent / University",
    description:
      "Building RAG, corrective retrieval, AI agents and full-stack AI products with an emphasis on reliable retrieval and practical automation.",
  },
  {
    period: "Current",
    title: "BS Software Engineering",
    organization: "National University of Modern Languages (NUML)",
    description:
      "Software engineering studies alongside independent specialization in Generative AI, RAG and agentic systems.",
  },
];

export const currentlyExploring = [
  "Agent reliability & evaluation",
  "Context engineering",
  "Multi-agent orchestration",
  "Production RAG observability",
  "AI product UX",
];

```

## `src/data/projects.ts`
```ts
import type { Project } from "@/types/project";

export const projects: Project[] = [
  {
    slug: "lifeops-ai",
    index: "01",
    title: "LifeOps AI",
    eyebrow: "Agentic AI · Life Administration",
    summary:
      "An agentic personal-life administration system that connects RAG, Google Calendar, Gmail intelligence and action-taking workflows.",
    description:
      "LifeOps AI is designed as a practical agentic assistant: it understands user intent, retrieves personal knowledge, reasons over tasks and can execute supported actions through connected services.",
    year: "2026",
    featured: true,
    image: "/projects/lifeops-ai.svg",
    stack: [
      "LangGraph",
      "FastAPI",
      "PostgreSQL",
      "pgvector",
      "React",
      "TypeScript",
      "Auth0",
      "Google APIs",
      "Docker",
    ],
    links: [
      {
        label: "GitHub",
        href: "https://github.com/Touqeer3417/life-ops-",
        type: "github",
      },
    ],
    problem:
      "Life-admin tasks are scattered across calendars, email and notes. Normal chatbots can answer questions, but they cannot reliably retrieve context and complete multi-step actions.",
    solution:
      "Built an agentic architecture with structured tools, RAG retrieval, OAuth-backed Google integrations, persistent application data and workflow routing for calendar and Gmail operations.",
    outcome:
      "A single conversational interface that can move from understanding a request to retrieving context and executing supported life-admin actions with explicit tool boundaries.",
    architecture: [
      "User request",
      "Intent + tool routing",
      "RAG / personal context",
      "LangGraph workflow",
      "Calendar / Gmail tools",
      "FastAPI services",
      "PostgreSQL + pgvector",
      "Structured response",
    ],
    highlights: [
      "Calendar event creation, update and deletion workflows",
      "Gmail intelligence and email metadata layer",
      "Parent-child chunking, retrieval and reranking pipeline",
      "Auth0 authentication and encrypted OAuth token handling",
    ],
    metrics: [
      { label: "Core agents", value: "Calendar + Gmail" },
      { label: "Architecture", value: "Agentic RAG" },
      { label: "Backend", value: "FastAPI" },
    ],
  },
  {
    slug: "corrective-rag",
    index: "02",
    title: "Corrective RAG",
    eyebrow: "RAG · Retrieval Reliability",
    summary:
      "A corrective retrieval pipeline that detects weak context, rewrites queries, searches again and reranks evidence before answering.",
    description:
      "A production-oriented RAG experiment focused on the failure mode that matters most: what happens when first-pass retrieval is irrelevant or incomplete.",
    year: "2026",
    featured: true,
    image: "/projects/corrective-rag.svg",
    stack: [
      "LangGraph",
      "LangChain",
      "Qdrant",
      "BM25",
      "Reranking",
      "FastAPI",
      "React",
      "Docker",
    ],
    links: [
      {
        label: "GitHub",
        href: "https://github.com/Touqeer3417/corrective-rag-",
        type: "github",
      },
    ],
    problem:
      "Conventional RAG can produce confident but poorly grounded answers when retrieval returns irrelevant documents or misses the right evidence.",
    solution:
      "Combined dense + BM25 hybrid retrieval with document grading, conditional routing, query transformation, optional web search, reranking and a corrective retry loop.",
    outcome:
      "A more resilient answering pipeline that explicitly checks retrieval quality before generation and returns grounded answers with citations when evidence is available.",
    architecture: [
      "Query",
      "Hybrid retrieval",
      "Document grading",
      "Relevant?",
      "Query rewrite",
      "Corrective retrieval",
      "Reranking",
      "Grounded answer",
    ],
    highlights: [
      "Dense + lexical hybrid search",
      "Conditional LangGraph correction loop",
      "Query rewrite when evidence is weak",
      "Reranking and citation-aware response generation",
    ],
    metrics: [
      { label: "Retrieval", value: "Hybrid" },
      { label: "Control flow", value: "LangGraph" },
      { label: "Vector DB", value: "Qdrant" },
    ],
  },
  {
    slug: "document-search-rag",
    index: "03",
    title: "Document Search RAG",
    eyebrow: "Document AI · Semantic Search",
    summary:
      "End-to-end document question answering with ingestion, chunking, embeddings, vector search and grounded LLM responses.",
    description:
      "A focused RAG application that turns uploaded documents into searchable knowledge and demonstrates the complete retrieval-to-generation pipeline.",
    year: "2026",
    featured: true,
    image: "/projects/document-rag.svg",
    stack: ["Python", "LangChain", "FAISS", "OpenAI", "Streamlit", "RAGAS"],
    links: [
      {
        label: "GitHub",
        href: "https://github.com/Touqeer3417/End-to-End-Rag-Docuemnt-Search-Project",
        type: "github",
      },
    ],
    problem:
      "Long documents are difficult to search manually, and generic LLM answers are not trustworthy when they are not tied to the source material.",
    solution:
      "Built a document ingestion and semantic retrieval flow using chunking, embeddings, FAISS vector search and context-constrained response generation.",
    outcome:
      "Users can ask natural-language questions against their documents and receive answers based on retrieved passages rather than model memory alone.",
    architecture: [
      "Documents",
      "Parsing",
      "Chunking",
      "Embeddings",
      "FAISS",
      "Retriever",
      "LLM",
      "Answer",
    ],
    highlights: [
      "End-to-end ingestion and retrieval pipeline",
      "Semantic vector search",
      "RAG evaluation workflow",
      "Simple interactive Streamlit interface",
    ],
    metrics: [
      { label: "Search", value: "Semantic" },
      { label: "Vector store", value: "FAISS" },
      { label: "Evaluation", value: "RAGAS" },
    ],
  },
  {
    slug: "business-ai-agent",
    index: "04",
    title: "Business AI Agent",
    eyebrow: "AI Automation · Customer Experience",
    summary:
      "A reusable blueprint for website chat, business knowledge retrieval, lead capture and workflow automation.",
    description:
      "A client-facing AI assistant concept designed for service businesses that need more than a FAQ bot: answers, qualification and structured handoff.",
    year: "2026",
    featured: false,
    image: "/projects/business-agent.svg",
    stack: ["Next.js", "FastAPI", "LangGraph", "RAG", "PostgreSQL", "Webhooks"],
    links: [],
    problem:
      "Many small businesses lose leads because website visitors cannot quickly get accurate answers or move into a clear booking or inquiry flow.",
    solution:
      "Designed a reusable assistant architecture that indexes business website content, retrieves relevant answers, captures lead details and triggers downstream workflows.",
    outcome:
      "A practical productized-service direction that combines AI chat with measurable business actions instead of stopping at conversation.",
    architecture: [
      "Website visitor",
      "Chat UI",
      "Intent detection",
      "Business RAG",
      "Lead qualification",
      "Workflow trigger",
      "CRM / email handoff",
    ],
    highlights: [
      "Website knowledge ingestion",
      "Lead qualification flow",
      "Human handoff path",
      "Reusable multi-client architecture concept",
    ],
    metrics: [
      { label: "Use case", value: "Lead + support" },
      { label: "Frontend", value: "Next.js" },
      { label: "Automation", value: "Webhooks" },
    ],
  },
];

export function getProject(slug: string) {
  return projects.find((project) => project.slug === slug);
}

```

## `src/data/skills.ts`
```ts
export const skillGroups = [
  {
    title: "AI / LLM",
    items: [
      "RAG",
      "Agentic RAG",
      "AI Agents",
      "Prompt Engineering",
      "Context Engineering",
      "LLM Evaluation",
    ],
  },
  {
    title: "Frameworks",
    items: ["LangChain", "LangGraph", "FastAPI", "Next.js", "React"],
  },
  {
    title: "Retrieval",
    items: ["Qdrant", "FAISS", "pgvector", "BM25", "Hybrid Search", "Reranking"],
  },
  {
    title: "Engineering",
    items: ["TypeScript", "Python", "PostgreSQL", "Docker", "Git/GitHub", "REST APIs"],
  },
];

export const services = [
  {
    number: "01",
    title: "AI Agent & Business Automation",
    description:
      "Agentic workflows that reason over business context, call tools and automate repeatable operational tasks.",
  },
  {
    number: "02",
    title: "Custom RAG Chatbots",
    description:
      "Grounded assistants for business documents, websites, internal knowledge bases and support content.",
  },
  {
    number: "03",
    title: "AI Chatbot Integration",
    description:
      "Embed AI assistants into existing websites with APIs, lead capture, analytics and human handoff flows.",
  },
  {
    number: "04",
    title: "Full-Stack Web Applications",
    description:
      "Modern frontend + backend products using Next.js/React, FastAPI, PostgreSQL and production APIs.",
  },
  {
    number: "05",
    title: "Landing Pages",
    description:
      "Premium responsive landing pages with clear positioning, conversion-focused UX and tasteful motion.",
  },
];

```

## `src/hooks/useMediaQuery.ts`
```ts
"use client";

import { useEffect, useState } from "react";

export function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    const update = () => setMatches(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, [query]);

  return matches;
}

```

## `src/hooks/useReducedMotion.ts`
```ts
"use client";

import { useMediaQuery } from "@/hooks/useMediaQuery";

export function useReducedMotion() {
  return useMediaQuery("(prefers-reduced-motion: reduce)");
}

```

## `src/lib/gsap.ts`
```ts
"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

export { gsap, ScrollTrigger };

```

## `src/lib/site.ts`
```ts
export const siteConfig = {
  name: "Touqeer Ali",
  shortName: "TA",
  role: "AI Engineer & Full-Stack Developer",
  headline: "I build AI agents, RAG systems & intelligent web experiences.",
  description:
    "Portfolio of Touqeer Ali — AI Engineering, RAG, Agentic AI, AI Agents, FastAPI, LangChain, LangGraph and full-stack development.",
  location: "Pakistan",
  availability: "Available for AI/RAG freelance projects and internships",
  email: "your-email@example.com",
  github: "https://github.com/Touqeer3417",
  linkedin: "https://www.linkedin.com/in/your-linkedin",
  resume: "/resume/touqeer-ali-resume.pdf",
} as const;

```

## `src/lib/utils.ts`
```ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

```

## `src/types/project.ts`
```ts
export type ProjectLink = {
  label: string;
  href: string;
  type: "github" | "live";
};

export type Project = {
  slug: string;
  index: string;
  title: string;
  eyebrow: string;
  summary: string;
  description: string;
  year: string;
  featured: boolean;
  image: string;
  stack: string[];
  links: ProjectLink[];
  problem: string;
  solution: string;
  outcome: string;
  architecture: string[];
  highlights: string[];
  metrics: { label: string; value: string }[];
};

```

## `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": [
    "next-env.d.ts",
    ".next/types/**/*.ts",
    "**/*.ts",
    "**/*.tsx"
  ],
  "exclude": ["node_modules"]
}

```
