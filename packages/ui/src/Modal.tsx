"use client";

import { useEffect, type ReactNode } from "react";
import { Button } from "./Button";

type ModalProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
};

export function Modal({ open, onClose, title, children, footer }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close overlay"
        className="absolute inset-0 bg-[var(--hp-overlay)]"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        className="relative z-10 w-full max-w-lg rounded-lg border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)] shadow-[var(--hp-shadow)]"
      >
        {title && (
          <div className="flex items-center justify-between border-b border-[var(--hp-border)] px-4 py-3">
            <h2 className="text-lg font-semibold text-[var(--hp-fg)]">{title}</h2>
            <Button variant="secondary" type="button" onClick={onClose} className="px-2 py-1">
              ✕
            </Button>
          </div>
        )}
        <div className="px-4 py-4 text-[var(--hp-fg)]">{children}</div>
        {footer && <div className="border-t border-[var(--hp-border)] px-4 py-3">{footer}</div>}
      </div>
    </div>
  );
}
