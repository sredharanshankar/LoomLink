import { useEffect, useRef, useCallback } from "react";
import { useAuthStore } from "./auth";

type WsMessage = { type: string; payload: unknown; ts: string };
type Handler = (msg: WsMessage) => void;

const WS_BASE = (() => {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}/api/v1/ws`;
})();

let ws: WebSocket | null = null;
let handlers: Map<string, Set<Handler>> = new Map();
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

function connect(token: string) {
  if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) return;
  ws = new WebSocket(`${WS_BASE}?token=${encodeURIComponent(token)}`);
  ws.onmessage = (e) => {
    try {
      const msg: WsMessage = JSON.parse(e.data);
      const parts = msg.type.split(".");
      for (let i = parts.length; i > 0; i--) {
        const prefix = parts.slice(0, i).join(".");
        handlers.get(prefix)?.forEach((h) => h(msg));
      }
      handlers.get("*")?.forEach((h) => h(msg));
    } catch {}
  };
  ws.onclose = () => {
    reconnectTimer = setTimeout(() => {
      const t = useAuthStore.getState().accessToken;
      if (t) connect(t);
    }, 3000);
  };
}

function subscribe(prefix: string, handler: Handler): () => void {
  if (!handlers.has(prefix)) handlers.set(prefix, new Set());
  handlers.get(prefix)!.add(handler);
  return () => handlers.get(prefix)?.delete(handler);
}

export function useWsEvent(prefix: string, handler: Handler) {
  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  const stableHandler = useCallback((msg: WsMessage) => handlerRef.current(msg), []);

  useEffect(() => {
    const token = useAuthStore.getState().accessToken;
    if (token) connect(token);
    return subscribe(prefix, stableHandler);
  }, [prefix, stableHandler]);
}