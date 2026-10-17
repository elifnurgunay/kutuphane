import { describe, expect, it } from "vitest";
import { formatDate } from "./format";

describe("formatDate", () => {
  it("tarihi gg.aa.yyyy biçimine çevirir", () => {
    expect(formatDate("2026-10-10")).toBe("10.10.2026");
    expect(formatDate("2026-10-17T11:22:33.000Z")).toBe("17.10.2026");
  });

  it("boş değer için tire döner", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate("")).toBe("—");
  });
});
