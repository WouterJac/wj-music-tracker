import { describe, expect, it } from "vitest";

import { NotFoundError } from "./library";
import { shouldRetry } from "./queryClient";

describe("shouldRetry", () => {
  it("never retries a 404, because the item will not appear by asking again", () => {
    expect(shouldRetry(0, new NotFoundError("/api/albums/9 not found"))).toBe(false);
  });

  it.each([0, 1])("retries other failures (attempt %s)", (failureCount) => {
    expect(shouldRetry(failureCount, new Error("network down"))).toBe(true);
  });

  it("gives up on other failures after two retries", () => {
    expect(shouldRetry(2, new Error("network down"))).toBe(false);
  });
});
