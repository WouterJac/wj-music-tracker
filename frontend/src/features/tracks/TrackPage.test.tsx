import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { TrackInfo } from "../../api/library";
import { mockApi, requestsTo } from "../../test/api";
import { breakingGlassInfo, noLyricsInfo, plainOnlyInfo } from "../../test/fixtures";
import { renderAt } from "../../test/render";

function trackApi(info: TrackInfo = breakingGlassInfo) {
  return mockApi((url) => {
    if (url.pathname === `/api/tracks/${String(info.id)}`) return info;
    return new Response("not found", { status: 404 });
  });
}

describe("TrackPage", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows a loading skeleton while the track loads", () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));

    renderAt("/tracks/1");

    expect(screen.getByRole("status", { name: "Loading track" })).toBeInTheDocument();
  });

  it("shows the title with links to its album and artist and the cover", async () => {
    trackApi();

    renderAt("/tracks/1");

    expect(
      await screen.findByRole("heading", { name: "Breaking Glass", level: 1 }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Low" })).toHaveAttribute("href", "/albums/1");
    expect(screen.getByRole("link", { name: "David Bowie" })).toHaveAttribute("href", "/artists/1");
    expect(screen.getByAltText("Cover of Low by David Bowie")).toHaveAttribute(
      "src",
      "/api/albums/1/cover",
    );
    expect(screen.getByText("3:20 · 16-bit / 44.1 kHz · Stereo")).toBeInTheDocument();
  });

  it("shows synced lyrics as timed lines", async () => {
    trackApi();

    renderAt("/tracks/1");

    const lines = await screen.findAllByRole("listitem");
    expect(lines.map((line) => line.textContent)).toEqual([
      "0:01Baby, I'm not special",
      "0:07Breaking glass",
    ]);
  });

  it("can hide the timestamps", async () => {
    trackApi();
    const user = userEvent.setup();
    renderAt("/tracks/1");

    await user.click(await screen.findByRole("checkbox", { name: "Show timestamps" }));

    expect(screen.getAllByRole("listitem").map((line) => line.textContent)).toEqual([
      "Baby, I'm not special",
      "Breaking glass",
    ]);
  });

  it("shows plain lyrics when there are no timed lines", async () => {
    trackApi(plainOnlyInfo);

    renderAt("/tracks/2");

    const lyrics = await screen.findByRole("region", { name: "Lyrics" });
    expect(lyrics).toHaveTextContent("Wind in the sky");
    expect(lyrics).toHaveTextContent("and the moon is high");
    expect(screen.queryByRole("checkbox", { name: "Show timestamps" })).not.toBeInTheDocument();
  });

  it("explains how to add lyrics when the track has none", async () => {
    trackApi(noLyricsInfo);

    renderAt("/tracks/3");

    expect(await screen.findByText(/No lyrics found for this track/)).toHaveTextContent(
      "wj-music scan",
    );
    expect(screen.queryByRole("searchbox", { name: "Find in lyrics" })).not.toBeInTheDocument();
  });

  it("highlights matches while finding in the lyrics and counts them", async () => {
    trackApi();
    const user = userEvent.setup();
    renderAt("/tracks/1");
    await screen.findByRole("region", { name: "Lyrics" });

    await user.type(screen.getByRole("searchbox", { name: "Find in lyrics" }), "glass");

    const marks = screen.getAllByText("glass", { selector: "mark" });
    expect(marks).toHaveLength(1);
    expect(screen.getByText("1 match")).toBeInTheDocument();
  });

  it("says when nothing matches", async () => {
    trackApi();
    const user = userEvent.setup();
    renderAt("/tracks/1");
    await screen.findByRole("region", { name: "Lyrics" });

    await user.type(screen.getByRole("searchbox", { name: "Find in lyrics" }), "zebra");

    expect(screen.getByText("No matches")).toBeInTheDocument();
    expect(within(screen.getByRole("region", { name: "Lyrics" })).queryByText("zebra")).toBeNull();
  });

  it("starts with the find box filled from the URL", async () => {
    trackApi();

    renderAt("/tracks/1?find=special");

    expect(await screen.findByRole("searchbox", { name: "Find in lyrics" })).toHaveValue("special");
    expect(screen.getAllByText("special", { selector: "mark" })).toHaveLength(1);
  });

  it("shows a not-found message for an unknown track", async () => {
    mockApi(() => new Response("not found", { status: 404 }));

    renderAt("/tracks/999");

    expect(await screen.findByRole("heading", { name: "Track not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to albums" })).toHaveAttribute("href", "/albums");
  });

  it("treats a non-numeric id as not found without calling the API", async () => {
    const fetchMock = trackApi();

    renderAt("/tracks/abc");

    expect(await screen.findByRole("heading", { name: "Track not found" })).toBeInTheDocument();
    expect(requestsTo(fetchMock, "/api/tracks/abc")).toEqual([]);
  });

  it("shows an error with a retry button", async () => {
    let attempts = 0;
    mockApi(() => {
      attempts += 1;
      return attempts === 1 ? new Response("boom", { status: 500 }) : breakingGlassInfo;
    });
    const user = userEvent.setup();

    renderAt("/tracks/1");

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load track");
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(
      await screen.findByRole("heading", { name: "Breaking Glass", level: 1 }),
    ).toBeInTheDocument();
  });
});
