// README ekran görüntülerini üretir (docs/screenshots).
// Önkoşul: backend (seed verisiyle) ve `npm run dev` çalışıyor olmalı.
// Kullanım: node scripts/screenshots.mjs   (bilgisayardaki Edge'i kullanır; tarayıcı indirmez)
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const BASE = process.env.APP_URL ?? "http://localhost:5173";
const OUT = fileURLToPath(new URL("../../docs/screenshots/", import.meta.url));
// Seed verisindeki varsayılan geliştirme hesapları (README'de listeli)
const STAFF = { email: "gorevli1@kutuphane.local", password: "Gorevli123!" };
const ADMIN = { email: "admin@kutuphane.local", password: "Admin123!" };
const MEMBER = { email: "ayse.yilmaz@kutuphane.local", password: "Uye12345!" };

async function tokens({ email, password }) {
  const response = await fetch(`${BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw new Error(`Giriş başarısız: ${email}`);
  return response.json();
}

async function session(browser, account, viewport = { width: 1280, height: 800 }) {
  const context = await browser.newContext({ viewport, locale: "tr-TR" });
  if (account) {
    const pair = await tokens(account);
    await context.addInitScript((p) => {
      localStorage.setItem("kutuphane.access_token", p.access_token);
      localStorage.setItem("kutuphane.refresh_token", p.refresh_token);
    }, pair);
  }
  return context.newPage();
}

async function shot(page, path, file, prepare) {
  await page.goto(`${BASE}${path}`);
  await page.waitForLoadState("networkidle");
  if (prepare) await prepare(page);
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${OUT}${file}` });
  console.log(`✓ ${file}`);
}

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ channel: "msedge" });
try {
  const guest = await session(browser, null);
  await shot(guest, "/giris", "01-giris.png");

  const staff = await session(browser, STAFF);
  await shot(staff, "/panel", "02-gosterge-paneli.png");
  await shot(staff, "/islem", "03-hizli-islem.png", async (page) => {
    const input = page.getByLabel("Üye numarası veya barkod");
    await input.fill("UYE-000001");
    await input.press("Enter");
    await page.getByText("Elindeki kitaplar").waitFor();
    await input.fill("KTP-0001-01");
    await input.press("Enter");
    await page.getByRole("button", { name: "Ödünç ver" }).waitFor();
  });
  await shot(staff, "/kitaplar", "04-kitaplar.png");
  await shot(staff, "/kitaplar/12", "05-kitap-detay.png");
  await shot(staff, "/uyeler/1", "06-uye-detay.png");
  await shot(staff, "/oduncler", "07-oduncler.png");
  await shot(staff, "/raporlar?rapor=category-stats", "08-raporlar.png");

  const admin = await session(browser, ADMIN);
  await shot(admin, "/ayarlar", "09-ayarlar.png");

  const member = await session(browser, MEMBER);
  await shot(member, "/hesabim", "10-uye-odunclerim.png");
  await shot(member, "/katalog", "11-uye-katalog.png");

  const mobile = await session(browser, STAFF, { width: 390, height: 844 });
  await shot(mobile, "/panel", "12-mobil.png");
} finally {
  await browser.close();
}
