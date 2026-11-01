import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Artist } from "../../api/library";
import { mockApi, requestsTo } from "../../test/api";
import { bowie, eno, page } from "../../test/fixtures";
import { renderAt } from "../../test/render";

function artistsApi(items: Artist[] = [eno, bowie]) {
  return mockApi((url) =>
    page(items, items.length, 24, Number(url.searchParams.get("offset") ?? 0)),
  );
}

describe("ArtistsPage", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows a loading skeleton while artists load", () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));

    renderAt("/artists");

    expect(screen.getByRole("status", { name: "Loading artists" })).toBeInTheDocument();
  });

  it("lists artists as links with their album counts", async () => {
    artistsApi();

    renderAt("/artists");

    const link = await screen.findByRole("link", { name: /David Bowie/ });
    expect(link).toHaveAttribute("href", "/artists/1");
    expect(link).toHaveTextContent("2 albums");
    expect(screen.getByRole("link", { name: /Brian Eno/ })).toHaveTextContent("1 album");
  });

  it("asks the user to scan when there are no artists", async () => {
    artistsApi([]);

    renderAt("/artists");

    expect(await screen.findByText(/No artists found\. Run/)).toHaveTextContent("wj-music scan");
  });

  it("explains an empty search result", async () => {
    artistsApi([]);

    renderAt("/artists?q=zzz");

    expect(await screen.findByText("No artists match your search.")).toBeInTheDocument();
  });

  it("shows an error with a retry button", async () => {
    let attempts = 0;
    mockApi(() => {
      attempts += 1;
      return attempts === 1 ? new Response("boom", { status: 500 }) : page([bowie]);
    });
    const user = userEvent.setup();

    renderAt("/artists");

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load artists");
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("link", { name: /David Bowie/ })).toBeInTheDocument();
  });

  it("searches as the user types and keeps the search in the URL", async () => {
    const fetchMock = artistsApi();
    const user = userEvent.setup();
    renderAt("/artists");
    await screen.findByRole("link", { name: /David Bowie/ });

    await user.type(screen.getByRole("searchbox", { name: "Search artists" }), "bow");

    await waitFor(() => {
      expect(requestsTo(fetchMock, "/api/artists").at(-1)?.searchParams.get("q")).toBe("bow");
    });
  });
});
