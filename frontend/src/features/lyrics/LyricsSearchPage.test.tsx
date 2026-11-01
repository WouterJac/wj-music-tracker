import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { LyricsHit } from "../../api/library";
import { mockApi, requestsTo } from "../../test/api";
import { campHit, page } from "../../test/fixtures";
import { renderAt } from "../../test/render";

function lyricsApi(items: LyricsHit[] = [campHit], total = items.length) {
  return mockApi((url) => page(items, total, 24, Number(url.searchParams.get("offset") ?? 0)));
}

describe("LyricsSearchPage", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("invites a search before anything is typed and asks for nothing from the server", () => {
    const fetchMock = lyricsApi();

    renderAt("/lyrics");

    expect(screen.getByText("Search the lyrics of your whole library.")).toBeInTheDocument();
    expect(requestsTo(fetchMock, "/api/lyrics/search")).toEqual([]);
  });

  it("asks for at least two characters and does not search yet", async () => {
    const fetchMock = lyricsApi();
    const user = userEvent.setup();
    renderAt("/lyrics");

    await user.type(screen.getByRole("searchbox", { name: "Search lyrics" }), "l");

    expect(screen.getByText("Type at least 2 characters to search.")).toBeInTheDocument();
    expect(requestsTo(fetchMock, "/api/lyrics/search")).toEqual([]);
  });

  it("shows a loading skeleton while searching", () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));

    renderAt("/lyrics?q=love");

    expect(screen.getByRole("status", { name: "Searching lyrics" })).toBeInTheDocument();
  });

  it("searches as the user types", async () => {
    const fetchMock = lyricsApi();
    const user = userEvent.setup();
    renderAt("/lyrics");

    await user.type(screen.getByRole("searchbox", { name: "Search lyrics" }), "love");

    await waitFor(() => {
      const last = requestsTo(fetchMock, "/api/lyrics/search").at(-1);
      expect(last?.searchParams.get("q")).toBe("love");
      expect(last?.searchParams.get("limit")).toBe("24");
    });
  });

  it("lists hits with title, artist, album and a highlighted snippet", async () => {
    lyricsApi();

    renderAt("/lyrics?q=love");

    const link = await screen.findByRole("link", { name: /Camera/ });
    expect(link).toHaveAttribute("href", "/tracks/78?find=love");
    expect(link).toHaveTextContent("Editors · The Back Room");
    expect(screen.getByText("love", { selector: "mark" })).toBeInTheDocument();
  });

  it("explains when nothing matches", async () => {
    lyricsApi([]);

    renderAt("/lyrics?q=zebra");

    expect(await screen.findByText("No lyrics match “zebra”.")).toBeInTheDocument();
  });

  it("shows an error with a retry button", async () => {
    let attempts = 0;
    mockApi(() => {
      attempts += 1;
      return attempts === 1 ? new Response("boom", { status: 500 }) : page([campHit]);
    });
    const user = userEvent.setup();

    renderAt("/lyrics?q=love");

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load lyrics");
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("link", { name: /Camera/ })).toBeInTheDocument();
  });

  it("reports the number of matching tracks and pages through them", async () => {
    const fetchMock = lyricsApi([campHit], 50);
    const user = userEvent.setup();
    renderAt("/lyrics?q=love");

    expect(await screen.findByText("50 tracks")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Next page" }));

    await waitFor(() => {
      expect(requestsTo(fetchMock, "/api/lyrics/search").at(-1)?.searchParams.get("offset")).toBe(
        "24",
      );
    });
  });
});
