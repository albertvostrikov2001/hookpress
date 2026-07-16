"use client";

import { Link } from "@/i18n/navigation";
import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

type NavMenuItem = {
  href: string;
  label: string;
};

type NavMenuAction = {
  label: string;
  onClick: () => void;
};

type NavMenuProps = {
  label: string;
  items: NavMenuItem[];
  pathname: string;
  active?: boolean;
  align?: "start" | "end";
  triggerClassName?: string;
  children?: ReactNode;
  actions?: NavMenuAction[];
};

export function NavMenu({
  label,
  items,
  pathname,
  active = false,
  align = "start",
  triggerClassName = "",
  children,
  actions = [],
}: NavMenuProps) {
  const menuId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const [menuStyle, setMenuStyle] = useState<{ top: number; left: number; minWidth: number } | null>(
    null,
  );

  const childActive = items.some((item) => pathname.startsWith(item.href));

  function updateMenuPosition() {
    const button = buttonRef.current;
    if (!button) return;
    const rect = button.getBoundingClientRect();
    const minWidth = Math.max(rect.width, 176);
    const left = align === "end" ? rect.right - minWidth : rect.left;
    setMenuStyle({ top: rect.bottom + 6, left, minWidth });
  }

  useEffect(() => {
    if (!open) return;
    updateMenuPosition();
    function onPointerDown(e: PointerEvent) {
      const target = e.target as Node;
      if (rootRef.current?.contains(target)) return;
      if (document.getElementById(menuId)?.contains(target)) return;
      setOpen(false);
    }
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    function onLayoutChange() {
      updateMenuPosition();
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    window.addEventListener("resize", onLayoutChange);
    window.addEventListener("scroll", onLayoutChange, true);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("resize", onLayoutChange);
      window.removeEventListener("scroll", onLayoutChange, true);
    };
  }, [open, align, menuId]);

  const menu =
    open && menuStyle ? (
      <div
        id={menuId}
        role="menu"
        style={{
          position: "fixed",
          top: menuStyle.top,
          left: menuStyle.left,
          minWidth: menuStyle.minWidth,
          zIndex: 100,
        }}
        className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)] py-1 shadow-lg"
      >
        {items.map((item) => {
          const itemActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              role="menuitem"
              onClick={() => setOpen(false)}
              className={`block px-3 py-2 text-sm transition ${
                itemActive
                  ? "bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]"
                  : "text-[var(--hp-fg)] hover:bg-[var(--hp-bg-subtle)]"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
        {actions.length > 0 && <div className="my-1 border-t border-[var(--hp-border)]" />}
        {actions.map((action) => (
          <button
            key={action.label}
            type="button"
            role="menuitem"
            onClick={() => {
              setOpen(false);
              action.onClick();
            }}
            className="block w-full px-3 py-2 text-left text-sm text-[var(--hp-fg-muted)] transition hover:bg-[var(--hp-bg-subtle)] hover:text-[var(--hp-fg)]"
          >
            {action.label}
          </button>
        ))}
      </div>
    ) : null;

  return (
    <div ref={rootRef} className="relative shrink-0">
      <button
        ref={buttonRef}
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={(e) => {
          e.stopPropagation();
          setOpen((v) => !v);
        }}
        className={`relative z-10 inline-flex shrink-0 cursor-pointer items-center gap-1 whitespace-nowrap rounded-[var(--hp-radius)] px-2.5 py-2 text-sm font-medium transition ${
          active || childActive
            ? "bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]"
            : "text-[var(--hp-fg-muted)] hover:bg-[var(--hp-bg-subtle)] hover:text-[var(--hp-fg)]"
        } ${triggerClassName}`}
      >
        {children ?? label}
        <span aria-hidden className="pointer-events-none text-[10px] opacity-60">
          ▾
        </span>
      </button>
      {typeof document !== "undefined" && menu ? createPortal(menu, document.body) : null}
    </div>
  );
}
