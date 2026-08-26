// ==UserScript==
// @name         Anime Bridge - 動畫瘋當季目錄同步
// @namespace    https://github.com/g36ck19941-crypto/baha-qbit
// @version      0.3.0
// @description  從動畫瘋公開「所有動畫」目錄同步本季度上架作品；不讀取帳號、Cookie 或收藏。
// @match        https://ani.gamer.com.tw/
// @match        https://ani.gamer.com.tw/animeList.php*
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// @run-at       document-idle
// ==/UserScript==

(function () {
  "use strict";

  const FORMAT = "anime-bridge-bahamut-current-quarter";
  const MAX_PAGES = 20;
  const BUTTON_ID = "anime-bridge-sync-current-quarter";
  const ENDPOINT = "__ANIME_BRIDGE_ENDPOINT__";
  const BRIDGE_TOKEN = "__ANIME_BRIDGE_BRIDGE_TOKEN__";
  const LAST_SYNC_KEY = "anime-bridge-last-catalog-sync";
  const AUTO_SYNC_INTERVAL_MS = 6 * 60 * 60 * 1000;

  function quarterFor(now = new Date()) {
    return {
      year: now.getFullYear(),
      startMonth: Math.floor(now.getMonth() / 3) * 3 + 1,
    };
  }

  function catalogPageUrl(page) {
    const url = new URL("/animeList.php", location.origin);
    url.searchParams.set("category", "全部");
    url.searchParams.set("sort", "1");
    url.searchParams.set("tags", "全部");
    url.searchParams.set("target", "全部");
    url.searchParams.set("page", String(page));
    return url.href;
  }

  async function readPage(page) {
    const response = await fetch(catalogPageUrl(page), {
      credentials: "omit",
      redirect: "follow",
      headers: { Accept: "text/html" },
    });
    if (!response.ok) throw new Error(`第 ${page} 頁返回 HTTP ${response.status}`);
    const parsed = new DOMParser().parseFromString(await response.text(), "text/html");
    if (/請稍候|just a moment/i.test(parsed.title || "")) {
      throw new Error("頁面返回了人機驗證，請先在瀏覽器完成驗證");
    }
    return parsed;
  }

  function extractPage(doc, page) {
    const elements = [...doc.querySelectorAll(
      ".animate-theme-list > .theme-list-block .theme-list-main, .theme-list-block .theme-list-main"
    )];
    const uniqueElements = [...new Set(elements)];
    return uniqueElements.map((element) => {
      const title = (element.querySelector(".theme-name")?.textContent || "")
        .replace(/\s+/g, " ").trim();
      const timeText = (element.querySelector(".theme-time")?.textContent || "").trim();
      const match = timeText.match(/(20\d{2})\s*[\/／-]\s*(\d{1,2})/);
      const anchor = element.matches("a[href]")
        ? element
        : element.querySelector("a[href*='animeRef.php']");
      if (!title || !match || !anchor) return null;
      const href = new URL(anchor.getAttribute("href"), location.origin);
      if (href.origin !== location.origin || href.pathname !== "/animeRef.php") return null;
      const snText = href.searchParams.get("sn");
      return {
        title,
        href: href.href,
        sn: snText && /^\d+$/.test(snText) ? Number(snText) : null,
        page,
        year: Number(match[1]),
        month: Number(match[2]),
      };
    }).filter(Boolean);
  }

  async function collectCurrentQuarter() {
    const quarter = quarterFor();
    const startKey = quarter.year * 12 + quarter.startMonth;
    const endKey = startKey + 3;
    const items = new Map();
    const warnings = [];
    let pagesScanned = 0;
    let boundaryReached = false;

    for (let page = 1; page <= MAX_PAGES; page += 1) {
      const doc = await readPage(page);
      pagesScanned += 1;
      const rows = extractPage(doc, page);
      const visibleCards = doc.querySelectorAll(".theme-list-main").length;
      if (visibleCards > 0 && rows.length !== visibleCards) {
        warnings.push(`第 ${page} 頁有 ${visibleCards - rows.length} 筆缺少標題、年月或有效連結`);
      }
      if (rows.length === 0) {
        if (page === 1) warnings.push("第一頁未識別到動畫目錄，頁面結構可能已變更");
        boundaryReached = true;
        break;
      }
      for (const item of rows) {
        const key = item.year * 12 + item.month;
        if (key >= startKey && key < endKey) {
          items.set(`${item.title}\n${item.href}`, item);
        }
      }
      if (rows.some((item) => item.year * 12 + item.month < startKey)) {
        boundaryReached = true;
        break;
      }
    }
    if (!boundaryReached) warnings.push(`達到 ${MAX_PAGES} 頁安全上限，尚未確認季度邊界`);
    return {
      format: FORMAT,
      schema_version: 1,
      exported_at: new Date().toISOString(),
      source_url: catalogPageUrl(1),
      quarter_year: quarter.year,
      quarter_start_month: quarter.startMonth,
      pages_scanned: pagesScanned,
      complete: warnings.length === 0,
      warnings,
      items: [...items.values()],
    };
  }

  function pushToAnimeBridge(payload) {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method: "POST",
        url: ENDPOINT,
        headers: {
          "Content-Type": "application/json",
          "X-Anime-Bridge-Bridge-Token": BRIDGE_TOKEN,
        },
        data: JSON.stringify(payload),
        timeout: 120000,
        onload(response) {
          let body;
          try { body = JSON.parse(response.responseText); }
          catch (_) { reject(new Error(`本機服務返回無法識別的回應（HTTP ${response.status}）`)); return; }
          if (response.status < 200 || response.status >= 300 || !body.ok) {
            reject(new Error(body.error || `本機服務返回 HTTP ${response.status}`));
            return;
          }
          resolve(body.result);
        },
        ontimeout() { reject(new Error("本機掃描逾時，請保持 Anime Bridge 執行後重試")); },
        onerror() { reject(new Error("無法連接本機 Anime Bridge，請先啟動程式")); },
      });
    });
  }

  if (document.getElementById(BUTTON_ID)) return;
  const button = document.createElement("button");
  button.id = BUTTON_ID;
  button.type = "button";
  button.textContent = "同步 Anime Bridge 當季目錄";
  Object.assign(button.style, {
    position: "fixed", right: "20px", bottom: "20px", zIndex: "2147483647",
    padding: "12px 16px", border: "1px solid #1f2937", borderRadius: "6px",
    background: "#f7c948", color: "#111827", font: "600 14px system-ui, sans-serif",
    cursor: "pointer",
  });

  async function synchronize({ manual = false } = {}) {
    button.disabled = true;
    button.textContent = "正在讀取公開當季目錄…";
    try {
      const payload = await collectCurrentQuarter();
      if (!payload.complete) throw new Error(payload.warnings.join("；") || "目錄讀取不完整");
      button.textContent = "正在生成候選筆記…";
      const result = await pushToAnimeBridge(payload);
      localStorage.setItem(LAST_SYNC_KEY, String(Date.now()));
      button.textContent = `已同步 ${payload.items.length} 項`;
      if (manual) alert(`Anime Bridge：已同步 ${payload.items.length} 部動畫瘋當季作品，生成 ${result.count} 個候選條目。`);
    } catch (error) {
      button.textContent = "同步失敗，點擊重試";
      if (manual) alert(`Anime Bridge 同步失敗：${error instanceof Error ? error.message : String(error)}`);
    } finally {
      button.disabled = false;
    }
  }

  button.addEventListener("click", () => synchronize({ manual: true }));
  document.body.appendChild(button);
  const lastSync = Number(localStorage.getItem(LAST_SYNC_KEY) || "0");
  if (Date.now() - lastSync >= AUTO_SYNC_INTERVAL_MS) {
    setTimeout(() => synchronize(), 800);
  }
})();
