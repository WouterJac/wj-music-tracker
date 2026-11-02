import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch, clearAuth, getToken, isPairingNeeded, pair, setToken } from "./auth";

function respond(status: number, body: unknown = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function jsonBody(init?: RequestInit): unknown {
  const body = init?.body;
  if (typeof body !== "string") throw new Error("the request had no JSON body");
  return JSON.parse(body) as unknown;
}

describe("apiFetch", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    clearAuth();
  });

  it("calls fetch exactly as given when there is no token", async () => {
    vi.mocked(fetch).mockResolvedValue(respond(200));

    await apiFetch("/api/albums");
    await apiFetch("/api/scan", { method: "POST" });

    expect(fetch).toHaveBeenNthCalledWith(1, "/api/albums");
    expect(fetch).toHaveBeenNthCalledWith(2, "/api/scan", { method: "POST" });
  });

  it("sends the stored token as a Bearer header and keeps other options", async () => {
    setToken("secret-token");
    vi.mocked(fetch).mockResolvedValue(respond(200));

    await apiFetch("/api/scan", { method: "POST" });

    const [url, init] = vi.mocked(fetch).mock.calls[0] ?? [];
    expect(url).toBe("/api/scan");
    expect(init?.method).toBe("POST");
    expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer secret-token");
  });

  it("forgets the token and asks for pairing when the server answers 401", async () => {
    setToken("stale");
    vi.mocked(fetch).mockResolvedValue(respond(401));

    const response = await apiFetch("/api/albums");

    expect(response.status).toBe(401);
    expect(getToken()).toBeNull();
    expect(isPairingNeeded()).toBe(true);
  });

  it("asks for pairing on 401 even when no token was stored yet", async () => {
    vi.mocked(fetch).mockResolvedValue(respond(401));

    await apiFetch("/api/albums");

    expect(isPairingNeeded()).toBe(true);
  });

  it("leaves the token alone for other errors", async () => {
    setToken("keep");
    vi.mocked(fetch).mockResolvedValue(respond(500));

    await apiFetch("/api/albums");

    expect(getToken()).toBe("keep");
    expect(isPairingNeeded()).toBe(false);
  });
});

describe("pair", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    clearAuth();
  });

  it("posts the code as JSON, stores the token and stops asking for pairing", async () => {
    vi.mocked(fetch).mockResolvedValue(respond(200, { token: "new-token" }));

    await pair("ABCD-2345");

    const [url, init] = vi.mocked(fetch).mock.calls[0] ?? [];
    expect(url).toBe("/api/pair");
    expect(init?.method).toBe("POST");
    expect(jsonBody(init)).toEqual({ code: "ABCD-2345" });
    expect(getToken()).toBe("new-token");
    expect(isPairingNeeded()).toBe(false);
  });

  it("explains a wrong or expired code", async () => {
    vi.mocked(fetch).mockResolvedValue(respond(401, { detail: "no" }));

    await expect(pair("WRONG")).rejects.toThrow(/wrong or has expired/);
    expect(getToken()).toBeNull();
  });

  it("explains rate limiting", async () => {
    vi.mocked(fetch).mockResolvedValue(respond(429));

    await expect(pair("WRONG")).rejects.toThrow(/Too many attempts/);
  });

  it("gives a generic message for other failures", async () => {
    vi.mocked(fetch).mockResolvedValue(respond(500));

    await expect(pair("WRONG")).rejects.toThrow(/Could not pair/);
  });

  it("rejects a reply without a token", async () => {
    vi.mocked(fetch).mockResolvedValue(respond(200, { nope: true }));

    await expect(pair("ABCD-2345")).rejects.toThrow(/Could not pair/);
    expect(getToken()).toBeNull();
  });
});
