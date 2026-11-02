import { screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { SimilarAlbum } from "../../api/library";
import { mockApi, requestsTo } from "../../test/api";
import { heroes, lowDetail } from "../../test/fixtures";
import { renderAt } from "../../test/render";

const suggestion: SimilarAlbum = {
  album: heroes,
  score: 6,
  reasons: ["Shared genre: Rock", "Same label: RCA", "Similar era: 1977"],
};

function albumApi(similar: () => unknown) {
  return mockApi((url) => {
    if (url.pathname === "/api/albums/1") return lowDetail;
    if (url.pathname === "/api/albums/1/similar") return similar();
    return new Response("not found", { status: 404 });
  });
}

describe("Similar albums on the album page", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("lists suggested albums with the reasons for each", async () => {
    const fetchMock = albumApi(() => [suggestion]);
    renderAt("/albums/1");

    const section = await screen.findByRole("region", { name: "You might also like" });
    const card = await within(section).findByRole("link", { name: /Heroes/ });
    expect(card).toHaveAttribute("href", "/albums/2");
    expect(within(section).getByText("Shared genre: Rock")).toBeVisible();
    expect(within(section).getByText("Same label: RCA")).toBeVisible();
    expect(requestsTo(fetchMock, "/api/albums/1/similar")).toHaveLength(1);
  });

  it("shows a placeholder while suggestions load, without hiding the album", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const text =
          typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
        const url = new URL(text, "http://localhost");
        if (url.pathname === "/health") {
          return Promise.resolve(Response.json({ status: "ok", version: "0.1.0" }));
        }
        if (url.pathname === "/api/albums/1") return Promise.resolve(Response.json(lowDetail));
        return new Promise(() => {});
      }),
    );
    renderAt("/albums/1");

    expect(await screen.findByRole("heading", { name: "Low", level: 1 })).toBeInTheDocument();
    expect(screen.getByRole("status", { name: "Loading suggestions" })).toBeInTheDocument();
  });

  it("leaves the section out when nothing is similar", async () => {
    albumApi(() => []);
    renderAt("/albums/1");

    await screen.findByRole("heading", { name: "Low", level: 1 });
    await vi.waitFor(() => {
      expect(screen.queryByRole("status", { name: "Loading suggestions" })).not.toBeInTheDocument();
    });
    expect(screen.queryByRole("region", { name: "You might also like" })).not.toBeInTheDocument();
  });

  it("keeps the album usable when suggestions fail", async () => {
    albumApi(() => new Response("boom", { status: 500 }));
    renderAt("/albums/1");

    expect(await screen.findByRole("heading", { name: "Low", level: 1 })).toBeInTheDocument();
    await vi.waitFor(() => {
      expect(screen.queryByRole("status", { name: "Loading suggestions" })).not.toBeInTheDocument();
    });
    expect(screen.queryByRole("region", { name: "You might also like" })).not.toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
