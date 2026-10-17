import { describe, expect, it } from "vitest";
import { homePathFor } from "./roles";

describe("homePathFor", () => {
  it("personeli panele, üyeyi hesabına yönlendirir", () => {
    expect(homePathFor("admin")).toBe("/panel");
    expect(homePathFor("librarian")).toBe("/panel");
    expect(homePathFor("member")).toBe("/hesabim");
  });
});
