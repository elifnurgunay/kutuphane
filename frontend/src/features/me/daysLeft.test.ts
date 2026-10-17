import { describe, expect, it } from "vitest";
import { daysLeft } from "./api";

describe("daysLeft", () => {
  it("kalan ve geçen günleri hesaplar", () => {
    expect(daysLeft("2026-10-25", "2026-10-17")).toBe(8);
    expect(daysLeft("2026-10-17", "2026-10-17")).toBe(0);
    expect(daysLeft("2026-10-15", "2026-10-17")).toBe(-2);
    expect(daysLeft("2027-01-01", "2026-12-31")).toBe(1);
  });
});
