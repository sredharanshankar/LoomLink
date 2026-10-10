import { createElement } from "react";

export function BolButton(p: {
  context: {
    screen: string;
    machine_id?: string;
    job_id?: string;
    batch_id?: string;
  };
  onConfirmed?: (result: unknown) => void;
}): JSX.Element {
  void p;
  return createElement(
    "button",
    {
      type: "button",
      disabled: true,
      className: "rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-500",
      title: "Bol voice commands are coming soon",
    },
    "Bol — coming soon",
  );
}
