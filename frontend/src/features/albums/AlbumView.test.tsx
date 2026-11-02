import { screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { mockApi } from "../../test/api";
import { lowDetail } from "../../test/fixtures";
import { renderAt } from "../../test/render";

function viewRequests(fetchMock: ReturnType<typeof mockApi>) {
  return fetchMock.mock.calls.filter(
    ([input, init]) => input === "/api/albums/1/view" && init?.method === "POST",
  );
}

describe("Recording album views", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("notes a view when an album page is opened", async () => {
    const fetchMock = mockApi((url) => {
      if (url.pathname === "/api/albums/1") return lowDetail;
      if (url.pathname === "/api/albums/1/view") return new Response(null, { status: 204 });
      return [];
    });
    renderAt("/albums/1");

    await screen.findByRole("heading", { name: "Low", level: 1 });

    await waitFor(() => {
      expect(viewRequests(fetchMock)).toHaveLength(1);
    });
  });

  it("keeps the album usable when the view cannot be recorded", async () => {
    mockApi((url) => {
      if (url.pathname === "/api/albums/1") return lowDetail;
      if (url.pathname === "/api/albums/1/view") return new Response("boom", { status: 500 });
      return [];
    });
    renderAt("/albums/1");

    expect(await screen.findByRole("heading", { name: "Low", level: 1 })).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
