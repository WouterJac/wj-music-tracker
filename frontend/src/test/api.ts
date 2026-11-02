import { vi } from "vitest";

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function toUrl(input: string | URL | Request): URL {
  const text = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
  return new URL(text, "http://localhost");
}

/**
 * Replaces fetch. The handler receives the request URL and returns a JSON body or a Response.
 * /health always answers ok so the layout's status line never needs its own setup.
 */
export function mockApi(handler: (url: URL) => unknown) {
  const fetchMock = vi.fn((input: string | URL | Request) => {
    const url = toUrl(input);
    if (url.pathname === "/health") {
      return Promise.resolve(jsonResponse({ status: "ok", version: "0.1.0" }));
    }
    const result = handler(url);
    return Promise.resolve(result instanceof Response ? result : jsonResponse(result));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/** The URLs the app requested for one API path, in order. */
export function requestsTo(fetchMock: ReturnType<typeof mockApi>, pathname: string): URL[] {
  return fetchMock.mock.calls.map(([input]) => toUrl(input)).filter((u) => u.pathname === pathname);
}
