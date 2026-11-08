import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { ListState } from "./ListState";
import PaginationBar from "./PaginationBar";

describe("ListState", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("list_state_renders_loading_when_fetching", () => {
    render(<ListState loading={true} items={[]} onRetry={vi.fn()} />);
    expect(screen.getByRole("progressbar")).toBeDefined();
  });

  it("list_state_renders_empty_when_no_data", () => {
    render(<ListState loading={false} items={[]} onRetry={vi.fn()} />);
    expect(screen.getByText("Sin datos")).toBeDefined();
  });

  it("list_state_renders_error_when_fetch_fails", () => {
    const onRetry = vi.fn();
    render(<ListState loading={false} items={[]} error="Error de red" onRetry={onRetry} />);
    expect(screen.getByText("Error de red")).toBeDefined();
    expect(screen.getByRole("button", { name: /reintentar/i })).toBeDefined();
  });

  it("pagination_bar_has_previous_next_buttons", () => {
    const onPrevious = vi.fn();
    const onNext = vi.fn();
    render(<PaginationBar page={0} hasMore={true} onPrevious={onPrevious} onNext={onNext} />);
    expect(screen.getByRole("button", { name: /siguiente/i })).toBeDefined();
    expect(screen.getByRole("button", { name: /anterior/i })).toBeDefined();
    expect(onPrevious).not.toHaveBeenCalled();
    expect(onNext).not.toHaveBeenCalled();
  });

  it("list_state_retries_on_error", () => {
    const onRetry = vi.fn();
    render(<ListState loading={false} items={[]} error="Error de red" onRetry={onRetry} />);
    const buttons = screen.getAllByRole("button", { name: /reintentar/i });
    expect(buttons).toHaveLength(1);
  });
});
