import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { BolButton } from "./index";

describe("Bol feature contract", () => {
  it("exposes a renderable button", () => {
    const markup = renderToStaticMarkup(BolButton({ context: { screen: "floor" } }));

    expect(markup).toContain("Bol");
  });
});
