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
