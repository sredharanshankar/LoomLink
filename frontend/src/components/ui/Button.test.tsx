import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Button from "./Button";

describe("Button", () => {
  it("renders children", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: "Click me" })).toBeInTheDocument();
  });

  it("shows spinner when loading", () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("calls onClick", async () => {
    const user = userEvent.setup();
    let called = false;
    render(<Button onClick={() => { called = true; }}>Go</Button>);
    await user.click(screen.getByRole("button"));
    expect(called).toBe(true);
  });
});