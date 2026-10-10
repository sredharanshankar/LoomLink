import type { RouteTemplate } from "./types";

export const routeTemplates: RouteTemplate[] = [
  {
    id: "rt-r1",
    code: "R1",
    name: "Weave → Dye → Finish",
    stages: ["weaving", "dyeing", "finishing"],
  },
  {
    id: "rt-r2",
    code: "R2",
    name: "Spin → Weave → Dye → Finish",
    stages: ["spinning", "weaving", "dyeing", "finishing"],
  },
];
