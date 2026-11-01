import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { mockApi } from "../../test/api";
import { bowieDetail } from "../../test/fixtures";
import { renderAt } from "../../test/render";

describe("ArtistDetailPage", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows a loading skeleton while the artist loads", () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));

    renderAt("/artists/1");

    expect(screen.getByRole("status", { name: "Loading artist" })).toBeInTheDocument();
  });

  it("shows the artist with their albums linking to album pages", async () => {
    mockApi(() => bowieDetail);

    renderAt("/artists/1");

    expect(await screen.findByRole("heading", { name: "David Bowie", level: 1 })).toBeVisible();
    expect(screen.getByText("2 albums")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Low/ })).toHaveAttribute("href", "/albums/1");
    expect(screen.getByRole("link", { name: /Heroes/ })).toHaveAttribute("href", "/albums/2");
  });

  it("says so when the artist has no albums", async () => {
    mockApi(() => ({ ...bowieDetail, albums: [] }));

    renderAt("/artists/1");

    expect(await screen.findByText("No albums found for this artist.")).toBeInTheDocument();
  });

  it("shows a not-found message for an unknown artist", async () => {
    mockApi(() => new Response("not found", { status: 404 }));

    renderAt("/artists/999");

    expect(await screen.findByRole("heading", { name: "Artist not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to artists" })).toHaveAttribute(
      "href",
      "/artists",
    );
  });

  it("treats a non-numeric id as not found", async () => {
    mockApi(() => bowieDetail);

    renderAt("/artists/abc");

    expect(await screen.findByRole("heading", { name: "Artist not found" })).toBeInTheDocument();
  });

  it("shows an error with a retry button", async () => {
    let attempts = 0;
    mockApi(() => {
      attempts += 1;
      return attempts === 1 ? new Response("boom", { status: 500 }) : bowieDetail;
    });
    const user = userEvent.setup();

    renderAt("/artists/1");

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load artist");
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: "David Bowie", level: 1 })).toBeVisible();
  });
});
