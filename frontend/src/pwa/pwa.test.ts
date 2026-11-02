import { afterEach, describe, expect, it, vi } from "vitest";

import indexHtml from "../../index.html?raw";
import manifestText from "../../public/manifest.webmanifest?raw";
import { registerServiceWorker } from "./register";

const publicFiles = import.meta.glob("../../public/*", { query: "?url", eager: true });

interface Manifest {
  name: string;
  short_name: string;
  start_url: string;
  display: string;
  background_color: string;
  theme_color: string;
  icons: { src: string; sizes: string; type: string; purpose?: string }[];
}

function manifest(): Manifest {
  return JSON.parse(manifestText) as Manifest;
}

describe("manifest", () => {
  it("makes the app installable as a standalone app", () => {
    const m = manifest();

    expect(m.name).toBe("WJ Music Tracker");
    expect(m.short_name.length).toBeLessThanOrEqual(12);
    expect(m.display).toBe("standalone");
    expect(m.start_url).toBe("/");
    expect(m.theme_color).toMatch(/^#[0-9a-f]{6}$/i);
    expect(m.background_color).toMatch(/^#[0-9a-f]{6}$/i);
  });

  it("lists 192 and 512 pixel icons that exist, plus a maskable one", () => {
    const { icons } = manifest();

    expect(icons.map((icon) => icon.sizes)).toEqual(expect.arrayContaining(["192x192", "512x512"]));
    expect(icons.some((icon) => icon.purpose?.includes("maskable"))).toBe(true);
    for (const icon of icons) {
      expect(icon.type).toBe("image/png");
      expect(Object.keys(publicFiles)).toContain(`../../public${icon.src}`);
    }
  });
});

describe("index.html", () => {
  it("links the manifest, the touch icon and the theme colour", () => {
    expect(indexHtml).toContain('rel="manifest" href="/manifest.webmanifest"');
    expect(indexHtml).toContain('rel="apple-touch-icon"');
    expect(indexHtml).toContain('name="theme-color"');
    expect(Object.keys(publicFiles)).toContain("../../public/apple-touch-icon.png");
  });

  it("lets the page use the whole screen on phones with notches", () => {
    expect(indexHtml).toContain("viewport-fit=cover");
  });
});

describe("registerServiceWorker", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    Reflect.deleteProperty(navigator, "serviceWorker");
  });

  it("registers /sw.js once the page has loaded", () => {
    const register = vi.fn(() => Promise.resolve({}));
    Object.defineProperty(navigator, "serviceWorker", { value: { register }, configurable: true });

    registerServiceWorker();
    expect(register).not.toHaveBeenCalled();
    window.dispatchEvent(new Event("load"));

    expect(register).toHaveBeenCalledWith("/sw.js");
  });

  it("logs a failed registration instead of breaking the app", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    const register = vi.fn(() => Promise.reject(new Error("blocked")));
    Object.defineProperty(navigator, "serviceWorker", { value: { register }, configurable: true });

    registerServiceWorker();
    window.dispatchEvent(new Event("load"));
    await vi.waitFor(() => {
      expect(error).toHaveBeenCalled();
    });
  });

  it("does nothing where service workers do not exist", () => {
    expect(() => {
      registerServiceWorker();
    }).not.toThrow();
  });
});
