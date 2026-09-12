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
