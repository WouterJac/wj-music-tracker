import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { jsonResponse, mockApi, requestsTo } from "../../test/api";
import { low } from "../../test/fixtures";
import { renderAt } from "../../test/render";

const summary = {
  added: 2,
  changed: 1,
  removed: 0,
  unchanged: 10,
  errors: 0,
  tracks: 13,
  albums: 4,
  artists: 2,
};

function api(scan: () => unknown) {
  return mockApi((url) => {
    if (url.pathname === "/api/scan") return scan();
    if (url.pathname === "/api/albums") {
      return { items: [low], total: 1, limit: 24, offset: 0 };
    }
    throw new Error(`unexpected request ${url.pathname}`);
  });
}

describe("RefreshLibraryButton", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("is available on every page", async () => {
    api(() => summary);
    renderAt("/albums");

    expect(await screen.findByRole("button", { name: "Refresh library" })).toBeEnabled();
  });

  it("posts a scan, shows what changed and reloads the data on screen", async () => {
    const fetchMock = api(() => summary);
    renderAt("/albums");
    await screen.findByRole("link", { name: /Low/ });
    expect(requestsTo(fetchMock, "/api/albums")).toHaveLength(1);

    await userEvent.click(screen.getByRole("button", { name: "Refresh library" }));

    const status = await screen.findByText(/Added 2, changed 1, removed 0/);
    expect(status).toHaveTextContent("13 tracks, 4 albums, 2 artists");
    const scanCall = fetchMock.mock.calls.find(([input]) => input === "/api/scan");
    expect(scanCall?.[1]).toMatchObject({ method: "POST" });
    await waitFor(() => {
      expect(requestsTo(fetchMock, "/api/albums")).toHaveLength(2);
    });
  });

  it("says when nothing changed", async () => {
    api(() => ({ ...summary, added: 0, changed: 0 }));
    renderAt("/albums");

    await userEvent.click(await screen.findByRole("button", { name: "Refresh library" }));

    expect(await screen.findByText(/Nothing changed/)).toBeInTheDocument();
  });

  it("mentions files that could not be read", async () => {
    api(() => ({ ...summary, errors: 2 }));
    renderAt("/albums");

    await userEvent.click(await screen.findByRole("button", { name: "Refresh library" }));

    expect(await screen.findByText(/2 files could not be read/)).toBeInTheDocument();
  });

  it("is disabled and says so while the scan runs", async () => {
    let finish: (response: Response) => void = () => {};
    api(
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve;
        }),
    );
    renderAt("/albums");

    await userEvent.click(await screen.findByRole("button", { name: "Refresh library" }));

    expect(await screen.findByRole("button", { name: "Scanning…" })).toBeDisabled();
    finish(jsonResponse(summary));
    expect(await screen.findByRole("button", { name: "Refresh library" })).toBeEnabled();
  });

  it("shows the reason the server gives when the scan cannot run", async () => {
    api(() => jsonResponse({ detail: "Music folder not found or not a directory: E:/Music" }, 422));
    renderAt("/albums");

    await userEvent.click(await screen.findByRole("button", { name: "Refresh library" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Music folder not found or not a directory: E:/Music",
    );
    expect(screen.getByRole("button", { name: "Refresh library" })).toBeEnabled();
  });

  it("explains a refused scan when one is already running", async () => {
    api(() => jsonResponse({ detail: "A scan is already running" }, 409));
    renderAt("/albums");

    await userEvent.click(await screen.findByRole("button", { name: "Refresh library" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("A scan is already running");
  });

  it("shows a generic message when the server cannot be reached", async () => {
    api(() => new Response("boom", { status: 500 }));
    renderAt("/albums");

    await userEvent.click(await screen.findByRole("button", { name: "Refresh library" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not refresh the library");
  });
});
