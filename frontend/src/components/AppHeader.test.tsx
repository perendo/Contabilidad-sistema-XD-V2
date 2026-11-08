import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { AppHeader } from "./AppHeader";

describe("AppHeader", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("app_header_renders_section_title", () => {
    const onNavigateToPanel = vi.fn();
    const onLogout = vi.fn();
    const toggle = vi.fn();
    render(
      <AppHeader
        title="Plan de cuentas"
        mode="dark"
        toggle={toggle}
        onNavigateToPanel={onNavigateToPanel}
        onLogout={onLogout}
      />
    );
    expect(screen.getByText("Plan de cuentas")).toBeDefined();
  });

  it("app_header_theme_toggle_changes_mode", () => {
    const toggle = vi.fn();
    const { container } = render(
      <AppHeader
        title="Plan de cuentas"
        mode="dark"
        toggle={toggle}
        onNavigateToPanel={vi.fn()}
        onLogout={vi.fn()}
      />
    );
    const buttons = container.querySelectorAll("button");
    act(() => {
      buttons[0].dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    expect(toggle).toHaveBeenCalledTimes(1);
  });

  it("app_header_panel_link_navigates_home", () => {
    const onNavigateToPanel = vi.fn();
    const { container } = render(
      <AppHeader
        title="Plan de cuentas"
        mode="dark"
        toggle={vi.fn()}
        onNavigateToPanel={onNavigateToPanel}
        onLogout={vi.fn()}
      />
    );
    const buttons = container.querySelectorAll("button");
    act(() => {
      buttons[1].dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    expect(onNavigateToPanel).toHaveBeenCalledTimes(1);
  });

  it("app_header_logout_calls_onLogout", () => {
    const onLogout = vi.fn();
    const { container } = render(
      <AppHeader
        title="Plan de cuentas"
        mode="dark"
        toggle={vi.fn()}
        onNavigateToPanel={vi.fn()}
        onLogout={onLogout}
      />
    );
    const buttons = container.querySelectorAll("button");
    act(() => {
      buttons[2].dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    expect(onLogout).toHaveBeenCalledTimes(1);
  });
});
