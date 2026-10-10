import { createElement } from "react";
import type { RouteObject } from "react-router-dom";

function BuyerLinePlaceholder(): JSX.Element {
  return createElement(
    "section",
    {
      className: "rounded-lg border border-dashed border-gray-300 bg-white p-6 text-gray-600",
      "aria-label": "Buyer Line",
    },
    createElement("h2", { className: "text-lg font-semibold text-gray-900" }, "Buyer Line"),
    createElement("p", { className: "mt-2 text-sm" }, "The demo chat simulator is coming soon."),
  );
}

export const buyerLineRoutes: RouteObject[] = [
  { path: "", element: createElement(BuyerLinePlaceholder) },
];
