import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { LibraryStats } from "../../api/library";
import { jsonResponse, mockApi } from "../../test/api";
import { renderAt } from "../../test/render";

const bucket = (label: string, count: number) => ({ label, count });

const stats: LibraryStats = {
  tracks: 198,
  albums: 16,
  artists: 4,
  total_duration_seconds: 3 * 3600 + 25 * 60,
  hires_tracks: 50,
  albums_by_decade: [bucket("1970s", 4), bucket("2000s", 12)],
  albums_by_year: [bucket("1977", 2), bucket("2003", 12)],
  tracks_by_format: [bucket("16-bit / 44.1 kHz", 148), bucket("24-bit / 96 kHz", 50)],
  tracks_by_channels: [bucket("Stereo", 198)],
  tracks_by_genre: [bucket("Rock", 120)],
  albums_by_track_count: [bucket("11–15 tracks", 9)],
  albums_by_length: [bucket("40–60 min", 7)],
  top_artists: [{ id: 2, name: "Brian Eno", tracks: 30, albums: 3 }],
};

const empty: LibraryStats = {
  ...stats,
  tracks: 0,
  albums: 0,
  artists: 0,
  total_duration_seconds: 0,
  hires_tracks: 0,
  albums_by_decade: [],
  albums_by_year: [],
  tracks_by_format: [],
  tracks_by_channels: [],
  tracks_by_genre: [],
  albums_by_track_count: [],
  albums_by_length: [],
  top_artists: [],
};

describe("StatsPage", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows the totals as labelled tiles", async () => {
    mockApi(() => stats);
    renderAt("/stats");

    const totals = await screen.findByRole("region", { name: "Totals" });
    expect(within(totals).getByText("198")).toBeInTheDocument();
    expect(within(totals).getByText("Tracks")).toBeInTheDocument();
    expect(within(totals).getByText("16")).toBeInTheDocument();
    expect(within(totals).getByText("3 h 25 min")).toBeInTheDocument();
    expect(within(totals).getByText("25%")).toBeInTheDocument();
    expect(within(totals).getByText("50 hi-res tracks")).toBeInTheDocument();
  });

  it.each([
    "Albums by decade",
    "Albums by year",
    "Tracks by format",
    "Tracks by channels",
    "Tracks by genre",
    "Tracks per album",
    "Album length",
    "Top artists",
  ])("has the %s chart", async (title) => {
    mockApi(() => stats);
    renderAt("/stats");

    expect(await screen.findByRole("figure", { name: title })).toBeInTheDocument();
  });

  it("links top artists to their page", async () => {
    mockApi(() => stats);
    renderAt("/stats");

    const link = await screen.findByRole("link", { name: /Brian Eno/ });
    expect(link).toHaveAttribute("href", "/artists/2");
  });

  it("leaves out a chart that has no data, such as genre when no file is tagged", async () => {
    mockApi(() => ({ ...stats, tracks_by_genre: [] }));
    renderAt("/stats");

    await screen.findByRole("figure", { name: "Albums by decade" });
    expect(screen.queryByRole("figure", { name: "Tracks by genre" })).not.toBeInTheDocument();
  });

  it("shows a skeleton while loading", () => {
    mockApi(() => new Promise(() => {}));
    renderAt("/stats");

    expect(screen.getByRole("status", { name: "Loading statistics" })).toBeInTheDocument();
  });

  it("explains how to fill an empty library", async () => {
    mockApi(() => empty);
    renderAt("/stats");

    expect(await screen.findByText(/No tracks yet/)).toBeInTheDocument();
    expect(screen.getByText("wj-music scan")).toBeInTheDocument();
    expect(screen.queryByRole("figure")).not.toBeInTheDocument();
  });

  it("offers a retry when the backend fails", async () => {
    let fail = true;
    mockApi(() => (fail ? jsonResponse({}, 500) : stats));
    renderAt("/stats");

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load statistics");
    fail = false;
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("region", { name: "Totals" })).toBeInTheDocument();
  });

  it("is reachable from the main navigation", () => {
    mockApi(() => stats);
    renderAt("/albums");

    expect(screen.getByRole("link", { name: "Statistics" })).toHaveAttribute("href", "/stats");
  });
});
