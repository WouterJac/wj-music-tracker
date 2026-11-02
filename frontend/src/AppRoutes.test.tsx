import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { mockApi } from "./test/api";
import { bowie, low, page } from "./test/fixtures";
import { renderAt } from "./test/render";

function api() {
  mockApi((url) => {
    if (url.pathname === "/api/years") return [1977];
    if (url.pathname === "/api/artists") return page([bowie]);
    return page([low]);
  });
}

describe("routes", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends the root URL to the albums page", async () => {
    api();

    renderAt("/");

    expect(await screen.findByRole("heading", { name: "Albums" })).toBeInTheDocument();
  });

  it("has navigation between albums and artists", async () => {
    api();
    const user = userEvent.setup();
    renderAt("/albums");

    await user.click(screen.getByRole("link", { name: "Artists" }));

    expect(await screen.findByRole("heading", { name: "Artists" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Artists" })).toHaveAttribute("aria-current", "page");
  });

  it("has a lyrics page in the navigation", async () => {
    api();
    const user = userEvent.setup();
    renderAt("/albums");

    await user.click(screen.getByRole("link", { name: "Lyrics" }));

    expect(await screen.findByRole("heading", { name: "Lyrics", level: 1 })).toBeInTheDocument();
  });

  it("shows the server status in the footer", async () => {
    api();

    renderAt("/albums");

    expect(await screen.findByText("Server is ok")).toBeInTheDocument();
  });

  it("shows a not-found page with a way back for unknown URLs", () => {
    api();

    renderAt("/nowhere");

    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to albums" })).toHaveAttribute("href", "/albums");
  });
});
