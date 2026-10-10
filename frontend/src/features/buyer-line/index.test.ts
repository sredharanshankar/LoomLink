import { describe, expect, it } from "vitest";

import { buyerLineRoutes } from "./index";

describe("Buyer Line feature contract", () => {
  it("registers the demo chat simulator index route", () => {
    expect(buyerLineRoutes.map((route) => route.path)).toEqual([""]);
  });
});
