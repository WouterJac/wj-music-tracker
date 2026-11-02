import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Album } from "../../api/library";
import { jsonResponse, mockApi, requestsTo } from "../../test/api";
import { heroes, low } from "../../test/fixtures";
import { renderAt } from "../../test/render";

const genres = [
  { name: "Rock", album_count: 12 },
  { name: "Ambient", album_count: 1 },
];

function exploreApi(random: () => Album[] = () => [low, heroes]) {
  return mockApi((url) => {
    if (url.pathname === "/api/albums/random") return random();
    if (url.pathname === "/api/genres") return genres;
    if (url.pathname === "/api/years") return [2023, 2016, 2009, 1977];
    throw new Error(`unexpected request ${url.pathname}`);
  });
}

describe("ExplorePage", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("is reachable from the main navigation", () => {
    exploreApi();
    renderAt("/albums");

    expect(screen.getByRole("link", { name: "Explore" })).toHaveAttribute("href", "/explore");
  });

  it("shows random albums as cards", async () => {
    const fetchMock = exploreApi();
    renderAt("/explore");

    const section = await screen.findByRole("region", { name: "Random picks" });
    expect(await within(section).findByRole("link", { name: /Low/ })).toHaveAttribute(
      "href",
      "/albums/1",
    );
    expect(within(section).getAllByRole("listitem")).toHaveLength(2);
    expect(requestsTo(fetchMock, "/api/albums/random")[0]?.searchParams.get("count")).toBe("6");
  });

  it("shuffles again for a new selection", async () => {
    let call = 0;
    const fetchMock = exploreApi(() => (call++ === 0 ? [low] : [heroes]));
    const user = userEvent.setup();
    renderAt("/explore");
    await screen.findByRole("link", { name: /Low/ });

    await user.click(screen.getByRole("button", { name: "Shuffle again" }));

    expect(await screen.findByRole("link", { name: /Heroes/ })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Low/ })).not.toBeInTheDocument();
    expect(requestsTo(fetchMock, "/api/albums/random")).toHaveLength(2);
  });

  it("browses by decade, newest first, using the years the library has", async () => {
    exploreApi();
    renderAt("/explore");

    const decades = await screen.findByRole("region", { name: "Browse by decade" });
    const links = within(decades).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual(["2020s", "2010s", "2000s", "1970s"]);
    expect(links[0]).toHaveAttribute("href", "/albums?decade=2020");
  });

  it("browses by genre with album counts", async () => {
    exploreApi();
    renderAt("/explore");

    const section = await screen.findByRole("region", { name: "Browse by genre" });
    const rock = within(section).getByRole("link", { name: /Rock/ });
    expect(rock).toHaveAttribute("href", "/albums?genre=Rock");
    expect(rock).toHaveTextContent("12");
  });

  it("leaves out the genre section when no file is tagged", async () => {
    mockApi((url) => {
      if (url.pathname === "/api/albums/random") return [low];
      if (url.pathname === "/api/genres") return [];
      return [1977];
    });
    renderAt("/explore");

    await screen.findByRole("region", { name: "Browse by decade" });
    expect(screen.queryByRole("region", { name: "Browse by genre" })).not.toBeInTheDocument();
  });

  it("shows a skeleton while loading", () => {
    mockApi(() => new Promise(() => {}));
    renderAt("/explore");

    expect(screen.getByRole("status", { name: "Loading random albums" })).toBeInTheDocument();
  });

  it("explains an empty library", async () => {
    mockApi((url) => {
      if (url.pathname === "/api/albums/random") return [];
      return [];
    });
    renderAt("/explore");

    expect(await screen.findByText(/No albums yet/)).toBeInTheDocument();
    expect(screen.getByText("wj-music scan")).toBeInTheDocument();
  });

  it("offers a retry when the backend fails", async () => {
    let fail = true;
    mockApi((url) => {
      if (url.pathname === "/api/albums/random") return fail ? jsonResponse({}, 500) : [low];
      return url.pathname === "/api/genres" ? genres : [1977];
    });
    renderAt("/explore");

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load random albums");
    fail = false;
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => {
      expect(screen.getByRole("link", { name: /Low/ })).toBeInTheDocument();
    });
  });
});
