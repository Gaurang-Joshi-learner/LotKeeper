import { describe, expect, it } from "vitest";
import { formatCountdown, formatPrice, timeAgo, vehicleTitle } from "./format";

describe("format helpers", () => {
  it("formats prices as whole dollars", () => {
    expect(formatPrice(24999.99)).toBe("$25,000");
  });

  it("formats countdowns and clamps below zero", () => {
    expect(formatCountdown(605)).toBe("10:05");
    expect(formatCountdown(9)).toBe("0:09");
    expect(formatCountdown(-4)).toBe("0:00");
  });

  it("builds a title and skips a missing year", () => {
    expect(vehicleTitle({ year: 2025, make: "Honda", model: "Civic" })).toBe("2025 Honda Civic");
    expect(vehicleTitle({ year: null, make: "Honda", model: "Civic" })).toBe("Honda Civic");
  });

  it("describes elapsed time", () => {
    const now = Date.parse("2026-01-01T12:00:00Z");
    expect(timeAgo("2026-01-01T11:59:58Z", now)).toBe("just now");
    expect(timeAgo("2026-01-01T11:55:00Z", now)).toBe("5m ago");
    expect(timeAgo("2025-12-30T12:00:00Z", now)).toBe("2d ago");
  });
});
