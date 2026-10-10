import { renderToStaticMarkup } from "react-dom/server";
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
    const components = [
      OrderHealthBadge({ orderId: "order-1" }),
      PromiseDatePanel({ draft: {} }),
      RippleFloor({}),
      RippleInboxWidget({}),
      LeakMeterWidget({}),
      IdleHunterWidget({}),
      RippleLiveToaster(),
    ];

    expect(components.map((component) => renderToStaticMarkup(component))).toHaveLength(7);
  });
});
