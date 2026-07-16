"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type WebSocketEvent = {
  type?: string;
  id?: string;
  client_message_id?: string;
  body?: string;
  sender_id?: string;
  user_id?: string;
  active?: boolean;
  echo?: boolean;
  created_at?: string;
};

type UseWebSocketOptions = {
  url: string | null;
  enabled?: boolean;
  onMessage?: (event: WebSocketEvent) => void;
  onOpen?: () => void;
  onClose?: () => void;
};

const MAX_BACKOFF_MS = 30_000;
const BASE_BACKOFF_MS = 1_000;

export function useWebSocket({
  url,
  enabled = true,
  onMessage,
  onOpen,
  onClose,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [connected, setConnected] = useState(false);

  const cleanup = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  const connect = useCallback(() => {
    if (!url || !enabled) return;
    cleanup();

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      retryRef.current = 0;
      setConnected(true);
      onOpen?.();
    };

    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as WebSocketEvent;
        onMessage?.(data);
      } catch {
        /* ignore malformed payloads */
      }
    };

    ws.onclose = () => {
      setConnected(false);
      onClose?.();
      if (!enabled) return;
      const delay = Math.min(BASE_BACKOFF_MS * 2 ** retryRef.current, MAX_BACKOFF_MS);
      retryRef.current += 1;
      reconnectTimer.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [cleanup, enabled, onClose, onMessage, onOpen, url]);

  useEffect(() => {
    connect();
    return cleanup;
  }, [connect, cleanup]);

  const send = useCallback((payload: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    }
  }, []);

  return { connected, send, reconnect: connect };
}
