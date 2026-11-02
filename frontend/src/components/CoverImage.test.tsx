import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { clearAuth, setToken } from "../api/auth";
import { CoverImage } from "./CoverImage";

const revoke = vi.fn();

describe("CoverImage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    URL.createObjectURL = vi.fn(() => "blob:cover-1");
    URL.revokeObjectURL = revoke;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    clearAuth();
  });

  it("is a plain image when there is no token", () => {
    render(<CoverImage src="/api/albums/1/cover" alt="Cover of Low" className="cover" />);

    expect(screen.getByRole("img", { name: "Cover of Low" })).toHaveAttribute(
      "src",
      "/api/albums/1/cover",
    );
    expect(fetch).not.toHaveBeenCalled();
  });

  it("fetches the image with the token and shows it from a blob", async () => {
    setToken("secret");
    vi.mocked(fetch).mockResolvedValue(new Response(new Blob(["jpeg"]), { status: 200 }));

    render(<CoverImage src="/api/albums/1/cover" alt="Cover of Low" className="cover" />);

    const image = await screen.findByRole("img", { name: "Cover of Low" });
    expect(image).toHaveAttribute("src", "blob:cover-1");
    const [url, init] = vi.mocked(fetch).mock.calls[0] ?? [];
    expect(url).toBe("/api/albums/1/cover");
    expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer secret");
  });

  it("shows a placeholder while loading and when the image cannot be fetched", async () => {
    setToken("secret");
    vi.mocked(fetch).mockResolvedValue(new Response("nope", { status: 404 }));

    const { container } = render(
      <CoverImage src="/api/albums/1/cover" alt="Cover of Low" className="cover" />,
    );

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(container.querySelector(".cover-placeholder")).toBeInTheDocument();
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("releases the blob when it goes away", async () => {
    setToken("secret");
    vi.mocked(fetch).mockResolvedValue(new Response(new Blob(["jpeg"]), { status: 200 }));

    const { unmount } = render(<CoverImage src="/api/albums/1/cover" alt="Cover" />);
    await screen.findByRole("img", { name: "Cover" });
    unmount();

    expect(revoke).toHaveBeenCalledWith("blob:cover-1");
  });
});
