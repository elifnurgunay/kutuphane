import { describe, expect, it } from "vitest";
import { toQueryString } from "./types";

describe("toQueryString", () => {
  it("boş değerleri atlar", () => {
    expect(
      toQueryString({ q: "suç ve ceza", page: 2, available: true, category: undefined, x: "" }),
    ).toBe("?q=su%C3%A7+ve+ceza&page=2&available=true");
  });

  it("hiç değer yoksa boş döner", () => {
    expect(toQueryString({ q: undefined })).toBe("");
  });
});
