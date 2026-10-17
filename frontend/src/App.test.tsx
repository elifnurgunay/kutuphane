import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
  it("başlığı gösterir", () => {
    expect(renderToString(<App />)).toContain("Kütüphane Otomasyon Sistemi");
  });
});
