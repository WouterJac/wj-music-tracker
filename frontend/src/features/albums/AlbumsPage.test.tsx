import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Album } from "../../api/library";
import { mockApi, requestsTo } from "../../test/api";
import { heroes, low, page } from "../../test/fixtures";
import { renderAt } from "../../test/render";

function albumsApi(items: Album[] = [low, heroes], total = items.length) {
  return mockApi((url) => {
    if (url.pathname === "/api/years") return [1977, 1975];
    if (url.pathname === "/api/albums") {
      return page(items, total, 24, Number(url.searchParams.get("offset") ?? 0));
    }
    throw new Error(`unexpected request ${url.pathname}`);
  });
}

describe("AlbumsPage", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows a loading skeleton while albums load", () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));

    renderAt("/albums");

    expect(screen.getByRole("status", { name: "Loading albums" })).toBeInTheDocument();
  });

  it("lists albums as links with cover art and artist", async () => {
    albumsApi();

    renderAt("/albums");

    const link = await screen.findByRole("link", { name: /Low/ });
    expect(link).toHaveAttribute("href", "/albums/1");
    expect(screen.getByText("David Bowie · 1977", { selector: "#album-1-meta" })).toBeVisible();
    expect(screen.getByAltText("Cover of Low by David Bowie")).toHaveAttribute(
      "src",
      "/api/albums/1/cover",
    );
  });

  it("shows a placeholder instead of an image when an album has no cover", async () => {
    albumsApi([heroes]);

    renderAt("/albums");

    await screen.findByRole("link", { name: /Heroes/ });
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("asks the user to scan when the library is empty", async () => {
    albumsApi([]);

    renderAt("/albums");

    expect(await screen.findByText(/No albums found\. Run/)).toHaveTextContent("wj-music scan");
  });

  it("explains an empty search result and offers to clear it", async () => {
    albumsApi([]);

    renderAt("/albums?q=zzz");

    expect(await screen.findByText("No albums match your search.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Clear filters" })).toHaveAttribute("href", "/albums");
  });

  it("shows an error with a retry button that loads the albums", async () => {
    let attempts = 0;
    mockApi((url) => {
      if (url.pathname === "/api/years") return [];
      attempts += 1;
      return attempts === 1 ? new Response("boom", { status: 500 }) : page([low]);
    });
    const user = userEvent.setup();

    renderAt("/albums");

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load albums");
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("link", { name: /Low/ })).toBeInTheDocument();
    expect(console.error).toHaveBeenCalled();
  });

  it("reads search, year and page from the URL", async () => {
    const fetchMock = albumsApi();

    renderAt("/albums?q=eno&year=1975&page=2");

    expect(screen.getByRole("searchbox", { name: "Search albums" })).toHaveValue("eno");
    await waitFor(() => {
      const request = requestsTo(fetchMock, "/api/albums").at(0);
      expect(request?.searchParams.get("q")).toBe("eno");
      expect(request?.searchParams.get("year")).toBe("1975");
      expect(request?.searchParams.get("limit")).toBe("24");
      expect(request?.searchParams.get("offset")).toBe("24");
    });
  });

  it("reads decade and genre from the URL and sends them to the API", async () => {
    const fetchMock = albumsApi();

    renderAt("/albums?decade=1970&genre=Art+Rock");

    await waitFor(() => {
      const request = requestsTo(fetchMock, "/api/albums").at(0);
      expect(request?.searchParams.get("decade")).toBe("1970");
      expect(request?.searchParams.get("genre")).toBe("Art Rock");
    });
  });

  it("names the active decade and genre filters and lets each be removed", async () => {
    albumsApi();
    renderAt("/albums?decade=1970&genre=Rock");
    await screen.findByRole("link", { name: /Low/ });

    expect(screen.getByRole("link", { name: "Remove decade 1970s" })).toHaveAttribute(
      "href",
      "/albums?genre=Rock",
    );
    expect(screen.getByRole("link", { name: "Remove genre Rock" })).toHaveAttribute(
      "href",
      "/albums?decade=1970",
    );
  });

  it("treats a decade or genre filter as a filter when nothing matches", async () => {
    albumsApi([]);

    renderAt("/albums?genre=Polka");

    expect(await screen.findByText("No albums match your search.")).toBeInTheDocument();
  });

  it("searches as the user types", async () => {
    const fetchMock = albumsApi();
    const user = userEvent.setup();
    renderAt("/albums");
    await screen.findByRole("link", { name: /Low/ });

    await user.type(screen.getByRole("searchbox", { name: "Search albums" }), "low");

    await waitFor(() => {
      expect(requestsTo(fetchMock, "/api/albums").at(-1)?.searchParams.get("q")).toBe("low");
    });
  });

  it("filters by year using the years the library has", async () => {
    const fetchMock = albumsApi();
    const user = userEvent.setup();
    renderAt("/albums");
    await screen.findByRole("option", { name: "1975" });

    await user.selectOptions(screen.getByRole("combobox", { name: "Year" }), "1975");

    await waitFor(() => {
      expect(requestsTo(fetchMock, "/api/albums").at(-1)?.searchParams.get("year")).toBe("1975");
    });
  });

  it("pages through results", async () => {
    const fetchMock = albumsApi([low, heroes], 50);
    const user = userEvent.setup();
    renderAt("/albums");

    expect(await screen.findByText("Page 1 of 3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous page" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Next page" }));

    expect(await screen.findByText("Page 2 of 3")).toBeInTheDocument();
    expect(requestsTo(fetchMock, "/api/albums").at(-1)?.searchParams.get("offset")).toBe("24");
  });

  it("hides pagination when everything fits on one page", async () => {
    albumsApi();

    renderAt("/albums");

    await screen.findByRole("link", { name: /Low/ });
    expect(screen.queryByRole("navigation", { name: "Pagination" })).not.toBeInTheDocument();
  });
});
