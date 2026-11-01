import { describe, expect, it } from "vitest";

import { countMatches, splitMatches } from "./highlight";

describe("splitMatches", () => {
  it("marks every match and keeps the original text", () => {
    expect(splitMatches("Hello hello", "hell")).toEqual([
      { text: "Hell", match: true },
      { text: "o ", match: false },
      { text: "hell", match: true },
      { text: "o", match: false },
    ]);
  });

  it("returns the text unchanged for an empty query", () => {
    expect(splitMatches("Hello", "")).toEqual([{ text: "Hello", match: false }]);
  });

  it("returns the text unchanged when nothing matches", () => {
    expect(splitMatches("Hello", "xyz")).toEqual([{ text: "Hello", match: false }]);
  });

  it("treats regex characters literally", () => {
    expect(splitMatches("is it (really) so?", "(really)")).toEqual([
      { text: "is it ", match: false },
      { text: "(really)", match: true },
      { text: " so?", match: false },
    ]);
  });

  it("matches non-ASCII text ignoring case", () => {
    expect(splitMatches("Va à l'ÉCOLE", "école")).toEqual([
      { text: "Va à l'", match: false },
      { text: "ÉCOLE", match: true },
    ]);
  });

  it("ignores a query that is only whitespace", () => {
    expect(splitMatches("a b", "  ")).toEqual([{ text: "a b", match: false }]);
  });
});

describe("countMatches", () => {
  it.each([
    [["Breaking glass", "glass door"], "glass", 2],
    [["aaa"], "aa", 1],
    [["nothing here"], "zebra", 0],
    [["anything"], "", 0],
  ])("counts %j for %s as %s", (lines, query, expected) => {
    expect(countMatches(lines, query)).toBe(expected);
  });
});
