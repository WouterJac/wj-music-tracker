import { describe, expect, it } from "vitest";

import { formatChannels, formatDuration, formatQuality, formatTotalDuration } from "./format";

describe("formatDuration", () => {
  it.each([
    [0, "0:00"],
    [59.4, "0:59"],
    [200, "3:20"],
    [111.5, "1:52"],
    [3725, "62:05"],
  ])("formats %s seconds as %s", (seconds, expected) => {
    expect(formatDuration(seconds)).toBe(expected);
  });
});

describe("formatTotalDuration", () => {
  it.each([
    [10, "1 min"],
    [350, "6 min"],
    [3600, "1 h"],
    [4500, "1 h 15 min"],
  ])("formats %s seconds as %s", (seconds, expected) => {
    expect(formatTotalDuration(seconds)).toBe(expected);
  });
});

describe("formatQuality", () => {
  it.each([
    [16, 44100, "16-bit / 44.1 kHz"],
    [24, 96000, "24-bit / 96 kHz"],
    [24, 88200, "24-bit / 88.2 kHz"],
  ])("formats %s-bit at %s Hz as %s", (bitDepth, sampleRate, expected) => {
    expect(formatQuality(bitDepth, sampleRate)).toBe(expected);
  });
});

describe("formatChannels", () => {
  it.each([
    [1, "Mono"],
    [2, "Stereo"],
    [6, "6 channels"],
  ])("formats %s channels as %s", (channels, expected) => {
    expect(formatChannels(channels)).toBe(expected);
  });
});
