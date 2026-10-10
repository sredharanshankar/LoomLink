import { createElement, Fragment } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";

import {
  IdleHunterWidget,
  LeakMeterWidget,
  OrderHealthBadge,
  PromiseDatePanel,
  RippleFloor,
  RippleInboxWidget,
  RippleLiveToaster,
  rippleRoutes,
} from "./index";

describe("Ripple feature contract", () => {
  it("registers every Ripple route mounted below /app", () => {
    expect(rippleRoutes.map((route) => route.path)).toEqual([
      "ripple",
      "ripple/:id",
      "leak",
      "what-if",
    ]);
  });

  it("exposes renderable placeholder components", () => {
    const queryClient = new QueryClient();
    const components = [
      createElement(OrderHealthBadge, { orderId: "order-1" }),
      createElement(PromiseDatePanel, { draft: {} }),
      createElement(RippleFloor),
      createElement(RippleInboxWidget),
      createElement(LeakMeterWidget),
      createElement(IdleHunterWidget),
      createElement(RippleLiveToaster),
    ];

    expect(() =>
      renderToStaticMarkup(
        createElement(
          QueryClientProvider,
          { client: queryClient },
          createElement(Fragment, null, ...components),
        ),
      ),
    ).not.toThrow();
  });
});
