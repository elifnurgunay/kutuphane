import { describe, expect, it } from "vitest";
import { classifyScan } from "./scan";

describe("classifyScan", () => {
  it("üye numarasını ve barkodu ayırır", () => {
    expect(classifyScan("UYE-000001")).toBe("member");
    expect(classifyScan("  uye-000001 ")).toBe("member");
    expect(classifyScan("KTP-0012-01")).toBe("copy");
    expect(classifyScan("   ")).toBe("empty");
  });
});
