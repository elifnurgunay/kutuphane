import { describe, expect, it } from "vitest";
import { addDaysIso, todayIso } from "../../lib/format";
import { dueState } from "./dueState";

describe("dueState", () => {
  it("vadesi geçmiş, yaklaşan ve normal ödünçleri ayırır", () => {
    expect(dueState("2026-10-16", "2026-10-17")).toBe("overdue");
    expect(dueState("2026-10-17", "2026-10-17")).toBe("soon");
    expect(dueState("2026-10-19", "2026-10-17")).toBe("soon");
    expect(dueState("2026-10-20", "2026-10-17")).toBe("ok");
  });
});

describe("tarih yardımcıları", () => {
  it("ay ve yıl sınırını aşarak gün ekler", () => {
    expect(addDaysIso("2026-12-31", 1)).toBe("2027-01-01");
    expect(addDaysIso("2026-02-28", 365)).toBe("2027-02-28");
  });

  it("bugünü yerel saatle verir", () => {
    expect(todayIso(new Date(2026, 9, 7))).toBe("2026-10-07");
  });
});
