import { Link } from "@/i18n/navigation";

type ChatBubbleProps = {
  body: string;
  senderId: string;
  createdAt?: string;
  isOwn?: boolean;
  pending?: boolean;
};

export function ChatBubble({ body, senderId, createdAt, isOwn, pending }: ChatBubbleProps) {
  return (
    <div className={`flex ${isOwn ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-[var(--hp-radius-lg)] px-3 py-2 text-sm ${
          isOwn
            ? "bg-[var(--hp-accent-muted)] text-[var(--hp-fg)]"
            : "border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)]"
        } ${pending ? "opacity-60" : ""}`}
      >
        {!isOwn && (
          <Link
            href={`/market/profiles/user/${senderId}`}
            className="mb-1 block font-mono text-[10px] text-[var(--hp-accent)] hover:underline"
          >
            {senderId.slice(0, 8)}
          </Link>
        )}
        <p>{body}</p>
        {createdAt && (
          <p className="mt-1 text-right font-mono text-[10px] text-[var(--hp-fg-muted)]">
            {new Date(createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </p>
        )}
      </div>
    </div>
  );
}
