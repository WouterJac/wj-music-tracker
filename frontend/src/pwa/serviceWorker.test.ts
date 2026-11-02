import { beforeEach, describe, expect, it, vi } from "vitest";

import source from "../../public/sw.js?raw";

type Handler = (event: unknown) => void;

interface FakeCache {
  match: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  addAll: ReturnType<typeof vi.fn>;
}

const ORIGIN = "https://music.example";

/** Runs sw.js against a fake service worker scope and returns what it registered. */
function loadWorker() {
  const handlers = new Map<string, Handler>();
  const stored = new Map<string, Response>();
  const cache: FakeCache = {
    match: vi.fn((key: string) => Promise.resolve(stored.get(key)?.clone())),
    put: vi.fn((key: string, response: Response) => {
      stored.set(key, response);
      return Promise.resolve();
    }),
    addAll: vi.fn(() => Promise.resolve()),
  };
  const caches = {
    open: vi.fn(() => Promise.resolve(cache)),
    keys: vi.fn(() => Promise.resolve(["wj-shell-old", "wj-shell-v1"])),
    delete: vi.fn(() => Promise.resolve(true)),
  };
  const self = {
    location: { origin: ORIGIN },
    addEventListener: (type: string, handler: Handler) => handlers.set(type, handler),
    skipWaiting: vi.fn(() => Promise.resolve()),
    clients: { claim: vi.fn(() => Promise.resolve()) },
  };
  const fetchMock = vi.fn<(request: unknown) => Promise<Response>>();
  // The worker is a plain script that expects `self`, `caches` and `fetch` as globals, so it is
  // run with fakes for them.
  // eslint-disable-next-line @typescript-eslint/no-implied-eval, @typescript-eslint/no-unsafe-call
  new Function("self", "caches", "fetch", source)(self, caches, fetchMock);
  return { handlers, cache, caches, stored, fetchMock, self };
}

function fetchEvent(path: string, init: { method?: string; mode?: string; origin?: string } = {}) {
  return {
    request: {
      method: init.method ?? "GET",
      mode: init.mode ?? "cors",
      url: `${init.origin ?? ORIGIN}${path}`,
    },
    respondWith: vi.fn(),
  };
}

async function answer(event: ReturnType<typeof fetchEvent>): Promise<Response> {
  expect(event.respondWith).toHaveBeenCalledTimes(1);
  return await (event.respondWith.mock.calls[0] as [Promise<Response>])[0];
}

describe("service worker", () => {
  let worker: ReturnType<typeof loadWorker>;

  beforeEach(() => {
    worker = loadWorker();
  });

  it("caches the app shell when installed and takes over at once", async () => {
    const waited: Promise<unknown>[] = [];
    worker.handlers.get("install")?.({ waitUntil: (p: Promise<unknown>) => waited.push(p) });
    await Promise.all(waited);

    expect(worker.cache.addAll).toHaveBeenCalledWith(["/"]);
    expect(worker.self.skipWaiting).toHaveBeenCalled();
  });

  it("drops caches from older versions when activated", async () => {
    const waited: Promise<unknown>[] = [];
    worker.handlers.get("activate")?.({ waitUntil: (p: Promise<unknown>) => waited.push(p) });
    await Promise.all(waited);

    expect(worker.caches.delete).toHaveBeenCalledWith("wj-shell-old");
    expect(worker.caches.delete).not.toHaveBeenCalledWith("wj-shell-v1");
  });

  it.each(["/api/albums", "/api/albums/1/cover", "/api/pair", "/health"])(
    "never touches %s, so no data or token is ever cached",
    (path) => {
      const event = fetchEvent(path);

      worker.handlers.get("fetch")?.(event);

      expect(event.respondWith).not.toHaveBeenCalled();
      expect(worker.cache.put).not.toHaveBeenCalled();
    },
  );

  it("ignores requests that are not plain same-origin GETs", () => {
    for (const event of [
      fetchEvent("/assets/app.js", { method: "POST" }),
      fetchEvent("/assets/app.js", { origin: "https://elsewhere.example" }),
    ]) {
      worker.handlers.get("fetch")?.(event);
      expect(event.respondWith).not.toHaveBeenCalled();
    }
  });

  it("serves built assets from the cache first", async () => {
    worker.stored.set("/assets/app.js", new Response("cached js"));
    const event = fetchEvent("/assets/app.js");

    worker.handlers.get("fetch")?.(event);

    expect(await (await answer(event)).text()).toBe("cached js");
    expect(worker.fetchMock).not.toHaveBeenCalled();
  });

  it("fetches a built asset once and remembers it", async () => {
    worker.fetchMock.mockResolvedValue(new Response("fresh js"));
    const event = fetchEvent("/assets/app.js");

    worker.handlers.get("fetch")?.(event);

    expect(await (await answer(event)).text()).toBe("fresh js");
    expect(worker.cache.put).toHaveBeenCalledWith("/assets/app.js", expect.any(Response));
  });

  it("loads pages from the network and keeps the latest shell", async () => {
    worker.fetchMock.mockResolvedValue(new Response("<html>new</html>"));
    const event = fetchEvent("/albums/3", { mode: "navigate" });

    worker.handlers.get("fetch")?.(event);

    expect(await (await answer(event)).text()).toBe("<html>new</html>");
    expect(worker.cache.put).toHaveBeenCalledWith("/", expect.any(Response));
  });

  it("opens the cached shell when a page cannot be fetched", async () => {
    worker.stored.set("/", new Response("<html>shell</html>"));
    worker.fetchMock.mockRejectedValue(new TypeError("offline"));
    const event = fetchEvent("/albums/3", { mode: "navigate" });

    worker.handlers.get("fetch")?.(event);

    expect(await (await answer(event)).text()).toBe("<html>shell</html>");
  });

  it("does not cache an error page as the shell", async () => {
    worker.fetchMock.mockResolvedValue(new Response("nope", { status: 500 }));
    const event = fetchEvent("/", { mode: "navigate" });

    worker.handlers.get("fetch")?.(event);
    await answer(event);

    expect(worker.cache.put).not.toHaveBeenCalled();
  });
});
