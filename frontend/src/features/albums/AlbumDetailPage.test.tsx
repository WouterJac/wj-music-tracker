import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { AlbumDetail } from "../../api/library";
import { mockApi, requestsTo } from "../../test/api";
import { breakingGlass, heroes, lowDetail, speedOfLife } from "../../test/fixtures";
import { renderAt } from "../../test/render";

function albumApi(detail: AlbumDetail = lowDetail) {
  return mockApi((url) => {
    if (url.pathname === `/api/albums/${String(detail.id)}`) return detail;
    return new Response("not found", { status: 404 });
  });
}

describe("AlbumDetailPage", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows a loading skeleton while the album loads", () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));

    renderAt("/albums/1");

    expect(screen.getByRole("status", { name: "Loading album" })).toBeInTheDocument();
  });

  it("shows title, linked artist, cover, year and totals", async () => {
    albumApi();

    renderAt("/albums/1");

    expect(await screen.findByRole("heading", { name: "Low", level: 1 })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "David Bowie" })).toHaveAttribute("href", "/artists/1");
    expect(screen.getByAltText("Cover of Low by David Bowie")).toHaveAttribute(
      "src",
      "/api/albums/1/cover",
    );
    expect(screen.getByText("1977 · 11 tracks · 6 min")).toBeInTheDocument();
  });

  it("lists tracks in order with number, title and duration", async () => {
    albumApi();

    renderAt("/albums/1");

    const rows = await screen.findAllByRole("row");
    const cells = rows.slice(1).map((row) => within(row).getAllByRole("cell"));
    expect(cells.map((c) => c.map((cell) => cell.textContent))).toEqual([
      ["1", "Breaking Glass", "3:20", "Lyrics"],
      ["2", "Speed of Life", "2:30", ""],
    ]);
  });

  it("links each track title to its track page", async () => {
    albumApi();

    renderAt("/albums/1");

    expect(await screen.findByRole("link", { name: "Breaking Glass" })).toHaveAttribute(
      "href",
      "/tracks/1",
    );
    expect(screen.getByRole("link", { name: "Speed of Life" })).toHaveAttribute(
      "href",
      "/tracks/2",
    );
  });

  it("shows technical info for the album", async () => {
    albumApi();

    renderAt("/albums/1");

    const info = await screen.findByRole("group", { name: "Technical info" });
    expect(within(info).getByText("16-bit / 44.1 kHz")).toBeInTheDocument();
    expect(within(info).getByText("Stereo")).toBeInTheDocument();
  });

  it("lists every format when tracks differ", async () => {
    albumApi({
      ...lowDetail,
      tracks: [breakingGlass, { ...speedOfLife, bit_depth: 24, sample_rate: 96000, channels: 1 }],
    });

    renderAt("/albums/1");

    const info = await screen.findByRole("group", { name: "Technical info" });
    expect(within(info).getByText("16-bit / 44.1 kHz, 24-bit / 96 kHz")).toBeInTheDocument();
    expect(within(info).getByText("Stereo, Mono")).toBeInTheDocument();
  });

  it("groups tracks under disc headings only when there is more than one disc", async () => {
    albumApi({
      ...lowDetail,
      tracks: [breakingGlass, { ...speedOfLife, id: 3, disc: 2, number: 1 }],
    });

    renderAt("/albums/1");

    expect(await screen.findByRole("heading", { name: "Disc 1" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Disc 2" })).toBeInTheDocument();
  });

  it("has no disc headings for a single disc", async () => {
    albumApi();

    renderAt("/albums/1");

    await screen.findByRole("table");
    expect(screen.queryByRole("heading", { name: /^Disc/ })).not.toBeInTheDocument();
  });

  it("shows a placeholder when the album has no cover", async () => {
    albumApi({ ...lowDetail, ...heroes, id: 1, tracks: [breakingGlass] });

    renderAt("/albums/1");

    await screen.findByRole("heading", { name: '"Heroes"' });
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("says so when the album has no tracks", async () => {
    albumApi({ ...lowDetail, tracks: [] });

    renderAt("/albums/1");

    expect(await screen.findByText("No tracks recorded for this album.")).toBeInTheDocument();
  });

  it("shows a not-found message for an unknown album", async () => {
    mockApi(() => new Response("not found", { status: 404 }));

    renderAt("/albums/999");

    expect(await screen.findByRole("heading", { name: "Album not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to albums" })).toHaveAttribute("href", "/albums");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("treats a non-numeric id as not found without calling the API", async () => {
    const fetchMock = albumApi();

    renderAt("/albums/abc");

    expect(await screen.findByRole("heading", { name: "Album not found" })).toBeInTheDocument();
    expect(requestsTo(fetchMock, "/api/albums/abc")).toEqual([]);
  });

  it("shows an error with a retry button that loads the album", async () => {
    let attempts = 0;
    mockApi(() => {
      attempts += 1;
      return attempts === 1 ? new Response("boom", { status: 500 }) : lowDetail;
    });
    const user = userEvent.setup();

    renderAt("/albums/1");

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load album");
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: "Low", level: 1 })).toBeInTheDocument();
  });
});
