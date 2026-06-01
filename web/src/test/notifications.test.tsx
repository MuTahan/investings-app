import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("../hooks/useNotifications", () => ({
  useNotifications: () => ({ data: { items: [] }, isLoading: false, isError: false }),
  useRunNotifications: () => ({ mutate: () => {}, isPending: false, isSuccess: false }),
}));

import { NotificationsPage } from "../features/notifications/NotificationsPage";

describe("NotificationsPage", () => {
  it("renders heading and empty state", () => {
    render(
      <MemoryRouter>
        <NotificationsPage />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Notifications" })).toBeInTheDocument();
    expect(screen.getByText("No notifications yet")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run now" })).toBeInTheDocument();
  });
});
