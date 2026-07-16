import type { ReactNode } from "react";
import { Container } from "./Container";

type PageShellProps = {
  children: ReactNode;
  className?: string;
  size?: "default" | "narrow" | "wide";
  noPadding?: boolean;
};

export function PageShell({ children, className = "", size = "default", noPadding = false }: PageShellProps) {
  return (
    <div className={`min-h-[calc(100vh-64px)] ${noPadding ? "" : "py-8 md:py-12"} ${className}`}>
      <Container size={size}>{children}</Container>
    </div>
  );
}
