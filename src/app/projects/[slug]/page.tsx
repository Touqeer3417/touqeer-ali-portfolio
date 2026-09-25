import type { Metadata } from "next";
import type { ComponentType, ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";
import path from "node:path";
import { readdir } from "node:fs/promises";
import { notFound } from "next/navigation";

import {
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  BrainCircuit,
  Check,
  Database,
  ExternalLink,
  FileSearch,
  Layers3,
  Search,
  Sparkles,
  Workflow,
} from "lucide-react";

import { GitHubIcon } from "@/components/icons/BrandIcons";
import { FadeIn } from "@/components/animation/FadeIn";
import { Container } from "@/components/ui/Container";
import { Badge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { projects, getProject } from "@/data/projects";

/* =========================================================
   CONFIG
========================================================= */

const DOCUMENT_PROJECT_SLUG = "document-search-rag";

const DOCUMENT_RAG_LIVE_URL =
  "https://agentic-rag-knowledge-assistant.streamlit.app/";

const SUPPORTED_IMAGE_TYPES = [
  ".png",
  ".jpg",
  ".jpeg",
  ".webp",
  ".avif",
];

const SCREENSHOT_FILE_ORDER = [
  "first",
  "second",
  "third",
];

const DOCUMENT_ARCHITECTURE_DETAILS: Record<string, string> = {
  Documents: "Source files enter the knowledge pipeline.",
  Parsing: "Readable text is extracted from the documents.",
  Chunking: "Text is split into smaller retrievable units.",
  Embeddings: "Chunks are encoded as semantic vectors.",
  FAISS: "Vectors are indexed for fast similarity search.",
  Retriever: "Relevant chunks are selected for the user query.",
  LLM: "The model receives the retrieved context for generation.",
  Answer: "A response is returned from the retrieved evidence.",
};

const DOCUMENT_HIGHLIGHT_DETAILS: Record<string, string> = {
  "End-to-end ingestion and retrieval pipeline":
    "The project covers the full path from raw documents to retrieved context and a final answer.",
  "Semantic vector search":
    "Embeddings and FAISS match relevant content by meaning instead of relying only on exact keywords.",
  "RAG evaluation workflow":
    "RAGAS is part of the stack so retrieval and generation quality can be evaluated systematically.",
  "Simple interactive Streamlit interface":
    "The RAG pipeline is exposed through a usable application rather than remaining a notebook-only experiment.",
};

const DOCUMENT_CAPABILITIES = [
  {
    title: "RAG architecture",
    text: "Designing a complete retrieval-to-generation pipeline rather than a single LLM prompt.",
  },
  {
    title: "Retrieval systems",
    text: "Working with chunking, embeddings, semantic search, FAISS, and context selection.",
  },
  {
    title: "Evaluation mindset",
    text: "Treating answer quality as something to measure through a dedicated RAG evaluation workflow.",
  },
  {
    title: "Product delivery",
    text: "Turning the AI pipeline into a deployed interface that people can actually use and test.",
  },
];

/* =========================================================
   SCREENSHOT DISCOVERY
========================================================= */

function sortScreenshotFiles(files: string[]) {
  return [...files].sort((a, b) => {
    const aName = path.parse(a).name.toLowerCase();
    const bName = path.parse(b).name.toLowerCase();

    const aIndex = SCREENSHOT_FILE_ORDER.findIndex((word) =>
      aName.includes(word)
    );

    const bIndex = SCREENSHOT_FILE_ORDER.findIndex((word) =>
      bName.includes(word)
    );

    const safeA = aIndex === -1 ? 999 : aIndex;
    const safeB = bIndex === -1 ? 999 : bIndex;

    if (safeA !== safeB) {
      return safeA - safeB;
    }

    return a.localeCompare(b, undefined, {
      numeric: true,
      sensitivity: "base",
    });
  });
}

async function getProjectScreenshots(
  slug: string
): Promise<string[]> {
  if (slug !== DOCUMENT_PROJECT_SLUG) {
    return [];
  }

  try {
    const publicRoot = path.join(process.cwd(), "public");

    const entries = await readdir(publicRoot, {
      withFileTypes: true,
    });

    const directories = entries.filter(
      (entry) => entry.isDirectory()
    );

    const folderCandidates: Array<{
      folder: string;
      files: string[];
      score: number;
    }> = [];

    for (const directory of directories) {
      try {
        const files = await readdir(
          path.join(publicRoot, directory.name)
        );

        const imageFiles = files.filter((file) =>
          SUPPORTED_IMAGE_TYPES.includes(
            path.extname(file).toLowerCase()
          )
        );

        if (imageFiles.length === 0) {
          continue;
        }

        const normalizedFolder = directory.name
          .toLowerCase()
          .replaceAll("_", " ")
          .replaceAll("-", " ");

        const orderedMatches =
          SCREENSHOT_FILE_ORDER.filter((word) =>
            imageFiles.some((file) =>
              path
                .parse(file)
                .name
                .toLowerCase()
                .includes(word)
            )
          ).length;

        let score = orderedMatches * 100;

        if (
          normalizedFolder.includes("document") ||
          normalizedFolder.includes("doucment") ||
          normalizedFolder.includes("docuemnt")
        ) {
          score += 30;
        }

        if (
          normalizedFolder.includes("screen") ||
          normalizedFolder.includes("screenshot")
        ) {
          score += 20;
        }

        if (normalizedFolder.includes("end to end")) {
          score += 10;
        }

        folderCandidates.push({
          folder: directory.name,
          files: imageFiles,
          score,
        });
      } catch {
        // Ignore unreadable public subfolders.
      }
    }

    const bestFolder = folderCandidates
      .filter((candidate) => candidate.score >= 200)
      .sort((a, b) => b.score - a.score)[0];

    if (!bestFolder) {
      return [];
    }

    return sortScreenshotFiles(bestFolder.files)
      .slice(0, 3)
      .map(
        (file) => `/${bestFolder.folder}/${file}`
      );
  } catch {
    return [];
  }
}

/* =========================================================
   STATIC PARAMS
========================================================= */

export function generateStaticParams() {
  return projects.map((project) => ({
    slug: project.slug,
  }));
}

/* =========================================================
   METADATA
========================================================= */

export async function generateMetadata({
  params,
}: {
  params: Promise<{
    slug: string;
  }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const project = getProject(slug);

  if (!project) {
    return {};
  }

  return {
    title: project.title,
    description: project.summary,
    openGraph: {
      title: project.title,
      description: project.summary,
      images: [
        {
          url: project.image,
        },
      ],
    },
  };
}

/* =========================================================
   PAGE
========================================================= */

export default async function ProjectPage({
  params,
}: {
  params: Promise<{
    slug: string;
  }>;
}) {
  const { slug } = await params;
  const project = getProject(slug);

  if (!project) {
    notFound();
  }

  const isDocumentRag = slug === DOCUMENT_PROJECT_SLUG;
  const screenshots = await getProjectScreenshots(slug);

  const githubLink = project.links.find(
    (link) => link.type === "github"
  );

  const projectLiveLink = project.links.find(
    (link) => link.type === "live"
  );

  const liveHref = isDocumentRag
    ? DOCUMENT_RAG_LIVE_URL
    : projectLiveLink?.href;

  const eyebrow = isDocumentRag
    ? "AI Engineering · RAG · Document Intelligence"
    : project.eyebrow;

  const heroDescription = isDocumentRag
    ? "A deployed document-intelligence application that turns source files into searchable knowledge using semantic retrieval and context-grounded LLM generation."
    : project.description;

  const challengeHeading = isDocumentRag
    ? "Finding the right answer inside long documents is still work."
    : "The problem worth solving.";

  const solutionHeading = isDocumentRag
    ? "Retrieve first. Generate from evidence."
    : "A focused path to the solution.";

  const architectureHeading = isDocumentRag
    ? "How a document becomes a grounded answer."
    : "How the system flows.";

  const outcomeHeading = isDocumentRag
    ? "A complete retrieval-to-generation product."
    : "What the project delivered.";

  const snapshotItems = isDocumentRag
    ? [
        ...project.metrics.map((metric) => ({
          label: metric.label,
          value: metric.value,
        })),
        {
          label: "Status",
          value: "Live · Deployed",
        },
      ]
    : project.metrics.map((metric) => ({
        label: metric.label,
        value: metric.value,
      }));

  return (
    <article className="overflow-hidden pb-24 pt-28 sm:pt-32 lg:pt-36">
      {/* =====================================================
          BACK
      ====================================================== */}

      <Container>
        <FadeIn>
          <Link
            href="/#work"
            className="
              group mb-8 inline-flex items-center gap-2
              rounded-full border border-(--line)
              bg-(--panel) px-4 py-2
              text-xs font-medium text-(--body-copy)
              backdrop-blur-xl transition duration-300
              hover:border-(--line-strong)
              hover:text-(--foreground)
            "
          >
            <ArrowLeft className="h-3.5 w-3.5 transition-transform group-hover:-translate-x-1" />
            Back to projects
          </Link>
        </FadeIn>
      </Container>

      {/* =====================================================
          01 — HERO
      ====================================================== */}

      <section>
        <Container>
          <div
            className="
              relative overflow-hidden rounded-4xl
              border border-(--line) bg-(--panel)
              shadow-[0_28px_100px_rgba(0,0,0,0.08)]
            "
          >
            <div
              aria-hidden
              className="
                pointer-events-none absolute -right-24 -top-40
                h-96 w-96 rounded-full
                bg-(--accent-soft) blur-3xl
              "
            />

            <div
              aria-hidden
              className="
                pointer-events-none absolute -bottom-48 -left-24
                h-80 w-80 rounded-full
                bg-(--accent-soft) opacity-50 blur-3xl
              "
            />

            <div className="relative z-10 p-7 sm:p-10 lg:p-14">
              <div className="grid gap-12 lg:grid-cols-[1.14fr_0.86fr] lg:items-end">
                <FadeIn>
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <span
                        className="
                          font-mono text-[10px] uppercase
                          tracking-[0.2em] text-(--accent)
                        "
                      >
                        {eyebrow}
                      </span>

                      <span className="h-1 w-1 rounded-full bg-(--muted)" />

                      <span
                        className="
                          font-mono text-[10px] uppercase
                          tracking-[0.18em] text-(--body-copy)
                        "
                      >
                        {project.year}
                      </span>
                    </div>

                    <h1
                      className="
                        mt-7 max-w-4xl
                        text-5xl font-semibold leading-[0.95]
                        tracking-[-0.055em]
                        text-(--foreground)
                        sm:text-6xl lg:text-[5.25rem]
                      "
                    >
                      {project.title}
                    </h1>

                    <p
                      className="
                        mt-7 max-w-3xl text-base
                        leading-8 text-(--body-copy)
                        sm:text-lg
                      "
                    >
                      {project.summary}
                    </p>
                  </div>
                </FadeIn>

                <FadeIn
                  delay={0.08}
                  className="lg:border-l lg:border-(--line) lg:pl-10"
                >
                  <p
                    className="
                      text-sm leading-7 text-(--body-copy)
                      sm:text-base
                    "
                  >
                    {heroDescription}
                  </p>

                  <div className="mt-7 flex flex-wrap gap-3">
                    {liveHref && (
                      <ButtonLink
                        href={liveHref}
                        external
                        variant="primary"
                      >
                        <ExternalLink className="h-4 w-4" />
                        Explore Live Application
                      </ButtonLink>
                    )}

                    {githubLink && (
                      <ButtonLink
                        href={githubLink.href}
                        external
                        variant="ghost"
                      >
                        <GitHubIcon className="h-4 w-4" />
                        View GitHub
                      </ButtonLink>
                    )}
                  </div>

                  {isDocumentRag && (
                    <div
                      className="
                        mt-6 inline-flex items-center gap-2
                        rounded-full border border-(--line)
                        bg-(--surface) px-3 py-2
                        font-mono text-[9px] uppercase
                        tracking-[0.14em] text-(--body-copy)
                      "
                    >
                      <span
                        className="
                          h-2 w-2 rounded-full bg-(--accent)
                          shadow-[0_0_16px_var(--accent)]
                        "
                      />
                      Deployed application
                    </div>
                  )}
                </FadeIn>
              </div>

              <FadeIn
                delay={0.12}
                className="mt-10 flex flex-wrap gap-2"
              >
                {project.stack.map((technology) => (
                  <Badge key={technology}>
                    {technology}
                  </Badge>
                ))}
              </FadeIn>
            </div>
          </div>
        </Container>
      </section>

      {/* =====================================================
          02 — PROJECT SNAPSHOT
      ====================================================== */}

      <section className="mt-6">
        <Container>
          <FadeIn>
            <div
              className="
                grid gap-px overflow-hidden rounded-3xl
                border border-(--line) bg-(--line)
                sm:grid-cols-2 lg:grid-cols-4
              "
            >
              {snapshotItems.slice(0, 4).map((item) => (
                <div
                  key={`${item.label}-${item.value}`}
                  className="bg-(--background) p-6 sm:p-7"
                >
                  <div
                    className="
                      font-mono text-[9px] uppercase
                      tracking-[0.18em] text-(--body-copy)
                    "
                  >
                    {item.label}
                  </div>

                  <div
                    className="
                      mt-3 text-xl font-semibold
                      tracking-[-0.035em]
                      text-(--foreground)
                    "
                  >
                    {item.value}
                  </div>
                </div>
              ))}
            </div>
          </FadeIn>
        </Container>
      </section>

      {/* =====================================================
          03 + 04 — CHALLENGE / SOLUTION
      ====================================================== */}

      <section className="mt-24">
        <Container>
          <FadeIn className="max-w-3xl">
            <SectionEyebrow>
              Why this project exists
            </SectionEyebrow>

            <h2
              className="
                mt-4 text-4xl font-semibold
                tracking-[-0.045em] text-(--foreground)
                sm:text-5xl
              "
            >
              Search less.
              <br />
              Find evidence faster.
            </h2>
          </FadeIn>

          <div className="mt-10 grid gap-5 lg:grid-cols-2">
            <StoryCard
              number="01"
              eyebrow="The challenge"
              title={challengeHeading}
              text={project.problem}
              icon={Search}
            />

            <StoryCard
              number="02"
              eyebrow="The solution"
              title={solutionHeading}
              text={project.solution}
              icon={BrainCircuit}
              delay={0.08}
            />
          </div>
        </Container>
      </section>

      {/* =====================================================
          05 — PRODUCT SCREENSHOTS
      ====================================================== */}

      {isDocumentRag && screenshots.length > 0 && (
        <section className="mt-24">
          <Container>
            <FadeIn
              className="
                grid gap-8
                lg:grid-cols-[0.8fr_1.2fr]
                lg:items-end
              "
            >
              <div>
                <SectionEyebrow>
                  Working product
                </SectionEyebrow>

                <h2
                  className="
                    mt-4 max-w-xl text-4xl
                    font-semibold leading-none
                    tracking-[-0.045em]
                    text-(--foreground)
                    sm:text-5xl
                  "
                >
                  From RAG pipeline
                  <br />
                  to usable product.
                </h2>
              </div>

              <p
                className="
                  max-w-2xl text-sm leading-7
                  text-(--body-copy)
                  sm:text-base lg:ml-auto
                "
              >
                Real screenshots from the deployed application.
                Each view is shown full-width so the interface,
                queries, and generated responses remain readable.
              </p>
            </FadeIn>

            <div className="mt-10 space-y-7">
              {screenshots[0] && (
                <FadeIn>
                  <ScreenshotCard
                    src={screenshots[0]}
                    alt={`${project.title} search workspace`}
                    index="01"
                    label="Search workspace"
                    priority
                  />
                </FadeIn>
              )}

              {screenshots[1] && (
                <FadeIn delay={0.06}>
                  <ScreenshotCard
                    src={screenshots[1]}
                    alt={`${project.title} generated answer`}
                    index="02"
                    label="Retrieved answer"
                  />
                </FadeIn>
              )}

              {screenshots[2] && (
                <FadeIn delay={0.12}>
                  <ScreenshotCard
                    src={screenshots[2]}
                    alt={`${project.title} document intelligence interface`}
                    index="03"
                    label="Document Q&A flow"
                  />
                </FadeIn>
              )}
            </div>

            {liveHref && (
              <FadeIn delay={0.12}>
                <div
                  className="
                    mt-6 flex flex-col gap-4
                    rounded-2xl border border-(--line)
                    bg-(--panel) p-5
                    sm:flex-row sm:items-center
                    sm:justify-between
                  "
                >
                  <div>
                    <div
                      className="
                        text-sm font-medium
                        text-(--foreground)
                      "
                    >
                      See the complete workflow live
                    </div>

                    <p className="mt-1 text-sm text-(--body-copy)">
                      Open the deployed app and test the
                      document-search experience yourself.
                    </p>
                  </div>

                  <a
                    href={liveHref}
                    target="_blank"
                    rel="noreferrer"
                    className="
                      group inline-flex shrink-0 items-center
                      gap-2 text-sm font-medium text-(--accent)
                    "
                  >
                    Launch live demo
                    <ArrowUpRight
                      className="
                        h-4 w-4 transition-transform
                        group-hover:-translate-y-0.5
                        group-hover:translate-x-0.5
                      "
                    />
                  </a>
                </div>
              </FadeIn>
            )}
          </Container>
        </section>
      )}

      {!isDocumentRag && (
        <section className="mt-24">
          <Container>
            <FadeIn
              className="
                relative aspect-16/8.5 overflow-hidden
                rounded-4xl border border-(--line)
                bg-(--panel)
              "
            >
              <Image
                src={project.image}
                alt={`${project.title} case study visual`}
                fill
                priority
                className="object-cover"
                sizes="100vw"
              />
            </FadeIn>
          </Container>
        </section>
      )}

      {/* =====================================================
          06 — ARCHITECTURE
      ====================================================== */}

      <section className="mt-24">
        <Container>
          <FadeIn
            className="
              grid gap-8
              lg:grid-cols-[0.72fr_1.28fr]
              lg:items-start
            "
          >
            <div className="lg:sticky lg:top-32">
              <SectionEyebrow icon={Workflow}>
                How it works
              </SectionEyebrow>

              <h2
                className="
                  mt-5 max-w-md text-4xl
                  font-semibold leading-none
                  tracking-[-0.045em]
                  text-(--foreground)
                  sm:text-5xl
                "
              >
                {architectureHeading}
              </h2>

              <p
                className="
                  mt-5 max-w-md text-sm leading-7
                  text-(--body-copy) sm:text-base
                "
              >
                Each stage has one clear job: prepare the
                documents, index meaning, retrieve context,
                and generate the final response from that
                context.
              </p>
            </div>

            <div
              className="
                rounded-4xl border border-(--line)
                bg-(--panel) p-4 sm:p-6
              "
            >
              <div className="grid gap-3 sm:grid-cols-2">
                {project.architecture.map((step, index) => (
                  <ArchitectureStep
                    key={`${step}-${index}`}
                    number={String(index + 1).padStart(2, "0")}
                    title={step}
                    description={
                      isDocumentRag
                        ? DOCUMENT_ARCHITECTURE_DETAILS[step]
                        : undefined
                    }
                  />
                ))}
              </div>
            </div>
          </FadeIn>
        </Container>
      </section>

      {/* =====================================================
          07 — ENGINEERING HIGHLIGHTS
      ====================================================== */}

      <section className="mt-24">
        <Container>
          <FadeIn
            className="
              grid gap-8
              lg:grid-cols-[0.78fr_1.22fr]
              lg:items-end
            "
          >
            <div>
              <SectionEyebrow icon={Sparkles}>
                Engineering highlights
              </SectionEyebrow>

              <h2
                className="
                  mt-4 max-w-xl text-4xl
                  font-semibold leading-none
                  tracking-[-0.045em]
                  text-(--foreground)
                  sm:text-5xl
                "
              >
                More than an
                <br />
                LLM text box.
              </h2>
            </div>

            <p
              className="
                max-w-2xl text-sm leading-7
                text-(--body-copy)
                sm:text-base lg:ml-auto
              "
            >
              The value is in the retrieval system around
              the model: document preparation, semantic
              search, context selection, evaluation, and a
              usable interface.
            </p>
          </FadeIn>

          <div className="mt-10 grid gap-4 md:grid-cols-2">
            {project.highlights.map((highlight, index) => (
              <FadeIn
                key={highlight}
                delay={0.05 * index}
                className="
                  group rounded-3xl border border-(--line)
                  bg-(--panel) p-6 transition duration-300
                  hover:-translate-y-1
                  hover:border-(--line-strong)
                "
              >
                <div className="flex items-start gap-4">
                  <span
                    className="
                      grid h-9 w-9 shrink-0 place-items-center
                      rounded-full border border-(--line)
                      bg-(--surface) font-mono text-[9px]
                      text-(--accent)
                    "
                  >
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <div>
                    <h3
                      className="
                        text-base font-semibold
                        tracking-[-0.02em]
                        text-(--foreground)
                      "
                    >
                      {highlight}
                    </h3>

                    {isDocumentRag &&
                      DOCUMENT_HIGHLIGHT_DETAILS[highlight] && (
                        <p
                          className="
                            mt-3 text-sm leading-6
                            text-(--body-copy)
                          "
                        >
                          {DOCUMENT_HIGHLIGHT_DETAILS[highlight]}
                        </p>
                      )}
                  </div>
                </div>
              </FadeIn>
            ))}

            {isDocumentRag && (
              <FadeIn
                delay={0.2}
                className="
                  group rounded-3xl border border-(--line)
                  bg-(--panel) p-6 transition duration-300
                  hover:-translate-y-1
                  hover:border-(--line-strong)
                "
              >
                <div className="flex items-start gap-4">
                  <span
                    className="
                      grid h-9 w-9 shrink-0 place-items-center
                      rounded-full border border-(--line)
                      bg-(--surface) font-mono text-[9px]
                      text-(--accent)
                    "
                  >
                    05
                  </span>

                  <div>
                    <h3
                      className="
                        text-base font-semibold
                        tracking-[-0.02em]
                        text-(--foreground)
                      "
                    >
                      Context-grounded generation
                    </h3>

                    <p
                      className="
                        mt-3 text-sm leading-6
                        text-(--body-copy)
                      "
                    >
                      Retrieved passages are supplied to the
                      model so the answer is based on document
                      context rather than model memory alone.
                    </p>
                  </div>
                </div>
              </FadeIn>
            )}
          </div>
        </Container>
      </section>

      {/* =====================================================
          08 — TECHNOLOGY
      ====================================================== */}

      <section className="mt-24">
        <Container>
          <FadeIn>
            <SectionEyebrow icon={Layers3}>
              Technology
            </SectionEyebrow>

            <h2
              className="
                mt-4 max-w-2xl text-4xl
                font-semibold tracking-[-0.045em]
                text-(--foreground) sm:text-5xl
              "
            >
              A focused stack for
              document intelligence.
            </h2>
          </FadeIn>

          {isDocumentRag ? (
            <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <TechGroup
                title="AI / Orchestration"
                items={["OpenAI", "LangChain"]}
                icon={BrainCircuit}
              />
              <TechGroup
                title="Retrieval"
                items={["FAISS"]}
                icon={Database}
                delay={0.05}
              />
              <TechGroup
                title="Evaluation"
                items={["RAGAS"]}
                icon={Check}
                delay={0.1}
              />
              <TechGroup
                title="Application"
                items={["Python", "Streamlit"]}
                icon={FileSearch}
                delay={0.15}
              />
            </div>
          ) : (
            <FadeIn className="mt-10 rounded-3xl border border-(--line) bg-(--panel) p-7">
              <div className="flex flex-wrap gap-2">
                {project.stack.map((technology) => (
                  <Badge key={technology}>
                    {technology}
                  </Badge>
                ))}
              </div>
            </FadeIn>
          )}
        </Container>
      </section>

      {/* =====================================================
          09 — OUTCOME
      ====================================================== */}

      <section className="mt-24">
        <Container>
          <FadeIn
            className="
              relative overflow-hidden rounded-4xl
              border border-(--line) bg-(--panel)
              p-7 sm:p-10 lg:p-12
            "
          >
            <div
              aria-hidden
              className="
                pointer-events-none absolute -right-20 -top-24
                h-72 w-72 rounded-full
                bg-(--accent-soft) opacity-60 blur-3xl
              "
            />

            <div
              className="
                relative z-10 grid gap-10
                lg:grid-cols-[0.85fr_1.15fr]
                lg:items-start
              "
            >
              <div>
                <SectionEyebrow icon={Check}>
                  Outcome
                </SectionEyebrow>

                <h2
                  className="
                    mt-4 max-w-lg text-4xl
                    font-semibold leading-none
                    tracking-[-0.045em]
                    text-(--foreground)
                    sm:text-5xl
                  "
                >
                  {outcomeHeading}
                </h2>
              </div>

              <div>
                <p
                  className="
                    max-w-2xl text-base leading-8
                    text-(--body-copy)
                  "
                >
                  {project.outcome}
                </p>

                {isDocumentRag && (
                  <div className="mt-7 grid gap-3 sm:grid-cols-3">
                    <OutcomePoint
                      number="01"
                      text="Documents become searchable knowledge."
                    />
                    <OutcomePoint
                      number="02"
                      text="Answers use retrieved passages as context."
                    />
                    <OutcomePoint
                      number="03"
                      text="RAGAS adds an evaluation workflow."
                    />
                  </div>
                )}
              </div>
            </div>
          </FadeIn>
        </Container>
      </section>

      {/* =====================================================
          10 — WHAT THIS DEMONSTRATES
      ====================================================== */}

      {isDocumentRag && (
        <section className="mt-24">
          <Container>
            <FadeIn className="max-w-3xl">
              <SectionEyebrow>
                What this demonstrates
              </SectionEyebrow>

              <h2
                className="
                  mt-4 text-4xl font-semibold
                  tracking-[-0.045em]
                  text-(--foreground)
                  sm:text-5xl
                "
              >
                Designing the system
                <br />
                around the model.
              </h2>

              <p
                className="
                  mt-5 max-w-2xl text-sm leading-7
                  text-(--body-copy) sm:text-base
                "
              >
                The project moves beyond a basic chatbot by
                treating retrieval, context quality,
                evaluation, and product delivery as part of
                the same engineering problem.
              </p>
            </FadeIn>

            <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {DOCUMENT_CAPABILITIES.map((capability, index) => (
                <FadeIn
                  key={capability.title}
                  delay={0.05 * index}
                  className="
                    rounded-3xl border border-(--line)
                    bg-(--panel) p-6
                  "
                >
                  <div
                    className="
                      font-mono text-[9px] uppercase
                      tracking-[0.18em] text-(--accent)
                    "
                  >
                    {String(index + 1).padStart(2, "0")}
                  </div>

                  <h3
                    className="
                      mt-5 text-lg font-semibold
                      tracking-[-0.025em]
                      text-(--foreground)
                    "
                  >
                    {capability.title}
                  </h3>

                  <p
                    className="
                      mt-3 text-sm leading-6
                      text-(--body-copy)
                    "
                  >
                    {capability.text}
                  </p>
                </FadeIn>
              ))}
            </div>
          </Container>
        </section>
      )}

      {/* =====================================================
          PROJECT LINKS
      ====================================================== */}

      {(liveHref || githubLink) && (
        <section className="mt-16">
          <Container>
            <div className="grid gap-3 sm:grid-cols-2">
              {liveHref && (
                <ProjectLinkCard
                  href={liveHref}
                  title="Explore live application"
                  subtitle="Try the deployed document-search experience"
                  icon={ExternalLink}
                />
              )}

              {githubLink && (
                <a
                  href={githubLink.href}
                  target="_blank"
                  rel="noreferrer"
                  className="
                    group flex items-center justify-between
                    rounded-2xl border border-(--line)
                    bg-(--panel) p-5 transition duration-300
                    hover:border-(--line-strong)
                  "
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="
                        grid h-11 w-11 place-items-center
                        rounded-xl border border-(--line)
                        bg-(--surface)
                      "
                    >
                      <GitHubIcon className="h-4 w-4 text-(--foreground)" />
                    </div>

                    <div>
                      <div
                        className="
                          text-sm font-medium
                          text-(--foreground)
                        "
                      >
                        View source code
                      </div>

                      <div className="mt-1 text-xs text-(--body-copy)">
                        Inspect the project implementation
                      </div>
                    </div>
                  </div>

                  <ArrowUpRight
                    className="
                      h-4 w-4 text-(--accent)
                      transition-transform
                      group-hover:-translate-y-0.5
                      group-hover:translate-x-0.5
                    "
                  />
                </a>
              )}
            </div>
          </Container>
        </section>
      )}

      {/* =====================================================
          11 — CTA
      ====================================================== */}

      <section className="mt-24">
        <Container>
          <FadeIn
            className="
              relative overflow-hidden rounded-4xl
              border border-(--line) bg-(--panel)
              p-8 sm:p-12 lg:p-14
            "
          >
            <div
              aria-hidden
              className="
                pointer-events-none absolute -right-20 -top-28
                h-80 w-80 rounded-full
                bg-(--accent-soft) blur-3xl
              "
            />

            <div
              className="
                relative z-10 grid gap-10
                lg:grid-cols-[1fr_auto]
                lg:items-end
              "
            >
              <div className="max-w-3xl">
                <SectionEyebrow>
                  Build with your own knowledge
                </SectionEyebrow>

                <h2
                  className="
                    mt-4 text-4xl font-semibold
                    leading-none tracking-[-0.045em]
                    text-(--foreground)
                    sm:text-5xl
                  "
                >
                  {isDocumentRag
                    ? "Have documents your team should be able to query?"
                    : "Have a product idea worth building?"}
                </h2>

                <p
                  className="
                    mt-5 max-w-2xl text-base
                    leading-7 text-(--body-copy)
                  "
                >
                  {isDocumentRag
                    ? "I build RAG systems, knowledge assistants, AI agents, and document-intelligence applications that turn private information into useful AI experiences."
                    : "I build practical AI applications with a focus on clear product value and reliable engineering."}
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <ButtonLink href="/#contact">
                  Start a conversation
                </ButtonLink>

                {liveHref && (
                  <ButtonLink
                    href={liveHref}
                    external
                    variant="ghost"
                  >
                    View Live Demo
                    <ArrowUpRight className="h-4 w-4" />
                  </ButtonLink>
                )}
              </div>
            </div>
          </FadeIn>
        </Container>
      </section>
    </article>
  );
}

/* =========================================================
   COMPONENTS
========================================================= */

function SectionEyebrow({
  children,
  icon: Icon,
}: {
  children: ReactNode;
  icon?: ComponentType<{
    className?: string;
  }>;
}) {
  return (
    <div
      className="
        inline-flex items-center gap-2
        font-mono text-[10px] uppercase
        tracking-[0.18em] text-(--accent)
      "
    >
      {Icon && <Icon className="h-4 w-4" />}
      {children}
    </div>
  );
}

function StoryCard({
  number,
  eyebrow,
  title,
  text,
  icon: Icon,
  delay = 0,
}: {
  number: string;
  eyebrow: string;
  title: string;
  text: string;
  icon: ComponentType<{
    className?: string;
  }>;
  delay?: number;
}) {
  return (
    <FadeIn
      delay={delay}
      className="
        group relative overflow-hidden rounded-3xl
        border border-(--line) bg-(--panel) p-7
        transition duration-300
        hover:-translate-y-1
        hover:border-(--line-strong)
      "
    >
      <div
        aria-hidden
        className="
          absolute -right-16 -top-16 h-40 w-40
          rounded-full bg-(--accent-soft)
          opacity-0 blur-3xl transition duration-500
          group-hover:opacity-100
        "
      />

      <div className="relative z-10">
        <div className="flex items-center justify-between gap-4">
          <div
            className="
              grid h-11 w-11 place-items-center
              rounded-2xl border border-(--line)
              bg-(--surface)
            "
          >
            <Icon className="h-4 w-4 text-(--accent)" />
          </div>

          <span className="font-mono text-[10px] text-(--body-copy)">
            {number}
          </span>
        </div>

        <div
          className="
            mt-8 font-mono text-[9px] uppercase
            tracking-[0.18em] text-(--accent)
          "
        >
          {eyebrow}
        </div>

        <h3
          className="
            mt-3 max-w-xl text-2xl font-semibold
            leading-tight tracking-[-0.035em]
            text-(--foreground)
          "
        >
          {title}
        </h3>

        <p
          className="
            mt-4 max-w-xl text-sm leading-7
            text-(--body-copy) sm:text-[15px]
          "
        >
          {text}
        </p>
      </div>
    </FadeIn>
  );
}

function ScreenshotCard({
  src,
  alt,
  index,
  label,
  priority = false,
}: {
  src: string;
  alt: string;
  index: string;
  label: string;
  priority?: boolean;
}) {
  return (
    <figure>
      <div
        className="
          group relative aspect-video w-full overflow-hidden
          rounded-3xl border border-(--line)
          bg-(--panel)
          shadow-[0_22px_70px_rgba(0,0,0,0.08)]
        "
      >
        <Image
          src={src}
          alt={alt}
          fill
          priority={priority}
          className="
            object-contain object-center
            transition duration-700
            group-hover:scale-[1.006]
          "
          sizes="(max-width: 1024px) 100vw, 1200px"
        />
      </div>

      <figcaption
        className="
          mt-3 flex items-center justify-between
          gap-4 px-1
        "
      >
        <span
          className="
            text-sm font-medium text-(--foreground)
          "
        >
          {label}
        </span>

        <span
          className="
            font-mono text-[9px] uppercase
            tracking-[0.18em] text-(--body-copy)
          "
        >
          {index}
        </span>
      </figcaption>
    </figure>
  );
}

function ArchitectureStep({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description?: string;
}) {
  return (
    <div
      className="
        group relative rounded-2xl border border-(--line)
        bg-(--surface) p-5 transition duration-300
        hover:border-(--line-strong)
      "
    >
      <div className="flex items-center justify-between gap-4">
        <span
          className="
            grid h-9 w-9 place-items-center rounded-full
            border border-(--line) bg-(--background)
            font-mono text-[9px] text-(--accent)
          "
        >
          {number}
        </span>

        <ArrowRight
          className="
            h-4 w-4 text-(--body-copy)
            transition-transform group-hover:translate-x-1
          "
        />
      </div>

      <h3
        className="
          mt-5 text-base font-semibold
          tracking-[-0.025em] text-(--foreground)
        "
      >
        {title}
      </h3>

      {description && (
        <p className="mt-2 text-sm leading-6 text-(--body-copy)">
          {description}
        </p>
      )}
    </div>
  );
}

function TechGroup({
  title,
  items,
  icon: Icon,
  delay = 0,
}: {
  title: string;
  items: string[];
  icon: ComponentType<{
    className?: string;
  }>;
  delay?: number;
}) {
  return (
    <FadeIn
      delay={delay}
      className="
        rounded-3xl border border-(--line)
        bg-(--panel) p-6
      "
    >
      <div
        className="
          grid h-11 w-11 place-items-center
          rounded-2xl border border-(--line)
          bg-(--surface)
        "
      >
        <Icon className="h-4 w-4 text-(--accent)" />
      </div>

      <div
        className="
          mt-6 font-mono text-[9px] uppercase
          tracking-[0.18em] text-(--body-copy)
        "
      >
        {title}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {items.map((item) => (
          <Badge key={item}>{item}</Badge>
        ))}
      </div>
    </FadeIn>
  );
}

function OutcomePoint({
  number,
  text,
}: {
  number: string;
  text: string;
}) {
  return (
    <div
      className="
        rounded-2xl border border-(--line)
        bg-(--surface) p-4
      "
    >
      <div className="font-mono text-[9px] text-(--accent)">
        {number}
      </div>

      <p
        className="
          mt-3 text-sm leading-6
          text-(--foreground)
        "
      >
        {text}
      </p>
    </div>
  );
}

function ProjectLinkCard({
  href,
  title,
  subtitle,
  icon: Icon,
}: {
  href: string;
  title: string;
  subtitle: string;
  icon: ComponentType<{
    className?: string;
  }>;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="
        group flex items-center justify-between
        rounded-2xl border border-(--line)
        bg-(--panel) p-5 transition duration-300
        hover:border-(--line-strong)
      "
    >
      <div className="flex items-center gap-3">
        <div
          className="
            grid h-11 w-11 place-items-center
            rounded-xl border border-(--line)
            bg-(--surface)
          "
        >
          <Icon className="h-4 w-4 text-(--accent)" />
        </div>

        <div>
          <div
            className="
              text-sm font-medium
              text-(--foreground)
            "
          >
            {title}
          </div>

          <div className="mt-1 text-xs text-(--body-copy)">
            {subtitle}
          </div>
        </div>
      </div>

      <ArrowUpRight
        className="
          h-4 w-4 text-(--accent)
          transition-transform
          group-hover:-translate-y-0.5
          group-hover:translate-x-0.5
        "
      />
    </a>
  );
}
