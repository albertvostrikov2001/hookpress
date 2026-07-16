import type { HTMLAttributes, ReactNode } from "react";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  hover?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
};

const paddingClasses = {
  none: "",
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
};

export function Card({
  children,
  hover = false,
  padding = "md",
  className = "",
  ...props
}: CardProps) {
  return (
    <div
      className={`rounded-[var(--hp-radius-lg)] border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)] shadow-[var(--hp-shadow)] ${paddingClasses[padding]} ${hover ? "transition-all duration-200 hover:border-[var(--hp-accent)]/30 hover:shadow-[var(--hp-shadow-lg)]" : ""} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
