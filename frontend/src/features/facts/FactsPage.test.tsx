import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Fact } from "../../api/library";
import { jsonResponse, mockApi } from "../../test/api";
import { renderAt } from "../../test/render";

const facts: Fact[] = [
  {
    key: "longest_album",
    title: "Longest album",
    text: "Another Green World by Brian Eno runs 1 h 15 min.",
    link: { kind: "album", id: 2 },
  },
  {
    key: "longest_track",
    title: "Longest track",
    text: "“Sky Saw” on Low lasts 2 h 30 min.",
    link: { kind: "track", id: 4 },
  },
  {
    key: "busiest_artist",
    title: "Busiest artist",
    text: "Brian Eno has 30 tracks.",
    link: { kind: "artist", id: 3 },
  },
];

describe("FactsPage", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows each fact with its title and text", async () => {
    mockApi(() => ({ items: facts }));
    renderAt("/facts");

    expect(await screen.findByRole("heading", { name: "Longest album" })).toBeInTheDocument();
    expect(screen.getByText("Another Green World by Brian Eno runs 1 h 15 min.")).toBeVisible();
    expect(screen.getAllByRole("listitem")).toHaveLength(3);
  });

  it.each([
    ["View album for Longest album", "/albums/2"],
    ["View track for Longest track", "/tracks/4"],
    ["View artist for Busiest artist", "/artists/3"],
  ])("links to the item behind a fact: %s", async (name, href) => {
    mockApi(() => ({ items: facts }));
    renderAt("/facts");

    expect(await screen.findByRole("link", { name })).toHaveAttribute("href", href);
  });

  it("shows a skeleton while loading", () => {
    mockApi(() => new Promise(() => {}));
    renderAt("/facts");

    expect(screen.getByRole("status", { name: "Loading facts" })).toBeInTheDocument();
  });

  it("explains an empty library", async () => {
    mockApi(() => ({ items: [] }));
    renderAt("/facts");

    expect(await screen.findByText(/No facts yet/)).toBeInTheDocument();
    expect(screen.getByText("wj-music scan")).toBeInTheDocument();
  });

  it("offers a retry when the backend fails", async () => {
    let fail = true;
    mockApi(() => (fail ? jsonResponse({}, 500) : { items: facts }));
    renderAt("/facts");

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load facts");
    fail = false;
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: "Longest album" })).toBeInTheDocument();
  });

  it("is reachable from the main navigation", () => {
    mockApi(() => ({ items: facts }));
    renderAt("/albums");

    expect(screen.getByRole("link", { name: "Facts" })).toHaveAttribute("href", "/facts");
  });
});
