import type { SVGProps } from "react";

type BrandIconProps = SVGProps<SVGSVGElement>;

export function GitHubIcon({
  className,
  ...props
}: BrandIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      <path d="M12 .5C5.73.5.75 5.62.75 12c0 5.1 3.44 9.42 8.2 10.95.6.12.82-.27.82-.59 0-.29-.01-1.06-.02-2.08-3.34.74-4.04-1.64-4.04-1.64-.55-1.42-1.33-1.8-1.33-1.8-1.09-.76.08-.75.08-.75 1.2.09 1.84 1.26 1.84 1.26 1.07 1.87 2.81 1.33 3.5 1.02.11-.79.42-1.33.76-1.64-2.66-.31-5.47-1.36-5.47-6.04 0-1.34.47-2.43 1.24-3.29-.12-.31-.54-1.56.12-3.24 0 0 1.01-.33 3.3 1.26a11.2 11.2 0 0 1 6 0c2.29-1.59 3.3-1.26 3.3-1.26.66 1.68.24 2.93.12 3.24.77.86 1.24 1.95 1.24 3.29 0 4.69-2.81 5.72-5.49 6.03.43.38.82 1.13.82 2.28 0 1.65-.02 2.98-.02 3.38 0 .33.22.71.83.59 4.75-1.53 8.19-5.85 8.19-10.95C23.25 5.62 18.27.5 12 .5Z" />
    </svg>
  );
}

export function LinkedInIcon({
  className,
  ...props
}: BrandIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      <path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28ZM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12ZM7.12 20.45H3.55V9h3.57v11.45Z" />
    </svg>
  );
}