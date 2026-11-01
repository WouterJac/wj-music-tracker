import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { HealthStatus } from "./HealthStatus";

function renderWithClient() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <HealthStatus />
    </QueryClientProvider>,
  );
}

describe("HealthStatus", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows a loading message while the request is pending", () => {
    vi.mocked(fetch).mockReturnValue(new Promise(() => {}));

    renderWithClient();

    expect(screen.getByRole("status")).toHaveTextContent("Checking the server");
  });

  it("shows the server status and version when /health answers ok", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ status: "ok", version: "0.1.0" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    renderWithClient();

    expect(await screen.findByText("Server is ok")).toBeInTheDocument();
    expect(screen.getByText("Version 0.1.0")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith("/health");
  });

  it("shows an error message when /health fails", async () => {
    vi.mocked(fetch).mockResolvedValue(new Response("boom", { status: 500 }));

    renderWithClient();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not reach the server. Check that the backend is running.",
    );
  });
});
