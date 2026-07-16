"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Badge, Button, Card, EmptyState, Input, SkeletonCard } from "@hookpress/ui";
import { AuthGate } from "@/components/AuthGate";
import { ChatBubble } from "@/components/chat/ChatBubble";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { useWebSocket } from "@/hooks/useWebSocket";
import { apiFetch, getMe, getToken, getWsBaseUrl, listChatRooms, type ChatRoom } from "@/lib/api";
import { useTranslations } from "next-intl";

type Message = {
  id: string;
  body: string;
  sender_id: string;
  client_message_id?: string;
  pending?: boolean;
  created_at?: string;
};

type MessagesPage = { items: Message[]; next_cursor?: string | null; has_more: boolean };

export default function ChatPage() {
  const t = useTranslations("chat");
  const [rooms, setRooms] = useState<ChatRoom[]>([]);
  const [roomId, setRoomId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [myId, setMyId] = useState<string | null>(null);
  const [loadingRooms, setLoadingRooms] = useState(true);
  const [text, setText] = useState("");
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const seenClientIds = useRef(new Set<string>());
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const wsUrl = useMemo(() => {
    if (!roomId) return null;
    const token = getToken();
    return `${getWsBaseUrl()}/api/v1/ws/chat/${roomId}?token=${token}`;
  }, [roomId]);

  const upsertMessage = useCallback((msg: Message) => {
    const clientId = msg.client_message_id;
    if (clientId && seenClientIds.current.has(clientId)) {
      setMessages((prev) =>
        prev.map((m) => (m.client_message_id === clientId ? { ...msg, pending: false } : m)),
      );
      return;
    }
    if (clientId) seenClientIds.current.add(clientId);
    setMessages((prev) => (prev.some((m) => m.id === msg.id) ? prev : [...prev, msg]));
  }, []);

  const { connected, send } = useWebSocket({
    url: wsUrl,
    enabled: Boolean(roomId),
    onMessage: (event) => {
      if (event.type === "typing") {
        if (event.active && event.user_id) {
          setTypingUsers((u) => [...new Set([...u, event.user_id as string])]);
        }
        return;
      }
      if (event.type && event.type !== "message") return;
      if (!event.id || !event.body || !event.sender_id) return;
      upsertMessage({
        id: event.id,
        body: event.body,
        sender_id: event.sender_id,
        client_message_id: event.client_message_id,
        created_at: event.created_at,
        pending: false,
      });
    },
  });

  useEffect(() => {
    void (async () => {
      try {
        const [roomList, me] = await Promise.all([listChatRooms(), getMe()]);
        setRooms(roomList);
        setMyId(me.id);
        if (roomList[0]) {
          setRoomId(roomList[0].id);
          const page = await apiFetch<MessagesPage>(`/api/v1/chat/rooms/${roomList[0].id}/messages`);
          setMessages(page.items ?? []);
        }
      } finally {
        setLoadingRooms(false);
      }
    })();
  }, []);

  async function createRoom() {
    const room = await apiFetch<ChatRoom>("/api/v1/chat/rooms", {
      method: "POST",
      body: JSON.stringify({ name: t("defaultRoomName"), member_ids: [] }),
    });
    setRooms((r) => [room, ...r]);
    void joinRoom(room.id);
  }

  async function joinRoom(id: string) {
    setRoomId(id);
    setTypingUsers([]);
    seenClientIds.current.clear();
    const page = await apiFetch<MessagesPage>(`/api/v1/chat/rooms/${id}/messages`);
    const list = page.items ?? [];
    list.forEach((m) => {
      if (m.client_message_id) seenClientIds.current.add(m.client_message_id);
    });
    setMessages(list);
  }

  function notifyTyping(active: boolean) {
    send({ type: "typing", active });
  }

  function handleTextChange(value: string) {
    setText(value);
    notifyTyping(true);
    if (typingTimer.current) clearTimeout(typingTimer.current);
    typingTimer.current = setTimeout(() => notifyTyping(false), 1500);
  }

  async function sendMessage() {
    if (!roomId || !text.trim()) return;
    const clientMessageId = crypto.randomUUID();
    seenClientIds.current.add(clientMessageId);
    const optimistic: Message = {
      id: `pending-${clientMessageId}`,
      body: text,
      sender_id: myId ?? "me",
      client_message_id: clientMessageId,
      pending: true,
    };
    setMessages((m) => [...m, optimistic]);
    setText("");

    send({ type: "message", body: optimistic.body, client_message_id: clientMessageId });

    try {
      await apiFetch(`/api/v1/chat/rooms/${roomId}/messages`, {
        method: "POST",
        body: JSON.stringify({ body: optimistic.body, client_message_id: clientMessageId }),
      });
    } catch {
      setMessages((m) => m.filter((msg) => msg.client_message_id !== clientMessageId));
      seenClientIds.current.delete(clientMessageId);
    }
  }

  const activeRoom = rooms.find((r) => r.id === roomId);

  return (
    <div className="flex min-h-[calc(100vh-64px)] flex-col">
      <PageShell size="wide">
        <PageHeader title={t("title")} subtitle={t("subtitle")} badge="Chat" />

        <AuthGate>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            {roomId && (
              <Badge variant={connected ? "success" : "warning"}>
                {connected ? t("connected") : t("reconnecting")}
              </Badge>
            )}
            {typingUsers.length > 0 && (
              <span className="text-xs text-[var(--hp-fg-muted)]">{t("typing")}</span>
            )}
            <Button variant="secondary" size="sm" onClick={() => void createRoom()}>
              {t("createRoom")}
            </Button>
          </div>

          <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
            <Card padding="sm">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--hp-fg-muted)]">
                {t("rooms")}
              </h2>
              {loadingRooms && <SkeletonCard />}
              {!loadingRooms && rooms.length === 0 && (
                <EmptyState title={t("noRooms")} description={t("noRoomsHint")} />
              )}
              <ul className="space-y-1">
                {rooms.map((r) => (
                  <li key={r.id}>
                    <button
                      type="button"
                      onClick={() => void joinRoom(r.id)}
                      className={`w-full rounded-[var(--hp-radius)] px-3 py-2 text-left text-sm ${
                        roomId === r.id ? "bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]" : "hover:bg-[var(--hp-bg-subtle)]"
                      }`}
                    >
                      {r.name}
                    </button>
                  </li>
                ))}
              </ul>
            </Card>

            {activeRoom ? (
              <Card padding="lg" className="flex min-h-[420px] flex-col">
                <h2 className="mb-4 font-display font-semibold">{activeRoom.name}</h2>
                <div className="flex-1 space-y-3 overflow-y-auto pr-1">
                  {messages.map((m) => (
                    <ChatBubble
                      key={m.id}
                      body={m.body}
                      senderId={m.sender_id}
                      createdAt={m.created_at}
                      isOwn={m.sender_id === myId}
                      pending={m.pending}
                    />
                  ))}
                  {messages.length === 0 && (
                    <p className="text-center text-sm text-[var(--hp-fg-muted)]">{t("emptyChat")}</p>
                  )}
                </div>
                <div className="mt-4 flex gap-2 border-t border-[var(--hp-border)] pt-4">
                  <Input
                    value={text}
                    onChange={(e) => handleTextChange(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && void sendMessage()}
                    placeholder={t("messagePlaceholder")}
                    className="flex-1"
                  />
                  <Button variant="primary" onClick={() => void sendMessage()}>
                    {t("send")}
                  </Button>
                </div>
              </Card>
            ) : (
              !loadingRooms && <EmptyState title={t("selectRoom")} description={t("selectRoomHint")} />
            )}
          </div>
        </AuthGate>
      </PageShell>
      <Footer />
    </div>
  );
}
