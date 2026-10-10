import { createElement, Fragment } from "react";
import type { RouteObject } from "react-router-dom";

type PlaceholderProps = {
  title: string;
};

function Placeholder({ title }: PlaceholderProps): JSX.Element {
  return createElement(
    "section",
    {
      className: "rounded-lg border border-dashed border-gray-300 bg-white p-6 text-gray-600",
      "aria-label": title,
    },
    createElement("h2", { className: "text-lg font-semibold text-gray-900" }, title),
    createElement("p", { className: "mt-2 text-sm" }, "Ripple intelligence is coming soon."),
  );
}

export const rippleRoutes: RouteObject[] = [
  { path: "ripple", element: createElement(Placeholder, { title: "Ripple Inbox" }) },
  { path: "ripple/:id", element: createElement(Placeholder, { title: "Ripple Event" }) },
  { path: "leak", element: createElement(Placeholder, { title: "Leak Meter" }) },
  { path: "what-if", element: createElement(Placeholder, { title: "What-if Simulator" }) },
];

export function OrderHealthBadge(p: {
  orderId: string;
  health?: "green" | "amber" | "red" | null;
  slackMinutes?: number | null;
  size?: "sm" | "md";
}): JSX.Element {
  const label = p.health ? `Order health: ${p.health}` : "Order health unavailable";
  return createElement("span", { "aria-label": label }, label);
}

export function PromiseDatePanel(p: {
  draft: {
    buyer_id?: string;
    fabric_type_id?: string;
    quantity_cm?: number;
    requested_date?: string;
    priority?: string;
  };
  onUseDate?: (isoDate: string) => void;
}): JSX.Element {
  void p;
  return createElement(Placeholder, { title: "Promise Date" });
}

export function RippleFloor(p: {
  compact?: boolean;
  onMachineClick?: (machineId: string) => void;
}): JSX.Element {
  void p;
  return createElement(Placeholder, { title: "Ripple Floor" });
}

export function RippleInboxWidget(p: { limit?: number }): JSX.Element {
  void p;
  return createElement(Placeholder, { title: "Ripple Inbox" });
}

export function LeakMeterWidget(p: { compact?: boolean }): JSX.Element {
  void p;
  return createElement(Placeholder, { title: "Leak Meter" });
}

export function IdleHunterWidget(p: { limit?: number }): JSX.Element {
  void p;
  return createElement(Placeholder, { title: "Idle Hunter" });
}

export function RippleLiveToaster(): JSX.Element {
  return createElement(Fragment);
}
