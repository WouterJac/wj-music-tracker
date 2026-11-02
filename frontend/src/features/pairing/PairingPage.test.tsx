import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { clearAuth, getToken, setToken } from "../../api/auth";
import { jsonResponse, mockApi, requestsTo } from "../../test/api";
import { low } from "../../test/fixtures";
import { renderAt } from "../../test/render";

const TOKEN = "the-access-token";
const albums = { items: [low], total: 1, limit: 24, offset: 0 };

/** A server that wants the token: /api/albums is 401 until the app has paired. */
function lockedApi(pairResponse: () => Response = () => jsonResponse({ token: TOKEN })) {
  return mockApi((url) => {
    if (url.pathname === "/api/pair") return pairResponse();
    if (url.pathname === "/api/albums") {
      return getToken() === TOKEN
        ? albums
        : jsonResponse({ detail: "Authentication required" }, 401);
    }
    throw new Error(`unexpected request ${url.pathname}`);
  });
}

function jsonBody(init?: RequestInit): unknown {
  const body = init?.body;
  if (typeof body !== "string") throw new Error("the request had no JSON body");
  return JSON.parse(body) as unknown;
}

function urlOf(input: string | URL | Request): string {
  return typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
}

describe("pairing", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    clearAuth();
  });

  it("asks for the code when the API answers 401", async () => {
    lockedApi();
    renderAt("/albums");

    expect(await screen.findByRole("heading", { name: "Pair this device" })).toBeInTheDocument();
    expect(screen.getByLabelText("Pairing code")).toBeInTheDocument();
    expect(screen.getByText("wj-music pair")).toBeInTheDocument();
  });

  it("pairs with the code, then shows the library and sends the token", async () => {
    const fetchMock = lockedApi();
    renderAt("/albums");

    await userEvent.type(await screen.findByLabelText("Pairing code"), "abcd-2345");
    await userEvent.click(screen.getByRole("button", { name: "Pair" }));

    expect(await screen.findByRole("link", { name: /Low/ })).toBeInTheDocument();
    const pairCall = fetchMock.mock.calls.find(([input]) => input === "/api/pair");
    expect(jsonBody(pairCall?.[1])).toEqual({ code: "abcd-2345" });
    expect(getToken()).toBe(TOKEN);
    const lastAlbums = fetchMock.mock.calls.filter(([input]) =>
      urlOf(input).startsWith("/api/albums"),
    );
    const headers = new Headers(lastAlbums.at(-1)?.[1]?.headers);
    expect(headers.get("Authorization")).toBe(`Bearer ${TOKEN}`);
  });

  it("never puts the token in a URL", async () => {
    const fetchMock = lockedApi();
    renderAt("/albums");

    await userEvent.type(await screen.findByLabelText("Pairing code"), "ABCD2345");
    await userEvent.click(screen.getByRole("button", { name: "Pair" }));
    await screen.findByRole("link", { name: /Low/ });

    for (const [input] of fetchMock.mock.calls) {
      expect(urlOf(input)).not.toContain(TOKEN);
    }
    expect(window.location.href).not.toContain(TOKEN);
  });

  it("says so when the code is wrong and stays on the pairing screen", async () => {
    lockedApi(() => jsonResponse({ detail: "no" }, 401));
    renderAt("/albums");

    await userEvent.type(await screen.findByLabelText("Pairing code"), "WRONG999");
    await userEvent.click(screen.getByRole("button", { name: "Pair" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("wrong or has expired");
    expect(screen.getByLabelText("Pairing code")).toBeInTheDocument();
    expect(getToken()).toBeNull();
  });

  it("says when there have been too many attempts", async () => {
    lockedApi(() => jsonResponse({ detail: "slow down" }, 429));
    renderAt("/albums");

    await userEvent.type(await screen.findByLabelText("Pairing code"), "WRONG999");
    await userEvent.click(screen.getByRole("button", { name: "Pair" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Too many attempts");
  });

  it("does not submit an empty code", async () => {
    const fetchMock = lockedApi();
    renderAt("/albums");

    await userEvent.click(await screen.findByRole("button", { name: "Pair" }));

    expect(requestsTo(fetchMock, "/api/pair")).toHaveLength(0);
  });

  it("returns to pairing when a stored token stops working", async () => {
    setToken("revoked");
    lockedApi();
    renderAt("/albums");

    expect(await screen.findByRole("heading", { name: "Pair this device" })).toBeInTheDocument();
    await waitFor(() => {
      expect(getToken()).toBeNull();
    });
  });

  it("goes straight to the app when the stored token works", async () => {
    setToken(TOKEN);
    lockedApi();
    renderAt("/albums");

    expect(await screen.findByRole("link", { name: /Low/ })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Pair this device" })).not.toBeInTheDocument();
  });
});
